import azure.functions as func
import logging
import json
import os
import requests
from datetime import datetime, timezone

from azure.storage.fileshare import ShareServiceClient
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

app = func.FunctionApp()

STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
FILE_SHARE_NAME           = os.environ["FILE_SHARE_NAME"]
BLOB_CONTAINER_NAME       = os.environ["BLOB_CONTAINER_NAME"]
DOC_INTELLIGENCE_ENDPOINT = os.environ["DOC_INTELLIGENCE_ENDPOINT"]
DOC_INTELLIGENCE_KEY      = os.environ["DOC_INTELLIGENCE_KEY"]
OPENAI_ENDPOINT           = os.environ["OPENAI_ENDPOINT"]
OPENAI_KEY                = os.environ["OPENAI_KEY"]
OPENAI_DEPLOYMENT_NAME    = os.environ.get("OPENAI_DEPLOYMENT_NAME", "gpt-4o")
DISCORD_WEBHOOK_URL       = os.environ.get("DISCORD_WEBHOOK_URL", "")
SLACK_WEBHOOK_URL         = os.environ.get("SLACK_WEBHOOK_URL", "")
STORAGE_ACCOUNT_NAME      = os.environ.get("STORAGE_ACCOUNT_NAME", "stbesstrongocr")

RESULTS_CONTAINER = "results"


def _blob_url(blob_name: str) -> str:
    return f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{RESULTS_CONTAINER}/{blob_name}"


# ── OCR + AI processing (Timer trigger every 5 min) ───────────────────────────

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def process_pdfs(timer: func.TimerRequest) -> None:
    logging.info("PDF processing triggered")

    share_client = ShareServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    share        = share_client.get_share_client(FILE_SHARE_NAME)
    blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    container    = blob_service.get_container_client(BLOB_CONTAINER_NAME)

    doc_client = DocumentIntelligenceClient(
        endpoint=DOC_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(DOC_INTELLIGENCE_KEY),
    )

    openai_client = AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        api_key=OPENAI_KEY,
        api_version="2024-02-01",
    )

    directory = share.get_directory_client("")
    for item in directory.list_directories_and_files():
        name = item["name"]
        if not name.lower().endswith(".pdf"):
            continue

        result_name = name.replace(".pdf", ".json")
        result_blob = container.get_blob_client(result_name)

        if result_blob.exists():
            logging.info("Skipping %s — already processed", name)
            continue

        logging.info("Processing %s", name)
        try:
            pdf_bytes = share.get_file_client(name).download_file().readall()
            final_json = _build_result(name, pdf_bytes, doc_client, openai_client)
            result_blob.upload_blob(
                json.dumps(final_json, indent=2, ensure_ascii=False),
                overwrite=True,
            )
            logging.info("Saved %s", result_name)
        except Exception as exc:
            logging.error("Failed to process %s: %s", name, exc)


def _build_result(
    file_name: str,
    pdf_bytes: bytes,
    doc_client: DocumentIntelligenceClient,
    openai_client: AzureOpenAI,
) -> dict:
    # ── Document Intelligence ─────────────────────────────────────────────────
    poller    = doc_client.begin_analyze_document(
        "prebuilt-layout",
        analyze_request=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
    )
    di_result = poller.result()

    ocr_data = {
        "page_count": len(di_result.pages) if di_result.pages else 0,
        "content":    di_result.content or "",
        "tables":     [],
        "key_value_pairs": [],
    }

    for table in di_result.tables or []:
        ocr_data["tables"].append({
            "rows": table.row_count,
            "cols": table.column_count,
            "cells": [
                {"row": c.row_index, "col": c.column_index, "text": c.content}
                for c in table.cells
            ],
        })

    for kv in di_result.key_value_pairs or []:
        if kv.key and kv.value:
            ocr_data["key_value_pairs"].append({
                "key":   kv.key.content,
                "value": kv.value.content,
            })

    # ── GPT-4o price analysis ─────────────────────────────────────────────────
    prompt = (
        "Analyze the document below and find all prices. "
        "For each price decide if it is HIGH or LOW based on context. "
        "Return ONLY valid JSON with keys: "
        "\"prices\" (list of {value, currency, context, classification}), "
        "\"highest_price\" ({value, currency, context}), "
        "\"lowest_price\" ({value, currency, context}), "
        "\"summary\" (string).\n\n"
        f"Document:\n{di_result.content[:4000]}"
    )

    response = openai_client.chat.completions.create(
        model=OPENAI_DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    price_analysis = json.loads(response.choices[0].message.content)

    return {
        "file_name":    file_name,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "ocr_result":   ocr_data,
        "ai_analysis": {
            "model":          OPENAI_DEPLOYMENT_NAME,
            "price_analysis": price_analysis,
        },
    }


# ── Notification on new result (Blob trigger) ─────────────────────────────────

@app.blob_trigger(
    arg_name="blob",
    path=f"{RESULTS_CONTAINER}/{{name}}",
    connection="AzureWebJobsStorage",
)
def notify_result(blob: func.InputStream) -> None:
    logging.info("New result blob: %s", blob.name)

    try:
        data = json.loads(blob.read())
    except Exception as exc:
        logging.error("Cannot parse result JSON: %s", exc)
        return

    file_name    = data.get("file_name", "unknown")
    processed_at = data.get("processed_at", "")
    analysis     = data.get("ai_analysis", {}).get("price_analysis", {})
    blob_name    = file_name.replace(".pdf", ".json")
    result_url   = _blob_url(blob_name)

    message = _format_message(file_name, processed_at, analysis, result_url)

    if DISCORD_WEBHOOK_URL:
        _send_discord(message)

    if SLACK_WEBHOOK_URL:
        _send_slack(message)


def _format_message(file_name: str, processed_at: str, analysis: dict, result_url: str = "") -> dict:
    highest = analysis.get("highest_price", {})
    lowest  = analysis.get("lowest_price", {})
    return {
        "file_name":     file_name,
        "processed_at":  processed_at,
        "summary":       analysis.get("summary", ""),
        "highest_price": f"{highest.get('value', '?')} {highest.get('currency', '')} — {highest.get('context', '')}",
        "lowest_price":  f"{lowest.get('value', '?')} {lowest.get('currency', '')} — {lowest.get('context', '')}",
        "result_url":    result_url,
    }


def _send_discord(message: dict) -> None:
    payload = {
        "embeds": [{
            "title":       f"PDF Processed: {message['file_name']}",
            "description": message["summary"],
            "url":         message.get("result_url", ""),
            "color":       3447003,
            "fields": [
                {"name": "Highest Price", "value": message["highest_price"],              "inline": True},
                {"name": "Lowest Price",  "value": message["lowest_price"],               "inline": True},
                {"name": "Processed At",  "value": message["processed_at"],               "inline": False},
                {"name": "Result JSON",   "value": message.get("result_url", "N/A"),      "inline": False},
            ],
        }]
    }
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    if not resp.ok:
        logging.warning("Discord notification failed: %s %s", resp.status_code, resp.text)


def _send_slack(message: dict) -> None:
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"PDF Processed: {message['file_name']}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message["summary"]},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Highest Price:*\n{message['highest_price']}"},
                    {"type": "mrkdwn", "text": f"*Lowest Price:*\n{message['lowest_price']}"},
                    {"type": "mrkdwn", "text": f"*Processed At:*\n{message['processed_at']}"},
                    {"type": "mrkdwn", "text": f"*Result JSON:*\n<{message.get('result_url', 'N/A')}|View JSON>"},
                ],
            },
        ]
    }
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    if not resp.ok:
        logging.warning("Slack notification failed: %s %s", resp.status_code, resp.text)
