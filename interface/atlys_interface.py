import logging
import ctypes
import os
import subprocess
from re import search
from sys import stdout
from time import sleep

from .fpga_interface import FpgaInterface

DMGR_DLL_PATH = os.path.join(os.path.dirname(__file__), "..\\lib64\\dmgr.dll")
DJTG_DLL_PATH = os.path.join(os.path.dirname(__file__), "..\\lib64\\djtg.dll")
DSTM_DLL_PATH = os.path.join(os.path.dirname(__file__), "..\\lib64\\dstm.dll")
DPC_DLL_PATH = os.path.join(os.path.dirname(__file__), "..\\lib64\\dpcutil.dll")
DEPP_DLL_PATH = os.path.join(os.path.dirname(__file__), "..\\lib64\\depp.dll")

MAX_NAME_LENGTH = 64
MAX_PATH_LENGTH = 260
MAX_ERR_LENGTH = 128
DEVICE_NAME = "Atlys"
JTAG_PROGRAM_EXE_PATH = os.path.join(
    os.path.dirname(__file__), "..\\binaries\\djtgcfg.exe"
)


class DVT(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * MAX_NAME_LENGTH),
        ("connection_string", ctypes.c_char * (MAX_PATH_LENGTH + 1)),
    ]


class AtlysInterface(FpgaInterface):
    def __init__(self, bitfile_path=None) -> None:
        super().__init__()
        self.dmgr_lib = ctypes.CDLL(str(DMGR_DLL_PATH))
        self.djtg_lib = ctypes.CDLL(str(DJTG_DLL_PATH))
        self.dstm_lib = ctypes.CDLL(str(DSTM_DLL_PATH))
        self.depp_lib = ctypes.CDLL(str(DEPP_DLL_PATH))
        self.logger, self.err_logger = self._setup_loggers()
        self.interface_handle = ctypes.c_uint32(0)

        self._define_lib_function_params()
        if self._is_connected():
            device = ctypes.create_string_buffer(
                size=len(DEVICE_NAME), init=DEVICE_NAME.encode()
            )
            if bitfile_path is not None:
                self._program_device(bitfile_path)
            self._call_func(
                self.dmgr_lib.DmgrOpen, ctypes.byref(self.interface_handle), device
            )
            self._call_func(self.depp_lib.DeppEnable, self.interface_handle)

    def __del__(self):
        self.depp_lib.DeppDisable(self.interface_handle)
        self.dmgr_lib.DmgrClose(self.interface_handle)
        self.dmgr_lib.DmgrFreeDvcEnum()

    def _setup_loggers(self):
        logger = logging.getLogger("AtlysLog")
        format = logging.Formatter(
            "[%(levelname)s] AtlysInterface::%(funcName)s(): %(message)s"
        )
        handler = logging.StreamHandler(stdout)
        handler.setFormatter(format)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        err_logger = logging.getLogger("AtlysErrLog")
        err_format = logging.Formatter("[%(levelname)s] AtlysInterface::%(message)s")
        err_handler = logging.StreamHandler(stdout)
        err_handler.setFormatter(err_format)
        err_logger.addHandler(err_handler)
        err_logger.setLevel(logging.ERROR)
        return logger, err_logger

    def _define_lib_function_params(self):
        # Dmgr
        self.dmgr_lib.DmgrEnumDevices.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self.dmgr_lib.DmgrEnumDevices.restype = ctypes.c_bool
        self.dmgr_lib.DmgrGetDvc.argtypes = [ctypes.c_int, ctypes.POINTER(DVT)]
        self.dmgr_lib.DmgrGetDvc.restype = ctypes.c_bool
        self.dmgr_lib.DmgrOpen.argtypes = [
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_char_p,
        ]
        self.dmgr_lib.DmgrOpen.restype = ctypes.c_bool
        self.dmgr_lib.DmgrClose.argtypes = [ctypes.c_uint32]
        self.dmgr_lib.DmgrGetLastError.argtypes = None
        self.dmgr_lib.DmgrGetLastError.restype = ctypes.c_int
        self.dmgr_lib.DmgrSzFromErc.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        self.dmgr_lib.DmgrSzFromErc.restype = ctypes.c_bool

        # Depp
        self.depp_lib.DeppEnable.restype = ctypes.c_bool
        self.depp_lib.DeppPutReg.argtypes = [
            ctypes.c_uint32,
            ctypes.c_byte,
            ctypes.c_byte,
            ctypes.c_bool,
        ]
        self.depp_lib.DeppPutReg.restype = ctypes.c_bool
        self.depp_lib.DeppGetReg.argtypes = [
            ctypes.c_uint32,
            ctypes.c_byte,
            ctypes.POINTER(ctypes.c_byte),
            ctypes.c_bool,
        ]
        self.depp_lib.DeppGetReg.restype = ctypes.c_bool

    def _call_func(self, func, *args) -> bool:
        """
        Calls a C function with args, return status

        If the call fails, fetch error code and log an error
        """
        if not func(*args):
            err_code = self.dmgr_lib.DmgrGetLastError()
            err_msg = ctypes.create_string_buffer(MAX_ERR_LENGTH)
            err_code_name = ctypes.create_string_buffer(MAX_ERR_LENGTH)
            self.dmgr_lib.DmgrSzFromErc(err_code, err_code_name, err_msg)
            self.err_logger.error(
                f"{func.__name__}(): {err_code_name.value.decode()} - {err_msg.value.decode()}"
            )
            return False
        return True

    def _is_connected(self) -> bool:
        device_num = ctypes.c_int()
        success = self.dmgr_lib.DmgrEnumDevices(ctypes.byref(device_num))
        if success:
            if device_num.value:
                self.logger.debug(
                    f"Found {device_num.value} Digilent device"
                    + ("s" if device_num.value > 1 else "")
                )
                for device in range(device_num.value):
                    device_info = DVT()
                    self.dmgr_lib.DmgrGetDvc(
                        ctypes.c_int(device), ctypes.byref(device_info)
                    )
                    if device_info.name.decode() == DEVICE_NAME:
                        self.logger.debug("Found Atlys device")
                    return True
            self.logger.info("No Atlys device found")
        else:
            self.logger.debug("Error enumerating device")
        return False

    def _program_device(self, bitfile_path):
        delay_after_prog = 5
        res = subprocess.run(
            f"{JTAG_PROGRAM_EXE_PATH} -d {str(DEVICE_NAME)} init", capture_output=True
        )
        device_id = search(r"(?<=Device )[0-9]+", str(res.stdout))
        self.logger.info(f"Attempting to program {DEVICE_NAME} device...")
        res = subprocess.run(
            f"{JTAG_PROGRAM_EXE_PATH} -d {str(DEVICE_NAME)} -i {device_id[0]} "
            + f"prog -f {bitfile_path}",
            stdout=subprocess.DEVNULL,
        )
        if res.returncode != 0:
            self.logger.error(
                f"Programming {DEVICE_NAME} device failed. Error code: {res.returncode}"
            )
            return
        self.logger.info("Programming succeeded.")
        self.logger.info(f"Waiting {delay_after_prog} seconds to let FPGA boot up...")
        sleep(delay_after_prog)  # wait a bit for FPGA to start up

    def write(self, address: int, value: int) -> bool:
        no_overlap = ctypes.c_bool(False)
        c_address = ctypes.c_byte(address)
        c_value = ctypes.c_byte(value)
        return self._call_func(
            self.depp_lib.DeppPutReg,
            self.interface_handle,
            c_address,
            c_value,
            no_overlap,
        )

    def read(self, address: int) -> int:
        no_overlap = ctypes.c_bool(False)
        c_address = ctypes.c_byte(address)
        c_readValue = ctypes.c_byte(0)
        self._call_func(
            self.depp_lib.DeppGetReg,
            self.interface_handle,
            c_address,
            ctypes.byref(c_readValue),
            no_overlap,
        )
        return int(c_readValue.value)
