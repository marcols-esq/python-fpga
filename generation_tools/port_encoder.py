import json
import re
from math import ceil
from pathlib import Path
from typing import List

import generation_tools.hdl.interfaces.interface_defs as defs

PARAMETER_KEYWORD = "parameter"
REG_KEYWORD = "reg"

class PortEncoder(json.JSONEncoder):
    def __init__(self):
        self.json_body = {}
        self.port_list = []
        self.next_input_address = 0
        self.next_output_address = 0
        self.verilog_params = {}
        self.clk_port_names = List[str]
        self.inout_params = []

    def parse(self, file_path: Path, clock_ports: List[str], fpga_interface: str=None):
        self.clk_port_names = clock_ports

        if fpga_interface is not None:
            self.json_body["fpga_interface"] = fpga_interface

        with open(file_path, "rt") as file:
            for line in file:
                keywords = line.split()
                if keywords and "//" not in keywords[0]:
                    if PARAMETER_KEYWORD == keywords[0]:
                        param_value = re.findall(r"([0-9]+)[;,]*", " ".join(keywords))
                        self.verilog_params[keywords[1]] = int(param_value[0])
                    elif defs.INPUT_KEYWORD in keywords[0] or defs.OUTPUT_KEYWORD in keywords[0] or defs.INOUT_KEYWORD in keywords[0]:
                        self._parse_port_definition(keywords)
        
        self.json_body["ports"] = self.port_list
    
    def parse_to_file(self, file_path: Path, clock_ports: List[str], output_path: Path, fpga_interface: str=None, inout_enables: List[str] = [], inout_active: List[str] = []):
        if inout_enables:
            if len(inout_enables) != len(inout_active):
                print("PortEncoder::parse_to_file(): Number of inout_enables does not match inout_active\n")
            for i in range(len(inout_enables)):
                self.inout_params.append((inout_enables[i], inout_active[i]))
        self.parse(file_path, clock_ports, fpga_interface)
        config_file_name = file_path.stem + "_config.json"
        with open(output_path / config_file_name, "wt") as file:
            file.write(json.dumps(self.json_body, indent=4))

    def get_encoded_port_list(self):
        return self.port_list

    def _extract_signal_names(self, params: List[str]) -> List[str]:
        s = " ".join(params)
        names = re.findall(r"([^;, ]+)", s)
        return names

    def _parse_port_definition(self, params: List[str]):
        # remove potential 'reg' keyword that may be present at outputs
        if REG_KEYWORD in params:
            params.pop(params.index(REG_KEYWORD))
        # if defined port is a vector, extract its width
        if '[' and ']' in params[1]:
            vector_range = "".join(char for char in params[1] if char not in '[]').split(':')
            msb = self.verilog_params[vector_range[0]] if vector_range[0] in self.verilog_params else int(vector_range[0])
            lsb = self.verilog_params[vector_range[1]] if vector_range[1] in self.verilog_params else int(vector_range[1])
            bit_width = msb - lsb + 1
            names = self._extract_signal_names(params[2:])
        else:
            bit_width = 1
            names = self._extract_signal_names(params[1:])
        
        for name in names:
            is_clock_port = True if name in self.clk_port_names else False
            if self.inout_params and params[0] == defs.INOUT_KEYWORD:
                enable_signal = self.inout_params[0][0]
                enable_signal_active = self.inout_params[0][1] 
                self.inout_params.pop(0)
            else:
                enable_signal = None
                enable_signal_active = None
            self._create_port(name=name, is_clock_port=is_clock_port, bit_width=bit_width, direction=params[0], enable_signal=enable_signal, enable_signal_active=enable_signal_active)

    def _create_port(self, **kwargs):
        bit_width = kwargs.get("bit_width", 1)
        direction = kwargs.get("direction", "input")
        port = {}
        port["name"] = kwargs.get("name")
        port["clock_port"] = kwargs.get("is_clock_port", False)
        port["bit_width"] = bit_width
        port["direction"] = direction
        if direction == defs.INOUT_KEYWORD:
            port["enable_signal"] = kwargs.get("enable_signal")
            port["enable_signal_active"] = kwargs.get("enable_signal_active")
        port["address"] = []
        for i in range(ceil(bit_width / defs.DATA_WIDTH)):
            if direction == defs.OUTPUT_KEYWORD:
                next_address = self.next_output_address
                self.next_output_address += 1
            else:
                next_address = self.next_input_address
                self.next_input_address += 1

            port["address"].append(f"{next_address:x}")

        self.port_list.append(port)