
class FpgaInterface(object):
    def __init__(self) -> None:
        pass

    def read(self, address: int) -> int:
        pass
    
    def write(self, address: int, value: int) -> bool:
        pass

    def read_peripheral(self, peripheral_name: str):
        pass

    def write_to_peripheral(self, peripheral_name: str, value):
        pass