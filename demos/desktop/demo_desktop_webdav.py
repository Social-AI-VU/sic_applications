import os

from utils.webdav_sync import WebDAVSync


class WebDAVDemo:
    """
    Steps to run demo:
     (1) Get path for folder in remote drive
     (2) Create App Password for WebDAV enabled remote drive.

     --------------------------------------------------------------
    (1) How to get a remote folder path in VU Research Drive

    Steps:

    1. Go to Research Drive (Nextcloud):
       https://vu.data.surf.nl
    2. Navigate to the right project folder.
    3. It will look something like this https://vu.data.surf.nl/apps/files/files/<some numbers>?dir=/<project_folder>
        Use the part after dir=/

     --------------------------------------------------------------
    (2) How to create an App Password for VU Research Drive (Nextcloud)

    Using an App Password is REQUIRED for WebDAV access. Your normal VU password will not work.

    Steps:

    1. Go to Research Drive (Nextcloud):
       https://vu.data.surf.nl

    2. Log in with your VU credentials (SURFconext).

    3. Open Settings:
       - Click your profile icon (top-right corner)
       - Select "Settings"

    4. Navigate to Security:
       - In the left sidebar, click "Security"

    5. Create an App Password:
       - Find the section "Devices & sessions"
       - Enter a name (e.g., "Python WebDAV Sync")
       - Click "Create new app password"

    6. Copy the generated password:
       - It will be shown only ONCE
       - Save it securely

    7. Use it in your code:

       Example:
           base_url = "https://vu.data.surf.nl/remote.php/dav/files/<vunetID>@vu.nl/"
           username = "<vunetID>@vu.nl"
           password = "<app-password>" # NOT your normal password

    Important Notes:
    ----------------
    - App passwords bypass MFA (2FA), which is why they are required
    - You can revoke them anytime from the Security page
    - Create separate app passwords for different applications for safety
    """

    def __init__(
        self,
        base_url,
        username,
        password,
        remote_folder,
        local_folder="local_test_sync_folder",
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.remote_folder = remote_folder
        self.local_folder = local_folder

    def run(self):
        test_local_file_path = os.path.join(self.local_folder, "test.md")
        test_2_local_file_path = os.path.join(self.local_folder, "test2.md")

        remote_test_folder = f"{self.remote_folder}/remote_test_sync_folder"
        remote_test_2_file_path = f"{remote_test_folder}/test2.md"

        os.makedirs(self.local_folder, exist_ok=True)

        if not os.path.isfile(test_local_file_path):
            with open(test_local_file_path, "w", encoding="utf-8") as f:
                f.write("Hello from WebDAV sync demo!")
        else:
            print("test.md already exists, not overwriting.")

        sync = WebDAVSync(
            base_url=self.base_url, username=self.username, password=self.password
        )

        sync.sync_once(local_folder=self.local_folder, remote_folder=remote_test_folder)

        # Upload to different remote location
        sync.upload_file(
            local_path=test_local_file_path, remote_path=remote_test_2_file_path
        )

        # Download file example
        sync.download_file(
            remote_path=remote_test_2_file_path, local_path=test_2_local_file_path
        )


if __name__ == "__main__":
    demo = WebDAVDemo(
        base_url="https://<host>/remote.php/dav/files/<username>/",
        username="<username>",
        password="<password>",
        remote_folder="<remote_folder>",
    )
    demo.run()
