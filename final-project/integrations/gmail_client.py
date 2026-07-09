"""Gmail API wrapper — send, thread-aware reply, list unread, read a message.

Pure MIME/parse helpers are separated from the network calls so the drafting and
formatting logic is unit-testable without credentials.
"""
import base64
from email.message import EmailMessage
from typing import Optional


def build_service(creds):
    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds)


def build_mime(to: list[str], subject: str, body: str,
               cc: Optional[list[str]] = None,
               attachments: Optional[list[str]] = None) -> str:
    """Build a base64url-encoded MIME message (raw form Gmail expects)."""
    msg = EmailMessage()
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.set_content(body)
    for path in attachments or []:
        with open(path, "rb") as fh:
            data = fh.read()
        import mimetypes
        ctype, _ = mimetypes.guess_type(path)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        import os
        msg.add_attachment(data, maintype=maintype, subtype=subtype,
                           filename=os.path.basename(path))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def send_message(service, to, subject, body, cc=None, attachments=None,
                 thread_id=None) -> dict:
    raw = build_mime(to, subject, body, cc, attachments)
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id
    return service.users().messages().send(userId="me", body=payload).execute()


def list_unread(service, max_results: int = 10) -> list[dict]:
    resp = service.users().messages().list(
        userId="me", q="is:unread", maxResults=max_results
    ).execute()
    out = []
    for ref in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        out.append({"id": msg["id"], "thread_id": msg.get("threadId"),
                    "from": headers.get("From", ""), "subject": headers.get("Subject", ""),
                    "snippet": msg.get("snippet", "")})
    return out


def get_thread_text(service, thread_id: str) -> str:
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    parts = []
    for msg in thread.get("messages", []):
        parts.append(msg.get("snippet", ""))
    return "\n\n".join(parts)
