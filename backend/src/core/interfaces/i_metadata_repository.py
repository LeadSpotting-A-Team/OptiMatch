from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.entities.cropped_face import CroppedFace
from src.core.entities.post_metadata import PostMetadata


class IMetadataRepository(ABC):
    """
    Contract for storing and querying post / face metadata.
    The core layer describes *what* to persist; the SQLite implementation
    in src/app/db/ handles *how* it is stored.
    """

    @abstractmethod
    def save_post(self, post: PostMetadata) -> None:
        # Inserts or replaces the given post record in the metadata store.
        # Raises no exception if a post with the same ID already exists
        # (upsert semantics).
        ...

    @abstractmethod
    def link_face_to_post(
        self,
        face_id: str,
        post_id: str,
        cropped_face: CroppedFace,
    ) -> None:
        # Creates an association between a face_id and a post_id and stores
        # the face's five landmark coordinates alongside it.
        # Raises no exception if the association already exists (upsert).
        ...

    @abstractmethod
    def get_post_by_face_id(self, face_id: str) -> PostMetadata | None:
        # Looks up the post that contains the given face_id.
        # Returns the full PostMetadata object, or None if not found.
        ...

    @abstractmethod
    def clear_all(self) -> None:
        # Drops and recreates all metadata tables, removing every stored record.
        # Intended for use in index rebuild scripts only.
        ...
