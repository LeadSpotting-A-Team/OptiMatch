import os
from mtcnn import MTCNN
import url_loader
import files_loader
from faces import *
import dataset_reader
#### WE NEED TO MOVE TO [ DeepFace ] library for face detection and embedding
#main function

detector = MTCNN()
posts_metadata = dataset_reader.read_dataset_as_csv("sandbox/dataset.csv")
posts_metadata_count = 0
for post_metadata in posts_metadata:
    url = post_metadata.get_media_url()
    try:
        file = url_loader.download_url_to_file(url, "sandbox")
        if url_loader.is_an_image_file(file):
            image = files_loader.load_as_rgb(file)
            faces = get_faces_coordinates_from_image(image, detector)
            if len(faces) == 0: print("No faces found in the image")
            save_faces_to_file(faces, image, "sandbox/faces", post_metadata)
            posts_metadata_count += 1
        else: print("File type is not supported by the system (only images are supported)")

        os.remove(file) #remove the file after the operation is done

    except Exception as e:
        print(f"Error: {e}")
print(f"Processed {posts_metadata_count} out of {len(posts_metadata)} posts.")