import json
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# Patch env vars before importing the module
ENV_VARS = {
    "STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=dGVzdA==;EndpointSuffix=core.windows.net",
    "FILE_SHARE_NAME":           "pdf-input",
    "BLOB_CONTAINER_NAME":       "results",
    "DOC_INTELLIGENCE_ENDPOINT": "https://test.cognitiveservices.azure.com/",
    "DOC_INTELLIGENCE_KEY":      "test-doc-key",
    "OPENAI_API_KEY":            "sk-test-openai-key",
    "OPENAI_DEPLOYMENT_NAME":    "gpt-4o",
    "DISCORD_WEBHOOK_URL":       "https://discord.com/api/webhooks/test",
    "SLACK_WEBHOOK_URL":         "https://hooks.slack.com/services/test",
}


@patch.dict("os.environ", ENV_VARS)
class TestFormatMessage(unittest.TestCase):
    def setUp(self):
        import importlib
        import sys
        for mod in list(sys.modules.keys()):
            if "function_app" in mod:
                del sys.modules[mod]

        with patch("azure.functions.FunctionApp"):
            import function_app as fa
            self.fa = fa

    def test_format_message_full(self):
        analysis = {
            "summary":       "Invoice with two prices",
            "highest_price": {"value": 999.99, "currency": "USD", "context": "Total"},
            "lowest_price":  {"value": 4.99,   "currency": "USD", "context": "Unit"},
        }
        result = self.fa._format_message("invoice.pdf", "2025-01-01T00:00:00+00:00", analysis)

        self.assertEqual(result["file_name"],    "invoice.pdf")
        self.assertIn("999.99",                  result["highest_price"])
        self.assertIn("4.99",                    result["lowest_price"])
        self.assertEqual(result["summary"],      "Invoice with two prices")

    def test_format_message_missing_prices(self):
        result = self.fa._format_message("doc.pdf", "2025-01-01T00:00:00+00:00", {})

        self.assertIn("?", result["highest_price"])
        self.assertIn("?", result["lowest_price"])

    def test_format_message_empty_summary(self):
        result = self.fa._format_message("doc.pdf", "", {})
        self.assertEqual(result["summary"], "")


@patch.dict("os.environ", ENV_VARS)
class TestSendDiscord(unittest.TestCase):
    def setUp(self):
        import sys
        for mod in list(sys.modules.keys()):
            if "function_app" in mod:
                del sys.modules[mod]

        with patch("azure.functions.FunctionApp"):
            import function_app as fa
            self.fa = fa

    @patch("requests.post")
    def test_discord_called_with_embed(self, mock_post):
        mock_post.return_value = MagicMock(ok=True)
        message = {
            "file_name":    "test.pdf",
            "summary":      "Test",
            "highest_price": "100 USD — Total",
            "lowest_price":  "10 USD — Unit",
            "processed_at": "2025-01-01T00:00:00+00:00",
        }
        self.fa._send_discord(message)

        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("embeds", payload)
        self.assertEqual(payload["embeds"][0]["title"], "PDF Processed: test.pdf")

    @patch("requests.post")
    def test_discord_logs_warning_on_failure(self, mock_post):
        mock_post.return_value = MagicMock(ok=False, status_code=400, text="Bad Request")
        message = {
            "file_name":    "test.pdf",
            "summary":      "",
            "highest_price": "?  — ",
            "lowest_price":  "?  — ",
            "processed_at": "",
        }
        # Should not raise
        self.fa._send_discord(message)
        mock_post.assert_called_once()


@patch.dict("os.environ", ENV_VARS)
class TestSendSlack(unittest.TestCase):
    def setUp(self):
        import sys
        for mod in list(sys.modules.keys()):
            if "function_app" in mod:
                del sys.modules[mod]

        with patch("azure.functions.FunctionApp"):
            import function_app as fa
            self.fa = fa

    @patch("requests.post")
    def test_slack_called_with_blocks(self, mock_post):
        mock_post.return_value = MagicMock(ok=True)
        message = {
            "file_name":    "test.pdf",
            "summary":      "Test summary",
            "highest_price": "100 USD — Total",
            "lowest_price":  "10 USD — Unit",
            "processed_at": "2025-01-01T00:00:00+00:00",
        }
        self.fa._send_slack(message)

        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("blocks", payload)

        header_block = payload["blocks"][0]
        self.assertEqual(header_block["type"], "header")
        self.assertIn("test.pdf", header_block["text"]["text"])


@patch.dict("os.environ", ENV_VARS)
class TestBuildResult(unittest.TestCase):
    def setUp(self):
        import sys
        for mod in list(sys.modules.keys()):
            if "function_app" in mod:
                del sys.modules[mod]

        with patch("azure.functions.FunctionApp"):
            import function_app as fa
            self.fa = fa

    def _make_di_result(self):
        result = MagicMock()
        result.content = "Invoice\nTotal: $100\nUnit: $10"
        result.pages   = [MagicMock()]
        result.tables  = []
        result.key_value_pairs = [
            MagicMock(key=MagicMock(content="Total"), value=MagicMock(content="$100")),
            MagicMock(key=MagicMock(content="Unit"),  value=MagicMock(content="$10")),
        ]
        return result

    def _make_openai_response(self):
        price_data = {
            "prices":        [{"value": 100, "currency": "USD", "context": "Total",  "classification": "HIGH"},
                              {"value": 10,  "currency": "USD", "context": "Unit",   "classification": "LOW"}],
            "highest_price": {"value": 100, "currency": "USD", "context": "Total"},
            "lowest_price":  {"value": 10,  "currency": "USD", "context": "Unit"},
            "summary":       "Two prices found",
        }
        msg      = MagicMock()
        msg.content = json.dumps(price_data)
        choice   = MagicMock()
        choice.message = msg
        response = MagicMock()
        response.choices = [choice]
        return response

    def test_build_result_structure(self):
        di_client     = MagicMock()
        openai_client = MagicMock()

        di_client.begin_analyze_document.return_value.result.return_value = self._make_di_result()
        openai_client.chat.completions.create.return_value = self._make_openai_response()

        result = self.fa._build_result("invoice.pdf", b"%PDF-fake", di_client, openai_client)

        self.assertEqual(result["file_name"], "invoice.pdf")
        self.assertIn("processed_at",         result)
        self.assertIn("ocr_result",           result)
        self.assertIn("ai_analysis",          result)

        ocr = result["ocr_result"]
        self.assertEqual(ocr["page_count"], 1)
        self.assertEqual(len(ocr["key_value_pairs"]), 2)

        ai = result["ai_analysis"]
        self.assertEqual(ai["model"], "gpt-4o")
        self.assertIn("price_analysis", ai)
        self.assertEqual(ai["price_analysis"]["summary"], "Two prices found")


if __name__ == "__main__":
    unittest.main()
