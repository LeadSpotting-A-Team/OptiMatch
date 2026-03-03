import cv2
def load_as_rgb(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) #convert bgr to rgb

def save_as_image(image_rgb, destination_path):
    result = cv2.imwrite(destination_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)) #convert rgb to bgr
    if(result == False):raise Exception(f"Failed to save image to {destination_path}")
    return True

def load_video_as_rgb(video_path):
    frames = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():raise Exception(f"Failed to open video {video_path}")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            if cap.get(cv2.CAP_PROP_POS_FRAMES) >= cap.get(cv2.CAP_PROP_FRAME_COUNT):
                break #if the frame is the last frame, break
            frames.append(None) #if the frame is not read, append None
        else:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
    return frames