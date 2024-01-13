from port_tools.port import IoPort, ClockPort


class UsbInterface(object):
    def __init__(self) -> None:
        pass

    def read(self, port: IoPort) -> int:
        pass

    def write(self, port: IoPort, value: int) -> bool:
        pass

    def write_clock_cycles(self, port: ClockPort, cycles: int) -> bool:
        pass
