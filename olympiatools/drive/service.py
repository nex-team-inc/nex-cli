from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pathlib import Path
import importlib.resources as pkg_resources
import re

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Path to the credentials and token files
CREDENTIALS_FILE = pkg_resources.path('olympiatools', 'config/google_oauth_client_credentials.json')
TOKEN_FILE = Path.home() / '.olympiatools/google_drive_token.json'

# Function to extract the file ID from a Google Drive URL
def extract_file_id(url):
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)/', url)
    return match.group(1) if match else None

# Function to authenticate and create a Google Drive service
def create_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)
