import sqlite3
import config
import Cropped_Face
#table name for the harvested faces to post id relationship
HARVESTED_FACES_TABLE_NAME = 'harvested_faces_TO_post_id' 
#table name for the posts metadata
POSTS_METADATA_TABLE_NAME = 'posts_metadata'

class Post_Metadata:
    def __init__(self, post_id , media_url , link_to_post , timestamp , platform):
        self.post_id = post_id
        self.media_url = media_url
        self.link_to_post = link_to_post
        self.timestamp = timestamp
        self.platform = platform

    def get_post_id(self):
        return self.post_id

    def get_media_url(self):
        return self.media_url

    def get_timestamp(self):
        return self.timestamp

    def get_platform(self):
        return self.platform

    def get_link_to_post(self):
        return self.link_to_post


def clear_tables() -> None:
    connection = None
    try:
        connection = sqlite3.connect(config.METADATA_PATH)
        cursor = connection.cursor()
        cursor.execute(f'''
            DROP TABLE IF EXISTS {POSTS_METADATA_TABLE_NAME}
        ''')
        cursor.execute(f'''
            DROP TABLE IF EXISTS {HARVESTED_FACES_TABLE_NAME}
        ''')
        connection.commit()
    finally:
        if connection: connection.close()

def link_harvested_faces_to_post(harvested_faces_id: str, post_id: str, cropped_face: Cropped_Face.CroppedFace):
    landmarks = cropped_face.get_landmarks()
    le = landmarks.get('left_eye', (None, None))
    re = landmarks.get('right_eye', (None, None))
    no = landmarks.get('nose', (None, None))
    ml = landmarks.get('mouth_left', (None, None))
    mr = landmarks.get('mouth_right', (None, None))
    connection = None
    try:
        connection = sqlite3.connect(config.METADATA_PATH)
        cursor = connection.cursor()
        cursor.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {HARVESTED_FACES_TABLE_NAME} 
            (
                harvested_faces_id TEXT PRIMARY KEY,
                post_id TEXT,
                left_eye_x REAL, left_eye_y REAL,
                right_eye_x REAL, right_eye_y REAL,
                nose_x REAL, nose_y REAL,
                mouth_left_x REAL, mouth_left_y REAL,
                mouth_right_x REAL, mouth_right_y REAL,
                FOREIGN KEY (post_id) REFERENCES {POSTS_METADATA_TABLE_NAME}(post_id)
            )
            '''
        )
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_post_id ON {HARVESTED_FACES_TABLE_NAME} (post_id)')
        cursor.execute(
            f'''
            INSERT OR REPLACE INTO {HARVESTED_FACES_TABLE_NAME}
            (harvested_faces_id, post_id, left_eye_x, left_eye_y, right_eye_x, right_eye_y, 
             nose_x, nose_y, mouth_left_x, mouth_left_y, mouth_right_x, mouth_right_y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (harvested_faces_id, post_id,
             le[0], le[1], re[0], re[1], no[0], no[1], ml[0], ml[1], mr[0], mr[1])
        )
        connection.commit()
    finally:
        if connection:
            connection.close()

def save_post_metadata(posts_metadata : Post_Metadata):
    connection = None
    try:
        connection = sqlite3.connect(config.METADATA_PATH)
        cursor = connection.cursor()
        # create table if not exists
        cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS {POSTS_METADATA_TABLE_NAME}
        (
            post_id TEXT PRIMARY KEY,
            media_url TEXT,
            link_to_post TEXT,
            timestamp TEXT,
            platform TEXT
        )
        ''')

        # insert or replace record
        cursor.execute(
        f'''
        INSERT OR REPLACE INTO {POSTS_METADATA_TABLE_NAME}
        (post_id, media_url, link_to_post, timestamp, platform)
        VALUES (?, ?, ?, ?, ?)
        ''', 
        (
        posts_metadata.get_post_id(),
        posts_metadata.get_media_url(),
        posts_metadata.get_link_to_post(),
        posts_metadata.get_timestamp(),
        posts_metadata.get_platform(),
        )
        )
        connection.commit()
    finally:
        if connection: connection.close()


def get_post_by_face_id(face_id: str) -> "Post_Metadata | None":
    """Fetch full post metadata for a face_id via JOIN. Returns None if not found."""
    connection = None
    try:
        connection = sqlite3.connect(config.METADATA_PATH)
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT p.post_id, p.media_url, p.link_to_post, p.timestamp, p.platform
            FROM {HARVESTED_FACES_TABLE_NAME} h
            JOIN {POSTS_METADATA_TABLE_NAME} p ON h.post_id = p.post_id
            WHERE h.harvested_faces_id = ?
            """,
            (face_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Post_Metadata(
            post_id=row[0],
            media_url=row[1],
            link_to_post=row[2],
            timestamp=row[3],
            platform=row[4],
        )
    finally:
        if connection:
            connection.close()


def add_post_dynamic(post_metadata: Post_Metadata):
    connection = None

    # Define SQL type mapping based on Python types
    SQL_TYPES = {
        int: 'INTEGER',
        float: 'REAL',
        str: 'TEXT',
        bool: 'INTEGER'
    }
    
    # Extract attributes directly from the object
    post_fields = post_metadata.__dict__
    
    # Build dynamic column definitions for CREATE TABLE
    col_definitions = []
    for key, value in post_fields.items():
        sql_type = SQL_TYPES.get(type(value), 'TEXT')
        # Define post_id as the PRIMARY KEY
        if key == 'post_id':
            col_definitions.append(f"{key} {sql_type} PRIMARY KEY")
        else:
            col_definitions.append(f"{key} {sql_type}")
    
    create_cols_str = ", ".join(col_definitions)
    
    # Prepare column names and placeholders for INSERT
    columns = ", ".join(post_fields.keys())
    placeholders = ", ".join(["?"] * len(post_fields))

    # Establish connection using context manager
    with sqlite3.connect(config.METADATA_PATH) as connection:
        cursor = connection.cursor()

        # Create table with dynamic schema
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {POSTS_METADATA_TABLE_NAME} ({create_cols_str})")

        # Execute INSERT OR REPLACE with values extracted from __dict__
        insert_query = f"INSERT OR REPLACE INTO {POSTS_METADATA_TABLE_NAME} ({columns}) VALUES ({placeholders})"
        cursor.execute(insert_query, tuple(post_fields.values()))
        
        # Commit changes to the database
        connection.commit()
