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
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *
from litex.soc.interconnect.axi import *

from verilog_axi.axi_common import *

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

# AXISimSoC ----------------------------------------------------------------------------------------

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
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq, bus_standard="axi-lite", uart_name="sim", integrated_rom_size=0x10000)
        self.add_config("BIOS_NO_BOOT")

        # AXI to AXI-Lite Tests --------------------------------------------------------------------
        def axi2axi_lite_syntax_test():
            from verilog_axi.axi_axil_adapter import AXI2AXILiteAdapter
            s_axi      = AXIInterface(data_width=32, address_width=32, id_width=8)
            m_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.submodules.axi_axi_lite_adapter = AXI2AXILiteAdapter(platform, s_axi, m_axi_lite)

        def axi2axi_lite_integration_test():
            # AXI-Lite Test Mapping.
            # ----------------------
            axil_map = {
                "axil_ram" : 0x010000,
            }
            # Add AXI-Lite RAM to SoC.
            # ------------------------

            # Test from LiteX BIOS:
            # mem_list
            # mem_write <AXIL_RAM_BASE> 0x5aa55aa5
            # mem_read  <AXIL_RAM_BASE> 32

            # 1) Create AXI-Lite interface and connect it to SoC.
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.bus.add_slave("axil_ram", s_axi_lite, region=SoCRegion(origin=axil_map["axil_ram"], size=0x1000))
            # 2) Convert AXI-Lite interface to AXI interface.
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.submodules += AXILite2AXI(s_axi_lite, s_axi)
            # 3) Convert AXI interface to AXI-Lite.
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            from verilog_axi.axi_axil_adapter import AXI2AXILiteAdapter
            self.submodules += AXI2AXILiteAdapter(platform, s_axi, s_axi_lite)
            # 4) Add AXILiteRAM.
            from verilog_axi.axi_lite.axil_ram import AXILiteRAM
            self.submodules += AXILiteRAM(platform, s_axi_lite, size=0x1000)

        axi2axi_lite_syntax_test()
        axi2axi_lite_integration_test()

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
