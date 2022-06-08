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

            from verilog_axi.axi_lite.axil_register import AXILiteRegister
            s_axi_lite = AXIInterface(data_width=32, address_width=32)
            m_axi_lite = AXIInterface(data_width=32, address_width=32)
            self.submodules.axi_lite_register = AXILiteRegister(platform, s_axi_lite, m_axi_lite)

            from verilog_axi.axi_lite.axil_cdc import AXILiteCDC
            s_axi_lite = AXIInterface(data_width=32, address_width=32)
            m_axi_lite = AXIInterface(data_width=32, address_width=32)
            self.submodules.axi_lite_cdc = AXILiteCDC(platform, s_axi_lite, m_axi_lite)

        def axi_lite_integration_test():
            # AXI-Lite Test Mapping.
            # ----------------------
            axil_map = {
                "axil_ram"      : 0x010000,
                "axil_dp_ram_a" : 0x011000,
                "axil_dp_ram_b" : 0x012000,
                "axil_ram_reg"  : 0x013000,
                "axil_ram_cdc"  : 0x014000,
                "axil_ram_xbar" : 0x100000,
                "axil_ram_int"  : 0x200000,
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
            self.bus.add_slave("axil_dp_ram_a", s_axi_lite_a, region=SoCRegion(origin=axil_map["axil_dp_ram_a"], size=0x1000))
            self.bus.add_slave("axil_dp_ram_b", s_axi_lite_b, region=SoCRegion(origin=axil_map["axil_dp_ram_b"], size=0x1000))
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

            # Add AXI-Lite RAM to SoC (Through AXI-Lite Register).
            # ----------------------------------------------------

            # Test from LiteX BIOS similar to AXI-Lite RAM but with AXIL_RAM_REG_BASE.

            # 1) Create AXI-Lite interface and connect it to SoC.
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.bus.add_slave("axil_ram_reg", s_axi_lite, region=SoCRegion(origin=axil_map["axil_ram_reg"], size=0x1000))
            # 2) Add AXILiteRegister.
            from verilog_axi.axi_lite.axil_register import AXILiteRegister
            s_axi_lite_reg = AXILiteInterface(data_width=32, address_width=32)
            self.submodules += AXILiteRegister(platform, s_axi_lite, s_axi_lite_reg)
            # 4) Add AXILiteSRAM.
            from verilog_axi.axi_lite.axil_ram import AXILiteRAM
            self.submodules += AXILiteRAM(platform, s_axi_lite_reg, size=0x1000)

            # Add AXI-Lite RAM to SoC (Through AXI-Lite CDC).
            # ----------------------------------------------------

            # Test from LiteX BIOS similar to AXI-Lite RAM but with AXIL_RAM_CDC_BASE.

            # 1) Create AXI-Lite interface and connect it to SoC.
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.bus.add_slave("axil_ram_cdc", s_axi_lite, region=SoCRegion(origin=axil_map["axil_ram_cdc"], size=0x1000))
            # 2) Add AXILiteCDC.
            from verilog_axi.axi_lite.axil_cdc import AXILiteCDC
            s_axi_lite_cdc = AXILiteInterface(data_width=32, address_width=32)
            self.submodules += AXILiteCDC(platform, s_axi_lite, s_axi_lite_cdc)
            # 4) Add AXILiteSRAM.
            from verilog_axi.axi_lite.axil_ram import AXILiteRAM
            self.submodules += AXILiteRAM(platform, s_axi_lite_cdc, size=0x1000)


            # Add AXI RAM to SoC (Through AXI-Lite Crossbar).
            # -----------------------------------------------

            # Test from LiteX BIOS similar to AXI RAM but with AXIL_RAM_XBAR_BASE.

            # 1) Create AXI-Lite interface and connect it to SoC.
            s_axi_lite = AXILiteInterface(data_width=32, address_width=32)
            self.bus.add_slave("axil_ram_xbar", s_axi_lite, region=SoCRegion(origin=axil_map["axil_ram_xbar"], size=0x10000))
            # 2) Add AXILiteCrossbar  (1 Slave / 2 Masters).
            from verilog_axi.axi_lite.axil_crossbar import AXILiteCrossbar
            self.submodules.axil_crossbar = AXILiteCrossbar(platform)
            self.axil_crossbar.add_slave(s_axil=s_axi_lite)
            m_axil_0 = AXILiteInterface(data_width=32, address_width=32)
            m_axil_1 = AXILiteInterface(data_width=32, address_width=32)
            self.axil_crossbar.add_master(m_axil=m_axil_0, origin=axil_map["axil_ram_xbar"] + 0x0000, size=0x1000)
            self.axil_crossbar.add_master(m_axil=m_axil_1, origin=axil_map["axil_ram_xbar"] + 0x1000, size=0x1000)
            # 4) Add 2 X AXILiteSRAM.
            from verilog_axi.axi_lite.axil_ram import AXILiteRAM
            self.submodules += AXILiteRAM(platform, m_axil_0, size=0x1000)
            self.submodules += AXILiteRAM(platform, m_axil_1, size=0x1000)

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
