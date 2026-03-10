from mtcnn import MTCNN

DOWNLOAD_PATH = "download" #path to the download folder
FACES_OUTPUT_PATH = "faces" #path to the faces output file
METADATA_PATH = "metadata.db" #path to the metadata file
DATASET_PATH = "dataset.csv" #path to the dataset file
FACE_CONFIDENCE_THRESHOLD = 0.5 #confidence threshold for the face detection
MIN_FACE_SIZE = 64 #minimum size of the face
#detector to use for the face detection
DETECTOR : MTCNN | str = MTCNN()
EMBEDDING_MODEL : str = 'ArcFace'