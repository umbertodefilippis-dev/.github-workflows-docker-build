import os
import numpy as np
from datetime import datetime
import spiceypy as spice
import pds4_tools

def raw2eng_DictionaryHK(t,hk_raw, config):
    os.environ['timeUTCformat'] = '%Y-%m-%dT%H:%M:%S.%fZ'
    os.environ['sw_title'] = 'HAA_CAL_ROUTINE'
    os.environ['sw_ver'] = '0.0.1'
    time_utc_format = os.getenv('timeUTCformat')
    DS = os.getenv('DS')
    current_datetime = datetime.utcnow()
    formatted_datetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    count = 1
    hk_eng = []

    # Populate hk_eng with ACC_JUICE_X, ACC_JUICE_Y, ACC_JUICE_Z, TIME_UTC, TIME_OBT data
    hk_eng = {'field': [{}]}

    # Assign values to the structure
    hk_eng['field'][count - 1]['TIME_UTC']  = {'data': np.char.mod('%s', np.asarray(t))}
    hk_eng['field'][count - 1]['TIME_OBT'] = {'data': [spice.sce2s(spice.bodn2c('JUICE'), spice.str2et(str(time))) for time in hk_eng['field'][count-1]['TIME_UTC']['data']]}
    hk_eng['field'][count - 1]['MODE'] = {'data': hk_raw['MODE']}
    hk_eng['field'][count - 1]['LOW_RATE'] = {'data': hk_raw['LOW_RATE']}
    hk_eng['field'][count - 1]['PRIM_CURR'] = {'data': hk_raw['PRIM_CURR']}
    hk_eng['field'][count - 1]['TEMP_FEE'] = {'data': hk_raw['TEMP_FEE']}
    hk_eng['field'][count - 1]['TEMP_IDA_FEE_HOTSPOT'] = {'data': hk_raw['TEMP_IDA_FEE_HOTSPOT']}
    hk_eng['field'][count - 1]['TEMP_IDA_FEE_DIGITAL'] = {'data': hk_raw['TEMP_IDA_FEE_DIGITAL']}
    hk_eng['field'][count - 1]['TEMP_IDA_BOUNDARY'] = {'data': hk_raw['TEMP_IDA_BOUNDARY']}
    hk_eng['field'][count - 1]['TEMP_ACC_0'] = {'data': hk_raw['TEMP_ACC_0']}
    hk_eng['field'][count - 1]['TEMP_ACC_1'] = {'data': hk_raw['TEMP_ACC_1']}
    hk_eng['field'][count - 1]['TEMP_ACC_2'] = {'data': hk_raw['TEMP_ACC_2']}
    hk_eng['field'][count - 1]['PWR_TEMP'] = {'data': hk_raw['PWR_TEMP']}
    hk_eng['field'][count - 1]['DELTA_TEMP_FEE'] = {'data': hk_raw['DELTA_TEMP_FEE']}
    hk_eng['field'][count - 1]['DELTA_TEMP_ACC_0'] = {'data': hk_raw['DELTA_TEMP_ACC_0']}
    hk_eng['field'][count - 1]['DELTA_TEMP_ACC_1'] = {'data': hk_raw['DELTA_TEMP_ACC_1']}
    hk_eng['field'][count - 1]['DELTA_TEMP_ACC_2'] = {'data': hk_raw['DELTA_TEMP_ACC_2']}
    hk_eng['field'][count - 1]['HEAT_STAT_FEE'] = {'data': hk_raw['HEAT_STAT_FEE']}
    hk_eng['field'][count - 1]['HEAT_STAT_ACC0'] = {'data': hk_raw['HEAT_STAT_ACC0']}
    hk_eng['field'][count - 1]['HEAT_STAT_ACC1'] = {'data': hk_raw['HEAT_STAT_ACC1']}
    hk_eng['field'][count - 1]['HEAT_STAT_ACC2'] = {'data': hk_raw['HEAT_STAT_ACC2']}
    hk_eng['field'][count - 1]['HEAT_CURR_FEE'] = {'data': hk_raw['HEAT_CURR_FEE']}
    hk_eng['field'][count - 1]['HEAT_CURR_ACC0'] = {'data': hk_raw['HEAT_CURR_ACC0']}
    hk_eng['field'][count - 1]['HEAT_CURR_ACC1'] = {'data': hk_raw['HEAT_CURR_ACC1']}
    hk_eng['field'][count - 1]['HEAT_CURR_ACC2'] = {'data': hk_raw['HEAT_CURR_ACC2']}
    hk_eng['field'][count - 1]['TEMP_REACH_ACC0'] = {'data': hk_raw['TEMP_REACH_ACC0']}
    hk_eng['field'][count - 1]['TEMP_REACH_ACC1'] = {'data': hk_raw['TEMP_REACH_ACC1']}
    hk_eng['field'][count - 1]['TEMP_REACH_ACC2'] = {'data': hk_raw['TEMP_REACH_ACC2']}
    hk_eng['field'][count - 1]['TR_FEE'] = {'data': hk_raw['TR_FEE']}
    hk_eng['field'][count - 1]['ICE_140V'] = {'data': hk_raw['ICE_140V']} 
    hk_eng['field'][count - 1]['ICE_3V'] = {'data': hk_raw['ICE_3V']}
    
    # Set file start and stop times
    hk_eng['fileStartTime'] = [str(t[0])]
    hk_eng['fileStopTime'] = [str(t[-1])]
    hk_eng['fileNum'] = count
    hk_eng['fileName'] = config['Mission_Information']['filename']
    hk_eng['file_size'] = config['Mission_Information']['filesize']
    hk_eng['records'] =  len(hk_raw['TIME_OBT'])

    
    # Construct lid
    lid_date = datetime.strptime(str(t[0]), time_utc_format).strftime('%Y%m%d')
    hk_eng['lid'] = config['Mission_Information']['filename'].replace('raw', 'cal')

    # Get geometric and generic info for PDS4
    Target_Identification = {
        'name': {'Text': config['Target_Identification']['name']},
        'type': {'Text': config['Target_Identification']['type']},
        'Internal_Reference': {
            'lid_reference': {'Text': config['Target_Identification']['lid_reference']},
            'reference_type': {'Text': 'data_to_target'}
        }
    }

    prod_target = config['Target_Identification']['name']
    

    psa_colon_Mission_Information = {
        'psa_colon_mission_phase_identifier': {'Text': config['Mission_Information']['mission_phase_identifier']},
        'psa_colon_spacecraft_clock_start_count': hk_eng['field'][count - 1]['TIME_OBT']['data'][0],
        'psa_colon_spacecraft_clock_stop_count': hk_eng['field'][count - 1]['TIME_OBT']['data'][-1],
        'psa_colon_mission_phase_name': {'Text': config['Mission_Information']['mission_phase_name']},
        'psa_colon_start_orbit_number': {'Text': '0'},
        'psa_colon_stop_orbit_number': {'Text': '0'}
    }

    Citation_Information = {
        "author_list": "TBD",
        "publication_year": "2024",
        "keyword": "Accelerometer",
        "description": "This product reports HAA housekeeping (packet 3,25) converted in engineering units."
    }
    Modification_History =  {
            'Modification_Detail': {
                'modification_date': '',
                'version_id': '0.1',
                'description': ''
        }
    }

    Time_Coordinates = {
        "start_date_time": hk_eng['fileStartTime'],
        "stop_date_time": hk_eng['fileStopTime']
    }
    Primary_Result_Summary= {
        "purpose": "Science",
        "processing_level": "Eng",
        "Science_Facets": {
            "wavelength_range": {"nilReason": "inapplicable", "nil": "true"},
            "discipline_name": "Radio Science"
        }
    }
    Investigation_Area= {
        "name": "JUICE",
        "type": "Mission",
        "Internal_Reference": {
            "lid_reference": "urn:esa:psa:context:investigation:mission.juice",
            "reference_type": "data_to_investigation"
        }
    }
    Observing_System = {
    "name": "JUICE HAA",
    'Observing_System_Component': [
        {
            "name": "JUICE",
            "type": "Host",
            "Internal_Reference": {
                "lid_reference": "urn:esa:psa:context:instrument_host:spacecraft.juice",
                "reference_type": "is_instrument_host"
            }
        },
        {
            "name": "HAA",
            "type": "Instrument",
            "description": "High Accuracy Accelerometer",
            "Internal_Reference": {
                "lid_reference": "urn:esa:psa:context:instrument:juice.haa",
                "reference_type": "is_instrument"
            }
        }
    ]
}
    
    Target_Identification= {
        'name': config['Target_Identification']['name'],
        'type': config['Target_Identification']['type'],
        'Internal_Reference': {
            'lid_reference': {config['Target_Identification']['lid_reference']},
            'reference_type': {'data_to_target'}
        }
    }
    Mission_Area= {
        'psa_Mission_Observation_Arearmation': {
            'psa_spacecraft_clock_start_count': hk_eng['field'][count-1]['TIME_UTC']['data'][0],
            'psa_spacecraft_clock_stop_count': hk_eng['field'][count-1]['TIME_UTC']['data'][-1],
            'psa_mission_phase_name': config['Mission_Information']['mission_phase_name'],
            'psa_mission_phase_identifier': config['Mission_Information']['mission_phase_identifier'],
            'psa_start_orbit_number': "",
            'psa_stop_orbit_number': ""
        },
        'Processing_Context': {
            'psa_processing_software_title': "raw2eng-haa",
            'psa_processing_software_version': "0.0.1",
            'psa_Processing_Inputs': {
                'psa_Processing_Input_Identification': {
                    'psa_type': "SPICE kernel",
                    'psa_file_name': config['Mission_Information']['filename'].replace('raw', 'eng')
                }
            }
        }
    }



    observation_file_area = {
            'File': {
                'file_name': config['Mission_Information']['filename'].replace('raw', 'eng')+'.csv',
                'creation_date_time': formatted_datetime,
                 'file_size': {
                    '_unit': 'byte',
                    '_text': hk_eng['file_size']
                        },
                'records': hk_eng['records'],
                'md5_checksum': ''
            },
            'Table_Delimited': {
                'name': 'HAA ENG HK DATA TABLE',
                'offset': {
                            '_unit': 'byte',
                            '_text': '0'
                          },
                'parsing_standard_id': 'PDS DSV 1',
                'records': hk_eng['records'],
                'record_delimiter': 'Carriage-Return Line-Feed',
                'field_delimiter': 'Comma',
                'Record_Delimited': {
                    'fields': '30',
                    'groups': '0',
                    'Field_Delimited': [
                        {
                            'name': 'TIME_UTC',
                            'field_number': '1',
                            'data_type': 'ASCII_Date_Time_YMD_UTC',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '24'
                            },
                            'description': 'UTC TIME OF OBSERVATION: YYYY-MM-DDTHH:MM:SS.SSSZ'
                        },
                        {
                            'name': 'TIME_OBT',
                            'field_number': '2',
                            'data_type': 'ASCII_String',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '18'
                            },
                            'description': 'S/C CLOCK AT OBSERVATION TIME: P/SSSSSSSSSS:FFFFF'
                        },
                        {
                            'name': 'MODE',
                            'field_number': '3',
                            'data_type': 'ASCII_String',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '4'
                            },
                            'description':'HAA operative mode code'
                        },
                        {
                            'name': 'LOW_RATE',
                            'field_number': '4',
                            'data_type': 'ASCII_String',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Science report rate flag [low rate,nominal rate]'
                        },
                        {
                            'name': 'PRIM_CURR',
                            'field_number': '5',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'A',
                            'description': 'ACU Monitor primary current - Eng value'
                        },
                        {
                            'name': 'TEMP_FEE',
                            'field_number': '6',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'ACU_FEE actual Temperature, read from sensor selected for thermal control- Eng value'
                        },
                        {
                            'name': 'TEMP_IDA_FEE_HOTSPOT',
                            'field_number': '7',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '6'
                            },
                            'unit' : 'C',
                            'description': 'IDA FEE Hotspot Temperature - Eng value'
                        },
                        {
                            'name': 'TEMP_IDA_FEE_DIGITAL',
                            'field_number': '8',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '6'
                            },
                            'unit' : 'C',
                            'description': 'IDA FEE Digital Temperature - Eng value'
                        },
                        {
                            'name': 'TEMP_IDA_BOUNDARY',
                            'field_number': '9',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '6'
                            },
                            'unit' : 'C',
                            'description': 'IDA boundary Temperature - Eng value'
                        },
                        {
                            'name': 'TEMP_ACC_0',
                            'field_number': '10',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'Acc. 0 actual Temperature - Eng value'
                        },
                        {
                            'name': 'TEMP_ACC_1',
                            'field_number': '11',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'Acc. 1 actual Temperature - Eng value'
                        },
                        {
                            'name': 'PWR_TEMP',
                            'field_number': '12',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'ACU_Temp1 - Pwr temperature - Eng value'
                        },
                        {
                            'name': 'DELTA_TEMP_FEE',
                            'field_number': '13',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'ADA_FEE Delta Temperature - Eng value'
                        },
                        {
                            'name': 'DELTA_TEMP_ACC_0',
                            'field_number': '14',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'Acc. 0 Delta Temperature - Eng value'
                        },
                        {
                            'name': 'DELTA_TEMP_ACC_1',
                            'field_number': '15',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'Acc. 1 Delta Temperature - Eng value'
                        },
                        {
                            'name': 'DELTA_TEMP_ACC_2',
                            'field_number': '16',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'unit' : 'C',
                            'description': 'Acc. 2 Delta Temperature - Eng value'
                        },
                        {
                            'name': 'HEAT_STAT_FEE',
                            'field_number': '17',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'ADA_FEE thermal control status [1=Thermal Control running, 0=stopped] '
                        },
                        {
                            'name': 'HEAT_STAT_ACC0',
                            'field_number': '18',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Acc. 0 thermal control status [1=Thermal Control running, 0=stopped] '
                        },
                        {
                            'name': 'HEAT_STAT_ACC1',
                            'field_number': '19',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Acc. 1 thermal control status [1=Thermal Control running, 0=stopped] '
                        },
                        {
                            'name': 'HEAT_STAT_ACC2',
                            'field_number': '20',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Acc. 2 thermal control status [1=Thermal Control running, 0=stopped] '
                        },
                        {
                            'name': 'HEAT_CURR_FEE',
                            'field_number': '21',
                            'data_type': 'FLOAT',
                            'unit' : 'A',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'description': 'ACU_FEE Heater Current Output - Eng value'
                        },
                        {
                            'name': 'HEAT_CURR_ACC0',
                            'field_number': '22',
                            'data_type': 'FLOAT',
                            'unit' : 'A',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'description': 'Acc.0 Heater Current Output - Eng value'
                        },
                        {
                            'name': 'HEAT_CURR_ACC1',
                            'field_number': '23',
                            'data_type': 'FLOAT',
                            'unit' : 'A',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'description': 'Acc.1 Heater Current Output - Eng value'
                        },
                        {
                            'name': 'HEAT_CURR_ACC2',
                            'field_number': '24',
                            'data_type': 'FLOAT',
                            'unit' : 'A',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'description': 'Acc.2 Heater Current Output - Eng value'
                        },
                        {
                            'name': 'TEMP_REACH_ACC0',
                            'field_number': '25',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Acc. 0 Temperature reached [1=T in tolerance, 0=T out tolerance] '
                        },
                        {
                            'name': 'TEMP_REACH_ACC1',
                            'field_number': '26',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Acc. 1 Temperature reached [1=T in tolerance, 0=T out tolerance] '
                        },
                        {
                            'name': 'TEMP_REACH_ACC2',
                            'field_number': '27',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'Acc. 2 Temperature reached [1=T in tolerance, 0=T out tolerance] '
                        },
                        {
                            'name': 'TR_FEE',
                            'field_number': '28',
                            'data_type': 'FLOAT',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '1'
                            },
                            'description': 'ADA_FEE 0 Temperature reached [1=T in tolerance, 0=T out tolerance] - Eng value'
                        },
                        {
                            'name': 'ICE_140V',
                            'field_number': '29',
                            'data_type': 'FLOAT',
                            'unit' : 'V',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'description': 'ACU Monitor 50V - Eng value'
                        },
                        {
                            'name': 'ICE_3V',
                            'field_number': '30',
                            'data_type': 'FLOAT',
                            'unit' : 'V',
                            'maximum_field_length': {
                                '_unit': 'byte',
                                '_text': '5'
                            },
                            'description': 'ACU Monitor 3,3V - Eng value'
                        },
                    ]
                }
            }
    }

    hk_eng['Product_Observational'] = {}
    hk_eng['Product_Observational']['Identification_Area'] = {}
    hk_eng['Product_Observational']['Identification_Area']['logical_identifier'] = config['Mission_Information']['lid']
    hk_eng['Product_Observational']['Identification_Area']['version_id'] = '0.1'
    hk_eng['Product_Observational']['Identification_Area']['title'] = 'JUICE HAA Eng HK data' + str(hk_eng['fileStartTime'])
    hk_eng['Product_Observational']['Identification_Area']['information_model_version'] = ''
    hk_eng['Product_Observational']['Identification_Area']['product_class'] = 'Product_Observational'
    hk_eng['Product_Observational']['Identification_Area']['Citation_Information'] = Citation_Information
    hk_eng['Product_Observational']['Identification_Area']['Modification_History'] = Modification_History
    hk_eng['Product_Observational']['Observation_Area'] = {}
    hk_eng['Product_Observational']['Observation_Area']['Time_Coordinates'] = Time_Coordinates
    hk_eng['Product_Observational']['Observation_Area']['Primary_Result_Summary'] = Primary_Result_Summary
    hk_eng['Product_Observational']['Observation_Area']['Investigation_Area'] = Investigation_Area
    hk_eng['Product_Observational']['Observation_Area']['Observing_System'] = Observing_System
    hk_eng['Product_Observational']['Observation_Area']['Target_Identification'] = Target_Identification
    hk_eng['Product_Observational']['Observation_Area']['Mission_Area'] = Mission_Area
    hk_eng['Product_Observational']['Observation_Area']['Discipline_Area'] = ''
    hk_eng['Product_Observational']['File_Area_Observational'] ={}
    hk_eng['Product_Observational']['File_Area_Observational'] = observation_file_area


    return hk_eng