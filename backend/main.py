import os
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
from mtcnn import MTCNN
warnings.filterwarnings('ignore', category=DeprecationWarning)

import Face_Harvester
import Digital_Identity


metadata_module.clear_tables()
detector = MTCNN()

#need to check difrent way to generate the face id
#we can use the face coordinates to generate a unique id

posts_metadata = dataset_reader.read_dataset_as_csv("sandbox/dataset.csv")
posts_metadata_count = 0
for post_metadata in posts_metadata:
    url = post_metadata.get_media_url()
    try:
        file = url_loader.download_url_to_file(url, "sandbox")
        if url_loader.is_an_image_file(file):
            image = files_loader.load_as_rgb(file)
            faces = Face_Harvester.Harveste_Image(image)
            if len(faces) == 0: print("No faces found in the image")
            Face_Harvester.save_faces_to_path(faces, image, "sandbox/faces", post_metadata)
            posts_metadata_count += 1
        else: print("File type is not supported by the system (only images are supported)")

        os.remove(file) #remove the file after the operation is done

    except Exception as e:
        print(f"Error: {e}")
print(f"Processed {posts_metadata_count} out of {len(posts_metadata)} posts.")