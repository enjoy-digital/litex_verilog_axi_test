#!/usr/bin/env python3

#
# This file is part of LiteX-Verilog-AXI-Test
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import argparse

from migen import *

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig
from litex.build.sim.verilator import verilator_build_args, verilator_build_argdict

from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.interconnect.axi import *

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst.
    ("sys_clk", 0, Pins(1)),
    ("sys_rst", 0, Pins(1)),

    # Serial.
    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),

        Subsignal("sink_valid", Pins(1)),
        Subsignal("sink_ready", Pins(1)),
        Subsignal("sink_data",  Pins(8)),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(SimPlatform):
    name = "sim"
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

# AXISimSoC -------------------------------------------------------------------------------------------

class AXISimSoC(SoCCore):
    def __init__(self):
        # Parameters.
        sys_clk_freq = int(100e6)

        # Platform.
        platform     = Platform()
        self.comb += platform.trace.eq(1)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq, uart_name="sim", integrated_rom_size=0x10000)
        self.add_config("NO_DELAYS")

        # AXI Tests --------------------------------------------------------------------------------
        from axi_adapter import AXIAdapter
        s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
        m_axi = AXIInterface(data_width=64, address_width=32, id_width=8)
        #self.submodules.axi_adapter = AXIAdapter(platform, s_axi, m_axi)

        from axi_ram import AXIRAM
        s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
        self.submodules.axi_ram = AXIRAM(platform, s_axi, depth=1024)

        from axi_register import AXIRegister
        s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
        m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
        self.submodules.axi_register = AXIRegister(platform, s_axi, m_axi)

        from axi_fifo import AXIFIFO
        s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
        m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
        self.submodules.axi_fifo = AXIFIFO(platform, s_axi, m_axi)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX Verilog AXI test simulation SoC ")
    verilator_build_args(parser)
    args = parser.parse_args()
    verilator_build_kwargs = verilator_build_argdict(args)
    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    soc = AXISimSoC()
    builder = Builder(soc)
    builder.build(sim_config=sim_config, **verilator_build_kwargs)

if __name__ == "__main__":
    main()
