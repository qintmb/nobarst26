#!/usr/bin/env python3
"""Nobar Gembira - Backend Server"""
import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

HERMES_HOME = Path(os.environ.get("HOME", "/home/prsementonasa")) / ".hermes"
sys.path.insert(0, str(HERMES_HOME / "profiles/noxia/skills/productivity/google-workspace/scripts"))

SPREADSHEET_ID = "11E7hmKvQtGMNWqSzyLK78HToDhiFgYEJ9XBchoG5c0g"
TOKEN_PATH = HERMES_HOME / "google_token.json"


def get_sheets_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    return build("sheets", "v4", credentials=creds)


def append_to_sheet(sheet_name, values):
    """Append a row to the specified sheet."""
    service = get_sheets_service()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


class NobarHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length else {}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            if parsed.path == "/api/daftar-hadir":
                cells = append_to_sheet("daftar hadir", [
                    body.get("nama", ""),
                    body.get("sap", ""),
                    body.get("unit_kerja", ""),
                ])
                response = {"status": "ok", "cells": cells}

            elif parsed.path == "/api/tebak-skor":
                cells = append_to_sheet("tebakskor", [
                    body.get("nama", ""),
                    body.get("sap", ""),
                    body.get("unit_kerja", ""),
                    body.get("juara", ""),
                    str(body.get("skor_argentina", "")),
                    str(body.get("skor_spanyol", "")),
                ])
                response = {"status": "ok", "cells": cells}

            else:
                response = {"status": "error", "message": "Unknown endpoint"}

        except Exception as e:
            response = {"status": "error", "message": str(e)}

        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]} {args[2]}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("0.0.0.0", port), NobarHandler)
    print(f"🚀 Nobar server running at http://localhost:{port}")
    print(f"📊 Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
