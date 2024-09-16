#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#


from pathlib import Path

import click
import dropbox
from dropbox.files import FolderMetadata


def traverse_folder(dbx, folder_name, cursor=None):
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
                for recursed_entry in traverse_folder(dbx, entry.path_display):
                    yield recursed_entry
            else:
                yield entry

        if not response.has_more:
            break

        cursor = response.cursor


def download_file(dbx, remote_path, local_path):
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
@click.option("--token", required=True, envvar="DBSYNC_REFRESH_TOKEN", help="The Dropbox token")
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
def main(token, app_key, app_secret, dropbox_folder, local_folder):
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=token, app_key=app_key, app_secret=app_secret
    )
    for entry in traverse_folder(dbx, dropbox_folder):
        path = Path(entry.path_display)
        Path(f"{local_folder}/{path.parent}").mkdir(parents=True, exist_ok=True)
        download_file(dbx, entry.path_display, f"{local_folder}/{entry.path_display}")


if __name__ == "__main__":
    main()
