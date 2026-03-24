from __future__ import annotations

import csv

from src.core.entities.post_metadata import PostMetadata


# Reads a CSV dataset file and returns a list of PostMetadata objects.
# Column names are configurable so the reader works with different CSV schemas.
# Skips the header row automatically.
# Returns a list of PostMetadata in the same order as the CSV rows.
def read_posts_from_csv(
    path: str,
    post_id_column: str       = "post_id",
    media_url_column: str     = "mediaurl",
    link_column: str          = "link",
    timestamp_column: str     = "creation_time",
    platform_column: str      = "source",
    username_column: str | None = None,
) -> list[PostMetadata]:
    posts: list[PostMetadata] = []

    with open(path, "r", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        header: dict[str, int] = {}

        for row_index, row in enumerate(reader):
            if row_index == 0:
                # Build a column-name → column-index lookup from the header row.
                header = {name: idx for idx, name in enumerate(row)}
                continue

            post = PostMetadata(
                post_id=row[header[post_id_column]],
                media_url=row[header[media_url_column]],
                link_to_post=row[header[link_column]],
                timestamp=row[header[timestamp_column]],
                platform=row[header[platform_column]],
                username=row[header[username_column]] if username_column and username_column in header else None,
            )
            posts.append(post)

    return posts
