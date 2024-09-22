#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#


import os.path
from pathlib import Path

import arrow
import click
import dropbox
from dropbox.files import FolderMetadata


def file_age_ok(dbx_file, max_age) -> bool:
    """
    Validates if the dropbox file is older than `max_age` or not.
    """
    total_seconds = (
        arrow.utcnow() - arrow.get(dbx_file.client_modified)
    ).total_seconds()
    if (total_seconds / 60 / 60 / 24) > max_age:
        return False
    return True


def traverse_dbx_folder(dbx, folder_name, cursor=None):
    """
    Recursively traverses the Dropbox folder `folder_name` and yields all
    found files.
    """
    while True:
        if cursor is None:
            response = dbx.files_list_folder(folder_name)
        else:
            response = dbx.files_list_folder_continue(cursor)

        for entry in response.entries:
            if isinstance(entry, FolderMetadata):
                for recursed_entry in traverse_dbx_folder(dbx, entry.path_display):
                    yield recursed_entry
            else:
                yield entry

        if not response.has_more:
            break

        cursor = response.cursor


def local_remote_hash_differs(local_path, dbx_file):
    print(dbx_file)


def download_file(dbx, remote_path, local_path):
    Path(f"{os.path.dirname(local_path)}").mkdir(parents=True, exist_ok=True)

    print(
        f'Copying dropbox://{remote_path} to local://{local_path.lstrip("/")}: ',
        end="",
    )
    with open(local_path, "wb") as f:
        metadata, res = dbx.files_download(remote_path)
        f.write(res.content)
    print("done")


@click.command(
    name="dbsync", help="A CLI sync a Dropbox folder to the local file system."
)
@click.option(
    "--token", required=True, envvar="DBSYNC_REFRESH_TOKEN", help="The Dropbox token"
)
@click.option(
    "--app-key", required=True, envvar="DBSYNC_APP_KEY", help="The Dropbox token"
)
@click.option(
    "--app-secret", required=True, envvar="DBSYNC_APP_SECRET", help="The Dropbox token"
)
@click.option(
    "--dropbox-folder",
    required=True,
    envvar="DBSYNC_DROPBOX_FOLDER",
    help="The Dropbox folder to sync from.",
)
@click.option(
    "--local-folder",
    required=True,
    envvar="DBSYNC_LOCAL_FOLDER",
    help="The local folder to sync to.",
)
@click.option(
    "--max-days",
    required=False,
    default="31",
    envvar="DBSYNC_MAX_DAYS",
    type=int,
    help="The the maximum file age expressed in number of days.",
)
def main(token, app_key, app_secret, dropbox_folder, local_folder, max_days):
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=token, app_key=app_key, app_secret=app_secret
    )
    for entry in traverse_dbx_folder(dbx, dropbox_folder):
        if file_age_ok(entry, max_days):
            local_file_name = os.path.abspath(f"{local_folder}/{entry.path_display}")
            if not os.path.isfile(local_file_name):
                download_file(dbx, entry.path_display, local_file_name)


if __name__ == "__main__":
    main()
