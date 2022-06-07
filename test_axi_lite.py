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

        # AXI-Lite Tests ---------------------------------------------------------------------------
        def axi_lite_syntax_test():
            from verilog_axi.axi_lite.axil_adapter import AXILiteAdapter
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            m_axi_lite = AXILiteInterface(data_width=64, address_width=32)
            self.submodules.axi_lite_adapter = AXILiteAdapter(platform, s_axi_lite, m_axi_lite)

            from verilog_axi.axi_lite.axil_ram import AXILiteRAM
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.submodules.axi_lite_ram = AXILiteRAM(platform, s_axi_lite, size=0x1000)

        def axi_lite_integration_test():
            # Add AXI-Lite RAM to SoC.
            # ------------------------

            # Test from LiteX BIOS:
            # mem_list
            # mem_write <AXIL_RAM_BASE> 0x5aa55aa5
            # mem_read  <AXIL_RAM_BASE> 32

            # 1) Create AXI-Lite interface and connect it to SoC.
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.bus.add_slave("axil_ram", s_axi_lite, region=SoCRegion(size=0x1000))
            # 2) Add AXILiteRAM.
            from verilog_axi.axi_lite.axil_ram import AXILiteRAM
            self.submodules += AXILiteRAM(platform, s_axi_lite, size=0x1000)
            # 4) Debug.
            if 0:
                self.submodules += AXIAWDebug(s_axi_lite, name="AXIRAM")
                self.submodules += AXIWDebug( s_axi_lite, name="AXIRAM")
                self.submodules += AXIARDebug(s_axi_lite, name="AXIRAM")
                self.submodules += AXIRDebug( s_axi_lite, name="AXIRAM")

            # Add AXI-Lite DP RAM to SoC.
            # ---------------------------

            # Test from LiteX BIOS:
            # mem_list
            # mem_write <AXIL_DP_RAM_A_BASE> 0x5aa55aa5
            # mem_read  <AXIL_DP_RAM_B_BASE> 32
            # mem_write <AXIL_DP_RAM_B_BASE + 4> 0xa55aa55a
            # mem_read  <AXIL_DP_RAM_A_BASE> 32

            # 1) Create AXI-Lite interfaces and connect them to SoC.
            s_axi_lite_a = AXILiteInterface(data_width=32, address_width=32)
            s_axi_lite_b = AXILiteInterface(data_width=32, address_width=32)
            self.bus.add_slave("axil_dp_ram_a", s_axi_lite_a, region=SoCRegion(size=0x1000))
            self.bus.add_slave("axil_dp_ram_b", s_axi_lite_b, region=SoCRegion(size=0x1000))
            # 2) Add AXILiteDPRAM.
            from verilog_axi.axi_lite.axil_dp_ram import AXILiteDPRAM
            self.submodules += AXILiteDPRAM(platform, s_axi_lite_a, s_axi_lite_b, size=0x1000)
            if 0:
                self.submodules += AXIAWDebug(s_axi_lite_a, name="AXILiteDPRAM_A")
                self.submodules += AXIWDebug( s_axi_lite_a, name="AXILiteDPRAM_A")
                self.submodules += AXIARDebug(s_axi_lite_a, name="AXILiteDPRAM_A")
                self.submodules += AXIRDebug( s_axi_lite_a, name="AXILiteDPRAM_A")
                self.submodules += AXIAWDebug(s_axi_lite_b, name="AXILiteDPRAM_B")
                self.submodules += AXIWDebug( s_axi_lite_b, name="AXILiteDPRAM_B")
                self.submodules += AXIARDebug(s_axi_lite_b, name="AXILiteDPRAM_B")
                self.submodules += AXIRDebug( s_axi_lite_b, name="AXILiteDPRAM_B")

        axi_lite_syntax_test()
        axi_lite_integration_test()

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
