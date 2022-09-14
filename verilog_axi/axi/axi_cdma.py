#
# This file is part of LiteX-Verilog-AXI-Test
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# LiteX wrapper around Alex Forencich Verilog-AXI's axi_cdma.v.

import os
import math

from migen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.axi import *

from verilog_axi.axi_common import *

# AXI CDMA -----------------------------------------------------------------------------------------

class AXICDMA(Module):
    def __init__(self, platform, m_axi, len_width=20, tag_width=8):
        self.logger = logging.getLogger("AXICDMA")

        # Get/Check Parameters.
        # ---------------------

        # Clock Domain.
        clock_domain = m_axi.clock_domain
        self.logger.info(f"Clock Domain: {colorer(clock_domain)}")

        # Address width.
        address_width = len(m_axi.aw.addr)
        self.logger.info(f"Address Width: {colorer(address_width)}")

        # Data width.
        data_width = len(m_axi.w.data)
        self.logger.info(f"Data Width: {colorer(data_width)}")

        # ID width.
        id_width = len(m_axi.aw.id)
        self.logger.info(f"ID Width: {colorer(id_width)}")

        # FIXME: Add checks on len/tag_width?

        # Descriptor Endpoints.
        # ---------------------

        desc_layout = [
            ("read_addr",  address_width),
            ("write_addr", address_width),
            ("len",            len_width),
            ("tag",            tag_width),
        ]
        desc_status_layout = [
            ("tag",   tag_width),
            ("error",         4),
        ]
        self.desc        = desc        = stream.Endpoint(desc_layout)
        self.desc_status = desc_status = stream.Endpoint(desc_status_layout)

        # Module instance.
        # ----------------

        self.specials += Instance("axi_cdma",
            # Parameters.
            # -----------
            p_AXI_DATA_WIDTH    = data_width,
            p_AXI_ADDR_WIDTH    = address_width,
            p_AXI_ID_WIDTH      = id_width,
            p_AXI_MAX_BURST_LEN = 16, # FIXME: Expose?
            p_LEN_WIDTH         = len_width,
            p_TAG_WIDTH         = tag_width,
            p_ENABLE_UNALIGNED  = 0,  # FIXME: Expose?

            # Clk / Rst.
            # ----------
            i_clk = ClockSignal(clock_domain),
            i_rst = ResetSignal(clock_domain),

            # AXI Descriptor Input.
            # ---------------------
            i_s_axis_desc_read_addr  = desc.read_addr,
            i_s_axis_desc_write_addr = desc.write_addr,
            i_s_axis_desc_len        = desc.len,
            i_s_axis_desc_tag        = desc.tag,
            i_s_axis_desc_valid      = desc.valid,
            o_s_axis_desc_ready      = desc.ready,

            # AXI Descriptor Output.
            # ----------------------
            o_m_axis_desc_status_tag    = desc_status.tag,
            o_m_axis_desc_status_error  = desc_status.error,
            o_m_axis_desc_status_valid  = desc_status.valid,

            # AXI Master Interface.
            # ---------------------
            # AW.
            i_m_axi_awid     = m_axi.aw.id,
            i_m_axi_awaddr   = m_axi.aw.addr,
            i_m_axi_awlen    = m_axi.aw.len,
            i_m_axi_awsize   = m_axi.aw.size,
            i_m_axi_awburst  = m_axi.aw.burst,
            i_m_axi_awlock   = m_axi.aw.lock,
            i_m_axi_awcache  = m_axi.aw.cache,
            i_m_axi_awprot   = m_axi.aw.prot,
            i_m_axi_awvalid  = m_axi.aw.valid,
            o_m_axi_awready  = m_axi.aw.ready,

            # W.
            i_m_axi_wdata    = m_axi.w.data,
            i_m_axi_wstrb    = m_axi.w.strb,
            i_m_axi_wlast    = m_axi.w.last,
            i_m_axi_wvalid   = m_axi.w.valid,
            o_m_axi_wready   = m_axi.w.ready,

            # B.
            o_m_axi_bid      = m_axi.b.id,
            o_m_axi_bresp    = m_axi.b.resp,
            o_m_axi_bvalid   = m_axi.b.valid,
            i_m_axi_bready   = m_axi.b.ready,

            # AR.
            i_m_axi_arid     = m_axi.ar.id,
            i_m_axi_araddr   = m_axi.ar.addr,
            i_m_axi_arlen    = m_axi.ar.len,
            i_m_axi_arsize   = m_axi.ar.size,
            i_m_axi_arburst  = m_axi.ar.burst,
            i_m_axi_arlock   = m_axi.ar.lock,
            i_m_axi_arcache  = m_axi.ar.cache,
            i_m_axi_arprot   = m_axi.ar.prot,
            i_m_axi_arvalid  = m_axi.ar.valid,
            o_m_axi_arready  = m_axi.ar.ready,

            # R.
            o_m_axi_rid      = m_axi.r.id,
            o_m_axi_rdata    = m_axi.r.data,
            o_m_axi_rresp    = m_axi.r.resp,
            o_m_axi_rlast    = m_axi.r.last,
            o_m_axi_rvalid   = m_axi.r.valid,
            i_m_axi_rready   = m_axi.r.ready,
        )

        # Add Sources.
        # ------------
        self.add_sources(platform)

    @staticmethod
    def add_sources(platform):
        rtl_dir = os.path.join(os.path.dirname(__file__), "..", "verilog", "rtl")
        platform.add_source(os.path.join(rtl_dir, "axi_cdma.v"))
