"""Netlify Function - Nobar Gembira Google Sheets API

Deployed as a single function that routes based on the request path.
"""
import json
import os
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "11E7hmKvQtGMNWqSzyLK78HToDhiFgYEJ9XBchoG5c0g")


def get_sheets_service():
    """Build Sheets service from environment variables."""
    creds = Credentials.from_authorized_user_info({
        "refresh_token": os.environ.get("GOOGLE_REFRESH_TOKEN", ""),
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": SCOPES,
    })
    return build("sheets", "v4", credentials=creds)


def append_row(sheet_name, values):
    """Append a row to the specified sheet."""
    service = get_sheets_service()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    row = [timestamp] + values
    body = {"values": [row]}
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:A",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    return result.get("updates", {}).get("updatedCells", 0)


def respond(status_code, data):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(data),
    }


def handler(event, context):
    """Netlify function handler - routes based on request path."""
    method = event.get("httpMethod", "GET")
    path = event.get("path", "")
    headers = event.get("headers", {})

    # CORS preflight
    if method == "OPTIONS":
        return respond(200, {})

    # Only accept POST
    if method != "POST":
        return respond(405, {"status": "error", "message": "Method not allowed"})

    # Parse body
    try:
        body_str = event.get("body", "{}")
        if event.get("isBase64Encoded"):
            import base64
            body_str = base64.b64decode(body_str).decode("utf-8")
        data = json.loads(body_str)
    except (json.JSONDecodeError, TypeError):
        return respond(400, {"status": "error", "message": "Invalid JSON body"})

    try:
        if path.endswith("/api/daftar-hadir"):
            cells = append_row("daftar hadir", [
                data.get("nama", ""),
                data.get("sap", ""),
                data.get("unit_kerja", ""),
            ])
            return respond(200, {"status": "ok", "cells": cells})

        elif path.endswith("/api/tebak-skor"):
            cells = append_row("tebakskor", [
                data.get("nama", ""),
                data.get("sap", ""),
                data.get("unit_kerja", ""),
                data.get("juara", ""),
                str(data.get("skor_argentina", "")),
                str(data.get("skor_spanyol", "")),
            ])
            return respond(200, {"status": "ok", "cells": cells})

        else:
            return respond(404, {"status": "error", "message": "Endpoint not found"})

    except Exception as e:
        return respond(500, {"status": "error", "message": str(e)})
