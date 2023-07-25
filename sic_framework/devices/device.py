import os.path
import pathlib
import shutil
import sys
import tarfile
import tempfile
import zipfile
from datetime import date

import paramiko
from scp import SCPClient

from sic_framework.core import utils
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.connector import SICConnector


class SICDevice(object):
    """
    Abstract class to facilitate property initialization for SICConnector properties.
    This way components of a device can easily be used without initializing all device components manually.
    """

    def __init__(self, ip, username=None, password=None):
        self.ip = ip

        # TODO ping device manager to quickly fail if ip is incorrect

        self.connectors = dict()
        self.configs = dict()

        if username is not None:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip, port=22, username=username, password=password, timeout=5)

    def auto_install(self):
        """
        Install the SICFramework on the device.
        :return:
        """

        framework_signature = "/tmp/sic_version_signature_{}_{}".format(utils.get_ip_adress(), date.today())

        # Check if the framework signature file exists
        stdin, stdout, stderr = self.self.ssh.exec_command('ls {}'.format(framework_signature))
        file_exists = len(stdout.readlines()) > 0

        def progress(filename, size, sent):
            print("\r {} progress: {}".format(filename.decode("utf-8"), round(float(sent) / float(size) * 100, 2)),
                  end="")

        if file_exists:
            print("Up to date framework is installed on the remote device.")
        else:
            print("Copying framework to the remote device.")
            with SCPClient(self.ssh.get_transport(), progress=progress) as scp:

                # Copy the framework to the remote computer
                root = str(pathlib.Path(__file__).parent.parent.parent.resolve())
                assert os.path.basename(root) == "framework", "Could not find SIC 'framework' directory."

                # List of selected files and directories to be zipped
                selected_files = [
                    "/setup.py",
                    "/conf",
                    "/lib",
                    "/sic_framework/core",
                    "/sic_framework/devices"
                ]

                with tempfile.NamedTemporaryFile(suffix='_sic_files.tar.gz') as f:
                    with tarfile.open(fileobj=f, mode='w:gz') as tar:
                        for file in selected_files:
                            tar.add(root + file, arcname=file)

                    f.flush()
                    self.ssh.exec_command("mkdir ~/framework")
                    scp.put(f.name, remote_path="~/framework/sic_files.tar.gz")
                # Unzip the file on the remote server
                stdin, stdout, stderr = self.ssh.exec_command("cd framework && tar -xvf sic_files.tar.gz")

                err = stderr.readlines()
                if len(err) > 0:
                    print("".join(err))
                    raise RuntimeError(
                        "\n\nError while extracting library on remote device. Please consult manual installation instructions.")

                # Remove the zipped file
                self.ssh.exec_command("rm ~/framework/sic_files.zip")

            # Install the framework and libraries on the remote computer
            lib_paths = ["~/framework/lib/redis",
                         "~/framework/lib/libtubojpeg/PyTurboJPEG-master",
                         "~/framework",
                         ]

            lib_install = ["pip install --user redis-3.5.3-py2.py3-none-any.whl",
                           "pip install --user .",
                           "pip install --user -e .",
                           ]

            for path, target in zip(lib_paths, lib_install):
                stdin, stdout, stderr = self.ssh.exec_command("cd {} && {}".format(path, target))

                out = stdout.readlines()
                if len(out) > 0:
                    print(out[-1], end="")

                err = stderr.readlines()
                if len(err) > 0:
                    print("".join(err))
                    print("Command:", "cd {} && {}".format(path, target))
                    raise RuntimeError(
                        "Error while installing library on remote device. Please consult manual installation instructions.")

            # Remove signatures from the remote computer
            # add own signature to the remote computer
            self.ssh.exec_command('rm /tmp/sic_version_signature_*')
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
