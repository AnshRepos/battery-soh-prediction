"""
    This Library is developed and maintained by BGSW

    File_name       :   tools.py
    Description     :   This File contains the classes to
                        handling logging and paths

    Date        Version   Author             Comments
    ***********************************************************************
    18-04-2022  1.0       myo1cob            Initial Development
    ***********************************************************************

"""
import sys
from robot.libraries.BuiltIn import BuiltIn
import os

global robot_executed


class Logging:
    """
    class for handling logging based on trigger instance.
    i.e., python, robot
    """

    def __init__(self):
        global robot_executed
        cmd_line_args = sys.argv

        python_execute_checker = cmd_line_args[-1].split(".")[-1].lower()

        if python_execute_checker == "py":
            robot_executed = False
        else:
            robot_executed = True

    def info(self, text, html=False):
        """
        basic logger info and image embedding is handled in this method

        :param:
            :text: logging info.
            :html: if the info needs to be HTML styled.

        :return: None
        """
        if html:
            if robot_executed:
                print("*HTML* "+text)
        else:
            print(text)


class PathHandler:
    """
    class for handling paths based on trigger instance.
    i.e., python, robot
    """

    def __init__(self):
        global robot_executed
        cmd_line_args = sys.argv

        python_execute_checker = cmd_line_args[-1].split(".")[-1].lower()

        if python_execute_checker == "py":
            robot_executed = False
        else:
            robot_executed = True

    def get_output_directory(self):
        """
        returns the output directory path.

        :param: None.

        :return: None.
        """
        if robot_executed:
            output_directory = BuiltIn().get_variable_value("${OUTPUT_DIR}")
        else:
            output_directory = os.getcwd()
        return output_directory
