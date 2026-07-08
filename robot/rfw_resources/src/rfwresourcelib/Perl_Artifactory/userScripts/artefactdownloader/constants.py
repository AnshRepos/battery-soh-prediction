######################################################################################################################
#                                                                                                                    #
# FILE          :  constants.py                                                                                      #
#                                                                                                                    #
# DESCRIPTION   :  Contains the constant files                                                                       #
#                                                                                                                    #
# VERSION       :  4.0                                                                                               #
#                                                                                                                    #
# HISTORY       :                                                                                                    #
#                                                                                                                    #
# Date          | Author                      |     Modification                                                     #
# 16.02.2018    | Sounak Patra (RBEI/ECA2)    |     Added constant files                                             #
# 11.05.2018   	| Sounak Patra (RBEI/ECQ2)    |     Updated window title                                             #
# 14.06.2018   	| Sounak Patra (RBEI/ECQ2)    |     Updated help document                                            #
# 02.08.2018   	| Sounak Patra (RBEI/ECQ2)    |     Updated window title and help document                           #
#                                                                                                                    #
######################################################################################################################
import os

# Artifactoy server URLs
ARTIFACTORY_SERVERS = {
    "HI": "https://rb-cmbinex-hi-p1.de.bosch.com/artifactory",
    "KOR": "https://rb-cmbinex-kor-p1.apac.bosch.com/artifactory",
    "COB": "https://rb-cmbinex-cob-p1.apac.bosch.com/artifactory",
    "SZH": "https://rb-cmbinex-szh-p1.apac.bosch.com/artifactory",
    "PG": "https://rb-cmbinex-pg-p1.apac.bosch.com/artifactory",
    "FE": "https://rb-cmbinex-fe-p1.de.bosch.com/artifactory",
    "LUND": "https://rb-cmbinex-lud-p1.emea.bosch.com/artifactory",
    "HC": "https://rb-cmbinex-lth-p1.apac.bosch.com/artifactory",
    "BP": "https://rb-cmbinex-bp-p1.emea.bosch.com/artifactory",
}
# config file to store user credentials and server details
CONFIG_PATH = os.path.join(os.getenv("USERPROFILE", ""), ".artifactory")
# config file to repository name and downlaod path
REPO_CONFIG_PATH = os.path.join(os.getenv("USERPROFILE", ""), ".artifactorytoolconfig")
# Name of the application
WINDOW_TITLE = "Artefact Downloader V4.0"
# Stylesheet of download button
DOWNLOAD_BUTTON_STYLE = "background-color: qlineargradient(x1: 0, y1: 0,\
                         x2: 0, y2: 1, stop: 0 #2198c0, stop: 1 #0d5ca6);\
                         border-style: outset;\
                         border-width: 2px;\
                         border-radius: 7px;\
                         border-color: #ffffff;\
                         font: bold 12px;\
                         min-width: 10em;\
                         padding: 5px"
# Stylesheet of cancel button
CANCEL_BUTTON_STYLE = "background-color: qlineargradient(x1: 0, y1: 0,\
                       x2: 0, y2: 1, stop: 0 #cf1d1d, stop: 1 #b62424);\
                       border-style: outset;\
                       border-width: 2px;\
                       border-radius: 7px;\
                       border-color: #ffffff;\
                       font: bold 12px;\
                       min-width: 10em;\
                       padding: 5px"
# Number of worker threads
# MAX_WORKER_THREADS = 5
# Text of help window
HELP_WINDOW_TEXT = (
    "<p><b>1. Introduction:</b></p><p>This tool helps to download the artefacts "
    + "from artifactory.</p><p><b>2. Key features:</b></p>"
    + '<ul style="list-style-type:disc">'
    + "<li>Download artefacts from Artifactory</li>"
    + "<li>Faster download</li>"
    + "<li>SHA1 checksum based download</li>"
    + "<li>Provides all artifactory locations under a single "
    + "tool to make download easier</li>"
    + "<li>Stores Artifactory configuration (including password "
    + "handling) for next use</li>"
    + "<li>Determines the corresponding Artifactory "
    + "download server</li>"
    + "<li>Takes URL or download path as parameter</li>"
    + "<li>Automatic determination of repository name</li>"
    + "<li>Supports extended ASCII characters</li>"
    + "</ul>"
    + "<p><b>3. Version:</b> 4.0</p>"
    + "<p><b>4. How to use:</b></p>"
    + "<p></p>"
    + '<table border="1">'
    + "<tr>"
    + "<th>Option</th>"
    + "<th>Description</th>"
    + "</tr>"
    + "<tr><td> Artifactory Location </td>"
    + "<td><ul> Default Artifactory download location. "
    + "Only changeable if the default location is not available."
    + "</ul></td>"
    + "</tr>"
    + "</tr>"
    + "<tr><td> Username </td>"
    + "<td><ul> By default, the tool reads the username from "
    + "environment variable. Should not be changed."
    + "</ul></td>"
    + "</tr>"
    + "<tr><td> Password </td>"
    + "<td><ul> "
    + "It specifies the password of your user account. The "
    + "application stores the password after first use and "
    + "provides it for next use. Change the password here if it "
    + "is expired or the location has changed."
    + "</ul></td>"
    + "</tr>"
    + "<tr><td> Path or URL</td>"
    + "<td><ul> "
    + "It specifies the path of artefact that you will download. "
    + "You can also specify the URL of artefact."
    + "</ul></td>"
    + "</tr>"
    + "<tr><td> Repository Name </td>"
    + "<td><ul> "
    + "It specifies the repository name from where you will "
    + "download the artefact. It provides all the repository "
    + "names once you start typing or it can select repository name "
    + "from URL provided in Artefact Path option."
    + "</ul></td>"
    + "</tr>"
    + "<tr><td> Artefact Type </td>"
    + "<td><ul> "
    + "It specifies the type of the artefact i.e. folder or file."
    + "</ul></td>"
    + "</tr>"
    + "<tr><td> Download Path </td>"
    + "<td><ul> "
    + "It specifies the path where the artefact will be downloaded. "
    + "Click on the button and one dialog window will pop up. "
    + "Create or select an existing folder and click on 'Choose' or "
    + "path will be created automatically based on provided "
    + "artefact path in user directory."
    + "</ul></td>"
    + "</tr>"
    + "</table>"
    + "<p><b>Wiki page: </b>"
    + '<a href="https://inside-docupedia.bosch.com/confluence/display/cmmtg/Binary+Repository">'
    + "https://inside-docupedia.bosch.com/confluence/display/cmmtg/Binary+Repository</a>"
    + "</p>"
    + "<p><b>Example:</b></p>"
    + '<ul style="list-style-type:disc">'
    + "<li><p><b>Use case 1:</b></p>"
    + "<p>To download artefacts from "
    + "https://rb-cmbinex-kor-p1.apac.bosch.com/artifactory/cmmtg-tools/artefactdownloader/latestversion:</p>"
    + '<ul style="list-style-type:square">'
    + "<li>provide password for authentication (only for first "
    + "time)</li>"
    + "<li>paste complete artefact URL into 'Path or URL'. "
    + "Repository Name and Artefact Path will be selected "
    + "automatically</li>"
    + "<li>select 'Folder' as Artefact Type</li>"
    + "<li>choose download path or path will be "
    + "created automatically based on artefact path</li>"
    + "<li>click on Download button to proceed</li>"
    + "</li>"
    + "<li><p><b>Use case 2:</b></p>"
    + "<p>To download artefacts from "
    + "https://rb-cmbinex-kor-p1.apac.bosch.com/artifactory/cmmtg-tools/artefactdownloader/latestversion:</p>"
    + '<ul style="list-style-type:square">'
    + "<li>select Artifactory location as KOR</li>"
    + "<li>provide password for authentication</li>"
    + "<li>enter 'cmmtg-tools' in Repository Name</li>"
    + "<li>paste 'artefactdownloader/latestversion' into "
    + "'Path or URL'</li>"
    + "<li>select Folder as Artefact Type</li>"
    + "<li>choose download path or path will be "
    + "created automatically based on artefact path</li>"
    + "<li>click on Download button to proceed</li>"
    + "</li>"
    + "</ul>"
)
