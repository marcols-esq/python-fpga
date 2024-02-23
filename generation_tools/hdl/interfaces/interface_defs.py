FPGA_INTERFACES = ["atlys"]
# After adding a new interface, its main CLK name is required in here:
INTERFACE_CLK_SIGNAL_NAMES = ["CLK"]

DATA_WIDTH = 8
INPUT_KEYWORD = "input"
OUTPUT_KEYWORD = "output"
INOUT_KEYWORD = "inout"
INPUT_MUX_NAME = "inputs"
OUTPUT_MUX_NAME = "outputs"
DATA_OUTPUT_PORT_NAME = "DATA_TX"
DATA_INPUT_PORT_NAME = "DATA_RX"
ADDRESS_PORT_NAME = "ADDR"