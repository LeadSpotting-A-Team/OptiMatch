import os

from metadata import Post_Metadata
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'  #disable tensorflow logging
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0' #disable oneDNN logging
from tensorflow.python.ops.math_ops import np
import url_loader
import files_loader
from faces import *
import dataset_reader
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
metadata_module.clear_tables()
from mtcnn import MTCNN
detector = MTCNN()

url = input("Enter the url of the image: ")
try:
    post_metadata = Post_Metadata(url, None, None, None, None)
    file = url_loader.download_url_to_file(url, "sandbox")
    if url_loader.is_an_image_file(file):
        image = files_loader.load_as_rgb(file)
        faces = get_faces_coordinates_from_image_by_detector(image,detector)
        if len(faces) == 0: print("No faces found in the image")
        else: print(f"Found {len(faces)} faces in the image")
        save_faces_to_file(faces, image, "sandbox/faces", post_metadata)
    else: print("File type is not supported by the system (only images are supported)")

    os.remove(file) #remove the file after the operation is done

except Exception as e:
    print(f"Error: {e}")