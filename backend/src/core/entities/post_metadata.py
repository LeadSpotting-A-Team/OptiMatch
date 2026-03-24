from __future__ import annotations


class PostMetadata:
    """
    Represents the metadata of a single social-media post that was ingested
    into the system. Stores identifying and descriptive information about the
    original source post; does not contain any image data.
    """

    def __init__(
        self,
        post_id: str,
        media_url: str,
        link_to_post: str | None = None,
        timestamp: str | None = None,
        platform: str | None = None,
        username: str | None = None,
    ) -> None:
        self.post_id = post_id
        self.media_url = media_url
        self.link_to_post = link_to_post
        self.timestamp = timestamp
        self.platform = platform
        self.username = username

    # Returns the unique identifier of this post.
    def get_post_id(self) -> str:
        return self.post_id

    # Returns the direct URL to the media file (image or video).
    def get_media_url(self) -> str:
        return self.media_url

    # Returns the URL linking back to the original post page, or None.
    def get_link_to_post(self) -> str | None:
        return self.link_to_post

    # Returns the publication timestamp as a string, or None if unknown.
    def get_timestamp(self) -> str | None:
        return self.timestamp

    # Returns the name of the social-media platform, or None if unknown.
    def get_platform(self) -> str | None:
        return self.platform

    # Returns the username of the post author, or None if unknown.
    def get_username(self) -> str | None:
        return self.username
