import pds4_tools
import numpy as np
from datetime import datetime as dt
import common_routines.raw2eng as raw2eng
import json
import matplotlib.dates as mdates
from datetime import datetime
import spiceypy as spice
from scipy.spatial.transform import Rotation
from common_routines.raw2cal_Dictionaryscience import raw2cal_Dictionaryscience
from common_routines.raw2eng_Dictionaryscience import raw2eng_Dictionaryscience
from common_routines.raw2eng_DictionaryHK import raw2eng_DictionaryHK
from common_routines.raw2cal_DictionaryscienceHR import raw2cal_DictionaryscienceHR
from common_routines.calibration_Dictionary import calibration_Dictionary
import os
from common_routines.csv_writer import csvwriter
from common_routines.csv_writer import process_calibration_file
import subprocess
import hashlib
from common_routines.vertex_reduction import data_reduction
import re
import sys
import argparse
import uuid
import shutil
import tarfile

# Helper to format log messages
def write_log(log_path, severity, origin, sw_module, exec_id, message):
    timestamp = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(log_path, "a") as log_file:
        log_file.write(f"{timestamp}|{severity}|{origin}|{sw_module}|{exec_id}|{message}\n")


def datenum(d):
    return 366 + d.toordinal() + (d - dt.fromordinal(d.toordinal())).total_seconds()/(24*60*60)

def angular_velocities(q1, q2, dt):
    return (2 / dt) * np.array([
        q1[0]*q2[1] - q1[1]*q2[0] - q1[2]*q2[3] + q1[3]*q2[2],
        q1[0]*q2[2] + q1[1]*q2[3] - q1[2]*q2[0] - q1[3]*q2[1],
        q1[0]*q2[3] - q1[1]*q2[2] + q1[2]*q2[1] - q1[3]*q2[0]])
def compute_checksum(file_path):
                """
                Calcola il checksum MD5 di un file.

                :param file_path: Percorso del file di cui calcolare il checksum.
                :return: Stringa con il checksum MD5.
                """
                hash_md5 = hashlib.md5()
                try:
                    with open(file_path, "rb") as file:
                        # Leggi il file in blocchi per evitare problemi con file di grandi dimensioni
                        for chunk in iter(lambda: file.read(4096), b""):
                            hash_md5.update(chunk)
                    return hash_md5.hexdigest()
                except FileNotFoundError:
                    print(f"Errore: Il file {file_path} non esiste.")
                    return None

def extract_version_id(file_path):
                # Percorso del file version_summary.json
                #file_path = os.path.join("src/inputs", "miscellaneous", "version_summary.json")
                
                try:
                    # Leggi il file JSON
                    with open(file_path, "r") as file:
                        data = json.load(file)
                    
                    # Estrai il valore di baseVersion
                    version_id = data.get("baseVersion", None)
                    
                    if version_id is None:
                        raise ValueError("baseVersion non trovato nel file JSON.")
                    
                    return version_id
                except FileNotFoundError:
                    raise FileNotFoundError(f"Il file {file_path} non esiste.")
                except json.JSONDecodeError:
                    raise ValueError(f"Errore nel parsing del file JSON: {file_path}")

def get_file_size(file_path):
                result = subprocess.check_output(['du', '-b', file_path]).split()[0].decode('utf-8')
                return result

# Funzione per ottenere il numero di righe del file
def get_file_records(file_path):
    result = subprocess.check_output(['wc', '-l', file_path]).split()[0].decode('utf-8')
    return result

def compute_spacecraft_target_distances(start_epoch: str, end_epoch: str, observer: str, target: str, num_points=1000):
    """
    Compute minimum and maximum distances between a spacecraft and a target over a given time range.

    Parameters:
    - start_epoch (str): Start time in UTC format (e.g., "2025-01-01T00:00:00").
    - end_epoch (str): End time in UTC format (e.g., "2025-12-31T00:00:00").
    - observer (str): NAIF name or ID of the spacecraft.
    - target (str): NAIF name or ID of the target body.
    - num_points (int): Number of time samples for calculations.

    Returns:
    - tuple: (min_distance, max_distance) in km
    """

    # Convert time to Ephemeris Time (ET)
    start_et = spice.str2et(start_epoch)
    end_et = spice.str2et(end_epoch)

    # Generate time samples
    times = np.linspace(start_et, end_et, num_points)

    # Define frame and aberration correction
    frame = "J2000"
    abcorr = "NONE"

    # Compute spacecraft-target distances
    distances = [
        np.linalg.norm(spice.spkezr(observer, et, frame, abcorr, target)[0][:3])
        for et in times
    ]

    # Return min and max distances
    return float(min(distances)), float(max(distances))

def generate_dyn_vector(par_data, service_events):
    """
    Generate a dyn vector based on the mode ('ExtRange' or 'NormDyn').

    Parameters:
    - par_data: Dictionary containing product data with 'TIME_UTC' as keys.
    - service_events: List of tuples containing (date, description) for service events.

    Returns:
    - dyn: List of integers (1 for 'ExtRange', 10 for 'NormDyn') with the same length as par_data['TIME_UTC'].
    """
    # Convert par_data['TIME_UTC'] to datetime objects
    time_utc = [datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ") for t in par_data['TIME_UTC']]

    # Convert service_events to datetime objects
    service_events_dt = [
        (datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ"), description)
        for date, description in service_events
    ]

    # Sort service events by time
    service_events_dt.sort(key=lambda x: x[0])

    # Initialize the dyn vector
    dyn = []

    # Iterate through each timestamp in par_data['TIME_UTC']
    for t in time_utc:
        # Find the most recent service event before or at the current time
        mode = None
        for i in range(len(service_events_dt)):
            if service_events_dt[i][0] <= t:
                mode = service_events_dt[i][1]
            else:
                break

        # Assign 1 for 'ExtRange' and 10 for 'NormDyn'
        if mode and "ExtRange" in mode:
            dyn.append(1)
        elif mode and "NormDyn" in mode:
            dyn.append(10)
        else:
            # Default value if no mode is found
            dyn.append(0)

    return dyn

def compute_angular_velocity(rotation_matrices, time_intervals):
    """
    Compute angular velocity from a series of rotation matrices.

    Parameters:
    - rotation_matrices: List of 3x3 rotation matrices (numpy arrays).
    - time_intervals: List of time intervals (in seconds) between consecutive matrices.

    Returns:
    - angular_velocities: List of angular velocity vectors (numpy arrays).
    """
    
    # Current and next rotation matrices
    R1 = rotation_matrices[0]
    R2 = rotation_matrices[1]

    # Time interval
    dt = time_intervals

    # Compute the derivative of the rotation matrix
    R_dot = (R2 - R1) / dt

    # Compute the angular velocity matrix
    omega_matrix = np.dot(R_dot, R1.T)

    # Extract the angular velocity vector from the skew-symmetric matrix
    omega = np.array([
        omega_matrix[2, 1],
        omega_matrix[0, 2],
        omega_matrix[1, 0]
    ])

    angular_velocities = omega

    return angular_velocities

# --- Automatically extract .tar.gz if present in the input directory ---
def extract_tar_gz(input_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith(".tar.gz"):
            archive_path = os.path.join(input_dir, filename)
            print(f"Extracting archive: {archive_path}")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=input_dir)
            print("Extraction complete.")

            # Normalize: move 'pds' and 'miscellaneous' from any subfolder to input_dir
            for entry in os.listdir(input_dir):
                full_path = os.path.join(input_dir, entry)
                if os.path.isdir(full_path):
                    for sub in ["pds", "miscellaneous"]:
                        src = os.path.join(full_path, sub)
                        dst = os.path.join(input_dir, sub)
                        if os.path.exists(src):
                            if os.path.exists(dst):
                                shutil.rmtree(dst)
                            shutil.move(src, dst)
                    # Remove the extracted parent folder if empty
                    if full_path != input_dir:
                        try:
                            os.rmdir(full_path)
                        except OSError:
                            pass  # folder not empty, leave it

# Parser
parser = argparse.ArgumentParser(description="HAA raw2cal pipeline")
parser.add_argument("-i", "--input", default="/data/input", help="Path to input data pack")
parser.add_argument("-o", "--output", default="/data/output", help="Path to output folder")
parser.add_argument("-l", "--log", default="/data/logs", help="Path to log folder")
args = parser.parse_args()

input_folder = args.input
folder_name = args.output
logs_directory = args.log

# Extraction + normalization
extract_tar_gz(input_folder)

pds_folder = os.path.join(input_folder, "pds")

origin = "raw2cal_pipeline"
exec_id = str(uuid.uuid4())  # or pass from main()

if not os.path.exists(pds_folder):
    raise FileNotFoundError(f"Expected folder {pds_folder} not found after extraction/normalization!")

# Create output/logs if not exist
os.makedirs(folder_name, exist_ok=True)
os.makedirs(logs_directory, exist_ok=True)

log_file_path = os.path.join(logs_directory, "haa_raw2cal.log")

# Path to your SPICE kernel file
kernel_name = 'juice_ops.tm'

# Clear the SPICE kernel 
spice.kclear()

original_mk = "/data/spice/mk/"+kernel_name
abs_mk = "/tmp/juice_ops_abs.tm"

# Read original metakernel and replace PATH_VALUES
with open(original_mk, "r") as infile:
    lines = infile.readlines()

with open(abs_mk, "w") as outfile:
    for line in lines:
        if "PATH_VALUES" in line:
            outfile.write("PATH_VALUES = ( '/data/spice' )\n")
        else:
            outfile.write(line)


# Then load the new metakernel
spice.furnsh(abs_mk)

# Create the logs directory if it doesn't exist
os.makedirs(logs_directory, exist_ok=True)


misc_folder = os.path.join(input_folder, "miscellaneous")

# Pattern groups to track files
hk_files = {}
sc_files = {}

# Scan files in input folder
for file in os.listdir(pds_folder):
    if file.startswith("haa_raw_hk_"):
        base = re.sub(r'\.(csv|lblx)$', '', file)
        hk_files.setdefault(base, set()).add(file)
    elif file.startswith("haa_raw_sc_"):
        base = re.sub(r'\.(csv|lblx)$', '', file)
        sc_files.setdefault(base, set()).add(file)

# Validation function
def check_file_pairs(file_groups):
    missing = []
    for base, files in file_groups.items():
        expected_csv = f"{base}.csv"
        expected_lblx = f"{base}.lblx"
        if expected_csv not in files or expected_lblx not in files:
            missing.append((base, expected_csv, expected_lblx))
    return missing

# Perform checks
missing_hk = check_file_pairs(hk_files)
missing_sc = check_file_pairs(sc_files)
version_summary_path = os.path.join(misc_folder, "version_summary.json")
has_version_summary = os.path.isfile(version_summary_path)
# New: check for event file
event_file_path = os.path.join(input_folder, 'pds', 'haa_raw_hk_event_report.lblx')
has_event_file = os.path.isfile(event_file_path)


# Controllo e log degli errori
if missing_hk:
    for base, csv, lblx in missing_hk:
        write_log(log_file_path, "ERROR", origin, "input_validator", exec_id,
                  f"Missing files for {base}: expected {csv} and {lblx}")
    sys.exit("Missing required HK input files. Exiting")

if missing_sc:
    for base, csv, lblx in missing_sc:
        write_log(log_file_path, "ERROR", origin, "input_validator", exec_id,
                  f"Missing files for {base}: expected {csv} and {lblx}")
    sys.exit("Missing required SC input files. Exiting")

if not has_version_summary:
    write_log(log_file_path, "ERROR", origin, "input_validator", exec_id,
              "Missing file: version_summary.json in miscellaneous folder")
    sys.exit("Missing version_summary.json. Exiting")

if not has_event_file:
    write_log(log_file_path, "ERROR", origin, "input_validator", exec_id,
              "Missing file: haa_raw_hk_event_report.lblx in input folder")
    sys.exit("Missing haa_raw_hk_event_report.lblx. Exiting")

write_log(log_file_path, "INFO", origin, "input_validator", exec_id,
          "All required input files are present.")

structures_event = pds4_tools.read(event_file_path)
event_data = structures_event[0].data
        
service_events = [
        (event_data['EVENT TIME UTC'][i], event_data['EVENT DESCRIPTION'][i])
        for i in range(len(event_data['EVENT NAME']))
        if event_data['EVENT NAME'][i] == 'Service Event'
]




for filename in os.listdir(pds_folder):
    #if 'haa_raw_sc_highrate' in filename:
    #    continue                                                # skip entirely highrate for now, TBD: implementation of high rate #
    if filename.endswith('.lblx'):
        file_path = os.path.join(pds_folder, filename)
        try:
            if 'haa_raw_sc_nominal' in filename:
                product_type = 'sc'
            elif 'haa_raw_sc_highrate' in filename:
                product_type = 'sc_hr'
            elif 'haa_raw_hk' in filename and 'haa_raw_hk_event' not in filename:
                product_type = 'hk'
            elif 'haa_raw_hk_event' in filename:
                continue
            else:
                # If the file does not match the expected patterns, skip it
                with open(log_file_path, "a") as log_file:
                    log_file.write(f"Skipping {filename} as it does not match expected patterns." + "\n")
                continue
            structures_par = pds4_tools.read(file_path)
            par_data = structures_par[0].data
            xmlschema = './src/xml_schema/haa_cal_sc_nominal_XXXXXXXX.lblx'
            xmlschema_config = './src/xml_schema/haa_calib_electronic-scale-factors.lblx'

            # Read calibration from JSON file
            with open('./src/common_routines/calibration.json', 'r') as file:
                calibration = json.load(file)

            par_data2 = {}
            for key in par_data.meta_data.keys():
                par_data2[key] = {
                        'name': {'Text': key},
                        'data': par_data[key], 
                        }
# Compute HAA selected dynamic  
            dyn = generate_dyn_vector(par_data, service_events)
            eng = raw2eng.raw2eng(par_data2, calibration, product_type, dyn)
            write_log(
                log_path=log_file_path,
                severity="INFO",
                origin=origin,
                sw_module="Data calibration",
                exec_id=exec_id,
                message=f"Starting calibration for {filename} with product type {product_type}"
            )


        except Exception as e:
            write_log(
                log_path=log_file_path,
                severity="ERROR",
                origin=origin,
                sw_module="Data calibration",
                exec_id=exec_id,
                message=f"Error processing {filename}: {e}"
            )

        if product_type == 'sc':
            #with open(log_file_path, "a") as log_file:
                    #log_file.write(f"Start processing science data" + "\n")
            Flyby_target = structures_par.label.findall('.//Target_Identification/name') 
            Flyby_target=Flyby_target[0].text


            eng_data = {key: eng[key]['data'] for key in eng.keys()}
            time = eng['TIME_UTC']['data']
            time_form = time[0].split("T")[0].replace("-", "")

            lid = structures_par.label.findall('.//Identification_Area/logical_identifier')
            mfn = structures_par.label.findall('.//psa:mission_phase_name')
            mfi = structures_par.label.findall('.//psa:mission_phase_identifier')
            type = structures_par.label.findall('.//Target_Identification/type')
            fn = structures_par.label.findall('.//file_name')
            l = structures_par.label.findall('.//file_size') 

            process_calibration_file(
                calib_json_path='./src/common_routines/calibration.json',
                sc_eng=eng_data,
                output_csv_path = os.path.join(folder_name, f"haa_calibration_{time_form}.csv")
            )
            namecsv_config = os.path.join(folder_name, f"haa_calibration_{time_form}.csv")
            xmlschema_edited_config = os.path.join(folder_name, f"haa_calibration_{time_form}.lblx")
            csv_checksum = compute_checksum(namecsv_config)
            v_id = extract_version_id(version_summary_path)
            
            config_cal = {
                'input_folder': '',
                'output_folder': '',
                'Mission_Information': {
                    'mission_phase_identifier': mfi[0].text,
                    'mission_phase_name': mfn[0].text,
                    'filename': f"haa_calibration_{time_form}",
                    'filesize':l[0].text,
                    'filename_csv' : f"haa_calibration_{time_form}.csv"
                },
                'Target_Identification': {
                    'name': Flyby_target,
                    'type': type[0].text,
                    'lid_reference': 'urn:nasa:pds:context:target:'+type[0].text.lower()+'.'+Flyby_target.lower()
                },
                'Modification_detail': {
                    'version_id': str(v_id),                     
                },
                'File_Area_Ancillary': {
                    'file_size': get_file_size(namecsv_config),
                    'records': get_file_records(namecsv_config),
                    'checksum': str(csv_checksum),
                },
                'Processing_Input_Identification': {
                     'file_name': kernel_name,
                }
            }
            
            calibration_Dictionary(time,xmlschema_config, xmlschema_edited_config, config_cal)

            file_name = fn[0].text
            file_name = file_name.replace('.csv', '')
            file_name = file_name.replace('raw', 'par')
            file_path_dic = os.path.join(folder_name, file_name)
         
            if os.path.exists(str(file_path_dic)+'.npz'):
                # Delete the file
                os.remove(str(file_path_dic)+'.npz')
        

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)


        
        
            # Split version_id in `i` e `j`
            version_parts = v_id.split(".")
            if len(version_parts) != 2:
                raise ValueError(f"Version ID {v_id} non è nel formato corretto i.j")

            i, j = version_parts
            xmlschema_edited = folder_name+f"{file_name}__{i}_{j}.lblx"
            file_name = f"{file_name}__{i}_{j}.csv"  # Aggiungi il suffisso

            csvwriter(eng_data,file_name,folder_name)
            # Combine the folder path and file name
            file_path_dic = os.path.join(folder_name, file_name)

            namecsv = file_path_dic 
                    
            csv_checksum = compute_checksum(folder_name+file_name)


            if os.path.isfile(folder_name + file_name):
                write_log(
                    log_path=log_file_path,
                    severity="INFO",
                    origin=origin,
                    sw_module="Creation of CSV file",
                    exec_id=exec_id,
                    message=f"Csv saved successfully with name: {file_path_dic}"
                )
            else:
                write_log(
                    log_path=log_file_path,
                    severity="ERROR",
                    origin=origin,
                    sw_module="Creation of CSV file",
                    exec_id=exec_id,
                    message=f"Error in saving Csv with name: {file_path_dic}"
                )

            if os.path.exists(str(file_path_dic)+'.npz'):
                # Delete the file
                os.remove(str(file_path_dic)+'.npz')
            
            SUNmin_dist, SUNmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", "SUN")
            Targetmin_dist, Targetmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", Flyby_target)
            Earthmin_dist, Earthmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", "Earth")


            config = {
                'input_folder': '',
                'output_folder': '',
                'dynamic': dyn,                                                
                'Mission_Information': {
                    'mission_phase_identifier': mfi[0].text,
                    'mission_phase_name': mfn[0].text,
                    'lid': lid[0].text,
                    'filename': os.path.splitext(fn[0].text)[0].replace('raw', 'par'),
                    'filesize':l[0].text,
                    'filename_csv' : file_name
                },
                'Target_Identification': {
                    'name': Flyby_target,
                    'type': type[0].text,
                    'lid_reference': 'urn:nasa:pds:context:target:'+type[0].text.lower()+'.'+Flyby_target.lower()
                },
                'Modification_detail': {
                    'version_id': str(v_id),                     
                },
                'File_Area_Observational': {
                    'file_size': get_file_size(namecsv),
                    'records': get_file_records(namecsv),
                    'checksum': str(csv_checksum),
                },
                'Processing_Input_Identification': {
                     'file_name': kernel_name,
                },
                'Distances_Min_Max': {
                    'minimum_spacecraft_heliocentric_distance': SUNmin_dist,
                    'maximum_spacecraft_heliocentric_distance': SUNmax_dist,
                    'minimum_spacecraft_target_center_distance': Targetmin_dist,
                    'maximum_spacecraft_target_center_distance': Targetmax_dist,
                    'minimum_target_geocentric_distance': Earthmin_dist,
                    'maximum_target_geocentric_distance': Earthmax_dist,
                },
                'Primary_Result_Summary': {
                    'processing_level': 'Partially Processed',
                }
                }

            raw2eng_Dictionaryscience(time, eng_data, xmlschema,xmlschema_edited, config)
                
            expected_filename = config["Mission_Information"]["filename"]

            if os.path.isfile(xmlschema_edited):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata saved successfully in: {xmlschema_edited}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata generation failed — expected file '{xmlschema_edited}' not found."
                )

            #folder_name = 'src/outputs'
            file_name = fn[0].text
            file_name = file_name.replace('.csv', '')
            file_name = file_name.replace('raw', 'cal')
            file_path_dic = os.path.join(folder_name, file_name)

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)


            
            v_id = extract_version_id(version_summary_path)
            # Split version_id in `i` e `j`
            version_parts = v_id.split(".")
            if len(version_parts) != 2:
                raise ValueError(f"Version ID {v_id} non è nel formato corretto i.j")

            i, j = version_parts
            xmlschema_edited = folder_name+f"{file_name}__{i}_{j}.lblx"
            file_name = f"{file_name}__{i}_{j}.csv"  # Aggiungi il suffisso

            # Combine the folder path and file name
            file_path_dic = os.path.join(folder_name, file_name)

            namecsv = file_path_dic 


            # Vertex reduction procedure ########## TO be tested ###########

            ets = [spice.str2et(str(time[0])),spice.str2et(str(time[-1]))]
            et = np.linspace(ets[0], ets[-1], len(time))
            angvel = []
            for i in range(len(et) - 1):                
                #sclkch = spice.sce2s(-28, t)  # Converti il tempo ET in SCLK string
                #sclkdp = spice.scencd(-28, sclkch)  # Converti la stringa SCLK in doppia precisione
                #(cmat,clkout) = spice.ckgp(int(-28000), sclkdp, 100, 'J2000')[0]
                time_intervals = et[i+1]-et[i]
                rotmat = spice.pxform('JUICE_SPACECRAFT', 'J2000', et[i])  # Ottieni la matrice di rotazione
                rotmat2 = spice.pxform('JUICE_SPACECRAFT', 'J2000', et[i+1])  # Ottieni la matrice di rotazione
                angvel.append(compute_angular_velocity([rotmat, rotmat2], time_intervals))

            angvel = np.array(angvel)  # Converti in array NumPy per calcoli successivi
            angvel = np.vstack((angvel, angvel[-1]))  # Aggiungi l'ultimo valore mancante
            # Calcola ANGDOT
            ANGDOT = np.diff(angvel, axis=0) / (np.diff(et)[:, None] * 86400)
            ANGDOT = np.vstack((ANGDOT, ANGDOT[-1]))  # Aggiungi l'ultimo valore mancante
            COM_FD = spice.spkpos( 'JUICE', et, 'JUICE_SPACECRAFT', 'LT', 'JUICE_SPACECRAFT')
            COM = COM_FD[0].T
            valuesGM = spice.bodvrd(Flyby_target, 'GM', 1)
            Radius = spice.bodvrd(Flyby_target, 'RADII', 3)
            [state, ltime] = spice.spkezr(Flyby_target, et, 'JUICE_SPACECRAFT', 'LT', 'JUICE')
            tolGG = 10**-9


            # Rotation matrix from HAA sensible axis to JUICE_SPACECRAFT reference frame 
            MSAD_SRF = spice.pxform('JUICE_HAA_URF', 'JUICE_SPACECRAFT', et[0])

            accx = eng_data['ACC_X_HAA_URF_DIRECTED']
            accy = eng_data['ACC_Y_HAA_URF_DIRECTED']
            accz = eng_data['ACC_Z_HAA_URF_DIRECTED']

            meas_acc = np.stack((np.array(accx), np.array(accy), np.array(accz)), axis=0)
            ACC_reduced = np.array(data_reduction(meas_acc,angvel,ANGDOT,MSAD_SRF,valuesGM[1],np.array(state).T,tolGG,et[0])).reshape((3,-1))
            eng_data['ACC_X_HAA_URF_DIRECTED'] = ACC_reduced[0]
            eng_data['ACC_Y_HAA_URF_DIRECTED'] = ACC_reduced[1]
            eng_data['ACC_Z_HAA_URF_DIRECTED'] = ACC_reduced[2] 

            csvwriter(eng_data,file_name,folder_name)
        
            if os.path.isfile(folder_name + file_name):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of CSV file",
                    exec_id,
                    f"CSV saved successfully with name: {file_path_dic}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of CSV file",
                    exec_id,
                    f"Error in saving CSV with name: {file_path_dic}"
                )
 
            csv_checksum = compute_checksum(folder_name+file_name)

            config = {
                'input_folder': '',
                'output_folder': '',
                'dynamic': dyn,                                                
                'Mission_Information': {
                    'mission_phase_identifier': mfi[0].text,
                    'mission_phase_name': mfn[0].text,
                    'lid': lid[0].text,
                    'filename': os.path.splitext(fn[0].text)[0].replace('raw', 'cal'),
                    'filesize':l[0].text,
                    'filename_csv' : file_name
                },
                'Target_Identification': {
                    'name': Flyby_target,
                    'type': type[0].text,
                    'lid_reference': 'urn:nasa:pds:context:target:'+type[0].text.lower()+'.'+Flyby_target.lower()
                },
                'Modification_detail': {
                    'version_id': str(v_id),                     
                },
                'File_Area_Observational': {
                    'file_size': get_file_size(namecsv),
                    'records': get_file_records(namecsv),
                    'checksum': str(csv_checksum),
                },
                'Processing_Input_Identification': {
                     'file_name': kernel_name,
                },
                'Distances_Min_Max': {
                    'minimum_spacecraft_heliocentric_distance': SUNmin_dist,
                    'maximum_spacecraft_heliocentric_distance': SUNmax_dist,
                    'minimum_spacecraft_target_center_distance': Targetmin_dist,
                    'maximum_spacecraft_target_center_distance': Targetmax_dist,
                    'minimum_target_geocentric_distance': Earthmin_dist,
                    'maximum_target_geocentric_distance': Earthmax_dist,
                },
                'Primary_Result_Summary': {
                    'processing_level': 'Calibrated'
                }
                }

            raw2cal_Dictionaryscience(time, eng_data, xmlschema,xmlschema_edited, config)

            expected_filename = config["Mission_Information"]["filename"]

            if os.path.isfile(xmlschema_edited):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata saved successfully in: {xmlschema_edited}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata generation failed — expected file '{xmlschema_edited}' not found."
                )

        if product_type == 'hk':

            Flyby_target = structures_par.label.findall('.//Target_Identification/name') 
            Flyby_target=Flyby_target[0].text


            eng_data = {key: eng[key]['data'] for key in eng.keys()}
            time = eng['TIME_UTC']['data']



            lid = structures_par.label.findall('.//Identification_Area/logical_identifier')
            mfn = structures_par.label.findall('.//psa:mission_phase_name')
            mfi = structures_par.label.findall('.//psa:mission_phase_identifier')
            type = structures_par.label.findall('.//Target_Identification/type')
            fn = structures_par.label.findall('.//file_name')
            l = structures_par.label.findall('.//file_size') 

            #folder_name = 'src/outputs'
            file_name = fn[0].text
            file_name = file_name.replace('.csv', '')
            file_name = file_name.replace('raw', 'cal')

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)


            v_id = extract_version_id(version_summary_path)
            # Split version_id in `i` e `j`
            version_parts = v_id.split(".")
            if len(version_parts) != 2:
                raise ValueError(f"Version ID {v_id} non è nel formato corretto i.j")

            i, j = version_parts
            xmlschema_edited = folder_name+f"{file_name}__{i}_{j}.lblx"
            file_name = f"{file_name}__{i}_{j}.csv"  # Aggiungi il suffisso

            # Combine the folder path and file name
            file_path_dic = os.path.join(folder_name, file_name)

            csvwriter(eng_data,file_name,folder_name)

            if os.path.isfile(folder_name + file_name):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of CSV file",
                    exec_id,
                    f"CSV saved successfully with name: {file_path_dic}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of CSV file",
                    exec_id,
                    f"Error in saving CSV with name: {file_path_dic}"
                )

            csv_checksum = compute_checksum(folder_name+file_name)                        

            # Combine the folder path and file name
            file_path_dic = os.path.join(folder_name, file_name)

            namecsv = file_path_dic 


            if os.path.exists(str(file_path_dic)+'.npz'):
                # Delete the file
                os.remove(str(file_path_dic)+'.npz')

            #if os.path.exists(file_path):
                # Delete the file
            #    os.remove(file_path)
            
            
            SUNmin_dist, SUNmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", "SUN")
            Targetmin_dist, Targetmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", Flyby_target)
            Earthmin_dist, Earthmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", "Earth")


            config = {
                'input_folder': '',
                'output_folder': '',
                'dynamic': dyn,                                                
                'Mission_Information': {
                    'mission_phase_identifier': mfi[0].text,
                    'mission_phase_name': mfn[0].text,
                    'lid': lid[0].text,
                    'filename': os.path.splitext(fn[0].text)[0].replace('raw', 'cal'),
                    'filesize':l[0].text,
                    'filename_csv' : file_name
                },
                'Target_Identification': {
                    'name': Flyby_target,
                    'type': type[0].text,
                    'lid_reference': 'urn:nasa:pds:context:target:'+type[0].text.lower()+'.'+Flyby_target.lower()
                },
                'Modification_detail': {
                    'version_id': str(v_id),                     
                },
                'File_Area_Observational': {
                    'file_size': get_file_size(namecsv),
                    'records': get_file_records(namecsv),
                    'checksum': str(csv_checksum),
                },
                'Processing_Input_Identification': {
                     'file_name': kernel_name,
                },
                'Distances_Min_Max': {
                    'minimum_spacecraft_heliocentric_distance': SUNmin_dist,
                    'maximum_spacecraft_heliocentric_distance': SUNmax_dist,
                    'minimum_spacecraft_target_center_distance': Targetmin_dist,
                    'maximum_spacecraft_target_center_distance': Targetmax_dist,
                    'minimum_target_geocentric_distance': Earthmin_dist,
                    'maximum_target_geocentric_distance': Earthmax_dist,
                }
                
                }
            xmlschema = './src/xml_schema/haa_cal_hk_XXXXXXXX.lblx'
            raw2eng_DictionaryHK(time, eng_data, xmlschema,xmlschema_edited, config)

            if os.path.isfile(xmlschema_edited):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata saved successfully in: {xmlschema_edited}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata generation failed — expected file '{xmlschema_edited}' not found."
                )

###################### add of calibrated highrate data (TBC) ########################
        if product_type == 'sc_hr':

            Flyby_target = structures_par.label.findall('.//Target_Identification/name') 
            Flyby_target=Flyby_target[0].text


            eng_data = {key: eng[key]['data'] for key in eng.keys()}
            time = eng['TIME_UTC']['data']
            
            print(eng.keys())

            lid = structures_par.label.findall('.//Identification_Area/logical_identifier')
            mfn = structures_par.label.findall('.//psa:mission_phase_name')
            mfi = structures_par.label.findall('.//psa:mission_phase_identifier')
            type = structures_par.label.findall('.//Target_Identification/type')
            fn = structures_par.label.findall('.//file_name')
            l = structures_par.label.findall('.//file_size') 

            #folder_name = 'src/outputs'
            file_name = fn[0].text
            file_name = file_name.replace('.csv', '')
            file_name = file_name.replace('raw', 'cal')

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)


            v_id = extract_version_id(version_summary_path)
            # Split version_id in `i` e `j`
            version_parts = v_id.split(".")
            if len(version_parts) != 2:
                raise ValueError(f"Version ID {v_id} non è nel formato corretto i.j")

            i, j = version_parts
            xmlschema_edited = folder_name+f"{file_name}__{i}_{j}.lblx"
            file_name = f"{file_name}__{i}_{j}.csv"  # Aggiungi il suffisso

            # Combine the folder path and file name
            file_path_dic = os.path.join(folder_name, file_name)

            csvwriter(eng_data,file_name,folder_name)

            if os.path.isfile(folder_name + file_name):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of CSV file",
                    exec_id,
                    f"CSV saved successfully with name: {file_path_dic}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of CSV file",
                    exec_id,
                    f"Error in saving CSV with name: {file_path_dic}"
                )

            csv_checksum = compute_checksum(folder_name+file_name)                        

            # Combine the folder path and file name
            file_path_dic = os.path.join(folder_name, file_name)

            namecsv = file_path_dic 


            if os.path.exists(str(file_path_dic)+'.npz'):
                # Delete the file
                os.remove(str(file_path_dic)+'.npz')

            #if os.path.exists(file_path):
                # Delete the file
            #    os.remove(file_path)
            
            
            SUNmin_dist, SUNmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", "SUN")
            Targetmin_dist, Targetmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", Flyby_target)
            Earthmin_dist, Earthmax_dist = compute_spacecraft_target_distances(str(time[0]), str(time[-1]), "JUICE", "Earth")


            config = {
                'input_folder': '',
                'output_folder': '',
                'dynamic': dyn,                                                
                'Mission_Information': {
                    'mission_phase_identifier': mfi[0].text,
                    'mission_phase_name': mfn[0].text,
                    'lid': lid[0].text,
                    'filename': os.path.splitext(fn[0].text)[0].replace('raw', 'cal'),
                    'filesize':l[0].text,
                    'filename_csv' : file_name
                },
                'Target_Identification': {
                    'name': Flyby_target,
                    'type': type[0].text,
                    'lid_reference': 'urn:nasa:pds:context:target:'+type[0].text.lower()+'.'+Flyby_target.lower()
                },
                'Modification_detail': {
                    'version_id': str(v_id),                     
                },
                'File_Area_Observational': {
                    'file_size': get_file_size(namecsv),
                    'records': get_file_records(namecsv),
                    'checksum': str(csv_checksum),
                },
                'Processing_Input_Identification': {
                    'file_name': kernel_name,
                },
                'Distances_Min_Max': {
                    'minimum_spacecraft_heliocentric_distance': SUNmin_dist,
                    'maximum_spacecraft_heliocentric_distance': SUNmax_dist,
                    'minimum_spacecraft_target_center_distance': Targetmin_dist,
                    'maximum_spacecraft_target_center_distance': Targetmax_dist,
                    'minimum_target_geocentric_distance': Earthmin_dist,
                    'maximum_target_geocentric_distance': Earthmax_dist,
                }
                
                }
            xmlschema = './src/xml_schema/haa_cal_sc_highrate_XXXXXXXX.lblx'
            raw2cal_DictionaryscienceHR(time, eng_data, xmlschema,xmlschema_edited, config)

            if os.path.isfile(xmlschema_edited):
                write_log(
                    log_file_path,
                    "INFO",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata saved successfully in: {xmlschema_edited}"
                )
            else:
                write_log(
                    log_file_path,
                    "ERROR",
                    origin,
                    "Creation of metadata file",
                    exec_id,
                    f"Metadata generation failed — expected file '{xmlschema_edited}' not found."
                )
