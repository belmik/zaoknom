import json
import os
from typing import BinaryIO, ContextManager

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
GOOGLE_SERVICE_ACCOUNT_CREDS = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDS"))
GDRIVE_CREDENTIALS = service_account.Credentials.from_service_account_info(
    GOOGLE_SERVICE_ACCOUNT_CREDS, scopes=SCOPES
)
GDRIVE_BACKUP_FOLDER_ID = os.getenv("GDRIVE_BACKUP_FOLDER_ID")


def get_service(gdrive_credentials=GDRIVE_CREDENTIALS) -> ContextManager:
    return build("drive", "v3", credentials=gdrive_credentials)


def upload_file(name: str, bytes_stream: BinaryIO, file_mimetype: str) -> tuple:
    file_metadata = {"name": name, "parents": [GDRIVE_BACKUP_FOLDER_ID]}
    with get_service() as drive_service:
        media = MediaIoBaseUpload(bytes_stream, mimetype=file_mimetype)
        response = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id, name, size")
            .execute()
        )

    return tuple(response.values())
