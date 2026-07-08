#!/usr/bin/env python
import argparse
import errno
import glob
import json
import logging
import os
import shutil
import subprocess
from multiprocessing import Pool

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


import requests
from bs4 import BeautifulSoup

# if tqdm for nice progress bar not available, define dummy class
try:
    from tqdm import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        class Dummy(object):
            def update(self, *_):
                pass

            def write(self, *_):
                pass

            def close(self):
                pass

        if args:
            return args[0]
        return kwargs.get("iterable", Dummy())


from jfrog_cli_config import get_jfrog_config  # NOQA


log = logging.getLogger("artifactory_download")
log.addHandler(logging.NullHandler())


# trick to avoid PicklingError for instancemethod: http://www.rueckstiess.net/research/snippets/show/ca1d7d90
def cache_artifact(args):
    session, artifact_path = args
    return session.cache_artifact(artifact_path)


class ArtifactorySession(object):
    def __init__(self):
        self._jfrog_config = get_jfrog_config()
        self._session = None
        self.server_url = self._jfrog_config.server_url
        self.user = self._jfrog_config.user
        self.api_key = self._jfrog_config.api_key
        self.artifactory_cli = self._jfrog_config.artifactory_cli

    @property
    def session(self):
        if not self._session:
            logger = logging.getLogger("requests.packages.urllib3.connectionpool")
            logger.setLevel(logging.WARNING)

            self._session = requests.session()
            self._session.auth = (self.user, self.api_key)
        return self._session

    def clean_temp(self):
        return self._jfrog_config.clean_temp()

    def artifacts_to_be_cached(self, path):
        url = urljoin(self.server_url, path)
        result = self.session.get(url)
        if result.ok:
            log.debug("checking for links in: %s", url)
            soup = BeautifulSoup(result.text, "html.parser")
            for node in soup.find_all("a"):
                if not node.text.endswith("/"):
                    if node.nextSibling.startswith("->"):
                        yield "{}{}".format(path, node.text)
                elif not node.text.startswith(".."):
                    for artifact_path in self.artifacts_to_be_cached("%s%s" % (path, node.text)):
                        yield artifact_path
        else:
            raise Exception("checking for links in %s failed for reason: %s" % (url, result.reason))

    def cache_artifact(self, artifact_path):
        # https://www.jfrog.com/confluence/display/RTF/Artifactory+REST+API#ArtifactoryRESTAPI-ArtifactSyncDownload
        url = urljoin(self.server_url, "api/download/{}?content=none".format(artifact_path))
        log.debug("caching %s", url)
        request = self.session.get(url)
        if request.ok:
            log.debug("%s: %s", artifact_path, request.text.strip())

    def populate_remote_cache(self, data_path):
        log.info("Checking Artifactory cache ...")
        artifact_list = list(self.artifacts_to_be_cached(data_path))
        log.info("Need to cache %d artifacts.", len(artifact_list))
        if artifact_list:
            pool = Pool(processes=4)
            pbar = tqdm(total=len(artifact_list), unit="artifacts")

            for _ in pool.imap_unordered(cache_artifact, ((self, path) for path in artifact_list)):
                pbar.update()

    def get_file_list(self, path):
        url = urljoin(self.server_url, "api/storage/{}?list&deep=1".format(path))
        log.debug("fetching file list: %s", url)
        request = self.session.get(url)
        if request.ok:
            return request.json().get("files")

    def download(self, source, destination, keep_source_path_prefix=True):
        self.makedirs(destination)
        # check if source is missing trailing '/'
        if source[-1] != "/":
            # check if any search results in case this is a single file download, else append '/'
            search_cmd = [self.artifactory_cli, "rt", "s", source]
            search_results = json.loads(subprocess.check_output(search_cmd, universal_newlines=True))
            if len(search_results) == 0:
                source += "/"
        data_path = os.path.normpath(source.split("/", 1)[-1]).replace("\\", "/")

        log.info("getting file list ...")
        files = self.get_file_list(source)
        if not files:
            raise Exception("no artifacts found in: %s" % source)
        file_sizes = {f["uri"]: f["size"] for f in files}

        download_cmd = [self.artifactory_cli, "rt", "dl", source]
        log.info('executing command: "%s" ...' % " ".join(download_cmd))
        total_size = sum(file_sizes.values())
        try:
            pbar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                dynamic_ncols=True,
                unit_divisor=1024,
                smoothing=0.1,
            )
            proc = subprocess.Popen(
                download_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=destination,
                universal_newlines=True,
            )
            json_start = False
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                if "Downloading" in line:
                    _, _, file_name = line.partition(data_path)
                    file_size = file_sizes.get(file_name, 0)
                    pbar.update(file_size)

                if line.startswith("{"):
                    json_start = True
                    pbar.close()

                if json_start:
                    print(line)
            proc.stdout.close()
            if proc.wait() != 0:
                raise Exception('An error occurred during execution of subprocess: "%s"' % " ".join(download_cmd))
            else:
                log.info('Finished subprocess: "%s"' % " ".join(download_cmd))
        except OSError as e:
            print(e)
            raise Exception('JFrog CLI tool not found. Make sure "jfrog" executable is in your search path.') from e

        if not keep_source_path_prefix:
            self.remove_source_path_prefix(data_path, destination)

    @staticmethod
    def remove_source_path_prefix(data_path, destination):
        start_folder = data_path.split("/", 1)[0]
        for item in list(glob.glob(os.path.join(destination, data_path, "*"))):
            item_path = os.path.join(destination, os.path.basename(item))
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

            try:
                shutil.move(item, destination)
            except shutil.Error as e:
                print(e)
        shutil.rmtree(os.path.join(destination, start_folder))

    @staticmethod
    def makedirs(destination):
        try:
            os.makedirs(destination)
        except OSError as e:
            # be happy if someone already created the path
            if e.errno != errno.EEXIST:
                raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--keep_source_path_prefix", action="store_true", default=False)
    args = parser.parse_args()
    session = ArtifactorySession()
    session.clean_temp()
    session.download(
        args.source,
        args.destination,
        keep_source_path_prefix=args.keep_source_path_prefix,
    )


if __name__ == "__main__":
    main()
