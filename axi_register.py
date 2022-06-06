#
# This file is part of LiteX-Verilog-AXI-Test
#
# Copyright (c) 2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

# LiteX wrapper around Alex Forencich Verilog-AXI's axi_register.v.

import argparse

from migen import *

from litex.soc.interconnect.axi import *

from axi_common import *

# AXI Register Type --------------------------------------------------------------------------------

class AXIRegisterType:
    BYPASS        = 0
    SIMPLE_BUFFER = 1
    SKID_BUFFER   = 2

# AXI Register -------------------------------------------------------------------------------------

class AXIRegister(Module):
    def __init__(self, platform, s_axi, m_axi,
        aw_reg_type = AXIRegisterType.SIMPLE_BUFFER,
        w_reg_type  = AXIRegisterType.SKID_BUFFER,
        b_reg_type  = AXIRegisterType.SIMPLE_BUFFER,
        ar_reg_type = AXIRegisterType.SIMPLE_BUFFER,
        r_reg_type  = AXIRegisterType.SKID_BUFFER,
    ):
        self.logger = logging.getLogger("AXIAdapter")

        # Get/Check Parameters.
        # ---------------------

        # Clock Domain.
        clock_domain = s_axi.clock_domain
        if s_axi.clock_domain != m_axi.clock_domain:
            self.logger.error("{} on {} (Slave: {} / Master: {}), should be {}.".format(
                colorer("Different Clock Domain", color="red"),
                colorer("AXI interfaces."),
                colorer(s_axi.clock_domain),
                colorer(m_axi.clock_domain),
                colorer("the same")))
            raise AXIError()
        else:
            self.logger.info(f"Clock Domain: {colorer(clock_domain)}")

        # Address width.
        address_width = len(s_axi.aw.addr)
        if len(s_axi.aw.addr) != len(m_axi.aw.addr):
            self.logger.error("{} on {} (Slave: {} / Master: {}), should be {}.".format(
                colorer("Different Address Width", color="red"),
                colorer("AXI interfaces."),
                colorer(len(s_axi.aw.addr)),
                colorer(len(m_axi.aw.addr)),
                colorer("the same")))
            raise AXIError()

            raise AXIError()
        else:
            self.logger.info(f"Address Width: {colorer(address_width)}")

        # Data width.
        data_width = len(s_axi.w.data)
        if len(s_axi.w.data) != len(m_axi.w.data):
            self.logger.error("{} on {} (Slave: {} / Master: {}), should be {}.".format(
                colorer("Different Data Width", color="red"),
                colorer("AXI interfaces."),
                colorer(len(s_axi.w.data)),
                colorer(len(m_axi.w.data)),
                colorer("the same")))
            raise AXIError()
        else:
            self.logger.info(f"Data Width: {colorer(data_width)}")

        # ID width.
        id_width = len(s_axi.aw.id)
        if len(s_axi.aw.id) != len(m_axi.aw.id):
            self.logger.error("{} on {} (Slave: {} / Master: {}), should be {}.".format(
                colorer("Different ID Width", color="red"),
                colorer("AXI interfaces."),
                colorer(len(s_axi.aw.id)),
                colorer(len(m_axi.aw.id)),
                colorer("the same")))
            raise AXIError()

            raise AXIError()
        else:
            self.logger.info(f"ID Width: {colorer(address_width)}")

        # Registers.
        self.logger.info(f"AW Reg Type: {aw_reg_type}.")
        self.logger.info(f" W Reg Type: {w_reg_type}.")
        self.logger.info(f" B Reg Type: {b_reg_type}.")
        self.logger.info(f"AR Reg Type: {ar_reg_type}.")
        self.logger.info(f" R Reg Type: {r_reg_type}.")

        # Module instance.
        # ----------------

        self.specials += Instance("axi_register",
            # Parameters.
            # -----------
            p_DATA_WIDTH = data_width,
            p_ADDR_WIDTH = address_width,
            p_STRB_WIDTH = data_width//8,
            p_ID_WIDTH   = id_width,

            # FIXME: Enable it in LiteX's AXIInterface and add support.
            p_AWUSER_ENABLE = 0,
            p_AWUSER_WIDTH  = 1,
            p_WUSER_ENABLE  = 0,
            p_WUSER_WIDTH   = 1,
            p_BUSER_ENABLE  = 0,
            p_BUSER_WIDTH   = 1,
            p_ARUSER_ENABLE = 0,
            p_ARUSER_WIDTH  = 1,
            p_RUSER_ENABLE  = 0,
            p_RUSER_WIDTH   = 1,

            # Register type.
            p_AW_REG_TYPE = aw_reg_type,
            p_W_REG_TYPE  = w_reg_type,
            p_B_REG_TYPE  = b_reg_type,
            p_AR_REG_TYPE = ar_reg_type,
            p_R_REG_TYPE  = r_reg_type,

            # Clk / Rst.
            # ----------
            i_clk = ClockSignal(clock_domain),
            i_rst = ResetSignal(clock_domain),

            # AXI Slave Interface.
            # --------------------
            # AW.
            i_s_axi_awid     = s_axi.aw.id,
            i_s_axi_awaddr   = s_axi.aw.addr,
            i_s_axi_awlen    = s_axi.aw.len,
            i_s_axi_awsize   = s_axi.aw.size,
            i_s_axi_awburst  = s_axi.aw.burst,
            i_s_axi_awlock   = s_axi.aw.lock,
            i_s_axi_awcache  = s_axi.aw.cache,
            i_s_axi_awprot   = s_axi.aw.prot,
            i_s_axi_awqos    = s_axi.aw.qos,
            i_s_axi_awregion = 0, # FIXME.
            i_s_axi_awuser   = 0, # FIXME.
            i_s_axi_awvalid  = s_axi.aw.valid,
            o_s_axi_awready  = s_axi.aw.ready,

            # W.
            i_s_axi_wdata    = s_axi.w.data,
            i_s_axi_wstrb    = s_axi.w.strb,
            i_s_axi_wlast    = s_axi.w.last,
            i_s_axi_wuser    = 0, # FIXME.
            i_s_axi_wvalid   = s_axi.w.valid,
            o_s_axi_wready   = s_axi.w.ready,

            # B.
            o_s_axi_bid      = s_axi.b.id,
            o_s_axi_bresp    = s_axi.b.resp,
            o_s_axi_buser    = Open(), # FIXME.
            o_s_axi_bvalid   = s_axi.b.valid,
            i_s_axi_bready   = s_axi.b.ready,

            # AR.
            i_s_axi_arid     = s_axi.ar.id,
            i_s_axi_araddr   = s_axi.ar.addr,
            i_s_axi_arlen    = s_axi.ar.len,
            i_s_axi_arsize   = s_axi.ar.size,
            i_s_axi_arburst  = s_axi.ar.burst,
            i_s_axi_arlock   = s_axi.ar.lock,
            i_s_axi_arcache  = s_axi.ar.cache,
            i_s_axi_arprot   = s_axi.ar.prot,
            i_s_axi_arqos    = s_axi.ar.qos,
            i_s_axi_arregion = 0, # FIXME.
            i_s_axi_aruser   = 0, # FIXME.
            i_s_axi_arvalid  = s_axi.ar.valid,
            o_s_axi_arready  = s_axi.ar.ready,

            # R.
            o_s_axi_rid      = s_axi.r.id,
            o_s_axi_rdata    = s_axi.r.data,
            o_s_axi_rresp    = s_axi.r.resp,
            o_s_axi_rlast    = s_axi.r.last,
            o_s_axi_ruser    = Open(), # FIXME.
            o_s_axi_rvalid   = s_axi.r.valid,
            i_s_axi_rready   = s_axi.r.ready,

            # AXI Master Interface.
            # ---------------------
            # AW.
            o_m_axi_awid     = m_axi.aw.id,
            o_m_axi_awaddr   = m_axi.aw.addr,
            o_m_axi_awlen    = m_axi.aw.len,
            o_m_axi_awsize   = m_axi.aw.size,
            o_m_axi_awburst  = m_axi.aw.burst,
            o_m_axi_awlock   = m_axi.aw.lock,
            o_m_axi_awcache  = m_axi.aw.cache,
            o_m_axi_awprot   = m_axi.aw.prot,
            o_m_axi_awqos    = m_axi.aw.qos,
            o_m_axi_awregion = Open(),
            o_m_axi_awuser   = Open(),
            o_m_axi_awvalid  = m_axi.aw.valid,
            i_m_axi_awready  = m_axi.aw.ready,

            # W.
            o_m_axi_wdata    = m_axi.w.data,
            o_m_axi_wstrb    = m_axi.w.strb,
            o_m_axi_wlast    = m_axi.w.last,
            o_m_axi_wuser    = Open(), # FIXME.
            o_m_axi_wvalid   = m_axi.w.valid,
            i_m_axi_wready   = m_axi.w.ready,

            # B.
            i_m_axi_bid      = m_axi.b.id,
            i_m_axi_bresp    = m_axi.b.resp,
            i_m_axi_buser    = 0, # FIXME.
            i_m_axi_bvalid   = m_axi.b.valid,
            o_m_axi_bready   = m_axi.b.ready,

            # AR.
            o_m_axi_arid     = m_axi.ar.id,
            o_m_axi_araddr   = m_axi.ar.addr,
            o_m_axi_arlen    = m_axi.ar.len,
            o_m_axi_arsize   = m_axi.ar.size,
            o_m_axi_arburst  = m_axi.ar.burst,
            o_m_axi_arlock   = m_axi.ar.lock,
            o_m_axi_arcache  = m_axi.ar.cache,
            o_m_axi_arprot   = m_axi.ar.prot,
            o_m_axi_arqos    = m_axi.ar.qos,
            o_m_axi_arregion = Open(),
            o_m_axi_aruser   = Open(),
            o_m_axi_arvalid  = m_axi.ar.valid,
            i_m_axi_arready  = m_axi.ar.ready,

            # R.
            i_m_axi_rid      = m_axi.r.id,
            i_m_axi_rdata    = m_axi.r.data,
            i_m_axi_rresp    = m_axi.r.resp,
            i_m_axi_rlast    = m_axi.r.last,
            i_m_axi_ruser    = 0, # FIXME.
            i_m_axi_rvalid   = m_axi.r.valid,
            o_m_axi_rready   = m_axi.r.ready,
        )

        # Add Sources.
        # ------------
        self.add_sources(platform)

    @staticmethod
    def add_sources(platform):
        platform.add_source("verilog-axi/rtl/axi_register_wr.v")
        platform.add_source("verilog-axi/rtl/axi_register_rd.v")
        platform.add_source("verilog-axi/rtl/axi_register.v")
