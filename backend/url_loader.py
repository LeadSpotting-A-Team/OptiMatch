import requests
import os

def get_file_name_from_url(url):
    return url.split("/")[-1].split("?")[0]

def is_an_image_file(file_path):
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))

def is_a_video_file(file_path):
    return file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv'))
    
def download_url_to_file(url, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)
    file_name = get_file_name_from_url(url)
    save_path = os.path.join(destination_folder, file_name)
    
    # Define custom headers to avoid 403 Forbidden errors
    headers = {'User-Agent': 'Face-Search-Engine/1.0 (educational project)'}

    # Execute the request with headers and streaming enabled
    response = requests.get(url, stream=True, headers=headers)

    # Check if the request was successful (Status Code 200)
    if response.status_code != 200:
        # Raise an exception including the specific status code for debugging
        raise Exception(f"Failed to load URL {url} - Status Code: {response.status_code}")

    # Open the local file for writing in binary mode
    with open(save_path, 'wb') as file:
        # Iterate over the response data in 1024-byte chunks
        for chunk in response.iter_content(1024):
            if chunk:
                file.write(chunk) # Write the chunk to the local file

    return save_path