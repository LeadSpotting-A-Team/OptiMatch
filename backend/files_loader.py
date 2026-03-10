import cv2
import config
def load_as_rgb(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if(img is None): 
        raise Exception(f"Failed to load image from {image_path}")
        
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) #convert bgr to rgb

def save_as_image(image_rgb, destination_path):
    result = cv2.imwrite(destination_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)) #convert rgb to bgr
    if(result == False):
        raise Exception(f"Failed to save image to {destination_path}")
    return True

def is_valid_image(image):
    if image.shape[0] < config.MIN_FACE_SIZE: return False  # height
    if image.shape[1] < config.MIN_FACE_SIZE: return False  # width
    return True


def load_video_as_rgb(video_path):
    frames = []
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():raise Exception(f"Failed to open video {video_path}")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if cap.get(cv2.CAP_PROP_POS_FRAMES) >= cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    #(CAP_PROP_POS_FRAMES) is the current frame number
                    #(CAP_PROP_FRAME_COUNT) is the total number of frames
                    #if the frame is the last frame, break
                    break 
                else:
                    #skip the broken frame
                    next_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) + 1
                    cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
                    frames.append(None) #append None to keep the same length as the frames list
            else:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
        return frames
    finally:
        if cap is not None:
            cap.release()