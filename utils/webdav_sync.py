import os
from datetime import datetime

from webdav3.client import Client


class WebDAVSync:
    """
    Flexible WebDAV sync utility (Nextcloud / Research Drive).

    Features:
    ---------
    - One-time two-way sync
    - Upload/download file or folder
    - Nested folder support
    - Automatic remote directory creation
    - Conflict handling ("keep both versions")

    Requirements:
    -------------
    - Base URL MUST be:
        https://<host>/remote.php/dav/files/<username>/
    - Use an App Password
    """

    def __init__(self, base_url, username, password, time_threshold=2):
        self.username = username
        self.time_threshold = time_threshold

        self.client = Client(
            {
                "webdav_hostname": base_url,
                "webdav_login": username,
                "webdav_password": password,
            }
        )

    # ------------------------
    # HELPERS
    # ------------------------
    @staticmethod
    def _remote_path(remote_base, path=""):
        remote_base = remote_base.strip("/")
        path = path.strip("/")

        if path:
            return f"/{remote_base}/{path}"
        return f"/{remote_base}"

    @staticmethod
    def _parse_remote_time(timestr):
        return datetime.strptime(timestr, "%a, %d %b %Y %H:%M:%S %Z").timestamp()

    @staticmethod
    def _conflict_name(path, suffix):
        base, ext = os.path.splitext(path)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{base}.{suffix}_conflict.{timestamp}{ext}"

    def _ensure_remote_dir(self, remote_path, is_dir=False):
        """
        Ensure that a remote directory (and its parents) exist.

        Parameters
        ----------
        remote_path : str
            Full remote path (file or directory)
        is_dir : bool
            If True, treat remote_path as a directory.
            If False, treat it as a file path (default).
        """
        parts = remote_path.strip("/").split("/")

        # If it's a file, exclude the last part
        if not is_dir:
            parts = parts[:-1]

        current = ""

        for part in parts:
            current += f"/{part}"
            if not self.client.check(current):
                print(f"Creating remote folder: {current}")
                self.client.mkdir(current)

    def _list_remote_files(self, remote_base):
        files = self.client.list(self._remote_path(remote_base), get_info=True)

        remote_files = {}
        prefix = f"remote.php/dav/files/{self.username}/"

        for f in files:
            if f["isdir"]:
                continue

            path = f["path"].lstrip("/")

            # strip Nextcloud prefix
            if path.startswith(prefix):
                path = path[len(prefix) :]

            # strip remote_base prefix
            if path.startswith(remote_base):
                path = path[len(remote_base) :].lstrip("/")

            remote_files[path] = {"size": f["size"], "modified": f["modified"]}

        return remote_files

    @staticmethod
    def _list_local_files(folder):
        local_files = {}

        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder).replace("\\", "/")

                local_files[rel_path] = {
                    "size": os.path.getsize(full_path),
                    "modified": os.path.getmtime(full_path),
                }

        return local_files

    # ------------------------
    # SYNC (ONE-TIME)
    # ------------------------
    def sync_once(self, local_folder, remote_folder):
        print(f"Sync local '{local_folder}' ↔ remote '{remote_folder}'")
        self._ensure_remote_dir(remote_folder, is_dir=True)

        local_files = self._list_local_files(local_folder)
        remote_files = self._list_remote_files(remote_folder)

        # Upload + conflict handling
        for path, local_meta in local_files.items():
            remote_path = self._remote_path(remote_folder, path)
            local_path = os.path.join(local_folder, path)

            if path not in remote_files:
                print(f"Uploading new: {path}")
                self._ensure_remote_dir(remote_path)
                self.client.upload_sync(remote_path, local_path)
                continue

            remote_meta = remote_files[path]
            local_mtime = local_meta["modified"]
            remote_mtime = self._parse_remote_time(remote_meta["modified"])

            if abs(local_mtime - remote_mtime) < self.time_threshold:
                continue

            if local_mtime > remote_mtime:
                print(f"Uploading updated: {path}")
                self._ensure_remote_dir(remote_path)
                self.client.upload_sync(remote_path, local_path)

            else:
                print(f"Conflict detected: {path}")
                conflict_path = self._conflict_name(local_path, "local")
                os.rename(local_path, conflict_path)

                print(f"Renamed local → {conflict_path}")

                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                self.client.download_sync(remote_path, local_path)

        # Download
        for path, remote_meta in remote_files.items():
            local_path = os.path.join(local_folder, path)

            if path not in local_files:
                print(f"Downloading new: {path}")
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                self.client.download_sync(
                    self._remote_path(remote_folder, path), local_path
                )
                continue

            local_meta = local_files[path]
            local_mtime = local_meta["modified"]
            remote_mtime = self._parse_remote_time(remote_meta["modified"])

            if abs(local_mtime - remote_mtime) < self.time_threshold:
                continue

            if remote_mtime > local_mtime:
                print(f"Downloading updated: {path}")
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                self.client.download_sync(
                    self._remote_path(remote_folder, path), local_path
                )

        print("Sync complete.")

    # ------------------------
    # UPLOAD
    # ------------------------
    def upload_file(self, local_path, remote_path):
        """
        Upload a single file to a remote location.

        Parameters
        ----------
        local_path : str
            Local file path
        remote_path : str
            Remote file path (including filename)
        """
        if os.path.isdir(local_path):
            raise ValueError("upload_file expects a file, got a directory")

        full_remote = "/" + remote_path.strip("/")

        self._ensure_remote_dir(full_remote)

        self.client.upload_sync(full_remote, local_path)

        print(f"Uploaded file → {remote_path}")

    def upload_folder(self, local_folder, remote_folder):
        """
        Upload an entire local folder to a remote folder.

        Parameters
        ----------
        local_folder : str
            Path to local folder
        remote_folder : str
            Remote folder path (destination root)
        """
        # Ensure remote base folder exists
        base_remote = "/" + remote_folder.strip("/")
        self._ensure_remote_dir(base_remote, is_dir=True)

        local_files = self._list_local_files(local_folder)

        for path in local_files:
            local_path = os.path.join(local_folder, path)

            full_remote = f"{base_remote}/{path}".replace("\\", "/")

            self._ensure_remote_dir(full_remote)

            self.client.upload_sync(full_remote, local_path)

            print(f"Uploaded: {path}")

    # ------------------------
    # DOWNLOAD
    # ------------------------
    def download_file(self, remote_path, local_path):
        self.client.download_sync("/" + remote_path.strip("/"), local_path)
        print(f"Downloaded file → {remote_path}")

    def download_folder(self, remote_folder, local_folder):
        remote_files = self._list_remote_files(remote_folder)

        for path in remote_files:
            local_path = os.path.join(local_folder, path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            self.client.download_sync(
                self._remote_path(remote_folder, path), local_path
            )
            print(f"Downloaded: {path}")
