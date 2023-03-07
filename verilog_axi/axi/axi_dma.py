#
# This file is part of LiteX-Verilog-AXI-Test
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2022 Victor Suarez Rovere <suarezvictor@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

# LiteX wrapper around Alex Forencich Verilog-AXI's axi_dma.v.

import os
import math

from migen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.axi import *
from litex.soc.interconnect.axi.axi_stream import AXIStreamInterface
from litex.soc.interconnect.csr import *

from verilog_axi.axi_common import *

# AXI DMA ------------------------------------------------------------------------------------------

class AXIDMA(Module, AutoCSR):
    def __init__(self, platform, m_axi, len_width=20, tag_width=8, dest_width=1, user_width=1):
        self.logger = logging.getLogger("AXIDMA")

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

        # FIXME: Add checks on len/tag/dest_width?

        # Descriptor Endpoints.
        # ---------------------

        read_desc_layout = [
            ("addr", address_width),
            ("len",      len_width),
            ("tag",      tag_width),
            ("id",        id_width),
            ("dest",    dest_width),
            ("user",    user_width),
        ]
        read_desc_status_layout = [
            ("tag",   tag_width),
            ("error",         4),
        ]
        data_layout = [
            ("data",    data_width),
            ("keep", data_width//8),
        ]
        self.read_desc        = read_desc        = stream.Endpoint(read_desc_layout)
        self.read_desc_status = read_desc_status = stream.Endpoint(read_desc_status_layout)
        self.read_data        = read_data        = AXIStreamInterface(
        	data_width,
        	data_width//8,
        	id_width,
        	dest_width,
        	user_width,
        	layout = data_layout)

        write_desc_layout = [
            ("addr", address_width),
            ("len",      len_width),
            ("tag",      tag_width),
        ]
        write_desc_status_layout = [
            ("len",      len_width),
            ("tag",      tag_width),
            ("id",        id_width),
            ("dest",    dest_width),
            ("user",    user_width),
            ("error",            4),
        ]

        self.write_desc        = write_desc        = stream.Endpoint(write_desc_layout)
        self.write_desc_status = write_desc_status = stream.Endpoint(write_desc_status_layout)
        self.write_data        = write_data        = AXIStreamInterface(
        	data_width,
        	data_width//8,
        	id_width,
        	dest_width,
        	user_width,
        	layout = data_layout)

        # Add CSR
        self.add_csr(address_width, len_width, tag_width)

        # Module instance.
        # ----------------

        self.specials += Instance("axi_dma",
            # Parameters.
            # -----------
            p_AXI_DATA_WIDTH    = data_width,
            p_AXI_ADDR_WIDTH    = address_width,
            p_AXI_ID_WIDTH      = id_width,
            p_AXI_MAX_BURST_LEN = 16, # FIXME: Expose?
            p_AXIS_LAST_ENABLE  = 1,
            p_AXIS_ID_ENABLE    = 0, # FIXME: Expose?
            p_AXIS_ID_WIDTH     = 8, # FIXME: Expose?
            p_AXIS_DEST_ENABLE  = 0, # FIXME: Expose?
            p_AXIS_DEST_WIDTH   = 8, # FIXME: Expose?
            p_AXIS_USER_ENABLE  = 0, # FIXME: Expose?
            p_AXIS_USER_WIDTH   = 1, # FIXME: Expose?
            p_LEN_WIDTH         = len_width,
            p_TAG_WIDTH         = tag_width,
            p_ENABLE_SG         = 0,
            p_ENABLE_UNALIGNED  = 0,  # FIXME: Expose?

            # Clk / Rst.
            # ----------
            i_clk = ClockSignal(clock_domain),
            i_rst = ResetSignal(clock_domain),

            # Configuration.
            # --------------
            i_read_enable  = 1, # FIXME: Expose.
            i_write_enable = 1, # FIXME: Expose.
            i_write_abort  = 0, # FIXME: Expose.

            # AXI Read Descriptor Input.
            # --------------------------
            i_s_axis_read_desc_addr  = read_desc.addr,
            i_s_axis_read_desc_len   = read_desc.len,
            i_s_axis_read_desc_tag   = read_desc.tag,
            i_s_axis_read_desc_id    = read_desc.id,
            i_s_axis_read_desc_dest  = read_desc.dest,
            i_s_axis_read_desc_user  = read_desc.user,
            i_s_axis_read_desc_valid = read_desc.valid,
            o_s_axis_read_desc_ready = read_desc.ready,

            # AXI Read Descriptor Status.
            # ---------------------------
            o_m_axis_read_desc_status_tag   = read_desc_status.tag,
            o_m_axis_read_desc_status_error = read_desc_status.error,
            o_m_axis_read_desc_status_valid = read_desc_status.valid,

            # AXI Read Data Output.
            # ---------------------
            o_m_axis_read_data_tdata  = read_data.data,
            o_m_axis_read_data_tkeep  = read_data.keep,
            o_m_axis_read_data_tvalid = read_data.valid,
            i_m_axis_read_data_tready = read_data.ready,
            o_m_axis_read_data_tlast  = read_data.last,
            o_m_axis_read_data_tid    = read_data.id,
            o_m_axis_read_data_tdest  = read_data.dest,
            o_m_axis_read_data_tuser  = read_data.user,

            # AXI Write Descriptor Input.
            # ---------------------------
            i_s_axis_write_desc_addr  = write_desc.addr,
            i_s_axis_write_desc_len   = write_desc.len,
            i_s_axis_write_desc_tag   = write_desc.tag,
            i_s_axis_write_desc_valid = write_desc.valid,
            o_s_axis_write_desc_ready = write_desc.ready,

            # AXI Write Descriptor Status.
            # ----------------------------
            o_m_axis_write_desc_status_len   = write_desc_status.len,
            o_m_axis_write_desc_status_tag   = write_desc_status.tag,
            o_m_axis_write_desc_status_id    = write_desc_status.id,
            o_m_axis_write_desc_status_dest  = write_desc_status.dest,
            o_m_axis_write_desc_status_user  = write_desc_status.user,
            o_m_axis_write_desc_status_error = write_desc_status.error,
            o_m_axis_write_desc_status_valid = write_desc_status.valid,

            # AXI Write Data Input.
            # ---------------------
            i_s_axis_write_data_tdata  = write_data.data,
            i_s_axis_write_data_tkeep  = write_data.keep,
            i_s_axis_write_data_tvalid = write_data.valid,
            o_s_axis_write_data_tready = write_data.ready,
            i_s_axis_write_data_tlast  = write_data.last,
            i_s_axis_write_data_tid    = write_data.id,
            i_s_axis_write_data_tdest  = write_data.dest,
            i_s_axis_write_data_tuser  = write_data.user,

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

    def add_csr(self, address_width, len_width, tag_width):
        self.read_addr		= CSRStorage(address_width)
        self.len			= CSRStorage(len_width)
        self.tag			= CSRStorage(tag_width)
        self.valid			= CSRStorage(fields=[CSRField("valid", pulse=True)])
        self.read_ready		= CSRStatus()
        #self.read_dummy1		= CSRStorage(32, reset=0xCCCCCCCC)
        self.read_status_tag	= CSRStatus(tag_width)
        self.read_status_error	= CSRStatus(4)
        #self.read_dummy2		= CSRStorage(32, reset=0xDDDDDDDD)
        self.comb += [
        	self.read_desc.addr.eq(self.read_addr.storage),
        	self.read_desc.len.eq(self.len.storage),
        	self.read_desc.tag.eq(self.tag.storage),
        	self.read_desc.valid.eq(self.valid.re),
        	self.read_ready.status.eq(self.read_desc.ready),
        	self.read_status_tag.status.eq(self.read_desc_status.tag),
        	self.read_status_error.status.eq(self.read_desc_status.error),
        	]

        self.write_addr			= CSRStorage(address_width)
        #self.write_len			= CSRStorage(len_width)
        #self.write_tag			= CSRStorage(tag_width)
        #self.write_valid		= CSRStorage()
        #self.write_dummy1		= CSRStorage(32, reset=0xEEEEEEEE)
        self.write_ready		= CSRStatus()
        self.write_status_tag	= CSRStatus(tag_width)
        self.write_status_error	= CSRStatus(4)
        #self.write_dummy2		= CSRStorage(32, reset=0xFFFFFFFF)
        self.comb += [
        	self.write_desc.addr.eq(self.write_addr.storage),
        	self.write_desc.len.eq(self.len.storage),
        	self.write_desc.tag.eq(self.tag.storage),
        	self.write_desc.valid.eq(self.valid.re),
        	self.write_ready.status.eq(self.write_desc.ready),
        	self.write_status_tag.status.eq(self.write_desc_status.tag),
        	self.write_status_error.status.eq(self.write_desc_status.error),
        	]

    @staticmethod
    def add_sources(platform):
        rtl_dir = os.path.join(os.path.dirname(__file__), "..", "verilog", "rtl")
        platform.add_source(os.path.join(rtl_dir, "arbiter.v"))
        platform.add_source(os.path.join(rtl_dir, "axi_dma_desc_mux.v"))
        platform.add_source(os.path.join(rtl_dir, "axi_dma_wr.v"))
        platform.add_source(os.path.join(rtl_dir, "axi_dma_rd.v"))
        platform.add_source(os.path.join(rtl_dir, "axi_dma.v"))
