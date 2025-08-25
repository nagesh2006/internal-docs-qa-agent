# fetch_gdocs.py
import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

# Load credentials either from env var or file
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")  # whole JSON as string (for Hugging Face)
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH", "./gcreds.json")  # fallback local file


def get_credentials():
    """Return Google service account credentials."""
    if GOOGLE_CREDS_JSON:
        creds_dict = json.loads(GOOGLE_CREDS_JSON)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/documents.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
        return creds

    elif GOOGLE_CREDS_PATH and os.path.exists(GOOGLE_CREDS_PATH):
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDS_PATH,
            scopes=[
                "https://www.googleapis.com/auth/documents.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
        return creds

    else:
        raise ValueError("❌ No valid Google credentials found. Set GOOGLE_CREDS_JSON or GOOGLE_CREDS_PATH.")


def fetch_doc_content(doc_id, docs_service):
    """Fetch plain text from a Google Doc by ID."""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = []

    def read_elements(elements):
        text_out = []
        for elem in elements:
            if "paragraph" in elem:
                for part in elem["paragraph"].get("elements", []):
                    if "textRun" in part:
                        txt = part["textRun"].get("content", "")
                        if txt.strip():
                            text_out.append(txt)
            elif "table" in elem:
                for row in elem["table"].get("tableRows", []):
                    for cell in row.get("tableCells", []):
                        text_out.extend(read_elements(cell.get("content", [])))
            elif "tableOfContents" in elem:
                text_out.extend(read_elements(elem["tableOfContents"].get("content", [])))
        return text_out

    body = doc.get("body", {}).get("content", [])
    content.extend(read_elements(body))
    return "".join(content).strip()


def fetch_all_shared_docs():
    """Fetch all Google Docs shared with the service account."""
    creds = get_credentials()

    # Build services
    drive_service = build("drive", "v3", credentials=creds)
    docs_service = build("docs", "v1", credentials=creds)

    # Search all Google Docs (files of type 'document') that service account has access to
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.document'",
        pageSize=50,
        fields="files(id, name)",
    ).execute()

    files = results.get("files", [])
    docs = []

    for f in files:
        doc_id = f["id"]
        name = f["name"]
        try:
            print(f"📄 Fetching Google Doc: {name} ({doc_id})")
            text = fetch_doc_content(doc_id, docs_service)
            if text:
                docs.append({"id": doc_id, "name": name, "text": text})
            else:
                print(f"⚠️ Google Doc {name} was empty, skipping.")
        except Exception as e:
            print(f"⚠️ Failed to fetch Google Doc {name}: {e}")

    return docs


if __name__ == "__main__":
    all_docs = fetch_all_shared_docs()
    print(f"✅ Fetched {len(all_docs)} documents")
