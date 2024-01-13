from sys import argv

from fpga_interface import FpgaInterface


def main():
    fpga = FpgaInterface(argv[1])
    ports = fpga.get_port_list()
    fpga.write(ports.LED, int("0xF5", 16))
    print(hex(fpga.read(ports.LED)))
    print(f"Switches: {hex(fpga.read(ports.SW))}")
    return 0


if __name__ == "__main__":
    main()
