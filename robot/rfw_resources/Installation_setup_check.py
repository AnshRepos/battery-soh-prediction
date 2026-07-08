try:
    import os

    import rfwresourcelib

    path = os.path.dirname(rfwresourcelib.__file__)
    exe_path = path + "\\gm\\ADB_Shell\\adb.exe"
    os.path.isfile(exe_path)
    print("Installation was successful......")

except Exception as err:
    print(str(err))
    print("Error occurred during installation, contact support team ask2cob,rru5cob")
