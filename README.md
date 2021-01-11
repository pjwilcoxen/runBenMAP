# runBenMAP

A Python script that facilitates running large numbers of BenMAP-CE simulations on CMAQ output. It builds a set of BenMAP CTLX control scripts and then runs BenMAP on each one. It requires a patched version of BenMAP that improves support for batch mode. That source code is available here from the "batch-mode-updates" branch of [this repository](https://github.com/pjwilcoxen/BenMAP-CE).

### About BenMAP

BenMAP is the environmental Benefits Mapping and Analysis Program  developed by the US EPA. More information is available at EPA's [BenMAP web site](https://www.epa.gov/benmap).

### Running BenMAP from the command line

BenMAP has an extensive graphical interface and is usually run in that mode. However, most of its functionality is also available from the command line by constructing an appropriate command file. Command files are plain text and contain instructions described in the command line appendix of the BenMAP manual. They must have the extension `ctlx` and are fed into BenMAP via a single command line argument consisting of the file's name. For example, `sample.ctlx` would be run via the command `benmap sample.ctlx`.

### About this script

BenMAP's command line mode is helpful when it is necessary to run a large number of analyses. For example, one might wish to examine the impacts of 10 policy scenarios affecting two pollutants in 6 different years. However, that potentially requires dozens of `ctlx` files that can be tedious to build and run by hand. The `run_benmap.py` script provided here automates that for CMAQ output by building and running the `ctlx` files based instructions in a few small JSON files. Basic examples for AQG, CFG and APV runs are provided in the three corresponding JSON files. Note that starting versions of the CFGX and APVX files must be constructed using the GUI version of BenMAP: the command line version is not able to produce them.
