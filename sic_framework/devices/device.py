from __future__ import print_function

import os.path
import tarfile
import tempfile
import time

import six

from sic_framework.core import utils
from sic_framework.core.connector import SICConnector

if six.PY3:
    import paramiko
    import pathlib
    from scp import SCPClient



class _SICLibrary(object):
    """
    A library to be installed on a remote device.
    """

    def __init__(self, name, lib_path, lib_install_cmd):
        self.name = name
        self.lib_path = lib_path
        self.lib_install_cmd = lib_install_cmd

    def check_if_installed(self, pip_freeze):
        for lib in pip_freeze:
            if self.name in lib:
                return True
        return False

    def install(self, ssh):
        print("Installing {} on remote device ".format(self.name), end="")
        stdin, stdout, stderr = ssh.exec_command("cd {} && {}".format(self.lib_path, self.lib_install_cmd))

        # print a dot every line to indicate progress
        while True:
            line = stdout.readline()
            # empty line means command is done
            if len(line) == 0:
                break

            print(".", end="")

        err = stderr.readlines()
        if len(err) > 0:
            print("".join(err))
            print("Command:", "cd {} && {}".format(self.lib_path, self.lib_install_cmd))
            raise RuntimeError(
                "Error while installing library on remote device. Please consult manual installation instructions.")
        else:
            print(" done.")


_LIBS_TO_INSTALL = [
    _SICLibrary("redis", "~/framework/lib/redis", "pip install --user redis-3.5.3-py2.py3-none-any.whl"),
    _SICLibrary("PyTurboJPEG", "~/framework/lib/libtubojpeg/PyTurboJPEG-master", "pip install --user ."),
    _SICLibrary("sic-framework", "~/framework", "pip install --user -e .")
]

def exclude_pyc(tarinfo):
    if tarinfo.name.endswith(".pyc"):
        return None
    else:
        return tarinfo



class SICDevice(object):
    """
    Abstract class to facilitate property initialization for SICConnector properties.
    This way components of a device can easily be used without initializing all device components manually.
    """

    def __init__(self, ip, username=None, passwords=None):
        """
        Connect to the device and ensure an up to date version of the framework is installed
        :param ip: the ip adress of the device
        :param username: the ssh login name
        :param passwords: the (list) of passwords to use
        """
        self.connectors = dict()
        self.configs = dict()
        self.ip = ip

        if username is not None:

            if not isinstance(passwords, list):
                passwords = [passwords]

            if not utils.ping_server(self.ip, port=22, timeout=3):
                raise RuntimeError(
                    "Could not connect to device on ip {}. Please check if it is reachable.".format(self.ip))

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # allow_agent=False, look_for_keys=False to disable asking for keyring (just use the password)
            for p in passwords:
                try:
                    self.ssh.connect(self.ip, port=22, username=username, password=p, timeout=3, allow_agent=False,
                                     look_for_keys=False)
                    break
                except (paramiko.ssh_exception.AuthenticationException, paramiko.ssh_exception.BadAuthenticationType):
                    pass
            else:
                raise paramiko.ssh_exception.AuthenticationException(
                    "Could not authenticate to device, please check ip adress and/or credentials. (Username: {} Passwords: {})".format(
                        username, passwords))

    def get_last_modified(self, root, paths):
        last_modified = 0

        for file_or_folder in paths:
            file_or_folder = root + file_or_folder
            if os.path.isdir(file_or_folder):
                sub_last_modified = max(os.path.getmtime(root) for root, _, _ in os.walk(file_or_folder))
                last_modified = max(sub_last_modified, last_modified)
            elif os.path.isfile(file_or_folder):
                last_modified = max(os.path.getmtime(file_or_folder), last_modified)

        assert last_modified > 0, "Could not find any files to transfer."
        last_modified = time.ctime(last_modified).replace(" ", "_").replace(":", "-")
        return last_modified

    def auto_install(self):
        """
        Install the SICFramework on the device.
        :return:
        """
        # Find framework root folder
        root = str(pathlib.Path(__file__).parent.parent.parent.resolve())
        assert os.path.basename(root) == "framework", "Could not find SIC 'framework' directory."

        # List of selected files and directories to be zipped and transferred
        selected_files = [
            "/setup.py",
            "/conf",
            "/lib",
            "/sic_framework/core",
            "/sic_framework/devices",
            "/sic_framework/__init__.py",
        ]


        last_modified = self.get_last_modified(root, selected_files)

        # Create a signature for the framework
        framework_signature = "~/framework/sic_version_signature_{}_{}".format(utils.get_ip_adress(), last_modified)

        # Check if the framework signature file exists
        stdin, stdout, stderr = self.ssh.exec_command('ls {}'.format(framework_signature))
        file_exists = len(stdout.readlines()) > 0

        if file_exists:
            print("Up to date framework is installed on the remote device.")
            return

        # prefetch slow pip freeze command
        _, stdout_pip_freeze, _ = self.ssh.exec_command("pip freeze")

        def progress(filename, size, sent):
            print("\r {} progress: {}".format(filename.decode("utf-8"), round(float(sent) / float(size) * 100, 2)),
                  end="")

        print("Copying framework to the remote device.")
        with SCPClient(self.ssh.get_transport(), progress=progress) as scp:

            # Copy the framework to the remote computer
            with tempfile.NamedTemporaryFile(suffix='_sic_files.tar.gz', delete=False) as f:
                with tarfile.open(fileobj=f, mode='w:gz') as tar:
                    for file in selected_files:
                        tar.add(root + file, arcname=file, filter=exclude_pyc)

                f.flush()
                self.ssh.exec_command("mkdir ~/framework")
                scp.put(f.name, remote_path="~/framework/sic_files.tar.gz")
                print()  # newline after progress bar
            # delete=False for windows compatibility, must delete file manually
            os.unlink(f.name)

            # Unzip the file on the remote server
            # use --touch to prevent files from having timestamps of 1970 which intefere with python caching
            stdin, stdout, stderr = self.ssh.exec_command("cd framework && tar --touch -xvf sic_files.tar.gz")

            err = stderr.readlines()
            if len(err) > 0:
                print("".join(err))
                raise RuntimeError(
                    "\n\nError while extracting library on remote device. Please consult manual installation instructions.")

            # Remove the zipped file
            self.ssh.exec_command("rm ~/framework/sic_files.tar.gz")

        # Check and/or install the framework and libraries on the remote computer
        print("Checking if libraries are installed on the remote device.")
        # stdout_pip_freeze is prefetched above because it is slow
        remote_libs = stdout_pip_freeze.readlines()
        for lib in _LIBS_TO_INSTALL:
            if not lib.check_if_installed(remote_libs):
                lib.install(self.ssh)

        # Remove signatures from the remote computer
        # add own signature to the remote computer
        self.ssh.exec_command('rm ~/framework/sic_version_signature_*')
        self.ssh.exec_command('touch {}'.format(framework_signature))

    def _get_connector(self, component_connector):
        """
        Get the active connection the component, or initialize it if it is not yet connected to.

        :param component_connector: The component connector class to start, e.g. NaoCamera
        :return: SICConnector
        """

        assert issubclass(component_connector, SICConnector), "Component connector must be a SICConnector"

        if component_connector not in self.connectors:
            conf = self.configs.get(component_connector, None)

            try:
                self.connectors[component_connector] = component_connector(self.ip, conf=conf)
            except TimeoutError as e:
                raise TimeoutError("Could not connect to {} on device {}.".format(
                    component_connector.component_class.get_component_name(), self.ip))
        return self.connectors[component_connector]


if __name__ == '__main__':
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # allow_agent=False, look_for_keys=False to disable asking for keyring (just use the password)
    ssh.connect("192.168.0.151", port=22, username="nao", password="nao", timeout=5, allow_agent=False,
                look_for_keys=False)

    # Unzip the file on the remote server
    stdin, stdout, stderr = ssh.exec_command("apt update")

    for i in range(10):
        line = stdout.readline()
        print(line)
        print(stderr.readline())
        # empty line means command is done
        if len(line) == 0:
            break
        time.sleep(1)
