import argparse
from pathlib import Path
from os import makedirs
from shutil import copy

from generation_tools.port_encoder import PortEncoder
from generation_tools.verilog_generator import VerilogGenerator
from sys import argv

SUPPORTED_INTERFACES = ['atlys']

def main():
    parser = argparse.ArgumentParser(description="Generator for JSON config and top Verilog interface module")
    parser.add_argument("-s", "--source_path", help="Path to Verilog source file (top module)", required=True)
    parser.add_argument("-i", "--interface", help="Interface schema to use when generating Verilog files", choices=SUPPORTED_INTERFACES, default=None)
    parser.add_argument("clock_signals", help="Names of clock signals present in source file", nargs='*')
    parser.add_argument("-o", "--output_path", help="Path where generated files should be saved", default=Path())
    parser.add_argument("--inout_enables", help="List signal names that drive tri-state buffers of inout signals (in order as defined in Verilog source)", nargs="*")
    parser.add_argument("--inout_active", help="List of signal levels indicating that inout_enable signals are allowing for driving tri-state buffer (active low / active high; in order as defined for --inout_enables)", nargs="*", choices=["0", "1"])

    args = parser.parse_args()

    source_path = Path(args.source_path)
    output_path = Path(args.output_path) / (source_path.stem + "_gen")
    makedirs(output_path, mode=777, exist_ok=True)
    port_encoder = PortEncoder()
    port_encoder.parse_to_file(source_path, args.clock_signals, output_path, args.interface.lower(), args.inout_enables, args.inout_active)
    code_generator = VerilogGenerator()
    config_path = output_path / (source_path.stem + "_config.json")
    code_generator.create_top_module(args.interface, source_path, config_path, output_path)
    used_interface_path = Path(f"./generation_tools/hdl/interfaces/{args.interface}/interface_{args.interface}.v")
    copy(used_interface_path, output_path)
    pulsegen_path = Path("./generation_tools/hdl/pulsegen_with_counter.v")
    copy(pulsegen_path, output_path)
    if args.inout_enables:
        inout_writer_path = Path("./generation_tools/hdl/inout_writer.v")
        copy(inout_writer_path, output_path)

if __name__ == "__main__":
    main()