class Face_Coordinates:
    def __init__(self, face_x, face_y, face_width, face_height):
        self.face_x = face_x
        self.face_y = face_y
        self.face_width = face_width
        self.face_height = face_height

    def get_left_upper_x(self):
        return self.face_x
    def get_left_upper_y(self):
        return self.face_y
    def get_right_lower_x(self):
        return self.face_x + self.face_width
    def get_right_lower_y(self):
        return self.face_y + self.face_height


def get_faces_from_image(image , detector):
    results = detector.detect_faces(image)
    faces = []
    for face in results:
        fc = Face_Coordinates(face['box'][0], face['box'][1], face['box'][2], face['box'][3])
        faces.append(fc)
    return faces

def save_faces_to_file(faces , image , path):
    i = 0
    for face in faces:
        face_img = image[face.get_left_upper_y():face.get_right_lower_y(), 
                        face.get_left_upper_x():face.get_right_lower_x()]
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)#convert rgb to bgr
        cv2.imwrite(f"{path}/face_{i}.jpg", face_img)#save the face image
        i += 1


