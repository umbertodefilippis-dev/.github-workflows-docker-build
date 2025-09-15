import lxml.etree as ET
import numpy as np
import csv
import os
import json
from datetime import datetime
import hashlib


def csvwriter(sc_eng, filename,folder_name):
    #folder_name = 'src/outputs'
    file_path = os.path.join(folder_name, filename)
    # Write data to CSV file
    csv_file_path = file_path

    # Estrarre i nomi dei campi dal dizionario
    field_names = list(sc_eng.keys())
    # Chiavi da escludere
    excluded_keys = {
        "MAX_POS_ACC_X_HAA_URF_DIRECTED",
        "MAX_POS_ACC_Y_HAA_URF_DIRECTED",
        "MAX_POS_ACC_Z_HAA_URF_DIRECTED",
        "INTERPOLATED"
    }

    # Filtra i campi inclusi
    included_keys = [key for key in field_names if key not in excluded_keys]

    # Colonne di dati da includere
    data_columns = [sc_eng[key] for key in included_keys]
    # Unire i dati per iterare riga per riga
    zipped_data = zip(*data_columns)

    # Scrivere i dati nel file CSV
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Iterare sulle righe di dati
        for row_data in zipped_data:
            formatted_row = []
            for key, value in zip(included_keys, row_data):
                if key in {"ACC_X_HAA_URF_DIRECTED", "ACC_Y_HAA_URF_DIRECTED", "ACC_Z_HAA_URF_DIRECTED",
                           "TEMP_X_HAA_URF_DIRECTED", "TEMP_Y_HAA_URF_DIRECTED", "TEMP_Z_HAA_URF_DIRECTED"}:
                    # Formattare in 22.15e
                    try:
                        formatted_row.append(f"{float(value):22.15e}")
                    except (ValueError, TypeError):
                        formatted_row.append(value)  # Se non è un numero, lascia il valore invariato
                elif key == "TIME_OBT":
                    # Formattare in -18s
                    try:
                        formatted_row.append(f"{str(value):>18s}")
                    except (ValueError, TypeError):
                        formatted_row.append(value)  # Se non è una stringa, lascia il valore invariato
                elif key == "TIME_UTC":
                    # Formattare in %24s
                    try:
                        formatted_row.append(f"{str(value):>24s}")
                    except (ValueError, TypeError):
                        formatted_row.append(value)  # Se non è una stringa, lascia il valore invariato
                else:
                    # Nessuna formattazione per altre chiavi
                    formatted_row.append(value)
            writer.writerow(formatted_row)


def process_calibration_file(calib_json_path, sc_eng, output_csv_path):
    # Estrai TIME_UTC e TIME_OBT da sc_eng
    time_utc = sc_eng.get("TIME_UTC", [""])[0]
    time_obt = sc_eng.get("TIME_OBT", [""])[0]

    # Formatta le stringhe con larghezza fissa
    time_utc_str = f"{str(time_utc):>24s}" if time_utc else ""
    time_obt_str = f"{str(time_obt):>18s}" if time_obt else ""

    # Carica il file JSON di calibrazione
    with open(calib_json_path, 'r') as f:
        calib_data = json.load(f)

    # Estrai tutti i valori dei campi 'data' mantenendo l’ordine e formattali
    flat = []
    for axis_key, axis_data in calib_data.items():
        for subkey, subdata in axis_data.items():
            if isinstance(subdata, dict) and 'data' in subdata:
                value = subdata['data']
                if isinstance(value, (int, float)):
                    flat.append(f"{value:+14.7e}")
                else:
                    flat.append(str(value))
            elif isinstance(subdata, dict):
                for poly_key, poly_val in subdata.items():
                    if isinstance(poly_val, dict) and 'data' in poly_val:
                        value = poly_val['data']
                        if isinstance(value, (int, float)):
                            flat.append(f"{value:+14.7e}")
                        else:
                            flat.append(str(value))

    # Riga con TIME_UTC, TIME_OBT e tutti i valori
    row = [time_utc_str, time_obt_str] + flat

    # Scrittura CSV (solo una riga di valori)
    with open(output_csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

    # Calcolo metadati
    size = os.path.getsize(output_csv_path)
    creation = datetime.now().isoformat()
    with open(output_csv_path, 'rb') as f:
        checksum = hashlib.md5(f.read()).hexdigest()

    return creation, size, checksum