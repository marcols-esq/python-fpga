#
#   Old interface for testing purposes - do not use
#

import os
import ctypes

from .usb_interface import UsbInterface

FTD2XX_DLL_PATH = os.path.join(os.path.dirname(__file__), "..\\lib64\\ftd2xx64.dll")

FT_LIST_DEVICES_FLAGS = {
    "number_only": 0x80000000,
    "by_index": 0x400000000,
    "all": 0x20000000,
}


class Ftd2xxInterface(UsbInterface):
    def __init__(self):
        ftd2xx_lib = ctypes.CDLL(FTD2XX_DLL_PATH)

        ftd2xx_lib.FT_ListDevices.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        ftd2xx_lib.FT_ListDevices.restype = ctypes.c_uint32

        device_num = ctypes.c_uint32(0)
        ret = ftd2xx_lib.FT_ListDevices(
            ctypes.byref(device_num), None, FT_LIST_DEVICES_FLAGS["number_only"]
        )
        print(ret)
        print(device_num.value)
