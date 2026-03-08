
import sqlite3
from dataclasses import dataclass, asdict
import config

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

def link_harvested_faces_to_post(harvested_faces_id : str, post_id : str):
    connection = None
    try:
        connection = sqlite3.connect(config.METADATA_PATH)
        cursor = connection.cursor()
        # create table if not exists
        cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS {HARVESTED_FACES_TABLE_NAME} 
        (
            harvested_faces_id TEXT PRIMARY KEY,
            post_id TEXT,
            FOREIGN KEY (post_id) REFERENCES {POSTS_METADATA_TABLE_NAME}(post_id)
        )
        '''
        )

        # indexing the post_id column for faster retrieval (ADDING MORE SPACE TO THE DATABASE)
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_post_id ON {HARVESTED_FACES_TABLE_NAME} (post_id)')

        # insert or replace record
        cursor.execute(
        f'''
        INSERT OR REPLACE INTO {HARVESTED_FACES_TABLE_NAME}
        (harvested_faces_id, post_id)
        VALUES (?, ?)
        ''', 
        (
        harvested_faces_id,
        post_id
        )
        )
        connection.commit()
    finally:
        if connection: connection.close()

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
