#
# This file is part of LiteX-Verilog-AXI-Test
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# LiteX wrapper around Alex Forencich Verilog-AXI's axil_dp_ram.v.

import os
import math

from migen import *

from litex.soc.interconnect.axi import *

from verilog_axi.axi_common import *

# AXI-Lite DP RAM ----------------------------------------------------------------------------------

class AXILiteDPRAM(Module):
    def __init__(self, platform, s_axil_a, s_axil_b, size=0x1000, pipeline_output=False):
        self.logger = logging.getLogger("AXILiteDPRAM")

        # Get/Check Parameters.
        # ---------------------

        # Clock Domain.
        self.logger.info(f"Clock Domain A: {colorer(s_axil_a.clock_domain)}")
        self.logger.info(f"Clock Domain B: {colorer(s_axil_b.clock_domain)}")

        # Address width.
        address_width = len(s_axil_a.aw.addr)
        if len(s_axil_a.aw.addr) != len(s_axil_b.aw.addr):
            self.logger.error("{} on {} (A: {} / B: {}), should be {}.".format(
                colorer("Different Address Width", color="red"),
                colorer("AXI-Lite interfaces."),
                colorer(len(s_axil_a.aw.addr)),
                colorer(len(s_axil_b.aw.addr)),
                colorer("the same")))
            raise AXIError()
        else:
            self.logger.info(f"Address Width: {colorer(address_width)}")

        # Data width.
        data_width = len(s_axil_a.w.data)
        if len(s_axil_a.w.data) != len(s_axil_b.w.data):
            self.logger.error("{} on {} (A: {} / B: {}), should be {}.".format(
                colorer("Different Data Width", color="red"),
                colorer("AXI-Lite interfaces."),
                colorer(len(s_axil_a.w.data)),
                colorer(len(m_axi_b.w.data)),
                colorer("the same")))
            raise AXIError()
        else:
            self.logger.info(f"Data Width: {colorer(data_width)}")

        # Size.
        self.logger.info(f"Size: {colorer(size)}bytes")

        # Pipeline.
        self.logger.info(f"Pipeline Output: {pipeline_output}.")

        # Module instance.
        # ----------------

        self.specials += Instance("axil_dp_ram",
            # Parameters.
            # -----------
            # Global.
            p_DATA_WIDTH = data_width,
            p_ADDR_WIDTH = math.ceil(math.log2(size)),

            # Pipeline.
            p_PIPELINE_OUTPUT = pipeline_output,

            # Clk / Rst.
            # ----------
            i_a_clk = ClockSignal(s_axil_a.clock_domain),
            i_a_rst = ResetSignal(s_axil_a.clock_domain),
            i_b_clk = ClockSignal(s_axil_b.clock_domain),
            i_b_rst = ResetSignal(s_axil_b.clock_domain),

            # AXI A Slave Interface.
            # --------------------
            # AW.
            i_s_axil_a_awaddr   = s_axil_a.aw.addr,
            i_s_axil_a_awprot   = 0b0, # CHECKME.
            i_s_axil_a_awvalid  = s_axil_a.aw.valid,
            o_s_axil_a_awready  = s_axil_a.aw.ready,

            # W.
            i_s_axil_a_wdata    = s_axil_a.w.data,
            i_s_axil_a_wstrb    = s_axil_a.w.strb,
            i_s_axil_a_wvalid   = s_axil_a.w.valid,
            o_s_axil_a_wready   = s_axil_a.w.ready,

            # B.
            o_s_axil_a_bresp    = s_axil_a.b.resp,
            o_s_axil_a_bvalid   = s_axil_a.b.valid,
            i_s_axil_a_bready   = s_axil_a.b.ready,

            # AR.
            i_s_axil_a_araddr   = s_axil_a.ar.addr,
            i_s_axil_a_arprot   = 0b0, # CHECKME.
            i_s_axil_a_arvalid  = s_axil_a.ar.valid,
            o_s_axil_a_arready  = s_axil_a.ar.ready,

            # R.
            o_s_axil_a_rdata    = s_axil_a.r.data,
            o_s_axil_a_rresp    = s_axil_a.r.resp,
            o_s_axil_a_rvalid   = s_axil_a.r.valid,
            i_s_axil_a_rready   = s_axil_a.r.ready,

            # AXI B Slave Interface.
            # --------------------
            # AW.
            i_s_axil_b_awaddr   = s_axil_b.aw.addr,
            i_s_axil_b_awprot   = 0b0, # CHECKME.
            i_s_axil_b_awvalid  = s_axil_b.aw.valid,
            o_s_axil_b_awready  = s_axil_b.aw.ready,

            # W.
            i_s_axil_b_wdata    = s_axil_b.w.data,
            i_s_axil_b_wstrb    = s_axil_b.w.strb,
            i_s_axil_b_wvalid   = s_axil_b.w.valid,
            o_s_axil_b_wready   = s_axil_b.w.ready,

            # B.
            o_s_axil_b_bresp    = s_axil_b.b.resp,
            o_s_axil_b_bvalid   = s_axil_b.b.valid,
            i_s_axil_b_bready   = s_axil_b.b.ready,

            # AR.
            i_s_axil_b_araddr   = s_axil_b.ar.addr,
            i_s_axil_b_arprot   = 0b0, # CHECKME.
            i_s_axil_b_arvalid  = s_axil_b.ar.valid,
            o_s_axil_b_arready  = s_axil_b.ar.ready,

            # R.
            o_s_axil_b_rdata    = s_axil_b.r.data,
            o_s_axil_b_rresp    = s_axil_b.r.resp,
            o_s_axil_b_rvalid   = s_axil_b.r.valid,
            i_s_axil_b_rready   = s_axil_b.r.ready,
        )

        # Add Sources.
        # ------------
        self.add_sources(platform)

    @staticmethod
    def add_sources(platform):
        rtl_dir = os.path.join(os.path.dirname(__file__), "..", "verilog", "rtl")
        platform.add_source(os.path.join(rtl_dir, "axil_dp_ram.v"))
