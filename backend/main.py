import os
from mtcnn import MTCNN
import url_loader
import files_loader
from faces import *
#### WE NEED TO MOVE TO [ DeepFace ] library for face detection and embedding
#main function

detector = MTCNN()
while True:
    url = input("Enter the URL of the image to download (type 'exit' to exit): ")
    if(url == "exit"): break

    try:
        file = url_loader.download_url_to_file(url, "sandbox")
        if url_loader.is_a_video_file(file):
            frames = files_loader.load_video_as_rgb(file)
            for frame in frames:
                faces = get_faces_coordinates_from_image(frame, detector)
        if url_loader.is_an_image_file(file):
            image = files_loader.load_as_rgb(file)
            faces = get_faces_coordinates_from_image(image, detector)
            if len(faces) == 0: print("No faces found in the image")
            save_faces_to_file(faces, image, "sandbox/faces")
        else: print("File type is not supported by the system (only images are supported)")

        os.remove(file) #remove the file after the operation is done

    except Exception as e:
        print(f"Error: {e}")