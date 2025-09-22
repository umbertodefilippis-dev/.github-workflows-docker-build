import os
import numpy as np
from datetime import datetime
import spiceypy as spice
import xml.etree.ElementTree as ET
from xml.dom import minidom
import hashlib

def raw2eng_Dictionaryscience(t, eng_data, schema_path, output_path, config):
    os.environ['timeUTCformat'] = '%Y-%m-%dT%H:%M:%S.%fZ'
    os.environ['sw_title'] = 'HAA_CAL_ROUTINE'
    os.environ['sw_ver'] = '0.0.1'
    time_utc_format = os.getenv('timeUTCformat')
    DS = os.getenv('DS')
    current_datetime = datetime.utcnow()
    formatted_datetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    count = 1
    sc_eng = []

    # Populate sc_eng with ACC_JUICE_X, ACC_JUICE_Y, ACC_JUICE_Z, TIME_UTC, TIME_OBT data
    sc_eng = {'field': [{}]}

    # Assign values to the structure
    sc_eng['field'][count - 1]['TIME_UTC'] = {'data': np.char.mod('%s', np.asarray(t))}
    sc_eng['field'][count - 1]['TIME_OBT'] = {'data': [spice.sce2s(spice.bodn2c('JUICE'), spice.str2et(str(time))) for time in sc_eng['field'][count-1]['TIME_UTC']['data']]}
    sc_eng['field'][count - 1]['ACC_JUICE_X'] = {'data': eng_data['ACC_X_HAA_URF_DIRECTED']}
    sc_eng['field'][count - 1]['ACC_JUICE_Y'] = {'data': eng_data['ACC_Y_HAA_URF_DIRECTED']}
    sc_eng['field'][count - 1]['ACC_JUICE_Z'] = {'data': eng_data['ACC_Z_HAA_URF_DIRECTED']}
    sc_eng['field'][count - 1]['ACC_TEMP_X'] = {'data': eng_data['TEMP_X_HAA_URF_DIRECTED']}
    sc_eng['field'][count - 1]['ACC_TEMP_Y'] = {'data': eng_data['TEMP_Y_HAA_URF_DIRECTED']}
    sc_eng['field'][count - 1]['ACC_TEMP_Z'] = {'data': eng_data['TEMP_Z_HAA_URF_DIRECTED']}

    # Set file start and stop times
    sc_eng['fileStartTime'] = [str(t[0])]
    sc_eng['fileStopTime'] = [str(t[-1])]
    sc_eng['fileNum'] = count
    sc_eng['fileName'] = config['Mission_Information']['filename']
    sc_eng['file_size'] = config['Mission_Information']['filesize']
    sc_eng['records'] = len(eng_data['ACC_X_HAA_URF_DIRECTED'])

    # Construct lid
    lid_date = datetime.strptime(str(t[0]), time_utc_format).strftime('%Y%m%d')
    sc_eng['lid'] = 'urn:esa:psa:juice_haa:data_partially_processed:' + config['Mission_Information']['filename']

    # Get geometric and generic Observation_Area for PDS4
    Target_Identification = {
        'name': config['Target_Identification']['name'],
        'type': config['Target_Identification']['type'],
        'Internal_Reference': {
            'lid_reference': config['Target_Identification']['lid_reference'],
            'reference_type': 'data_to_target'
        }
    }

    prod_target = config['Target_Identification']['name']

    ets = spice.str2et([str(t[0]), str(t[-1])])
    et = np.linspace(ets[0], ets[1], len(t))
    JUICE_EARTH_J2000 = spice.spkpos('JUICE', et, 'ECLIPJ2000', 'LT', 'EARTH')[0]
    JUICE_SUN_J2000 = spice.spkpos('JUICE', et, 'ECLIPJ2000', 'NONE', 'SUN')[0]
    JUICE_TARGET_J2000 = spice.spkpos('JUICE', et, 'ECLIPJ2000', 'NONE', prod_target)[0]

    def fill_xml_with_computed_values(schema_path, output_path, sc_eng, config):
        def remove_default_namespace(tree, default_namespace):
            for elem in tree.iter():
                if elem.tag.startswith(f"{{{default_namespace}}}"):
                    elem.tag = elem.tag.split('}', 1)[1]  # Rimuove il namespace predefinito
            return tree
                # Parse the XML schema
        tree = ET.parse(schema_path)
        root = tree.getroot()
        # Define namespaces
        namespaces = {
            'pds': "http://pds.nasa.gov/pds4/pds/v1",
            'geom': "http://pds.nasa.gov/pds4/geom/v1",
            'juice': "http://psa.esa.int/psa/juice/v1",
            'psa': "http://psa.esa.int/psa/v1"
        }
        

        # Register namespaces (for writing the XML back later)
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)
        
        # Fill Identification_Area
        identification_area = root.find(".//pds:Identification_Area", namespaces)
        if identification_area is None:
            raise ValueError("Could not find Identification_Area in the XML schema.")

        identification_area.find(".//pds:logical_identifier", namespaces).text = sc_eng['lid']
        identification_area.find(".//pds:version_id", namespaces).text = "0.1"
        identification_area.find(".//pds:title", namespaces).text = config['Mission_Information']['filename']
        identification_area.find(".//pds:information_model_version", namespaces).text = "1.19.0.0"
        cit_info = identification_area.find(".//pds:Citation_Information", namespaces)
        cit_info.find(".//pds:author_list", namespaces).text = "U. De Filippis"
        cit_info.find(".//pds:publication_year", namespaces).text = datetime.utcnow().strftime('%Y')
        cit_info.find(".//pds:description", namespaces).text = "Partially processed science product. Records the acceleration and temperature of each accelerometer with engineering units."

        # TBD: Fill Modification_Detail and insert previous versions with related modification details

        mod_detail = identification_area.find(".//pds:Modification_Detail", namespaces)
        mod_detail.find(".//pds:modification_date", namespaces).text = datetime.utcnow().strftime('%Y-%m-%d')
        mod_detail.find(".//pds:version_id", namespaces).text = config['Modification_detail']['version_id']
        mod_detail.find(".//pds:description", namespaces).text = "Draft version"

        # Fill Observation_Area
        observation_area = root.find(".//pds:Observation_Area", namespaces)

        # Time Coordinates
        time_coords = observation_area.find(".//pds:Time_Coordinates", namespaces)
        time_coords.find(".//pds:start_date_time", namespaces).text = sc_eng['fileStartTime'][0]
        time_coords.find(".//pds:stop_date_time", namespaces).text = sc_eng['fileStopTime'][0]
        prim_res = observation_area.find(".//pds:Primary_Result_Summary", namespaces)
        prim_res.find(".//pds:processing_level", namespaces).text = config['Primary_Result_Summary']['processing_level']

        # Target_Identification
        target_identification = observation_area.find(".//pds:Target_Identification", namespaces)
        target_identification.find(".//pds:name", namespaces).text = config['Target_Identification']['name']
        target_identification.find(".//pds:type", namespaces).text = config['Target_Identification']['type']
        target_identification.find(".//pds:lid_reference", namespaces).text = config['Target_Identification']['lid_reference']

        # Mission_Area
        mission_area = observation_area.find(".//pds:Mission_Area", namespaces)
        mission_info = mission_area.find(".//psa:Mission_Information", namespaces)
        mission_info.find(".//psa:spacecraft_clock_start_count", namespaces).text = sc_eng['field'][0]['TIME_OBT']['data'][0]
        mission_info.find(".//psa:spacecraft_clock_stop_count", namespaces).text = sc_eng['field'][0]['TIME_OBT']['data'][-1]
        mission_info.find(".//psa:mission_phase_name", namespaces).text = config['Mission_Information']['mission_phase_name']
        mission_info.find(".//psa:mission_phase_identifier", namespaces).text = config['Mission_Information']['mission_phase_identifier']
        mission_info.find(".//psa:start_orbit_number", namespaces).text = '0'     #TBD: inserst the actual orbit number
        mission_info.find(".//psa:stop_orbit_number", namespaces).text = '0'      #TBD: inserst the actual orbit number
        Processing_Context = observation_area.find(".//psa:Processing_Context", namespaces)
        Processing_Context.find(".//psa:processing_software_title", namespaces).text ='raw2par-haa'

        # Geometry_Area

        geometry_area = observation_area.find(".//geom:Geometry", namespaces)
        geom_orbiter = geometry_area.find(".//geom:Geometry_Orbiter", namespaces)
        geom_orbiter.find(".//geom:geometry_reference_time_utc", namespaces).text = sc_eng['fileStartTime'][0]
        geom_orbiter_id = geom_orbiter.find(".//geom:Orbiter_Identification", namespaces)
        geom_orbiter_targ_id = geom_orbiter_id.find(".//geom:Geometry_Target_Identification", namespaces)
        geom_orbiter_targ_id.find(".//geom:body_spice_name", namespaces).text = config['Target_Identification']['name']
        geom_orbiter_dist = geom_orbiter.find(".//geom:Distances", namespaces)
        Distances_Min_Max = geom_orbiter_dist.find(".//geom:Distances_Min_Max", namespaces)
        Distances_Min_Max.find(".//geom:minimum_spacecraft_heliocentric_distance", namespaces).text = str(config['Distances_Min_Max']['minimum_spacecraft_heliocentric_distance'])
        Distances_Min_Max.find(".//geom:maximum_spacecraft_heliocentric_distance", namespaces).text = str(config['Distances_Min_Max']['maximum_spacecraft_heliocentric_distance'])
        Distances_Min_Max.find(".//geom:minimum_spacecraft_target_center_distance", namespaces).text = str(config['Distances_Min_Max']['minimum_spacecraft_target_center_distance'])
        Distances_Min_Max.find(".//geom:maximum_spacecraft_target_center_distance", namespaces).text = str(config['Distances_Min_Max']['maximum_spacecraft_target_center_distance'])
        Distances_Min_Max.find(".//geom:minimum_target_geocentric_distance", namespaces).text = str(config['Distances_Min_Max']['minimum_target_geocentric_distance'])
        Distances_Min_Max.find(".//geom:maximum_target_geocentric_distance", namespaces).text = str(config['Distances_Min_Max']['maximum_target_geocentric_distance'])
        geom_vect = geom_orbiter.find(".//geom:Vectors", namespaces)
        Vectors_Cartesian_Specific = geom_vect.find(".//geom:Vectors_Cartesian_Specific", namespaces)
        Vector_Cartesian_Position_Spacecraft_To_Target = Vectors_Cartesian_Specific.find(".//geom:Vector_Cartesian_Position_Spacecraft_To_Target", namespaces)
        Vector_Cartesian_Position_Spacecraft_To_Target.find(".//geom:x_position", namespaces).text = str(JUICE_TARGET_J2000[0][0])
        Vector_Cartesian_Position_Spacecraft_To_Target.find(".//geom:y_position", namespaces).text = str(JUICE_TARGET_J2000[0][1])
        Vector_Cartesian_Position_Spacecraft_To_Target.find(".//geom:z_position", namespaces).text = str(JUICE_TARGET_J2000[0][2])
        Generic_Vectors = geom_vect.find(".//geom:Generic_Vectors", namespaces)
        Vector_Cartesian_Position_Generic_List = Generic_Vectors.findall(".//geom:Vector_Cartesian_Position_Generic", namespaces)

        # Modifica ogni elemento in modo diverso
        for i, Vector_Cartesian_Position_Generic in enumerate(Vector_Cartesian_Position_Generic_List):
            if i == 0:
                # Modifica per il primo elemento
                Vector_Cartesian_Position_Generic.find(".//geom:x_position", namespaces).text = str(JUICE_EARTH_J2000[0][0])
                Vector_Cartesian_Position_Generic.find(".//geom:y_position", namespaces).text = str(JUICE_EARTH_J2000[0][1])
                Vector_Cartesian_Position_Generic.find(".//geom:z_position", namespaces).text = str(JUICE_EARTH_J2000[0][2])
            elif i == 1:
                # Modifica per il secondo elemento
                Vector_Cartesian_Position_Generic.find(".//geom:x_position", namespaces).text = str(JUICE_SUN_J2000[0][0])
                Vector_Cartesian_Position_Generic.find(".//geom:y_position", namespaces).text = str(JUICE_SUN_J2000[0][1])
                Vector_Cartesian_Position_Generic.find(".//geom:z_position", namespaces).text = str(JUICE_SUN_J2000[0][2])



        proc_cont = mission_area.find(".//psa:Processing_Context", namespaces)
        proc_cont.find(".//psa:processing_software_version", namespaces).text = '0.0.1'     #TBD: inserst the actual software version
        proc_inp = proc_cont.find(".//psa:Processing_Inputs", namespaces)
        proc_inp_id = proc_inp.find(".//psa:Processing_Input_Identification", namespaces)
        proc_inp_id.find(".//psa:file_name", namespaces).text =  config['Processing_Input_Identification']['file_name']

        # File_Area_Observational
        file_area = root.find(".//pds:File_Area_Observational", namespaces)
        file_element = file_area.find(".//pds:File", namespaces)
        file_element.find(".//pds:file_name", namespaces).text = config['Mission_Information']['filename_csv']
        file_element.find(".//pds:creation_date_time", namespaces).text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        file_element.find(".//pds:file_size", namespaces).text = config['File_Area_Observational']['file_size']
        file_element.find(".//pds:records", namespaces).text = config['File_Area_Observational']['records']

        table_element = file_area.find(".//pds:Table_Delimited", namespaces)
        table_element.find(".//pds:records", namespaces).text = config['File_Area_Observational']['records']
        table_element.find(".//pds:name", namespaces).text = 'HAA PARTIALLY CAL SCIENCE DATA TABLE'



        # Generate checksum
        file_element.find(".//pds:md5_checksum", namespaces).text = config['File_Area_Observational']['checksum']      
        """
        # Remove namespaces from tags in XML
        for elem in root.iter():
            if elem.tag.startswith("{http://pds.nasa.gov/pds4/pds/v1}"):
                elem.tag = elem.tag.split('}', 1)[-1]  # Remove the namespace prefix from the tag
        """
        # Rimuovi solo il namespace predefinito
        #tree = remove_default_namespace(tree, namespaces['pds'])

        # Rimuovi il prefisso `pds:` dai tag e aggiorna il namespace predefinito
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

    # Call the function to fill the XML with computed values and save it
    fill_xml_with_computed_values(schema_path, output_path, sc_eng, config)
