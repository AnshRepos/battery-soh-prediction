######################################################################################################################
#                                                                                                                    #
# FILE          :  artefact_downloader.py                                                                            #
#                                                                                                                    #
# DESCRIPTION   :  Creates UI to download artefacts from Artifactory                                                 #
#                                                                                                                    #
# VERSION       :  4.0                                                                                               #
#                                                                                                                    #
# HISTORY       :															                                         #
#                                                                                                                    #
# Date          | Author                      |     Modification                                                     #
# 07.02.2018    | Sounak Patra (RBEI/ECA2)    | 	Created UI 				                                         #
# 16.02.2018    | Sounak Patra (RBEI/ECA2)    | 	Updated option to read data from config file and added help      #
#                                                   window	                                                         #
# 07.06.2018    | Sounak Patra (RBEI/ECQ2)    |     Improved download performance and fixed improper text color in   #
#                                                   log window 				                                         #
# 13.06.2018    | Sounak Patra (RBEI/ECQ2)    |     Feature added to initiate checksum based download                #
# 14.06.2018    | Sounak Patra (RBEI/ECQ2)    |     Updated directory creation based on artefact path                #
# 02.08.2018    | Sounak Patra (RBEI/ECQ2)    |     Created custom widget to update context menu of toolbar and log  #
#                                                   window                                                           #
#                                                                                                                    #
######################################################################################################################
import concurrent.futures
import json
import os
import socket
import sys
import threading
import time

import constants as con
import download_artefacts as da
from PySide import QtCore, QtGui
from urlparse import urlparse


class CustomToolbar(QtGui.QToolBar):
    """
    Class to add custom features of QToolbar.
    """

    def __init__(self, *args, **kargs):
        super(CustomToolbar, self).__init__(*args)
        self.menu = None
        self.log_window = kargs["log_window"]
        self.__create_custom_context_menu()

    def __create_custom_context_menu(self):
        # Adds custom context menu
        self.log_window_action = QtGui.QAction(self)
        self.log_window_action.setCheckable(True)
        self.log_window_action.setChecked(True)
        self.log_window_action.setText(self.log_window.windowTitle())
        self.log_window_action.triggered.connect(self.__display)
        self.menu = QtGui.QMenu(self)
        self.menu.addAction(self.log_window_action)

    def __display(self):
        # Checks/unchecks the checkbox
        if self.log_window_action.isChecked():
            self.log_window.show()
        else:
            self.log_window.hide()

    def contextMenuEvent(self, event):
        """
        Brings up context menu on clicked mouse cursor position.

        Parameters
        ----------
        event (object): Specifies the click event.
        """
        if self.menu:
            self.menu.exec_(QtGui.QCursor.pos())

    def set_log_window_status(self, value):
        """
        Set the checkbox action status.

        Parameters
        ----------
        value (bool): Unchecks the checkbox if specified as false .
        """
        self.log_window_action.setChecked(value)


class CustomDockWidget(QtGui.QDockWidget):
    """
    Class to add custom features of QDockWidget.
    """

    def __init__(self, *args, **kargs):
        self.parent_widget = args[1]
        super(CustomDockWidget, self).__init__(*args)

    def contextMenuEvent(self, event):
        """
        Overrides the default contextMenuEvent of QDockWidget.

        Parameters
        ----------
        event (object): Specifies the click event.
        """
        return

    def closeEvent(self, event):
        """
        Overrides the default closeEvent of QDockWidget.

        Parameters
        ----------
        event (object): Specifies the click event.
        """
        self.parent_widget.set_dock_widget_state(False)

    def showEvent(self, event):
        """
        Overrides the default showEvent of QDockWidget.

        Parameters
        ----------
        event (object): Specifies the click event.
        """
        self.parent_widget.set_dock_widget_state(True)


class DownloaderWindow(QtGui.QMainWindow):
    """
    Class to create UI for application.
    """

    sig_file_count = QtCore.Signal(list)  # Signal to initiate download
    sig_progress_count = QtCore.Signal(int, bool)  # Signal to update progress
    sig_instance_status = QtCore.Signal(bool)  # Signal to update instance
    sig_enable_cancel_btn = QtCore.Signal(bool)  # Enable/Disable cancel button
    sig_update_log = QtCore.Signal(str)  # Updates log window
    sig_set_log_color = QtCore.Signal(str)  # Updates log window test color
    sig_cancelled_files = QtCore.Signal(str)  # Updates cancelled files

    def __init__(self):
        super(DownloaderWindow, self).__init__()
        # Dictionary that contains all artifactory instances
        self.d_art_instance = con.ARTIFACTORY_SERVERS
        self.toolbar = None
        self.https_url = True
        self.help_open = False
        self.cancel_download = False
        # Stores information about download path
        self.download_path = None
        self.download_path_original = None
        # List to store repository names
        self.repo_names = []
        # List to store cancelled files
        self.cancelled_files = []
        # Specifies the configuration file path to store user data
        self.config_path = con.CONFIG_PATH
        self.repo_config_path = con.REPO_CONFIG_PATH
        # Creates UI
        self.create_ui()
        # Connects signals to slots
        self.sig_file_count.connect(self.__read_file_completion)
        self.sig_progress_count.connect(self.__update_progress_bar)
        self.sig_instance_status.connect(self.__update_art_instance_option)
        self.sig_enable_cancel_btn.connect(self.__update_cancel_button)
        self.sig_update_log.connect(self.__update_log_window)
        self.sig_set_log_color.connect(self.__update_log_window_text_color)
        self.sig_cancelled_files.connect(self.__update_cancelled_files)
        # Reads config file if present
        self.__read_config()

    def __create_config(self, d_data):
        # Stores user data in json format.
        with open(self.repo_config_path, "w") as fp:
            json.dump({"REPOSITORY": d_data["REPOSITORY"], "DOWNLOADPATH": d_data["DOWNLOADPATH"]}, fp)
        with open(self.config_path, "w") as file:
            url = d_data["SERVER"]
            if not self.https_url:
                url = url.replace("https", "http")
                url = url.replace("com", "com:8081")
            file.write("SERVER=" + url + "\n")
            file.write("USER=" + d_data["USER"] + "\n")
            file.write("PWD=" + d_data["PWD"] + "\n")

    def __set_artifactory_instance(self, text):
        # Set artifactory instance
        index = self.combo_box.findText(text, QtCore.Qt.MatchFixedString)
        self.combo_box.setCurrentIndex(index)

    def __read_config(self):
        # Reads user data from config file
        l_server_data = {}
        d_repo_data = {}

        def get_subdomain(url):
            return (url.split(":")[1]).split(".")[0]

        # Read .artifactorytoolconfig file
        if os.path.isfile(self.repo_config_path):
            with open(self.repo_config_path) as json_data:
                d_repo_data = json.load(json_data)
        # Read .artifactory file
        if os.path.isfile(self.config_path):
            with open(self.config_path, "r") as conf_file:
                l_server_data = conf_file.readlines()
        if l_server_data:
            for value in l_server_data:
                if "SERVER" in value:
                    url_data = (value.split("=")[1]).rstrip()
                    if "https" not in url_data:
                        self.https_url = False
                    for serv_key, serv_url in self.d_art_instance.items():
                        if get_subdomain(url_data) == get_subdomain(serv_url):
                            self.__set_artifactory_instance(serv_key)
                            break
                elif "USER" in value:
                    self.username.setText((value.split("=")[1]).rstrip())
                elif "PWD" in value:
                    self.password.setText((value.split("=")[1]).rstrip())

            if d_repo_data:
                self.repo_name.setText(d_repo_data["REPOSITORY"])
                self.download_path = str(d_repo_data["DOWNLOADPATH"])
                self.download_path_original = self.download_path
                self.log_window.append("INFO: Selected download path: " + self.download_path)
                self.download_label.setText(str(self.download_path))
        else:
            full_domain_name = socket.getfqdn().split(".", 1)
            if len(full_domain_name) > 1:
                dns_domain = full_domain_name[1].split(".")[0]
                if dns_domain.upper() in self.d_art_instance.keys():
                    self.__set_artifactory_instance(dns_domain.upper())

    def __update_progress_bar(self, progress_count, set_externally):
        # Updates progress bar percentage
        if set_externally:
            self.progress_bar.setValue(progress_count)
        else:
            self.download_file_count += progress_count
            if self.download_file_count == self.total_no_of_files:
                self.progress_bar.setValue(100)
                self.sig_set_log_color.emit("green")
                self.log_window.append("INFO: Download has been completed")
                self.sig_set_log_color.emit("black")
                self.download_button.setDisabled(False)
                self.sig_enable_cancel_btn.emit(True)
                time.sleep(2)
                self.progress_bar.setValue(0)
            else:
                self.progress_bar.setValue(self.download_file_count * self.progress_level_value)

    def __get_repo_list(self):
        # Process the list of repository names from artifactory
        try:
            result = json.loads(
                da.get_output(
                    self.d_art_instance[self.combo_box.currentText()] + "/api/repositories",
                    self.username.text(),
                    self.password.text(),
                )
            )
            self.repo_names = [value["key"] for value in result]
            if not self.completer:
                self.completer = QtGui.QCompleter()
                self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                self.repo_name.setCompleter(self.completer)
            model = QtGui.QStringListModel()
            model.setStringList(self.repo_names)
            self.completer.setModel(model)
        except Exception as ex:
            if self.completer:
                self.repo_names = []
                model = QtGui.QStringListModel()
                model.setStringList(self.repo_names)
                self.completer.setModel(model)
            print(ex)
            self.log_window.append(
                "ERROR: Please update your password " + "for " + self.combo_box.currentText() + " artifactory instance"
            )

    def __text_change(self, val):
        # Process repository names from artifactory on change of text in repository name field
        if self.combo_box.currentText() != "NONE" and not self.repo_names:
            self.__get_repo_list()

    def __set_download_path(self):
        # Set download path
        if not self.download_path:
            drive = os.path.splitdrive(os.getenv("USERPROFILE"))[0]
            self.download_path = os.path.join(drive, os.sep, os.path.normpath(self.artifact_path.text()))
        else:
            self.download_path = os.path.normpath(os.path.join(self.download_path_original, self.artifact_path.text()))

        self.download_label.setText(self.download_path)
        self.log_window.append("Selected download path: " + str(self.download_path))

    def __artefact_path_change(self, val):
        # Slot to set artifactory instance, repository and artefact path if full URL path is provided as input
        # to artefact path
        correct_path = self.artifact_path.text().rstrip()
        if "http:" in correct_path:
            parsed_data = urlparse(correct_path)
            port = parsed_data.port
            correct_path = correct_path.replace("http:", "https:")
            correct_path = correct_path.replace(":" + str(port), "")

        if "https" in correct_path:
            # Normalizing artifactory native browser URL
            if "/artifactory/list/" in correct_path:
                correct_path = correct_path.replace("/artifactory/list/", "/artifactory/")
            # Normalizing artifactory web app URL
            if "/artifactory/webapp/#/artifacts/browse/tree/General/" in correct_path:
                correct_path = correct_path.replace(
                    "/artifactory/webapp/#/artifacts/browse/tree/General/", "/artifactory/"
                )
            url_path = correct_path.split("artifactory/")
            instance_url = url_path[0] + "artifactory"
            for serv_key, serv_url in self.d_art_instance.items():
                if serv_url == instance_url:
                    self.__set_artifactory_instance(serv_key)
            if len(url_path) > 1:
                artefact_path = url_path[1]
                repo_path = artefact_path.split("/", 1)
                repo = repo_path[0]
                self.repo_name.setText(str(repo))
                if len(repo_path) > 1:
                    self.artifact_path.setText(repo_path[1].strip("/"))
        else:
            self.artifact_path.setText(correct_path.strip("/"))

        if self.artifact_path.text() != "" and self.extend_path.isChecked():
            self.__set_download_path()

    def __help_closed(self):
        # Helps to set modal property of help window
        self.help_open = False

    def __add_help_window(self):
        # Creates help window
        if not self.help_open:
            self.help_open = True
            help_dialog = QtGui.QDialog(self)
            help_dialog.setWindowTitle("Help")
            help_dialog.setMinimumSize(500, 300)
            # Creates text window to show information about tool
            help_window = QtGui.QTextEdit()
            help_window.setHtml(con.HELP_WINDOW_TEXT)
            help_window.setReadOnly(True)
            layout = QtGui.QVBoxLayout()
            # Adds text window in layout
            layout.addWidget(help_window)
            # Adds layout in dialog box
            help_dialog.setLayout(layout)
            help_dialog.setModal(False)
            help_dialog.accepted.connect(self.__help_closed)
            help_dialog.rejected.connect(self.__help_closed)
            help_dialog.show()

    def __enable_button(self):
        # Enables download button
        self.download_button.setDisabled(False)

    def __update_art_instance_option(self, value):
        # Enables/Disables artifactory instance seletion option
        self.combo_box.setDisabled(value)
        # Set focus on password field if selected instance is online
        if value:
            self.password.setFocus()

    def __ping_artifactory_server(self):
        # Pings artifactoy server to check whether it is online or offline
        try:
            da.get_output(self.d_art_instance[self.combo_box.currentText()] + "/api/system/ping", None, None)
            self.log_window.append("INFO: Selected artifactory instance is online.")
            self.sig_instance_status.emit(True)
        except Exception:
            self.sig_instance_status.emit(False)
            self.log_window.append("ERROR: Selected artifactory instance is offline.")

    def __select_artifactory_instance(self, index):
        # Changes UI on artifactory instance selection
        self.repo_names = []
        if self.combo_box.currentText() == "NONE":
            self.repo_name.setDisabled(True)
            self.repo_name.clear()
            self.artifact_path.setPlaceholderText("Enter full path of artefact")
            self.log_window.append("Selected Artifactory instance: None")
        else:
            self.repo_name.setDisabled(False)
            self.artifact_path.setPlaceholderText("Enter artefact path")
            self.log_window.append(
                "Selected Artifactory instance: " + self.d_art_instance[self.combo_box.currentText()]
            )
            # Pings server to check server status
            thread = threading.Thread(target=self.__ping_artifactory_server, args=())
            thread.daemon = True
            thread.start()

    def __open_dialog(self):
        # Opens dialog window to select download path
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly)

        if dialog.exec_():
            filenames = dialog.selectedFiles()
            self.download_path = str(filenames[0])
            self.download_path_original = self.download_path
            if self.extend_path.isChecked():
                self.__set_download_path()
            else:
                self.log_window.append("Selected download path: " + str(self.download_path))
                self.download_label.setText(str(self.download_path))

    def __extend_path(self):
        # Extends download path to artefact path
        if self.extend_path.isChecked():
            self.__set_download_path()
        else:
            if self.download_path_original:
                self.download_path = os.path.normpath(self.download_path_original)
                self.log_window.append("Selected download path: " + str(self.download_path))
                self.download_label.setText(str(self.download_path))
            else:
                self.download_path = None
                self.log_window.append("Selected download path: ")
                self.download_label.setText("")

    def __read_file_completion(self, result):
        # Slots to trigger download after completion of read operation
        if result:
            file_list = result[0]
            total_no_of_files = len(file_list)
            self.sig_update_log.emit("Total no of files: " + str(total_no_of_files))

            if total_no_of_files == 0:
                self.download_button.setDisabled(False)
                self.extend_path.setDisabled(False)
            else:
                self.progress_level_value = float(100) / total_no_of_files
                uid = result[1]
                pwd = result[2]
                sha1_data = result[3]
                self.cancel_button.setDisabled(False)
                download_thread = threading.Thread(
                    target=self.download_file_artefacts, args=(file_list, uid, pwd, sha1_data)
                )
                download_thread.daemon = True
                download_thread.start()

    def __update_cancel_button(self, value):
        # Enables / Disables cancel button
        self.cancel_button.setDisabled(value)

    def __cancel_download(self):
        # Updates the value of cancellation status
        self.cancel_download = True
        self.sig_set_log_color.emit("red")
        self.log_window.append("INFO: Aborting download. Please wait...")
        self.sig_set_log_color.emit("black")
        da.update_download_status(True)

    def __update_log_window(self, text):
        # Updates text in log window
        self.log_window.append(text)

    def __update_log_window_text_color(self, color):
        # Updates text color in log window
        if color == "red":
            self.log_window.setTextColor(QtGui.QColor(255, 0, 0))
        elif color == "black":
            self.log_window.setTextColor(QtGui.QColor(0, 0, 0))
        elif color == "green":
            self.log_window.setTextColor(QtGui.QColor(0, 128, 0))

    def __update_cancelled_files(self, file):
        # Updates cancelled file list
        self.cancelled_files.append(file)

    def create_ui(self):
        """Creates the UI of the application."""
        # Creates central widget of the window
        self.central_widget = QtGui.QWidget()
        # Creates form layout to receive user input
        self.form_layout = QtGui.QFormLayout()
        # Creates dropdown list for arifactory instances
        self.combo_box = QtGui.QComboBox()
        items = ["NONE"] + self.d_art_instance.keys()
        self.combo_box.addItems(items)
        self.form_layout.addRow("Artifactory Location", self.combo_box)
        self.combo_box.currentIndexChanged.connect(self.__select_artifactory_instance)
        # Creates field to receive username
        self.username = QtGui.QLineEdit()
        self.username.setPlaceholderText("Enter your username")
        self.username.setText(os.getenv("username"))
        self.form_layout.addRow("Username", self.username)
        # Creates field to receive password
        self.password = QtGui.QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.form_layout.addRow("Password", self.password)
        # Creates field to receive artefact path
        self.artifact_path = QtGui.QLineEdit()
        self.artifact_path.textEdited.connect(self.__artefact_path_change)
        self.form_layout.addRow("Path or URL", self.artifact_path)
        # Creates field to receive repository name
        self.repo_name = QtGui.QLineEdit()
        self.repo_name.setPlaceholderText("Enter repository name")
        self.repo_name.textEdited.connect(self.__text_change)
        self.completer = None
        self.form_layout.addRow("Repository Name", self.repo_name)
        # Disables repository field if artifactory instance is selected as None
        if self.combo_box.currentText() == "NONE":
            self.repo_name.setDisabled(True)
            self.repo_name.clear()
            self.artifact_path.setPlaceholderText("Enter full URL of artefact")
        # Creates dropdown list for artefact types
        self.artefact_type = QtGui.QComboBox()
        item_types = ["Folder", "File"]
        self.artefact_type.addItems(item_types)
        self.form_layout.addRow("Artefact Type", self.artefact_type)
        # Creates dialog to choose download path
        dialog_button = QtGui.QPushButton("Select Download Path")
        dialog_button.setFixedWidth(200)
        dialog_button.clicked.connect(self.__open_dialog)
        self.form_layout.addRow("Download Path", dialog_button)
        # Creates checkbox to extend download path as artefact path
        self.extend_path = QtGui.QCheckBox("Extend download path as artefact path (Default is user directory)")
        self.extend_path.clicked.connect(self.__extend_path)
        self.form_layout.addRow("", self.extend_path)
        # Creates label to show download path
        self.download_label = QtGui.QLabel("")
        self.form_layout.addRow("", self.download_label)
        # Creates child layourt to add download and cancel button
        child_layout = QtGui.QHBoxLayout()
        # Creates downlaod button to initiate downloading
        self.download_button = QtGui.QPushButton("Download")
        self.download_button.setFixedWidth(110)
        self.download_button.setStyleSheet(con.DOWNLOAD_BUTTON_STYLE)
        self.download_button.clicked.connect(self.download_artefacts)
        # Creates cancel button to stop download
        self.cancel_button = QtGui.QPushButton("Cancel Download")
        self.cancel_button.setFixedWidth(110)
        self.cancel_button.setStyleSheet(con.CANCEL_BUTTON_STYLE)
        self.cancel_button.setDisabled(True)
        self.cancel_button.clicked.connect(self.__cancel_download)
        child_layout.addWidget(self.download_button)
        child_layout.addWidget(self.cancel_button)
        self.form_layout.addItem(child_layout)
        # Adds for layout to central widget
        self.central_widget.setLayout(self.form_layout)
        self.setCentralWidget(self.central_widget)
        # Created dock widget for logging
        self.log_window = QtGui.QTextEdit()
        self.log_window.setReadOnly(True)
        self.dock_window = CustomDockWidget("Log Window", self)
        self.dock_window.setWidget(self.log_window)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dock_window)
        # Creates toolbar of the application
        self.toolbar = CustomToolbar(self, log_window=self.dock_window)
        self.toolbar.setFixedHeight(30)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        # Adds option to close the application
        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setToolTip("Close the application")
        exit_action.triggered.connect(self.close)
        self.toolbar.addAction(exit_action)
        # Adds option to clear the log
        clear_action = QtGui.QAction("Clear Log", self)
        clear_action.setToolTip("Clear Log Window")
        clear_action.triggered.connect(self.log_window.clear)
        self.toolbar.addAction(clear_action)
        # Adds option to enable download button in case of error
        enable_download = QtGui.QAction("Enable Download", self)
        enable_download.setToolTip("Enable Download Button")
        enable_download.triggered.connect(self.__enable_button)
        self.toolbar.addAction(enable_download)
        # Adds help window
        help_action = QtGui.QAction("Help", self)
        help_action.setToolTip("Help")
        help_action.setShortcut("Ctrl+H")
        help_action.triggered.connect(self.__add_help_window)
        self.toolbar.addAction(help_action)
        # Adds progress bar to show the progress of download
        progress_label = QtGui.QLabel(self)
        progress_label.setText("	Download Progress: ")
        self.toolbar.addWidget(progress_label)
        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setGeometry(50, 50, 50, 20)
        self.toolbar.addWidget(self.progress_bar)
        # Set the width and height of the application
        self.setFixedSize(700, 500)
        # Set the application name
        self.setWindowTitle(con.WINDOW_TITLE)
        # Set the application icon
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")))
        # Set the window parameters of application
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        self.show()

    def set_dock_widget_state(self, value):
        """
        Set dock widget status in toolbar context menu

        Parameters
        ----------
        value: Boolean
            Specifies the wiget is hidden or open
        """
        self.toolbar.set_log_window_status(value)

    def download_file_artefacts(self, file_list, uid, pwd, sha1_data):
        """
        Download files from artifactory

        Parameters
        ----------
        file_list: list
            Specifies list of files which will be downloaded
        uid: string
            Specifies username
        pwd: string
            Specifies password
        sha1_data: list
            Specifies the data that contains sha1 file name and sha1 checksum values
        """
        error_list = []
        self.total_no_of_files = len(file_list)
        sha1_file, sha1_file_content, sha1_file_detail = sha1_data

        # download_dir = os.path.dirname(sha1_file)
        def time_info(time_val):
            return time.strftime("%H:%M:%S", time.gmtime(time_val))

        self.sig_update_log.emit("Download Start Time: " + time.ctime())
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for i, file in enumerate(file_list):
                if not self.cancel_download:
                    executor.submit(
                        da.download_file,
                        file[0],
                        uid,
                        pwd,
                        file[1],
                        self.sig_update_log,
                        error_list,
                        self.sig_progress_count,
                        i,
                        self.total_no_of_files,
                        self.sig_cancelled_files,
                    )

        download_time = time.time() - start_time

        if self.cancel_download:
            self.cancel_download = False
            self.sig_set_log_color.emit("red")
            self.sig_update_log.emit("INFO: Download has been cancelled")
            # Remove cancelled files from sha1 data
            if self.cancelled_files:
                for file_url in sha1_file_detail.keys():
                    if file_url in self.cancelled_files:
                        del sha1_file_content[sha1_file_detail[file_url]]
        else:
            self.sig_update_log.emit("Download time: " + time_info(download_time))

        if error_list:
            self.sig_set_log_color.emit("red")
            self.sig_update_log.emit("ERROR: Can't download below files: ")
            for err_ind, err_file in enumerate(error_list):
                if err_file in sha1_file_detail.keys():
                    del sha1_file_content[sha1_file_detail[err_file]]
                self.sig_update_log.emit(("[{0}] {1}").format(err_ind + 1, err_file))

        with open(sha1_file, "w") as fp:
            json.dump(sha1_file_content, fp)

        self.cancelled_files = []
        self.sig_enable_cancel_btn.emit(True)
        self.download_button.setDisabled(False)
        self.extend_path.setDisabled(False)
        self.sig_set_log_color.emit("black")
        time.sleep(2)
        self.sig_progress_count.emit(0, True)
        da.update_download_status(False)

    def get_folder_info(self, repo_url, down_loc, uid, pwd):
        """
        Read the list of files from artefact path

        Parameters
        ----------
        repo_url: string
            Specifies the full path of artefact in artifactory
        down_loc: string
            Specifies the downlaod path
        uid: string
            Specifies username
        pwd: string
            Specifies password
        """
        self.download_button.setDisabled(True)
        self.extend_path.setDisabled(True)
        file_list = []

        try:
            if not os.path.exists(down_loc):
                os.makedirs(down_loc)
        except Exception:
            self.sig_update_log.emit("ERROR: Cannot create directory " + down_loc)
            self.download_button.setDisabled(False)

        if self.artefact_type.currentText() == "Folder":
            # cmd_ext = '?list&deep=1&listFolders=1'
            thread = threading.Thread(
                target=da.read_file_list,
                args=(repo_url, uid, pwd, file_list, down_loc, self.sig_update_log, self.sig_file_count),
            )
            thread.daemon = True
            thread.start()
        else:
            file_list = [[repo_url, os.path.join(down_loc, os.path.basename(repo_url))]]
            modified_file_list, sha1_data = da.verify_checksum(file_list, down_loc, uid, pwd, self.sig_update_log)
            self.__read_file_completion([modified_file_list, uid, pwd, sha1_data])

    def get_encrypted_password(self, art_url, repo_name):
        """
        Get the user encrypted password from artifactory.

        Parameters
        ----------
        art_url: String
            Specifies the URL of artifactory instance
        repo_name: String
            Specifies the repository name

        Returns
        -------
        User encrypted passworad as string
        """
        enc_pwd = None
        data = {}
        try:
            enc_pwd = da.get_output(
                art_url + "/api/security/encryptedPassword", self.username.text(), self.password.text()
            )
            for _server_key, server_url in self.d_art_instance.items():
                if art_url == server_url:
                    data["SERVER"] = server_url
                    break
            data["USER"] = self.username.text()
            data["PWD"] = enc_pwd
            data["REPOSITORY"] = repo_name
            data["DOWNLOADPATH"] = self.download_path
            self.__create_config(data)
        except Exception as ex:
            self.sig_update_log.emit(
                "ERROR: Can't get encrypted password. Enter username / password correctly. " + "Abort..."
            )
            self.sig_update_log.emit("ERROR: " + str(ex))
        return enc_pwd

    def download_artefacts(self):
        """Read and download files from artifactory."""
        self.total_no_of_files = 0
        self.download_file_count = 0

        if self.download_path and self.username.text() and self.password.text():
            if self.combo_box.currentText() == "NONE":
                if self.artifact_path.text() == "":
                    self.sig_update_log.emit("ERROR: Enter full artefact path")
                else:
                    url_path = self.artifact_path.text().split("artifactory")
                    url = url_path[0] + "artifactory"
                    if len(url_path) > 1:
                        repo_name = url_path[1].split("/")[1]
                    else:
                        repo_name = ""
                    enc_pwd = self.get_encrypted_password(url, repo_name)
                    if enc_pwd:
                        self.sig_update_log.emit("INFO: Reading artefacts that will be downloaded...")
                        self.get_folder_info(
                            self.artifact_path.text(), self.download_path, self.username.text(), self.password.text()
                        )
            else:
                if self.repo_name.text() == "":
                    self.sig_update_log.emit("ERROR: Enter repository name")
                elif self.artifact_path.text() == "":
                    self.sig_update_log.emit("ERROR: Enter artefact path")
                else:
                    enc_pwd = self.get_encrypted_password(
                        self.d_art_instance[self.combo_box.currentText()], self.repo_name.text()
                    )
                    if enc_pwd:
                        self.sig_update_log.emit("INFO: Reading artefacts that will be downloaded...")
                        repo_url = (
                            self.d_art_instance[self.combo_box.currentText()]
                            + "/"
                            + self.repo_name.text()
                            + "/"
                            + self.artifact_path.text()
                        )
                        self.get_folder_info(repo_url, self.download_path, self.username.text(), self.password.text())
        else:
            self.sig_update_log.emit("ERROR: Enter value for required fields")


def main():
    app = QtGui.QApplication(sys.argv)
    DownloaderWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
