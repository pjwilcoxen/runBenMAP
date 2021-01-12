#! /usr/bin/python3
#  Jan 21 (PJW)
#
#  Build input control files for BenMAP and then run it in batch mode.
#

import json
import subprocess
import sys
import os
import string
import datetime
import fnmatch

#
#  ----------------
#  Define functions
#  ----------------
#

#
#  run_benmap
#
#     Build a BenMAP control file from a template and input 
#     dictionary of substituions. Then run it.
#

def run_benmap(info,ctlx_stem):

    template = get_template(info['mode'])
    file_text = template.substitute(info)

    work_dir = info['work_dir']

    ctlx_file = f"{work_dir}/{ctlx_stem}.ctlx"
    log_file  = f"{work_dir}/{ctlx_stem}.log"

    fh = open(ctlx_file,'w')
    fh.write( file_text )
    fh.close()

    if info['dryrun']:
        print(f"Wrote {ctlx_file}, skipping run",flush=True);
        return

    print(f"\nProcessing {ctlx_file}...",flush=True)
    proc = subprocess.run([info['benmap_exe'],ctlx_file],capture_output=True,text=True)
    print(proc.stdout)
        
    if proc.returncode != 0:
        print(f"Error code returned: {proc.returncode:X}")
    else:
        fh = open(log_file,'w')
        fh.write( proc.stdout )
        fh.close()

#
#  get_basenames
#
#     Return a standardized list of file names that match a pattern, 
#     omitting their extensions.
#

def get_basenames(dir,pat):
    names = [f.lower() for f in os.listdir(dir) if fnmatch.fnmatch(f,pat)]
    return [os.path.splitext(f)[0] for f in names]
    
#
#  not_done
#
#     Return items in the first list that aren't in the second one
#

def not_done(inp,out):
    return [i for i in inp if i not in out]

#
#  do_aqg
#
#      Convert all unconverted CSV files to AQGX format
#

def do_aqg(info):

    #
    #  Pollutants known to BenMAP
    #

    known_pollutants = {
        'pm':'PM2.5',
        'o3':'Ozone'
        }

    #
    #  Build lists of the input files and any previously-built output
    #  files. Won't rebuild files if they already exist.
    #

    csv_files = get_basenames(info['csv_dir'],'*.csv')
    aqg_files = get_basenames(info['aqg_dir'],'*.aqgx')

    todo = not_done(csv_files,aqg_files)

    #
    #  Process the input files one by one
    #

    for stem in todo:

        #  What pollutant?

        pollutant = stem[-2:]
        if pollutant not in known_pollutants:
            print("skipping unexpected pollutant file:",stem+'.csv')
            continue;
            
        #  Store information for loading the template

        info['run_data'] = stem
        info['pollutant'] = known_pollutants[pollutant]

        #  Run it

        run_benmap(info,stem)

#
#  do_cfg
#
#     Run all unprocessed AQGX files for a given year and pollutant
#

def do_cfg(info):

    #
    #  Extract some key data
    #

    year = info['year']
    pol = info['pollutant'].lower()

    suffix = f"{year}_{pol}"

    info['bau_data'] = f"bau_{suffix}"

    #
    #  Build a list of matching runs in the AQG directory
    #

    aqg_files = get_basenames(info['aqg_dir'],f'*_{suffix}.aqgx')
    cfg_files = get_basenames(info['cfgr_dir'],'*.cfgrx')

    todo = not_done(aqg_files,cfg_files)

    runs = [ f.replace(suffix,'') for f in todo ] 

    if 'bau' not in runs:
        print("No BAU run found for {pol} in {year}")
        sys.exit(0)

    #
    #  Run the analysis
    #

    runs.remove('bau')

    for run in runs:
        run_stem = f"{run}_{suffix}"
        info['alt_data'] = run_stem
        run_benmap(info,run_stem)

#
#  do_apv
#
#     Produce reports for all unprocessed CFGRX files
#

def do_apv(info):

    template = get_template('apv')

    cfgr_files = get_basenames(info['cfgr_dir'],'*.cfgrx')
    apvr_files = get_basenames(info['apvr_dir'],'*.apvrx')

    todo = not_done(cfgr_files,apvr_files)

    for f in todo:
        info['alt_data'] = f
        run_benmap(info,f)

#
#  get_template
#
#      Get the template for a given command mode
#

def get_template(mode):

    if mode == 'aqg':
        return string.Template("""## BenMAP-CE batch control file
## $now

VARIABLES

COMMANDS

SETACTIVESETUP -ActiveSetup United States

CREATE AQG

-Filename $aqg_dir\$run_data.aqgx
-GridType "CMAQ 36km"
-Pollutant $pollutant

ModelDirect

-ModelFilename $csv_dir\$run_data.csv
-DSNName "Text Files"

GENERATE REPORT AuditTrail

-InputFile  $aqg_dir\$run_data.aqgx
-ReportFile $aqg_dir\$run_data.txt

""")

    if mode == 'cfg':
        return string.Template("""## BenMAP-CE batch control file
## $now

VARIABLES

COMMANDS

SETACTIVESETUP -ActiveSetup United States

RUN CFG 

-CFGFilename      $cfg_dir/$cfg_file
-ResultsFilename  $cfgr_dir/$alt_data.cfgrx
-BaselineAQG      $aqg_dir/$bau_data.aqgx
-ControlAQG       $aqg_dir/$alt_data.aqgx
-Year             $year

GENERATE REPORT AuditTrail

-InputFile  $cfgr_dir/$alt_data.cfgrx
-ReportFile $cfgr_dir/$alt_data.txt

""")

    if mode == 'apv':
        return string.Template("""## BenMAP-CE batch control file
## $now

VARIABLES

COMMANDS

SETACTIVESETUP -ActiveSetup United States

RUN APV

-APVFilename           $apv_dir/$apv_file
-CFGRFilename          $cfgr_dir/$alt_data.cfgrx
-ResultsFilename       $apvr_dir/$alt_data.apvrx
-IncidenceAggregation  County
-ValuationAggregation  County

GENERATE REPORT AuditTrail

-InputFile  $apvr_dir/$alt_data.apvrx
-ReportFile $apvr_dir/$alt_data.txt

GENERATE REPORT APVR

-InputFile  $apvr_dir/$alt_data.apvrx
-ReportFile $apvr_dir/$alt_data-incidence.csv
-ResultType PooledIncidence

GENERATE REPORT APVR

-InputFile  $apvr_dir/$alt_data.apvrx
-ReportFile $apvr_dir/$alt_data-valuation.csv
-ResultType PooledValuation

""")

    print("error, unexpected mode:",mode)
    sys.exit()

#  
#  ---------------------------
#  Main processing begins here
#  ---------------------------
#

#
#  Check the command line for the command mode to use
#

args = sys.argv[1:]
if len(args) < 1 or args[0].lower() not in ['aqg','cfg','apv']:
    print("Usage: run_benmap.py aqg|cfg|apv [-n]")
    sys.exit()

mode = args[0].lower()

dryrun = False
if len(args) > 1 and args[1].lower() == '-n':
    dryrun = True

#
#  Default settings; can be overridden in the JSON input file
#

info = {
    'aqg_dir' :'aqg',   # where to find AQG files
    'cfg_dir' :'cfg',   # where to find the cfgx file
    'cfgr_dir':'cfgr',  # where to put the cfgrx files
    'apv_dir' :'apv',   # where to find the apvx file
    'apvr_dir':'apvr',  # where to put the apvrx files
    }

#
#  The work directory is where to put CTLX and log files
#

work_dirs = {
    'aqg':'aqg',
    'cfg':'cfgr',
    'apv':'apvr'
    }

info['work_dir'] = work_dirs[mode]

#
#  Required input file and settings for each mode
#

if mode == 'aqg':
    info_file = 'run_aqg.json'
    info_req  = [
        'benmap_exe', # path to benmap
        'csv_dir'     # path to CMAQ CSV files
        ]

if mode == 'cfg':
    info_file = 'run_cfg.json'
    info_req  = [
        'benmap_exe',  # path to benmap
        'cfg_file',    # name of the cfgx file
        'pollutant',   # pollutant (pm or o3)
        'year'         # year
        ]

if mode == 'apv':
    info_file = 'run_apv.json'
    info_req  = [
        'benmap_exe', # path to benmap
        'apv_file'
        ]

#
#  Read the JSON file and make sure it contains the required information
#

info_raw = json.load( open(info_file) )

for k,v in info_raw.items():
    info[k.lower()] = v

keys_bad = False
for r in info_req:
    if r not in info:
        print("Required key not found:",r)
        keys_bad = True

if keys_bad:
    sys.exit(0)

#
#  Add in the mode and the current date
#

info['mode'] = mode
info['now'] = datetime.datetime.now().strftime("%c")
info['dryrun'] = dryrun

#
#  Now go do the work that's specific to this task
#

if mode == 'aqg':
    do_aqg(info)

if mode == 'cfg':
    do_cfg(info)

if mode == 'apv':
    do_apv(info)

