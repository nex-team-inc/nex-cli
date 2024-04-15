def is_google_drive_uri(uri: str) -> bool:
    return uri.startswith("https://drive.google.com/")