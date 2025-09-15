import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import spiceypy as spice
import numpy as np


def calibration_Dictionary(t,schema_path, output_path, config):
    os.environ['timeUTCformat'] = '%Y-%m-%dT%H:%M:%S.%fZ'
    os.environ['sw_title'] = 'HAA_CAL_ROUTINE'
    os.environ['sw_ver'] = '0.0.1'
    time_utc_format = os.getenv('timeUTCformat')
    DS = os.getenv('DS')
    current_datetime = datetime.utcnow()
    formatted_datetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    count = 1
    hk_cal = []
    hk_cal = {'field': [{}]}
    
    hk_cal['fileStartTime'] = str(t[0])
    hk_cal['fileStopTime'] = str(t[-1])

    def fill_xml_with_computed_values(schema_path, output_path, hk_cal, config):
        # Construct lid
        lid_date = datetime.strptime(str(t[0]), time_utc_format).strftime('%Y%m%d')
        hk_cal['lid'] = 'urn:esa:psa:juice_haa:calibration_files:' + config['Mission_Information']['filename']
        # Parse the XML file
        tree = ET.parse(schema_path)
        root = tree.getroot()

        # Define namespaces
        namespaces = {
            'pds': "http://pds.nasa.gov/pds4/pds/v1",
            'geom': "http://pds.nasa.gov/pds4/geom/v1",
            'juice': "http://psa.esa.int/psa/juice/v1",
            'psa': "http://psa.esa.int/psa/v1"
        }

        # Register namespaces
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        # Update Identification_Area
        identification_area = root.find(".//pds:Identification_Area", namespaces)
        if identification_area is None:
            raise ValueError("Could not find Identification_Area in the XML schema.")

        identification_area.find(".//pds:logical_identifier", namespaces).text = hk_cal['lid']
        identification_area.find(".//pds:version_id", namespaces).text = "0.1"
        identification_area.find(".//pds:title", namespaces).text = config['Mission_Information']['filename']
        identification_area.find(".//pds:information_model_version", namespaces).text = "1.19.0.0"

        # Update Citation_Information
        cit_info = identification_area.find(".//pds:Citation_Information", namespaces)
        cit_info.find(".//pds:author_list", namespaces).text = "U. De Filippis"
        cit_info.find(".//pds:publication_year", namespaces).text = datetime.utcnow().strftime('%Y')

        # Update Modification_History
        mod_detail = identification_area.find(".//pds:Modification_Detail", namespaces)
        mod_detail.find(".//pds:modification_date", namespaces).text = datetime.utcnow().strftime('%Y-%m-%d')
        mod_detail.find(".//pds:version_id", namespaces).text = config['Modification_detail']['version_id']
        mod_detail.find(".//pds:description", namespaces).text = "Draft version"

        # Update Observation_Area
        context_area = root.find(".//pds:Context_Area", namespaces)

        # Update Time_Coordinates
        time_coords = context_area.find(".//pds:Time_Coordinates", namespaces)
        time_coords.find(".//pds:start_date_time", namespaces).text = hk_cal['fileStartTime']
        time_coords.find(".//pds:stop_date_time", namespaces).text = hk_cal['fileStopTime']

        # Update Target_Identification
        target_identification = context_area.find(".//pds:Target_Identification", namespaces)
        target_identification.find(".//pds:name", namespaces).text = config['Target_Identification']['name']
        target_identification.find(".//pds:type", namespaces).text = config['Target_Identification']['type']
        target_identification.find(".//pds:lid_reference", namespaces).text = config['Target_Identification']['lid_reference']

        # Update Mission_Area
        mission_area = context_area.find(".//pds:Mission_Area", namespaces)
        #mission_info = mission_area.find(".//psa:Mission_Information", namespaces)
        #mission_info.find(".//psa:spacecraft_clock_start_count", namespaces).text = hk_cal['field'][0]['TIME_OBT']['data'][0]
        #mission_info.find(".//psa:spacecraft_clock_stop_count", namespaces).text = hk_cal['field'][0]['TIME_OBT']['data'][-1]
        #mission_info.find(".//psa:mission_phase_name", namespaces).text = config['Mission_Information']['mission_phase_name']
        #mission_info.find(".//psa:mission_phase_identifier", namespaces).text = config['Mission_Information']['mission_phase_identifier']
        #mission_info.find(".//psa:stop_orbit_number", namespaces).text = '0'
        ##mission_info.find(".//psa:start_orbit_number", namespaces).text = '0'

        proc_cont = mission_area.find(".//psa:Processing_Context", namespaces)
        proc_cont.find(".//psa:processing_software_version", namespaces).text = '0.0.1'     #TBD: inserst the actual software version
        #proc_inp = proc_cont.find(".//psa:Processing_Inputs", namespaces)
        #proc_inp_id = proc_inp.find(".//psa:Processing_Input_Identification", namespaces)
        #proc_inp_id.find(".//psa:file_name", namespaces).text =  config['Processing_Input_Identification']['file_name']


        # Update File_Area_Observational
        file_area = root.find(".//pds:File_Area_Ancillary", namespaces)
        file_element = file_area.find(".//pds:File", namespaces)
        file_element.find(".//pds:file_name", namespaces).text = config['Mission_Information']['filename_csv']
        file_element.find(".//pds:creation_date_time", namespaces).text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        file_element.find(".//pds:file_size", namespaces).text = config['File_Area_Ancillary']['file_size']
        file_element.find(".//pds:records", namespaces).text = config['File_Area_Ancillary']['records']
        # Generate checksum
        file_element.find(".//pds:md5_checksum", namespaces).text = config['File_Area_Ancillary']['checksum']

        for elem in root.iter():
            if elem.tag.startswith(f"{{{namespaces['pds']}}}"):
                elem.tag = elem.tag.split('}', 1)[1]  # Rimuove il prefisso `pds:`

        # Aggiorna il namespace predefinito nel tag radice
        root.attrib["xmlns"] = namespaces["pds"]
        if "xmlns:pds" in root.attrib:
            del root.attrib["xmlns:pds"]

        # Convert the updated XML tree to a string and pretty format it
        xml_string = ET.tostring(root, encoding="UTF-8",xml_declaration=False)
        formatted_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
        # Rimuovi la dichiarazione XML aggiunta da minidom
        formatted_xml = "\n".join(formatted_xml.splitlines()[1:])

        # Add Schematron declarations
        schematron_declarations = """<?xml version="1.0" ?>
<?xml-model href="https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1J00.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="https://pds.nasa.gov/pds4/geom/v1/PDS4_GEOM_1J00_1980.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="https://psa.esa.int/psa/v1/PDS4_PSA_1J00_1401.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<?xml-model href="https://psa.esa.int/psa/juice/v1/PDS4_JUICE_1J00_1003.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>"""

        # Combine Schematron declarations with the formatted XML
        final_xml =  schematron_declarations + "\n" + formatted_xml 


        # Write the final XML to the output file
        with open(output_path, "w") as output_file:
            output_file.write(final_xml)

    
    fill_xml_with_computed_values(schema_path, output_path, hk_cal,config)