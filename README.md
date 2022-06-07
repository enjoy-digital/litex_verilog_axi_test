[> Intro
--------
This repository is an experiment to wrap Alex Forenchich's Verilog-AXI core with LiteX to easily compose AXI systems with it.

[> AXI-Lite Status
---------------------

| Module            | Status                     |
|-------------------|----------------------------|
| axil_adapter      | Done, passing simple tests |
| axil_cdc          | Done, passing simple tests |
| axil_crossbar     | TODO                       |
| axil_dp_ram       | Done, passing simple tests |
| axil_interconnect | TODO  |
| axil_ram          | Done, passing simple tests |
| axil_register     | Done, passing simple tests |

[> AXI Status
----------------

| Module            | Status                                           |
|-------------------|--------------------------------------------------|
| axi_adapter       | Done, Verilator compil issue                     |
| axi_cdma          | TODO                                             |
| axi_crossbar      | Mostly Done, need to add base addresses and test |
| axi_dma           | TODO                                             |
| axi_dp_ram        | Done, passing simple tests                       |
| axi_fifo          | Done, passing simple tests                       |
| axi_interconnect  | Mostly Done, need to add base addresses and test |
| axi_ram           | Done, passing simple tests                       |
| axi _register     | Done, passing simple tests                       |
