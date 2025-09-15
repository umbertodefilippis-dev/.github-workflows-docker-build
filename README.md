haa_raw2cal_pipeline - Docker Usage Guide
=========================================

Overview
--------
This Docker image runs the haa_raw2cal pipeline, processing HAA instrument telemetry and science data files to produce calibrated outputs. It is self-contained and includes all required dependencies.
----------------------------------------
INSTALLATION
----------------------------------------

1. Load the Docker Image

To load the image from a .tar.gz file:

    docker load < /yourabsolutepath/3gm_haa_raw2cal_0.1.0.tar.gz

You should see a message like:
    Loaded image: 3gm_haa_raw2cal_0.1.0:latest

PASS:
- Output: 'Loaded image: 3gm_haa_raw2cal_0.1.0:latest' (or similar)
FAIL:
- Error about file not found or permission denied.

----------------------------------------
FOLDER STRUCTURE
----------------------------------------

The following folder structure MUST exist on your local machine:

    /yourabsolutepath/
    |-inputs/
    |   |-- pds/                    <-- Raw data files (.csv, .lblx)
    |   |-- miscellaneous/
    |       |--version_summary.json
    |-- outputs/                    <-- To be created locally! Will contain processed results
    |-- logs/                       <-- To be created locally! Will contain execution logs

Ensure the input directory structure matches what the script expects:
- 'inputs/pds' contains .csv/.lblx files (in pairs)
- 'inputs/miscellaneous/version_summary.json' is present

FAIL:
- Missing version_summary.json
- Missing or unpaired .csv/.lblx files

----------------------------------------
Run the Docker Container
----------------------------------------

*********** IMPORTANT ***********
The actual kernel version does not include the HAA reference frame.
However, temporary files have been created ('juice_struct_v22.bsp' and 'juice_v43.tf' provided in the projects repository) which MUST be added in the FK and SPK folders as well as in the metakernel (juice_ops.tm), before running the docker image.
*********************************

Use the following command:

docker run --rm \
  -v /Users/yourabsolutepath/kernels:/data/spice:ro \
  -v /Users/yourabsolutepath/inputs:/app/inputs \
  -v /Users/yourabsolutepath/outputs:/app/outputs \
  -v /Users/yourabsolutepath/logs:/app/logs \
  3gm_haa_raw2cal_0.1.0


The folders inputs, outputs, logs and kernels must exist on your machine. 
Replace /yourabsolutepath/ with the actual absolute path on your machine (e.g., /Users/yourname/Desktop/haa_data/inputs).

PASS:
- The container starts and runs to completion.
- 'outputs/' contains generated files.
- 'logs/' contains log files with 'INFO' and no 'ERROR' messages.

FAIL:
- Error messages like:  
    - 'Missing version_summary.json. Exiting'  
    - 'Missing required HK input files. Exiting'
- No new output or log files created.


----------------------------------------
Output
----------------------------------------

- Processed files will be written to:

      /yourabsolutepath/outputs/

- Logs of the execution will be saved in:

      /yourabsolutepath/logs/

PASS:
- New files exist in `/outputs/` and `/logs/`
- Log file shows pipeline reached "All required input files are present."
FAIL:
- Log contains "ERROR" entries
- No files in 'outputs/'

----------------------------------------
Troubleshooting
----------------------------------------

- Check file/folder permissions if you get "permission denied" errors.
- Ensure Docker Desktop is running (macOS/Windows).
- All volumes must point to existing local paths.

----------------------------------------

----------------------------------------
SPICE Kernels Usage
----------------------------------------

Current Version:
We assume that the latest operational kernels will always be mounted to your image read-only in these three locations:
/data/spice
/data/kernels
/data/spice_kernels
To follow the SPICE teams recommendations to "absolutize" the metakernel, we have:
Copied from /data/spice/mk/juice_ops.mk to /tmp/juice_abs_ops.mk
Replaced all paths within the metakernel with the chosen mounted directory (one of the three above options)
Referenced /tmp/juice_abs_ops.mk from the pipeline instead of the immutable (read-only) /data/spice/mk/juice_ops.mk



PASS:
- No errors
FAIL:
- SPICE(UNKNOWNFRAME) --
The frame JUICE_HAA_URF was not recognized as a known reference frame.
pxform_c --> PXFORM


Future Versions:
- These two files will be added in the SPICE mission kernels.

----------------------------------------
Test case
----------------------------------------
In the input folder uploaded in the gitlab project there are some files which can be used as a test.

PASS:
At the end of the pipeline execution the outputs folder must contain the following files:
haa_cal_hk_20230504__0_1.csv/.lblx
haa_cal_sc_nominal_20240819__0_1.csv/.lblx
haa_par_sc_nominal_20240819__0_1.csv/.lblx

The LOG file must contains only |INFO| messages.
During execution these lines will be printed on the desktop: 

Processing label: /app/inputs/pds/haa_raw_hk_event_report.lblx
Now processing a Table_Delimited structure: HAA RAW EVENT REPORT
Processing label: /app/inputs/pds/haa_raw_hk_20230504.lblx
Now processing a Table_Delimited structure: HAA RAW HOUSEKEEPING
Processing label: /app/inputs/pds/haa_raw_sc_nominal_20240819.lblx
Now processing a Table_Delimited structure: HAA RAW SCIENCE DATA TABLE

FAIL:
Missing files in the outputs directory or |ERROR| messages in the LOG file

Author: Umberto De Filippis
Version: 0.1.0
Date: 2025-06-03
