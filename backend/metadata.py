import sqlite3

METADATA_PATH = 'sandbox/metadata.db' #path to the face metadata database

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


def link_face_to_post(face_id : str, post_id : str):
    connection = sqlite3.connect(METADATA_PATH)
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_id_TO_post_id (
            face_id      TEXT PRIMARY KEY,
            post_id      TEXT ,
            FOREIGN KEY (post_id) REFERENCES posts_metadata(post_id)
        )
    ''')

    cursor.execute('''
        INSERT OR REPLACE INTO face_id_TO_post_id
        (face_id, post_id)
        VALUES (?, ?)
    ''', (face_id, post_id))
    connection.commit()

def save_post_metadata(posts_metadata : Post_Metadata):
    connection = sqlite3.connect(METADATA_PATH)
    cursor = connection.cursor()

    # create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts_metadata (
            post_id      TEXT PRIMARY KEY,
            media_url    TEXT,
            link_to_post TEXT,
            timestamp    TEXT,
            platform     TEXT
        )
    ''')

    # insert or replace record
    cursor.execute('''
        INSERT OR REPLACE INTO posts_metadata
        (post_id, media_url, link_to_post, timestamp, platform)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        posts_metadata.get_post_id(),
        posts_metadata.get_media_url(),
        posts_metadata.get_link_to_post(),
        posts_metadata.get_timestamp(),
        posts_metadata.get_platform()
    ))

    connection.commit()