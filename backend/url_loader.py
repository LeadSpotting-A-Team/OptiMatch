import files_loader as fl
import requests
import os

def get_file_name_from_url(url):
    return url.split("/")[-1]

def is_an_image_file(file_path):
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))

def is_a_video_file(file_path):
    return file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv'))
def download_url_to_file(url , destination_folder):
    os.makedirs(destination_folder, exist_ok=True)
    file_name = get_file_name_from_url(url)
    save_path = os.path.join(destination_folder, file_name)

    response = requests.get(url, stream=True)

    if response.status_code != 200: #if the response is not 200 (OK - Success), raise an exception
        raise Exception(f"Failed to load URL {url}")
    with open(save_path, 'wb') as file: #write the response to the file (flags: wb - write binary)
        for chunk in response.iter_content(1024):
            file.write(chunk)

    return save_path