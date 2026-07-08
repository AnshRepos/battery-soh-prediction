######################################################################################################################
#                                                                                                                    #
# FILE          :  download_artefacts.py                                                                             #
#                                                                                                                    #
# DESCRIPTION	:  download artefacts from Artifactory                                                               #
#                                                                                                                    #
# VERSION		:  4.0                                                                                               #
#                                                                                                                    #
# HISTORY		:                                                                                                    #
#                                                                                                                    #
# Date         	| Author                	  | 	Modification                                                     #
# 07.02.2018   	| Sounak Patra (RBEI/ECA2)    |     Created basic functions to download artefacts                    #
# 08.02.2018   	| Sounak Patra (RBEI/ECA2)    |     Removed extra arguments                                          #
# 07.06.2018   	| Sounak Patra (RBEI/ECQ2)    |     Improved download performance                                    #
# 13.06.2018   	| Sounak Patra (RBEI/ECQ2)    |     Feature added to initiate checksum based download                #
# 11.01.2019   	| Sounak Patra (RBEI/ECQ2)    |     Feature added to support extended ASCII characters               #
#                                                                                                                    #
######################################################################################################################
import base64
import concurrent.futures
import json
import os
import re

import urllib2

cancel_download = False


def update_download_status(value):
    """
    Updates status of download.

    Parameters
    ----------
    value: boolean
        Specifies the status of download whether to proceed or abort.
    """
    global cancel_download
    cancel_download = value


def encode_credentials(user, password):
    """
    utf-8 encoding of userid and password to support extended ASCII characters.

    Parameters
    ----------
    user: String
        Specifies the admin user name.
    password: string
        Specifies the encrypted password.

    Returns
    -------
    Returns the encoded string.
    """
    encoding = "utf-8"
    credentials = "%s:%s" % (user, password)
    base64string = (base64.b64encode(credentials.encode(encoding)).decode(encoding)).replace("\n", "")

    return base64string


def get_output(url, user, password, request_type=None, data=None):
    """
    Reads the response for specified http methods

    Parameters
    ----------
    url: string
        Specifies the url of server.
    user: String
        Specifies the admin user name.
    password: string
        Specifies the encrypted password.
    request_type: string, optional, {Default: None}
        Specifies the HTTP methods. If not specified then it processes GET HTTP method
    data: dictionary, optional, {Default: None}
        Specifies data if HTTP method is POST / PUT

    Returns
    -------
    Returns the output of the specified http request.
    """
    if data:
        request = urllib2.Request(
            url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
    else:
        request = urllib2.Request(url, headers={"Content-Type": "text/plain; charset=utf-8"})

    if user and password:
        base64string = encode_credentials(user, password)
        request.add_header("Authorization", "Basic %s" % base64string)
    if request_type:
        request.get_method = lambda: request_type
    response = urllib2.urlopen(request, timeout=3000)
    if request_type == "HEAD":
        return response.info()
    else:
        return response.read()


def download_file(
    url,
    userid,
    password,
    download_location,
    sig_update_log,
    error_list,
    sig_progress_count,
    index,
    total_no_files,
    sig_cancelled_files,
):
    """
    Download file artefact

    Parameters
    ----------
    url: string
        Specifies the url of artefact.
    userid: String
        Specifies the admin username.
    password: string
        Specifies the encrypted password.
    download_location: string
        Specifies the downlaod pah of artefact
    sig_update_log: object
        Specifies the signal object to log status of progress
    error_list: list
        List to trap file artefacts with downlaod errors
    sig_progress_count: object
        Signal to update the progress bar
    index: int
        Specifies the current file index of download
    total_no_files: int
        Specifies the total number of files for download
    sig_cancelled_files: object
        Signal to update cancelled files during download
    """
    global cancel_download
    if not cancel_download:
        try:
            sig_update_log.emit("Downloading [{0}/{1}] ".format(index + 1, total_no_files) + url)
            request = urllib2.Request(url, headers={"Content-Type": "text/plain; charset=utf-8"})
            base64string = encode_credentials(userid, password)
            request.add_header("Authorization", "Basic %s" % base64string)
            response = urllib2.urlopen(request, timeout=10000)
            mem_chunk = 16 * 1024
            with open(download_location, "wb") as f:
                while True:
                    chunk = response.read(mem_chunk)
                    if not chunk:
                        break
                    f.write(chunk)
            sig_progress_count.emit(1, False)
        except urllib2.HTTPError as ex:
            error_list.append(url)
            sig_update_log.emit("ERROR >> DOWNLOAD_FILE >> " + url + ": HTTPError = " + str(ex))
            sig_update_log.emit(str(ex.read()))
        except urllib2.URLError as ex:
            error_list.append(url)
            sig_update_log.emit("ERROR >> DOWNLOAD_FILE >> " + url + ": URLError = " + str(ex))
        except Exception as ex:
            error_list.append(url)
            sig_update_log.emit("ERROR >> DOWNLOAD_FILE >> " + url + ": Generic exception: " + str(ex))
    else:
        sig_cancelled_files.emit(url)


def get_artifactory_generated_sha1(url, uid, pwd, sig_update_log):
    """
    Finds the arifactory generated sha1 checksum value.

    Parameters
    ----------
    url: string
        Specifies the url of artefact.
    uid: String
        Specifies the admin username.
    pwd: string
        Specifies the encrypted password.
    sig_update_log: object
        Specifies the signal object to log status of progress
    """
    sha1 = ""
    try:
        output = get_output(url, uid, pwd, request_type="HEAD")
        output_data = str(output).split("\n")

        def get_sha1(data):
            return [value for value in data if "Sha1" in value]

        sha1_value = get_sha1(output_data)[0]
        sha1 = ((sha1_value.replace("\r", "")).split(":")[1]).strip()
    except Exception:
        sig_update_log.emit("ERROR >> Cannot find sha1 checksum of " + url)

    return sha1


def prepare_sha1_data(
    data,
    new_files,
    uid,
    pwd,
    sha1_file_content,
    sha1_file_detail,
    file_exist,
    sig_update_log,
):
    """
    Helps to initiate checksum based download.

    Parameters
    ----------
    data: list
        Specifes list which contains file url and download location
    new_files: list
        Specifes list to contain new or modified file names
    file_list: list
        list to store file artefacts for download
    download_location: string
        Specifies the download path of artefact
    uid: String
        Specifies the admin username.
    pwd: string
        Specifies the encrypted password.
    sha1_file_content: dictionary
        Specifies dictionary that contains file names and sha1 checksum values
    sha1_file_detail: dictionary
        Specifies dictionary that contains file urls and names
    file_exist: boolean
        Specifies if checksum file exists or not
    sig_update_log: object
        Specifies the signal object to log status of progress
    """
    sha1_value = get_artifactory_generated_sha1(data[0], uid, pwd, sig_update_log)
    file_name = os.path.normpath(data[1])

    if file_exist:
        if sha1_file_content.has_key(file_name) and str(sha1_file_content[file_name]) != sha1_value:
            new_files.append(data)
            sha1_file_content[file_name] = sha1_value
            sha1_file_detail[data[0]] = file_name
        elif not sha1_file_content.has_key(file_name):
            new_files.append(data)
            sha1_file_content[file_name] = sha1_value
            sha1_file_detail[data[0]] = file_name
    else:
        new_files.append(data)
        sha1_file_content[file_name] = sha1_value
        sha1_file_detail[data[0]] = file_name


def verify_checksum(file_list, download_location, uid, pwd, sig_update_log):
    """
    Helps to initiate checksum based download.

    Parameters
    ----------
    file_list: list
        list to store file artefacts for download
    download_location: string
        Specifies the downlaod path of artefact
    uid: String
        Specifies the admin username.
    pwd: string
        Specifies the encrypted password.
    sig_update_log: object
        Specifies the signal object to log status of progress
    """
    sig_update_log.emit(
        "INFO: Checking sha1 checksum. It may take some "
        + "time if repository is a Remote repository due to caching process..."
    )
    sha1_file = os.path.join(download_location, "content.sha1")
    file_exist = True if os.path.isfile(sha1_file) else False
    new_files = []
    sha1_file_content = {}
    sha1_file_detail = {}

    if file_exist:
        with open(sha1_file) as sha1_data:
            sha1_file_content = json.load(sha1_data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for data in file_list:
            executor.submit(
                prepare_sha1_data,
                data,
                new_files,
                uid,
                pwd,
                sha1_file_content,
                sha1_file_detail,
                file_exist,
                sig_update_log,
            )

    return new_files, [sha1_file, sha1_file_content, sha1_file_detail]


def read_file_list(url, uid, pwd, file_list, download_location, sig_update_log, sig_file_count):
    """
    Read and emit list of files from specified artefact path

    Parameters
    ----------
    url: string
        Specifies the url of artefact.
    uid: String
        Specifies the admin username.
    pwd: string
        Specifies the encrypted password.
    file_list: list
        list to store file artefacts for download
    download_location: string
        Specifies the downlaod path of artefact
    sig_update_log: object
        Specifies the signal object to log status of progress
    sig_file_count: object
        Signal to send the file list to initiate download
    """
    get_file_list(url, uid, pwd, file_list, download_location, sig_update_log)
    modified_file_list, sha1_data = verify_checksum(file_list, download_location, uid, pwd, sig_update_log)
    sig_file_count.emit([modified_file_list, uid, pwd, sha1_data])


def get_file_list(repo_url, uid, pwd, file_list, download_location, sig_update_log):
    """
    Read files from specified artefact path

    Parameters
    ----------
    repo_url: string
        Specifies the url of artefact.
    uid: String
        Specifies the admin username.
    pwd: string
        Specifies the encrypted password.
    file_list: list
        list to store file artefacts for download
    download_location: string
        Specifies the downlaod path of artefact
    sig_update_log: object
        Specifies the signal object to log status of progress
    """
    try:
        repo_url = repo_url.replace(" ", "%20")
        output = get_output(repo_url, uid, pwd)
        final_result = output.split("\n")

        for result in final_result:
            if "<a href" in result and "../" not in result:
                file_name = re.findall(r">(.*)<", result)[0]
                if "/" in file_name:
                    file_name = file_name.replace("/", "")
                    url = repo_url + "/" + file_name
                    location = os.path.join(download_location, file_name)
                    if not os.path.exists(location):
                        os.makedirs(location)
                    get_file_list(url, uid, pwd, file_list, location, sig_update_log)
                else:
                    if (".md5" in file_name) or (".sha1" in file_name) or (".sha256" in file_name):
                        continue
                    else:
                        file_list.append(
                            [
                                repo_url + "/" + file_name,
                                os.path.join(download_location, file_name),
                            ]
                        )
    except urllib2.HTTPError as ex:
        sig_update_log.emit("ERROR >> GET_FILE_LIST >> " + repo_url + ": HTTPError = " + str(ex))
    except urllib2.URLError as ex:
        sig_update_log.emit("ERROR >> GET_FILE_LIST >> " + repo_url + "URLError = " + str(ex))
    except Exception as ex:
        sig_update_log.emit("ERROR >> GET_FILE_LIST >> " + repo_url + "Generic exception: " + str(ex))
