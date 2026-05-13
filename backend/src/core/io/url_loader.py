from __future__ import annotations

import os

import requests


# Extracts the bare filename from a URL by stripping the path and query string.
# For example: "https://cdn.example.com/img.jpg?v=2" → "img.jpg".
def get_filename_from_url(url: str) -> str:
    filename = url.split("/")[-1].split("?")[0]
    if not '.' in filename:
        filename = filename + ".jpg"
    return filename


# Returns True when the file path ends with a known image extension.
def is_image_file(file_path: str) -> bool:
    return file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"))


# Returns True when the file path ends with a known video extension.
def is_video_file(file_path: str) -> bool:
    return file_path.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".wmv"))


# Downloads the content at url into destination_folder and returns the local
# file path.  The folder is created if it does not already exist.
# Raises an exception when the HTTP response status is not 200.
def download_to_temp_file(url: str, destination_folder: str) -> str:
    os.makedirs(destination_folder, exist_ok=True)
    file_name = get_filename_from_url(url)
    save_path = os.path.join(destination_folder, file_name)

    headers = {"User-Agent": "Face-Search-Engine/1.0 (educational project)"}
    response = requests.get(url, stream=True, headers=headers)

    if response.status_code != 200:
        os.remove(save_path)
        raise IOError(
            f"Failed to download URL {url} — HTTP {response.status_code}"
        )

    with open(save_path, "wb") as file:
        for chunk in response.iter_content(1024):
            if chunk:
                file.write(chunk)

    return save_path
