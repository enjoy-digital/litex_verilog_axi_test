[> Intro
--------
This repository is an experiment to wrap Alex Forenchich's Verilog-AXI core with LiteX to easily compose AXI systems with it.

[> AXI-Lite Status
---------------------

| Module            | Status                     |
|-------------------|----------------------------|
| axil_adapter      | Done, passing simple tests |
| axil_cdc          | Done, passing simple tests |
| axil_crossbar     | Done, passing simple tests |
| axil_dp_ram       | Done, passing simple tests |
| axil_interconnect | Done, passing simple tests |
| axil_ram          | Done, passing simple tests |
| axil_register     | Done, passing simple tests |

[> AXI <-> AXI-Lite Status
--------------------------

| Module            | Status                                           |
|-------------------|--------------------------------------------------|
| axi_axil_adapter  | Done, passing simple tests                       |

[> AXI Status
----------------

| Module            | Status                                           |
|-------------------|--------------------------------------------------|
| axi_adapter       | Done, Verilator compil issue                     |
| axi_cdma          | Wrapped, need testing                            |
| axi_crossbar      | Done, passing simple tests                       |
| axi_dma           | Wrapped, need testing                            |
| axi_dp_ram        | Done, passing simple tests                       |
| axi_fifo          | Done, passing simple tests                       |
| axi_interconnect  | Done, passing simple tests                       |
| axi_ram           | Done, passing simple tests                       |
| axi _register     | Done, passing simple tests                       |
