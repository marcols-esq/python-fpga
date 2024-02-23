import json
import re

from pathlib import Path
import generation_tools.hdl.interfaces.interface_defs as defs
from port_tools.port_manager import PortManager
from port_tools.port import ClockPort
from generation_tools.port_encoder import PortEncoder

TOP_TEMPLATE_PATH = Path("./generation_tools/hdl/top_template.txt")
CNT_PULSE_GEN_MODULE_NAME = "cnt_pulsegen"

class VerilogGenerator():
    def create_top_module(self, interface_schema: str, verilog_module_path: Path, json_path: Path, output_path: Path):
        if interface_schema not in defs.FPGA_INTERFACES:
            print("VerilogGenerator(): Unknown interface schema provided, Verilog interface module will not be generated")
            return
        
        target_interface_path = Path(f"./generation_tools/hdl/interfaces/{interface_schema}/interface_{interface_schema}.v")
        self.interface_port_list = self._get_interface_port_list(target_interface_path)

        with open(json_path) as file:
            raw_json = json.load(file)
            self.dut_port_manager = PortManager(raw_json)

        top_module_name = self._get_module_name(verilog_module_path)
        dut_ports = self.dut_port_manager.get_port_list()
        port_declarations = self._get_port_declarations(self.interface_port_list)
        interface_module_name = self._get_module_name(target_interface_path)
        interface_connections = self._get_port_connections(self.interface_port_list)
        dut_input_count = 0
        dut_output_count = 0
        clk_generators = []
        inout_port_enables = {}
        for port in dut_ports:
            if isinstance(port, ClockPort):
                for interface_port in self.interface_port_list:
                    if interface_port['clock_port']:
                        top_clk_port_name = interface_port['name']
                        break
                clk_generators.append(self._create_clk_generator(port, top_clk_port_name))
                dut_input_count += 1
            elif defs.INPUT_KEYWORD == port.direction:
                dut_input_count += 1
            elif defs.OUTPUT_KEYWORD == port.direction:
                dut_output_count += 1
            elif defs.INOUT_KEYWORD == port.direction:
                inout_port_enables[port.enable_signal] = port.name

        if inout_port_enables:
            self.inout_params = {}
            for port in dut_ports:
                if port.name in inout_port_enables:
                    self.inout_params[inout_port_enables[port.name]] = port.address[0]

        dut_connections, support_wires = self._create_dut_connections(dut_ports)

        with open(TOP_TEMPLATE_PATH) as template:
            template_str = template.read()

        template_str = template_str.format(
            interface_schema,
            top_module_name,
            "".join(port_declarations),
            defs.DATA_WIDTH - 1,
            " ".join([defs.DATA_INPUT_PORT_NAME + ",", defs.DATA_OUTPUT_PORT_NAME + ",", defs.ADDRESS_PORT_NAME]),
            defs.DATA_WIDTH - 1,
            defs.INPUT_MUX_NAME,
            dut_input_count,
            defs.DATA_WIDTH - 1,
            defs.OUTPUT_MUX_NAME,
            dut_output_count,
            interface_module_name,
            "".join(interface_connections),
            "".join(clk_generators),
            "".join(support_wires),
            top_module_name,
            dut_connections,
            defs.INPUT_MUX_NAME,
            defs.ADDRESS_PORT_NAME,
            defs.DATA_INPUT_PORT_NAME,
            defs.DATA_OUTPUT_PORT_NAME,
            defs.OUTPUT_MUX_NAME,
            defs.ADDRESS_PORT_NAME
        )

        output_file_name = "".join(["top_", verilog_module_path.stem, ".v"])
        with open(output_path / output_file_name, "wt") as file:
            file.write(template_str)

    
    def _get_interface_port_list(self, interface_path):
        interface_port_encoder = PortEncoder()
        interface_port_encoder.parse(interface_path, defs.INTERFACE_CLK_SIGNAL_NAMES, interface_path.parent.name)

        return interface_port_encoder.get_encoded_port_list()
    

    def _get_port_connections(self, port_list):
        port_connections = []
        for port in port_list:
            port_connections.append(f".{port['name']}({port['name']}),\n")
        port_connections[-1] = port_connections[-1].replace(",", "") 

        return port_connections


    def _get_port_declarations(self, port_list):
        port_declarations = []
        for port in port_list:
            size_str = ""
            if port['name'] not in [defs.ADDRESS_PORT_NAME, defs.DATA_INPUT_PORT_NAME, defs.DATA_OUTPUT_PORT_NAME]:
                if port['bit_width'] > 1:
                    size_str = "".join(['[', str(port['bit_width'] - 1), ':', '0', ']', ' '])

                port_declarations.append(f"{port['direction']} {size_str}{port['name']},\n")

        port_declarations[-1] = port_declarations[-1].replace(",", "")            

        return port_declarations


    def _get_module_name(self, file_path: Path):
        module_name = None
        with open(file_path, "rt") as file:
            for line in file:
                match = re.findall(r"^\s*module ([a-zA-Z0-9_-]+)", line)
                if match:
                    module_name = match[0]
                    break

        return module_name
    

    def _create_clk_generator(self, clk_port, top_clk_port_name):
        trg_wire_name = "_".join([clk_port.name, "GEN", "TRG"])
        generator_definition = ""
        generator_definition += f"wire {trg_wire_name}, {clk_port.name}_WIRE;\n"
        generator_definition += f"assign {trg_wire_name} = {defs.ADDRESS_PORT_NAME} == {defs.DATA_WIDTH}'h{clk_port.address[0]};\n"
        generator_definition += f"{CNT_PULSE_GEN_MODULE_NAME} {clk_port.name}_GEN (\n"
        generator_definition += f"\t.MAIN_CLK({top_clk_port_name}),\n\t.CNT({defs.INPUT_MUX_NAME}[{clk_port.address[0]}]),\n"
        generator_definition += f"\t.TRG({trg_wire_name}),\n\t.CLK({clk_port.name}_WIRE)\n"
        generator_definition += ");\n"

        return generator_definition
    

    def _create_dut_connections(self, port_list):
        dut_connections = ""
        support_declarations = []
        port_count = len(port_list)
        i = 0
        for port in port_list:
            if isinstance(port, ClockPort):
                dut_connections += f".{port.name}({port.name}_WIRE)"
            else:
                if port.direction == defs.INOUT_KEYWORD:
                    negation = "~" if not port.enable_signal_active else ""
                    inout_writer = f"wire [{port.bit_width - 1}:0] {port.name}_WIRE;\n"
                    inout_writer += f"inout_writer #(\n"
                    inout_writer += f"\t.data_size({port.bit_width})\n) {port.name}_WRITER (\n"
                    inout_writer += f"\t.INOUT({port.name}_WIRE),\n\t.IN({port.name}_INOUT),\n"
                    inout_writer += f"\t.WR_EN({negation}{defs.OUTPUT_MUX_NAME}[{self.inout_params[port.name]}])\n);\n"

                    inout_wire = f"wire [{port.bit_width - 1}:0] {port.name}_INOUT;\n"
                    inout_out = "assign "
                    if len(port.address) > 1:
                        inout_out += "{"
                        for address in reversed(port.address):
                            inout_out += f"{defs.OUTPUT_MUX_NAME}[{address}]"
                            inout_out += ", " if address != port.address[0] else "}"
                    else:
                        inout_out += f"{defs.OUTPUT_MUX_NAME}{port.address} "
                        
                    inout_out += f"= {port.name}_WIRE;\n"
                    connection = f"{port.name}_WIRE"
                    declarations = inout_wire + inout_writer + inout_out
                    support_declarations.append(declarations)
                else:
                    mux_name = defs.OUTPUT_MUX_NAME if port.direction == defs.OUTPUT_KEYWORD else defs.INPUT_MUX_NAME
                    if len(port.address) > 1:
                        wire_def = f"wire [{port.bit_width - 1}:0] {port.name}_WIRE;\n"
                        connection = f"{port.name}_WIRE"
                        wire_def += f"assign {port.name}_WIRE = {{"
                        for address in reversed(port.address):
                            wire_def += f"{mux_name}[{address}]"
                            wire_def += ", " if address != port.address[0] else "};\n"
                        support_declarations.append(wire_def)
                    else:
                        connection = f"{mux_name}{port.address}"
                dut_connections += f".{port.name}({connection})"
            i += 1
            dut_connections += ",\n" if i != port_count else "\n"

        return dut_connections, support_declarations
        
# test = VerilogGenerator()
# test.create_top_module("atlys", Path("./tv80_cpu.v"), Path("./tv80_cpu_config.json"), Path())