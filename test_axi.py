#!/usr/bin/env python3

#
# This file is part of LiteX-Verilog-AXI-Test
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2022 Victor Suarez Rovere <suarezvictor@gmail.com>
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

        # AXI Tests --------------------------------------------------------------------------------
        def axi_syntax_test():
            # AXI Adapter.
            # ------------
            from verilog_axi.axi.axi_adapter import AXIAdapter
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            #self.submodules.axi_adapter = AXIAdapter(platform, s_axi, m_axi) #brings verilator errors

            # AXI RAM.
            # --------
            from verilog_axi.axi.axi_ram import AXIRAM
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_ram = AXIRAM(platform, s_axi, size=0x1000)

            # AXI Register.
            # -------------
            from verilog_axi.axi.axi_register import AXIRegister
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_register = AXIRegister(platform, s_axi, m_axi)

            # AXI FIFO.
            # ---------
            from verilog_axi.axi.axi_fifo import AXIFIFO
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_fifo = AXIFIFO(platform, s_axi, m_axi)

            # AXI DPRAM.
            # ----------
            from verilog_axi.axi.axi_dp_ram import AXIDPRAM
            s_axi_a = AXIInterface(data_width=32, address_width=32, id_width=8)
            s_axi_b = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_dp_ram = AXIDPRAM(platform, s_axi_a, s_axi_b, size=0x1000)

            # AXI Crossbar.
            # -------------
            from verilog_axi.axi.axi_crossbar import AXICrossbar
            self.submodules.axi_crossbar = AXICrossbar(platform)
            self.axi_crossbar.add_slave(s_axi=AXIInterface(data_width=32, address_width=32, id_width=8))
            self.axi_crossbar.add_slave(s_axi=AXIInterface(data_width=32, address_width=32, id_width=8))
            self.axi_crossbar.add_master(m_axi=AXIInterface(data_width=32, address_width=32, id_width=8), origin=0x0000_0000, size=0x0100_0000)
            self.axi_crossbar.add_master(m_axi=AXIInterface(data_width=32, address_width=32, id_width=8), origin=0x1000_0000, size=0x0100_0000)

            # AXI Interconnect.
            # -----------------
            from verilog_axi.axi.axi_interconnect import AXIInterconnect
            self.submodules.axi_interconnect = AXIInterconnect(platform)
            self.axi_interconnect.add_slave(s_axi=AXIInterface(data_width=32, address_width=32, id_width=8))
            self.axi_interconnect.add_slave(s_axi=AXIInterface(data_width=32, address_width=32, id_width=8))
            self.axi_interconnect.add_master(m_axi=AXIInterface(data_width=32, address_width=32, id_width=8), origin=0x0000_0000, size=0x0100_0000)
            self.axi_interconnect.add_master(m_axi=AXIInterface(data_width=32, address_width=32, id_width=8), origin=0x1000_0000, size=0x0100_0000)

            # AXI CDMA.
            # ---------
            from verilog_axi.axi.axi_cdma import AXICDMA
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_cdma = AXICDMA(platform, m_axi)

            # AXI DMA.
            # --------
            from verilog_axi.axi.axi_dma import AXIDMA
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_dma = AXIDMA(platform, m_axi)

        def axi_integration_test():
            # AXI Test Mapping.
            # -----------------
            axi_map = {
                "axi_ram"      : 0x010000,
                "axi_dp_ram_1a": 0x011000,
                "axi_dp_ram_2a": 0x012000,
                "axi_ram_reg"  : 0x013000,
                "axi_ram_fifo" : 0x014000,
                "axi_ram_xbar" : 0x100000,
                "axi_ram_int"  : 0x200000,
            }

            # Add AXI RAM to SoC.
            # -------------------

            # Test from LiteX BIOS:
            # mem_list
            # mem_write <AXI_RAM_BASE> 0x5aa55aa5
            # mem_read  <AXI_RAM_BASE> 32

            # 1) Create AXI interface and connect it to SoC.
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.bus.add_slave("axi_ram", s_axi, region=SoCRegion(origin=axi_map["axi_ram"], size=0x1000))
            # 2) Add AXIRAM.
            from verilog_axi.axi.axi_ram import AXIRAM
            self.submodules += AXIRAM(platform, s_axi, size=0x1000)
            # 3) Debug.
            if 0:
                self.submodules += AXIAWDebug(s_axi, name="AXIRAM")
                self.submodules += AXIWDebug(s_axi,  name="AXIRAM")
                self.submodules += AXIARDebug(s_axi, name="AXIRAM")
                self.submodules += AXIRDebug(s_axi,  name="AXIRAM")

            # Add AXI DP RAM to SoC.
            # ----------------------

            # Test from LiteX BIOS:
            # mem_list
            # mem_write <AXI_DP_RAM_A_BASE> 0x5aa55aa5
            # mem_read  <AXI_DP_RAM_B_BASE> 32
            # mem_write <AXI_DP_RAM_B_BASE + 4> 0xa55aa55a
            # mem_read  <AXI_DP_RAM_A_BASE> 32

            # 1) Create AXI interfaces and connect them to SoC.
            s_axi_1a = AXIInterface(data_width=32, address_width=32, id_width=1)
            s_axi_1b = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.bus.add_slave("axi_dp_ram_1a", s_axi_1a, region=SoCRegion(origin=axi_map["axi_dp_ram_1a"], size=0x1000))
            #self.bus.add_slave("axi_dp_ram_b", s_axi_1b, region=SoCRegion(origin=axi_map["axi_dp_ram_1b"], size=0x1000))
            # 2) Add AXIDPRAM.
            from verilog_axi.axi.axi_dp_ram import AXIDPRAM
            #self.submodules += AXIDPRAM(platform, s_axi_1a, s_axi_1b, size=0x1000, b_interleave=True) #interleave allows DMA to control the core
            if 0:
                self.submodules += AXIAWDebug(s_axi_1a, name="AXIDPRAM1_A")
                self.submodules += AXIWDebug(s_axi_1a,  name="AXIDPRAM1_A")
                self.submodules += AXIARDebug(s_axi_1a, name="AXIDPRAM1_A")
                self.submodules += AXIRDebug(s_axi_1a,  name="AXIDPRAM1_A")
                self.submodules += AXIAWDebug(s_axi_1b, name="AXIDPRAM1_B")
                self.submodules += AXIWDebug(s_axi_1b,  name="AXIDPRAM1_B")
                self.submodules += AXIARDebug(s_axi_1b, name="AXIDPRAM1_B")
                self.submodules += AXIRDebug(s_axi_1b,  name="AXIDPRAM1_B")


            # Add AXI RAM to SoC (Through AXI Register).
            # -----------------------------------------

            # Test from LiteX BIOS similar to AXI RAM but with AXI_RAM_REG_BASE.

            # 1) Create AXI interface and connect it to SoC.
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.bus.add_slave("axi_ram_reg", s_axi, region=SoCRegion(origin=axi_map["axi_ram_reg"], size=0x1000))
            # 2) Add AXIRegister.
            from verilog_axi.axi.axi_register import AXIRegister
            s_axi_reg = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.submodules += AXIRegister(platform, s_axi, s_axi_reg)
            # 3) Add AXISRAM.
            from verilog_axi.axi.axi_ram import AXIRAM
            self.submodules += AXIRAM(platform, s_axi_reg, size=0x1000)


            # Add AXI RAM to SoC (Through AXI FIFO).
            # --------------------------------------

            # Test from LiteX BIOS similar to AXI RAM but with AXI_RAM_FIFO_BASE.

            # 1) Create AXI interface and connect it to SoC.
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.bus.add_slave("axi_ram_fifo", s_axi, region=SoCRegion(origin=axi_map["axi_ram_fifo"], size=0x1000))
            # 2) Add AXIFIFO.
            from verilog_axi.axi.axi_fifo import AXIFIFO
            s_axi_fifo = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.submodules += AXIFIFO(platform, s_axi, s_axi_fifo)
            # 3) Add AXISRAM.
            from verilog_axi.axi.axi_ram import AXIRAM
            self.submodules += AXIRAM(platform, s_axi_fifo, size=0x1000)

            # Add AXI RAM to SoC (Through AXI Crossbar).
            # ------------------------------------------

            # Test from LiteX BIOS similar to AXI RAM but with AXI_RAM_XBAR_BASE.

            # 1) Create AXI interface and connect it to SoC.
            s_axi = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.bus.add_slave("axi_ram_xbar", s_axi, region=SoCRegion(origin=axi_map["axi_ram_xbar"], size=0x10000))
            # 2) Add AXICrossbar  (1 Slave / 3 Masters).
            from verilog_axi.axi.axi_crossbar import AXICrossbar
            self.submodules.axi_crossbar = AXICrossbar(platform)
            self.axi_crossbar.add_slave(s_axi=s_axi)
            m_axi_0 = AXIInterface(data_width=32, address_width=32, id_width=1)
            m_axi_1 = AXIInterface(data_width=32, address_width=32, id_width=1)
            m_axi_2 = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.axi_crossbar.add_master(m_axi=m_axi_0, origin=axi_map["axi_ram_xbar"] + 0x0000, size=0x1000)
            self.axi_crossbar.add_master(m_axi=m_axi_1, origin=axi_map["axi_ram_xbar"] + 0x1000, size=0x1000)
            self.axi_crossbar.add_master(m_axi=m_axi_2, origin=axi_map["axi_ram_xbar"] + 0x2000, size=0x1000)
            # 3) Add 3 X AXISRAM.
            from verilog_axi.axi.axi_ram import AXIRAM
            self.submodules += AXIRAM(platform, m_axi_0, size=0x1000)
            self.submodules += AXIRAM(platform, m_axi_1, size=0x1000)
            self.submodules += AXIRAM(platform, m_axi_2, size=0x1000)

            # Add AXI RAM to SoC (Through AXI Interconnect).
            # ------------------------------------------

            # Test from LiteX BIOS similar to AXI RAM but with AXI_RAM_INT_BASE.

            # 1) Create AXI interface and connect it to SoC.
            s_axi = AXIInterface(data_width=32, address_width=32)
            self.bus.add_slave("axi_ram_int", s_axi, region=SoCRegion(origin=axi_map["axi_ram_int"], size=0x10000))
            # 2) Add AXIInterconnect  (1 Slave / 3 Masters).
            from verilog_axi.axi.axi_interconnect import AXIInterconnect
            self.submodules.axi_interconnect = AXIInterconnect(platform)
            self.axi_interconnect.add_slave(s_axi=s_axi)
            m_axi_0 = AXIInterface(data_width=32, address_width=32, id_width=1)
            m_axi_1 = AXIInterface(data_width=32, address_width=32, id_width=1)
            m_axi_2 = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.axi_interconnect.add_master(m_axi=m_axi_0, origin=axi_map["axi_ram_int"] + 0x0000, size=0x1000)
            self.axi_interconnect.add_master(m_axi=m_axi_1, origin=axi_map["axi_ram_int"] + 0x1000, size=0x1000)
            self.axi_interconnect.add_master(m_axi=m_axi_2, origin=axi_map["axi_ram_int"] + 0x2000, size=0x1000)
            # 3) Add 3 X AXISRAM.
            from verilog_axi.axi.axi_ram import AXIRAM
            self.submodules += AXIRAM(platform, m_axi_0, size=0x1000)
            self.submodules += AXIRAM(platform, m_axi_1, size=0x1000)
            self.submodules += AXIRAM(platform, m_axi_2, size=0x1000)
            # 4) Debug.
            for i, m_axi in enumerate([s_axi]):
                self.submodules += AXIAWDebug(s_axi, name=f"S_AXI_{i}")
                self.submodules += AXIWDebug(s_axi,  name=f"S_AXI_{i}")
                self.submodules += AXIARDebug(s_axi, name=f"S_AXI_{i}")
                self.submodules += AXIRDebug(s_axi,  name=f"S_AXI_{i}")
            for i, m_axi in enumerate([m_axi_0, m_axi_1, m_axi_2]):
                self.submodules += AXIAWDebug(m_axi, name=f"M_AXI_{i}")
                self.submodules += AXIWDebug(m_axi,  name=f"M_AXI_{i}")
                self.submodules += AXIARDebug(m_axi, name=f"M_AXI_{i}")
                self.submodules += AXIRDebug(m_axi,  name=f"M_AXI_{i}")
                
            # AXI CDMA.
            # ---------
            #mem_write 0x11000 0x41 4			<-- sets some values in RAM
            #mem_read 0x11000 64				<-- dump original contents
            #mem_write 0xf0000000 0				<-- source address
            #mem_write 0xf0000004 0x20			<-- destination address
            #mem_write 0xf0000008 0x10			<-- length (AXI format)
            #mem_write 0xf0000010 1				<-- toogle VALID (starts when set to 1)
            #mem_write 0xf0000010 0
            #mem_read 0x11000 64				<-- dump updated contents
            
            from verilog_axi.axi.axi_cdma import AXICDMA
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.submodules.axi_cdma = axi_cdma = AXICDMA(platform, m_axi, len_width=32)
            self.submodules.dpram1 = AXIDPRAM(platform, s_axi_1a, s_axi_1b, size=0x1000)
            #self.comb += m_axi.connect(s_axi_1b) #connect CDMA to DPRAM port B
            self.comb += connect_axi_read(m_axi, s_axi_1b) #connect CDMA read port to DPRAM port B
            self.comb += connect_axi_write(m_axi, s_axi_1b) #connect CDMA write pòrt to DPRAM port B

            if 0:
                self.submodules += AXIAWDebug(m_axi, name="AXICDMA")
                self.submodules += AXIWDebug(m_axi,  name="AXICDMA")
                self.submodules += AXIARDebug(m_axi, name="AXICDMA")
                self.submodules += AXIRDebug(m_axi,  name="AXICDMA")
                self.submodules += AXIAWDebug(s_axi_1b, name="AXIDPRAM1_B")
                self.submodules += AXIWDebug(s_axi_1b,  name="AXIDPRAM1_B")
                self.submodules += AXIARDebug(s_axi_1b, name="AXIDPRAM1_B")
                self.submodules += AXIRDebug(s_axi_1b,  name="AXIDPRAM1_B")


            # AXI DMA.
            # --------
            #mem_write 0x12000 0x42 4			<-- sets some values in RAM
            #mem_read 0x12000 64				<-- dump original contents
            #mem_write 0xf0000800 0				<-- source address
            #mem_write 0xf0000824 0x20			<-- destination address
            #mem_write 0xf0000804 0x10			<-- length (AXI format)
            #mem_write 0xf000080c 1				<-- toogle VALID (starts when set to 1)
            #mem_write 0xf000080c 0
            #mem_read 0x12000 64				<-- dump updated contents
            from verilog_axi.axi.axi_dma import AXIDMA
            m_axi = AXIInterface(data_width=32, address_width=32, id_width=8)
            self.submodules.axi_dma = axi_dma = AXIDMA(platform, m_axi, len_width=32)
            self.comb += axi_dma.read_data.connect(axi_dma.write_data) #interconect output to input stream

            s_axi_2a = AXIInterface(data_width=32, address_width=32, id_width=1)
            s_axi_2b = AXIInterface(data_width=32, address_width=32, id_width=1)
            self.bus.add_slave("axi_dp_ram_2a", s_axi_2a, region=SoCRegion(origin=axi_map["axi_dp_ram_2a"], size=0x1000))

            self.submodules.dpram2 = AXIDPRAM(platform, s_axi_2a, s_axi_2b, size=0x1000)
            self.comb += connect_axi_read(m_axi, s_axi_2b) #connect DMA read port to DPRAM port B
            self.comb += connect_axi_write(m_axi, s_axi_2b) #connect DMA write pòrt to DPRAM port B

            if 1:
                self.submodules += AXIAWDebug(m_axi, name="AXIDMA")
                self.submodules += AXIWDebug(m_axi,  name="AXIDMA")
                #self.submodules += AXIARDebug(m_axi, name="AXIDMA")
                self.submodules += AXIRDebug(m_axi,  name="AXIDMA")
                self.submodules += AXISWDebug(axi_dma.write_data, m_axi.clock_domain, name="AXIDMA_WD")
                self.submodules += AXISRDebug(axi_dma.read_data,  m_axi.clock_domain, name="AXIDMA_RD")
                self.submodules += AXIAWDebug(s_axi_2b, name="AXIDPRAM2_B")
                self.submodules += AXIWDebug(s_axi_2b,  name="AXIDPRAM2_B")
                #self.submodules += AXIARDebug(s_axi_2b, name="AXIDPRAM2_B")
                self.submodules += AXIRDebug(s_axi_2b,  name="AXIDPRAM2_B")


        #axi_syntax_test()
        axi_integration_test()

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
