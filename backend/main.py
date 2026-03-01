from mtcnn import MTCNN
import cv2
from faces import *

#main function


# 1. טעינת התמונה (מומלץ להשתמש ב-OpenCV)
img = cv2.cvtColor(cv2.imread("sandbox/image.jpg"), cv2.COLOR_BGR2RGB)

# 2. יצירת האובייקט של המזהה
detector = MTCNN()

faces = get_faces_from_image(img , detector)
save_faces_to_file(faces , img , "sandbox/faces/")