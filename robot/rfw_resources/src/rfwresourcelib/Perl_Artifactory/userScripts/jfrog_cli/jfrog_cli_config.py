#!/usr/bin/env python
"""Wrapper for JFrog Artifactory commandline tool configuration.

Use get_jfrog_config() to get a valid configuration.
config = get_jfrog_config()
Installs artifactory command line tool 'jfrog' if not in system path.
If configuration not yet existing, user will be prompted for input.
After that, you can either use the Artifactory command line tool: config.artifactory_cli
or query parameters for own api requests: config.user, config.server_url, config.api_key

Check also README.md beside this module.
https://www.jfrog.com/getcli
https://www.jfrog.com/confluence/display/CLI/CLI+for+JFrog+Artifactory
"""

import errno
import getpass
import glob
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile

import requests

# input/raw_input in python 2 and 3
# Using input() directly for Python 3 compatibility


JFROG_CLI_VERSION = "1.13.1"
BOSCH_COM_ARTIFACTORY = "https://rb-cmbinex-%s.bosch.com/artifactory/"

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def getpassword(prompt):
    return getpass.getpass(prompt)


class JFrogCLIConfig(object):
    """Wrapper for command line tool configuration.

    Builds server url from chosen site location.
    Generates api key from user and password input if necessary.
    Installs artifactory command line tool 'jfrog' if not in system path.
    Provides access to configuration parameters:
    artifactory_cli, user, server_url, api_key
    """

    servers = {
        "cob": "cob-p1.apac",
        "fe": "fe-p1.de",
        "hi": "hi-p1.de",
        "kor": "kor-p1.apac",
        "szh": "szh-p1.apac",
    }

    def __init__(self, artifactory_cli=None, location=None, user=None, api_key=None):
        self._artifactory_cli = artifactory_cli
        self._location = location
        self._user = user
        self._api_key = api_key
        self._server_url = None

    @property
    def artifactory_cli(self):
        """Returns path to binary used."""
        if not self._artifactory_cli:
            if sys.platform == "win32":
                self._artifactory_cli = os.path.join(os.getenv("USERPROFILE"), "jfrog")
            else:
                self._artifactory_cli = os.path.expanduser("~/bin/jfrog")
        return self._artifactory_cli

    @property
    def location(self):
        """Returns server site location."""
        if not self._location:
            location = input("Please pick a server location [%s]:  " % ("|".join(self.servers)))
            assert location in self.servers, 'Picked location "%s" not any of [%s]' % (
                location,
                "|".join(self.servers),
            )
            self._location = location
        return self._location

    @property
    def user(self):
        if not self._user:
            self._user = input("Please enter login user: ")
        return self._user

    @property
    def api_key(self):
        if not self._api_key:
            log.warning("No API key available, will fetch from server.")
            self._api_key = self.get_api_key()
        return self._api_key

    @property
    def server_url(self):
        if not self._server_url:
            self._server_url = BOSCH_COM_ARTIFACTORY % self.servers[self.location]
        return self._server_url

    @staticmethod
    def config_file():
        home = os.path.expanduser("~")  # expands to USERPROFILE if HOME not set
        config_file = os.path.join(home, ".jfrog", "jfrog-cli.conf")

        return config_file

    def read_config(self, server_id="Default-Server"):
        """Can be used by external tools to access artifactory e.g. via requests."""

        if not os.path.isfile(JFrogCLIConfig.config_file()):
            return

        with open(JFrogCLIConfig.config_file()) as open_file:
            config = json.load(open_file)

        # config structure has changed with version 1.9.0 and contains a list for different servers
        if isinstance(config["artifactory"], list):
            if server_id == "Default-Server":
                [server_config] = [
                    server_config for server_config in config["artifactory"] if server_config.get("isDefault")
                ]
            else:
                raise NotImplementedError("currently only Default-Server supported")
        else:
            # old config type
            server_config = config["artifactory"]

        self._user = server_config.get("user")
        self._api_key = server_config.get("apiKey")
        self._server_url = server_config.get("url").replace("http:", "https:").replace(":8081", "")
        for location, suffix in self.servers.items():
            if suffix in server_config["url"]:
                self._location = location
                break

    def configure(self):
        cmd = [
            self.artifactory_cli,
            "rt",
            "config",
            "--url",
            self.server_url,
            "--user",
            self.user,
            "--apikey",
            self.api_key,
        ]
        print("calling: %s: " % " ".join(cmd))
        print('When asked for "Artifactory server ID" press return for default.')
        subprocess.check_call(cmd)

    def get_api_key(self):
        if sys.platform == "win32":
            print("please manually call:\n/usr/bin/python %s" % __file__)
            sys.exit(1)

        user = self.user
        password = getpassword("Please enter login password (will not be stored): ")
        api_key_url = self.server_url + "api/security/apiKey"
        result = requests.get(api_key_url, auth=(user, password))
        if not result.ok:
            raise Exception(result.reason)

        if "apiKey" not in result.json():
            result = requests.post(api_key_url, auth=(user, password))
            if not result.ok:
                raise Exception(result.reason)

        return result.json()["apiKey"]

    def install_artifactory_cli(self):
        binary_prefix = "{version}/jfrog-{version}".format(version=JFROG_CLI_VERSION)
        source_path = "{server}{binary_path}/{binary_prefix}".format(
            server=BOSCH_COM_ARTIFACTORY % self.servers[self.location],
            binary_path="cm-build-tools-repos/common/jfrog/cli",
            binary_prefix=binary_prefix,
        )

        if sys.platform.startswith("linux"):
            source_path = "%s-Linux-amd64" % source_path
        elif sys.platform == "cygwin":
            source_path = "%s-Windows-amd64" % source_path
        elif sys.platform == "win32":
            source_path = "%s-Windows-amd64" % source_path
        elif sys.platform.startswith("darwin"):
            source_path = "%s-Mac-amd64" % source_path
        else:
            raise NotImplementedError('Platform "%s" not supported' % sys.platform)

        destination_dir = os.path.dirname(self.artifactory_cli)
        if not os.path.exists(destination_dir):
            try:
                os.makedirs(destination_dir)
            except OSError as e:
                # be happy if someone already created the path
                if e.errno != errno.EEXIST:
                    raise

        self.download_cli(source_path, self.artifactory_cli)
        os.chmod(self.artifactory_cli, os.stat(self.artifactory_cli).st_mode | stat.S_IEXEC)

    def download_cli(self, source_path, destination_path):
        log.info("Downloading %s to %s" % (source_path, destination_path))
        session = requests.Session()
        session.headers = {"X-JFrog-Art-Api": self.api_key}
        # for using https:
        # session.cert = os.path.join(os.path.dirname(__file__), '..', 'Certificates', 'Bosch-CA1-DE_150512_pem.crt')
        # throws: requests.exceptions.SSLError: [SSL] PEM lib (_ssl.c:2718)
        result = session.get(source_path)
        if not result.ok:
            raise Exception(result.reason)
        with open(destination_path, "wb") as f:
            f.write(result.content)

    def check_config(self):
        log.info("Checking artifactory command line configuration ...")
        try:
            cli_version = subprocess.check_output([self.artifactory_cli, "--version"], universal_newlines=True)
            if JFROG_CLI_VERSION not in cli_version:
                log.warning(
                    "JFrog CLI tool version has changed from %s to %s. Will try to install."
                    % (cli_version.split()[-1], JFROG_CLI_VERSION)
                )
                self.install_artifactory_cli()
        except Exception:
            log.warning("JFrog CLI tool not found. Will try to install.")
            self.install_artifactory_cli()

        if not os.path.isfile(self.config_file()):
            self.configure()

        cli_version = subprocess.check_output([self.artifactory_cli, "--version"], universal_newlines=True)
        self.search_artifactory_root()
        log.info("Command line configuration ok: %s", cli_version)

    def search_artifactory_root(self):
        with open(os.devnull, "w") as devnull:
            subprocess.check_call(
                [self.artifactory_cli, "rt", "search", "*"],
                stdout=devnull,
                stderr=devnull,
            )
        sys.stdout.flush()
        sys.stderr.flush()

    @staticmethod
    def clean_temp():
        """Removes download artifacts from temp that remain if download process was interrupted."""
        temp_list = glob.glob(os.path.join(tempfile.gettempdir(), "jfrog.cli.*"))
        for temp_item in temp_list:
            shutil.rmtree(temp_item)


def get_jfrog_config(server_id="Default-Server"):
    cli_config = JFrogCLIConfig()
    cli_config.read_config(server_id)
    cli_config.check_config()
    return cli_config


if __name__ == "__main__":
    log_format = "[%(asctime)s|%(levelname)7s|{}] %(message)s".format("jfrog_cli_config")
    logging.basicConfig(level=logging.INFO, format=log_format)
    get_jfrog_config()
