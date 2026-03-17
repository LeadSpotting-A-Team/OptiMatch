import os
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

# ── IVF / FAISS configuration ─────────────────────────────────────────────────

# Single source of truth for the default number of Voronoi clusters.
# All other modules (IVF.py) reference this constant so that changing one
# value here propagates everywhere without touching multiple files.
IVF_DEFAULT_NLIST: int = 100

# Active value used at runtime.  Can be overridden via the IVF_NLIST environment
# variable (e.g. IVF_NLIST=300 python simple_main.py) without editing source.
IVF_NLIST: int = int(os.environ.get("IVF_NLIST", IVF_DEFAULT_NLIST))