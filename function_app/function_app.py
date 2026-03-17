import azure.functions as func
import logging
import json
import os
import re
import requests
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI

app = func.FunctionApp()

STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
BLOB_CONTAINER_NAME       = os.environ["BLOB_CONTAINER_NAME"]
DOC_INTELLIGENCE_ENDPOINT = os.environ["DOC_INTELLIGENCE_ENDPOINT"]
DOC_INTELLIGENCE_KEY      = os.environ["DOC_INTELLIGENCE_KEY"]
OPENAI_API_KEY            = os.environ["OPENAI_API_KEY"]
OPENAI_DEPLOYMENT_NAME    = os.environ.get("OPENAI_DEPLOYMENT_NAME", "gpt-4o")
DISCORD_WEBHOOK_URL       = os.environ.get("DISCORD_WEBHOOK_URL", "")
SLACK_WEBHOOK_URL         = os.environ.get("SLACK_WEBHOOK_URL", "")
STORAGE_ACCOUNT_NAME      = os.environ.get("STORAGE_ACCOUNT_NAME", "stbesstrongocrdev")

PDF_INPUT_CONTAINER = "pdf-input"
RESULTS_CONTAINER   = "results"


def _blob_url(blob_name: str) -> str:
    return f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{RESULTS_CONTAINER}/{blob_name}"


def _rule_based_price_analysis(content: str) -> dict:
    """Fallback when OpenAI API fails (quota, rate limit)."""
    pattern = re.compile(
        r'(?P<cur1>\$|€|£|USD|EUR|UAH|GBP)?\s*'
        r'(?P<val>\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)'
        r'\s*(?P<cur2>USD|EUR|UAH|GBP|\$|€|£)?',
        re.IGNORECASE,
    )
    prices = []
    for m in pattern.finditer(content):
        raw = m.group("val").replace(",", "").replace(" ", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        if val < 1:
            continue
        currency = (m.group("cur1") or m.group("cur2") or "USD").strip()
        s, e = max(0, m.start() - 50), min(len(content), m.end() + 50)
        ctx = content[s:e].replace("\n", " ").strip()
        prices.append({"value": val, "currency": currency, "context": ctx})

    if not prices:
        return {"prices": [], "highest_price": {}, "lowest_price": {},
                "summary": "No prices found.", "method": "rule-based"}

    median = sorted(prices, key=lambda p: p["value"])[len(prices) // 2]["value"]
    for p in prices:
        p["classification"] = (
            "HIGH"   if p["value"] >= median * 1.5 else
            "LOW"    if p["value"] <= median * 0.5 else "MEDIUM"
        )
    highest = max(prices, key=lambda p: p["value"])
    lowest  = min(prices, key=lambda p: p["value"])
    return {
        "prices":        prices,
        "highest_price": highest,
        "lowest_price":  lowest,
        "summary":       (f"Found {len(prices)} price(s). "
                          f"Highest: {highest['value']} {highest.get('currency', '')}. "
                          f"Lowest: {lowest['value']} {lowest.get('currency', '')}."),
        "method": "rule-based (OpenAI unavailable)",
    }


# ── OCR + AI processing — Blob trigger on pdf-input container ─────────────────
# Fires instantly when a PDF is uploaded to the pdf-input blob container.

@app.blob_trigger(
    arg_name="input_blob",
    path=f"{PDF_INPUT_CONTAINER}/{{name}}",
    connection="AzureWebJobsStorage",
)
def process_pdf_blob(input_blob: func.InputStream) -> None:
    name = input_blob.name.split("/")[-1]
    logging.info("Blob trigger fired for: %s", name)

    if not name.lower().endswith(".pdf"):
        logging.info("Not a PDF, skipping: %s", name)
        return

    blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    results      = blob_service.get_container_client(RESULTS_CONTAINER)
    result_name  = name.replace(".pdf", ".json")
    result_blob  = results.get_blob_client(result_name)

    if result_blob.exists():
        logging.info("Already processed, skipping: %s", name)
        return

    doc_client = DocumentIntelligenceClient(
        endpoint=DOC_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(DOC_INTELLIGENCE_KEY),
    )
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        pdf_bytes  = input_blob.read()
        final_json = _build_result(name, pdf_bytes, doc_client, openai_client)
        result_blob.upload_blob(
            json.dumps(final_json, indent=2, ensure_ascii=False),
            overwrite=True,
        )
        logging.info("Saved result: %s", result_name)
    except Exception as exc:
        logging.error("Failed to process %s: %s", name, exc)


def _build_result(
    file_name: str,
    pdf_bytes: bytes,
    doc_client: DocumentIntelligenceClient,
    openai_client: OpenAI,
) -> dict:
    # ── Document Intelligence ─────────────────────────────────────────────────
    poller    = doc_client.begin_analyze_document(
        "prebuilt-layout",
        body=AnalyzeDocumentRequest(bytes_source=pdf_bytes),
    )
    di_result = poller.result()

    ocr_data = {
        "page_count":      len(di_result.pages) if di_result.pages else 0,
        "content":         di_result.content or "",
        "tables":          [],
        "key_value_pairs": [],
    }
    for table in di_result.tables or []:
        ocr_data["tables"].append({
            "rows":  table.row_count,
            "cols":  table.column_count,
            "cells": [{"row": c.row_index, "col": c.column_index, "text": c.content}
                      for c in table.cells],
        })
    for kv in di_result.key_value_pairs or []:
        if kv.key and kv.value:
            ocr_data["key_value_pairs"].append({"key": kv.key.content, "value": kv.value.content})

    # ── GPT-4o price analysis (fallback to rule-based if OpenAI fails) ────────
    ocr_content = di_result.content or ""
    prompt = (
        "Analyze the document below and find all prices. "
        "For each price decide if it is HIGH or LOW based on context. "
        "Return ONLY valid JSON with keys: "
        "\"prices\" (list of {value, currency, context, classification}), "
        "\"highest_price\" ({value, currency, context}), "
        "\"lowest_price\" ({value, currency, context}), "
        "\"summary\" (string).\n\n"
        f"Document:\n{ocr_content[:4000]}"
    )
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        price_analysis = json.loads(response.choices[0].message.content)
    except Exception as exc:
        logging.warning("OpenAI failed (%s), using rule-based fallback", exc)
        price_analysis = _rule_based_price_analysis(ocr_content)

    return {
        "file_name":    file_name,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "ocr_result":   ocr_data,
        "ai_analysis": {
            "model":          OPENAI_DEPLOYMENT_NAME,
            "price_analysis": price_analysis,
        },
    }


# ── Notification — Blob trigger on results container ─────────────────────────

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
    result_url   = _blob_url(file_name.replace(".pdf", ".json"))
    message      = _format_message(file_name, processed_at, analysis, result_url)

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
                {"name": "Highest Price", "value": message["highest_price"], "inline": True},
                {"name": "Lowest Price",  "value": message["lowest_price"],  "inline": True},
                {"name": "Processed At",  "value": message["processed_at"],  "inline": False},
                {"name": "Result JSON",   "value": message.get("result_url", "N/A"), "inline": False},
            ],
        }]
    }
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    if not resp.ok:
        logging.warning("Discord notification failed: %s %s", resp.status_code, resp.text)


def _send_slack(message: dict) -> None:
    payload = {
        "blocks": [
            {"type": "header",
             "text": {"type": "plain_text", "text": f"PDF Processed: {message['file_name']}"}},
            {"type": "section",
             "text": {"type": "mrkdwn", "text": message["summary"]}},
            {"type": "section",
             "fields": [
                 {"type": "mrkdwn", "text": f"*Highest Price:*\n{message['highest_price']}"},
                 {"type": "mrkdwn", "text": f"*Lowest Price:*\n{message['lowest_price']}"},
                 {"type": "mrkdwn", "text": f"*Processed At:*\n{message['processed_at']}"},
                 {"type": "mrkdwn", "text": f"*Result JSON:*\n<{message.get('result_url', 'N/A')}|View JSON>"},
             ]},
        ]
    }
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    if not resp.ok:
        logging.warning("Slack notification failed: %s %s", resp.status_code, resp.text)
