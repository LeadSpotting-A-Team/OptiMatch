from __future__ import annotations

import sqlite3
from pathlib import Path

from src.core.entities.cropped_face import CroppedFace
from src.core.entities.post_metadata import PostMetadata
from src.core.interfaces.i_metadata_repository import IMetadataRepository

# Table names — defined as constants to avoid raw string duplication.
_POSTS_TABLE = "posts_metadata"
_FACES_TABLE = "face_id_to_post_id"


class SqliteMetadataRepository(IMetadataRepository):
    """
    SQLite implementation of IMetadataRepository.

    Stores post metadata and face-to-post associations in a local SQLite
    database file.  Each public method opens and closes its own connection so
    the repository is safe to share across threads without a connection pool.
    """

    def __init__(self, db_path: str | Path) -> None:
        # Store the path; do not open a connection at construction time so the
        # repository can be instantiated before the data directory exists.
        self._db_path = str(db_path)
        # Ensure the parent directory exists before any write operation.
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # ── Write operations ──────────────────────────────────────────────────────

    # Inserts or replaces a post record in the posts_metadata table.
    # Creates the table automatically on first call.
    def save_post(self, post: PostMetadata) -> None:
        connection = None
        try:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_POSTS_TABLE} (
                    post_id      TEXT PRIMARY KEY,
                    media_url    TEXT,
                    link_to_post TEXT,
                    timestamp    TEXT,
                    platform     TEXT,
                    username     TEXT
                )
                """
            )
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {_POSTS_TABLE}
                    (post_id, media_url, link_to_post, timestamp, platform, username)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    post.get_post_id(),
                    post.get_media_url(),
                    post.get_link_to_post(),
                    post.get_timestamp(),
                    post.get_platform(),
                    post.get_username(),
                ),
            )
            connection.commit()
        finally:
            if connection:
                connection.close()

    # Creates an association between a face_id and a post_id, storing the
    # five facial landmark coordinates alongside it.
    # Creates the table and its index automatically on first call.
    def link_face_to_post(
        self,
        face_id: str,
        post_id: str,
        cropped_face: CroppedFace,
    ) -> None:
        landmarks = cropped_face.get_landmarks()
        le = landmarks.get("left_eye",    (None, None))
        re = landmarks.get("right_eye",   (None, None))
        no = landmarks.get("nose",        (None, None))
        ml = landmarks.get("mouth_left",  (None, None))
        mr = landmarks.get("mouth_right", (None, None))

        connection = None
        try:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_FACES_TABLE} (
                    face_id       TEXT PRIMARY KEY,
                    post_id       TEXT,
                    left_eye_x    REAL, left_eye_y    REAL,
                    right_eye_x   REAL, right_eye_y   REAL,
                    nose_x        REAL, nose_y        REAL,
                    mouth_left_x  REAL, mouth_left_y  REAL,
                    mouth_right_x REAL, mouth_right_y REAL,
                    FOREIGN KEY (post_id) REFERENCES {_POSTS_TABLE}(post_id)
                )
                """
            )
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_post_id ON {_FACES_TABLE} (post_id)"
            )
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {_FACES_TABLE}
                    (face_id, post_id,
                     left_eye_x, left_eye_y, right_eye_x, right_eye_y,
                     nose_x, nose_y, mouth_left_x, mouth_left_y,
                     mouth_right_x, mouth_right_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    face_id, post_id,
                    le[0], le[1], re[0], re[1],
                    no[0], no[1], ml[0], ml[1],
                    mr[0], mr[1],
                ),
            )
            connection.commit()
        finally:
            if connection:
                connection.close()

    # ── Read operations ───────────────────────────────────────────────────────

    # Looks up the post that contains the given face_id via a JOIN query.
    # Returns a fully populated PostMetadata object, or None if not found.
    def get_post_by_face_id(self, face_id: str) -> PostMetadata | None:
        connection = None
        try:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
            cursor.execute(
                f"""
                SELECT p.post_id, p.media_url, p.link_to_post,
                       p.timestamp, p.platform, p.username
                FROM   {_FACES_TABLE} f
                JOIN   {_POSTS_TABLE} p ON f.post_id = p.post_id
                WHERE  f.face_id = ?
                """,
                (face_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return PostMetadata(
                post_id=row[0],
                media_url=row[1],
                link_to_post=row[2],
                timestamp=row[3],
                platform=row[4],
                username=row[5],
            )
        finally:
            if connection:
                connection.close()

    # ── Maintenance ───────────────────────────────────────────────────────────

    # Drops both metadata tables and removes all stored records.
    # Used by index-rebuild scripts to start a fresh ingestion run.
    def clear_all(self) -> None:
        connection = None
        try:
            connection = sqlite3.connect(self._db_path)
            cursor = connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {_FACES_TABLE}")
            cursor.execute(f"DROP TABLE IF EXISTS {_POSTS_TABLE}")
            connection.commit()
        finally:
            if connection:
                connection.close()
