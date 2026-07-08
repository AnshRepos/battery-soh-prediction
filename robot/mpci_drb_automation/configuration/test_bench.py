# -------- PPS Configuration -------- #
PPS_ADDR = "192.168.3.123"
PPS_BAUDRATE = None
PPS_VENDOR = "R_S_HMC_8042_PPS"
INTERFACE_TYPE = "ETHERNET"
PPS_VOLTAGE = 12
PPS_CURRENT = 12

# -------- SSH Configuration -------- #
SSH_HOST = "192.168.0.11"
SSH_USER = "root"
SSH_PASSWORD = "root"
SSH_TIMEOUT = 20

# -------- File Transfer ------------ #
Recovery_Mode = False
REMOTE_DIRECTORY = "/scratch"
RECOVERY_REMOTE_DIRECTORY = "/tmp"
LOCAL_DIRECTORY = r"D:/WAM5KOR/SW/Robot_Framework/conan_package_all"

# -------- LUM Stub -------- #
LUM_APP_PATH = "/usr/sbin"
LUM_CMD = "./rbLumStubApp"
LOCAL_TGZ = "C:/Users/WPW2KOR/Downloads/conan_package_LUM/mpci-enve-b-2.4.0-system.tgz_c"
REMOTE_DIR = "/scratch"
PERMISSIONS = 0o744

# -------- Logs -------- #
LOG_PATH = "/tmp/slog.txt"

ELF_FILE = "C:/build/output/application.elf"
FUNCTIONS = ["init", "rb_pcb_tempmon_init", "Iic_Write"]

# -------- CANoe Configuration -------- #
CAN_CFG = "C:/Users/WPW2KOR/Downloads/gl2_CAN.cfg"
ONE_RBS = "C:/RFW/_DRB-jobs_drb-sw-sys-vnv_develop/test/canoe/01_RBS/OneRBS/MPCI_RBS.cfg"
CHANNEL = 1
CAN_BAUDRATE = 500000
REQ_CAN_ID = 0x10
RESP_CAN_ID = 0x1D
EVENT_ID = 0x80
TIMEOUT = 10

# -------- TRACE32 -------- #
exe_path = "C:/T32/bin/windows64/t32marm.exe"
config_file_path = "C:/T32"
cmm_script_path = "C:/T32/demo/arm/hardware/versal/vck190/vck190-cr5/vck190-cr5_sieve_sram.cmm"
ftti_time_limit = 1200
dll_path = "C:/T32/demo/api/python/legacy/t32api64.dll"
config_file_contents = [
    b"\n",
    b"OS=\n",
    ("SYS=" + config_file_path + "\n").encode("ascii"),
    b"TMP=C:\\Users\\wpw2kor\\AppData\\Local\\Temp\n",
    b"ID=T32_1000001\n\n",
    b"PBI=\n",
    b"USB\n\n",
    b"SCREEN=\n",
    b"FONT=SMALL\n",
    b"HEADER=TRACE32 PowerView for TriCore 0 [Power Debug USB @ ]\n\n",
    b"RCL=NETASSIST\n",
    b"PACKLEN=1024\n",
    b"PORT=20000\n",
]

# -------- DLT Viewer -------- #
ECU = "QNX"
DLT_MODE = 0
TRACE_PATH = "D:/DLT/GM_VCU.trc"
PLUGIN_PATH = "D:/DLT/GMVCU_DLT_TCS.xml"
ECU_BAUDRATE = 115200
DLT_CTID = "ADIS"
DLT_TIMEOUT = 10
DLT_FILE = "adis_dlt_capture.dlt"
# DLT_FILE = "adis_dlt_capture.dlt"
DLT_IP = "fe80::7d:faff:fe01:8600"
