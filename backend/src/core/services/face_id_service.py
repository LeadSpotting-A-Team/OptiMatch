import hashlib


# Generates a deterministic, unique face identifier from its origin media URL,
# the face's position index within a frame, and the frame index within the media.
# Returns a hex-digest string in the format: <sha256_of_url>_<face_index>_<frame_index>.
def generate_face_id(media_url: str, face_index: int, frame_index: int) -> str:
    url_hash = hashlib.sha256(media_url.encode()).hexdigest()
    return f"{url_hash}_{face_index}_{frame_index}"
