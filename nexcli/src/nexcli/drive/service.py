import importlib.resources as pkg_resources
import io
import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm

# Scopes for Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Path to the credentials and token files
OAUTH_CLIENT_CREDENTIALS = pkg_resources.path(
    "nexcli", "google_oauth_client_credentials.json"
)
USER_AUTH_TOKEN = Path.home() / ".nexcli/google_drive_token.json"


# Function to extract the file ID from a Google Drive URL
def extract_file_id(url):
    match = re.search(r"/file/d/([a-zA-Z0-9_-]+)/", url)
    if match:
        return match.group(1)
    else:
        raise Exception(f"Invalid Google Drive URL: {url}")


# Function to authenticate and create a Google Drive service
def create_service():
    creds = None
    if USER_AUTH_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(USER_AUTH_TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            with OAUTH_CLIENT_CREDENTIALS as file:
                flow = InstalledAppFlow.from_client_secrets_file(file, SCOPES)
                creds = flow.run_local_server(port=0)
        USER_AUTH_TOKEN.parent.mkdir(parents=True, exist_ok=True)
        USER_AUTH_TOKEN.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


# Function to download a file from Google Drive given a shareable link
def download(url, output_file=None):
    file_id = extract_file_id(url)

    service = create_service()

    # Extract the file name from the file metadata
    file_metadata = (
        service.files().get(fileId=file_id, supportsAllDrives=True).execute()
    )
    if output_file is None:
        output_file = file_metadata.get("name", "downloaded_file")

    # Download the content
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    with tqdm(unit="B", unit_scale=True, unit_divisor=1024) as pbar:
        done = False
        last_progress = 0
        while not done:
            status, done = downloader.next_chunk()
            pbar.total = status.total_size
            pbar.update(status.resumable_progress - last_progress)
            last_progress = status.resumable_progress

    # Save to local file
    with open(output_file, "wb") as f:
        fh.seek(0)
        f.write(fh.read())

    return output_file
