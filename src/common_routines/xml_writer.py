import lxml.etree as ET
import numpy as np

def dict_to_xml(parent_element, data):
    for key, value in data.items():
        # Check if the key starts with an underscore, indicating an attribute
        if key.startswith('_'):
            # Special handling for text content
            if key == '_text':
                parent_element.text = str(value)
            else:
                parent_element.set(key[1:], str(value))  # Set attribute
        else:
            if isinstance(value, dict):
                # If the value is a dictionary, create a new XML element for it
                sub_element = ET.SubElement(parent_element,key)
                dict_to_xml(sub_element, value)  # Recursive call to handle nested dictionary
            elif isinstance(value, list):
                # If the value is a list, create separate XML elements for each item in the list
                for item in value:
                    # Create a new XML element for the list item
                    sub_element = ET.SubElement(parent_element,key)
                    if isinstance(item, dict):
                        # If the list item is a dictionary, handle it recursively
                        dict_to_xml(sub_element, item)
                    else:
                        # If the list item is not a dictionary, assign its string representation to the element's text
                        sub_element.text = str(item)
            else:
                # If the value is not a dictionary or a list, create a new XML element and assign the value to it
                sub_element = ET.SubElement(parent_element,key)
                sub_element.text = str(value)

def convert_to_pds4_xml(sc_eng):
    info_element = ET.Element(
        'Product_Observational',
        xmlns="http://pds.nasa.gov/pds4/pds/v1",
        xmlns_geom="http://pds.nasa.gov/pds4/geom/v1",
        xmlns_juice="http://psa.esa.int/psa/juice/v1",
        xmlns_psa="http://psa.esa.int/psa/v1",
        xmlns_xsi="http://www.w3.org/2001/XMLSchema-instance",
        xsi_schemaLocation=(
            "http://pds.nasa.gov/pds4/pds/v1 "
            "https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1J00.xsd "
            "http://pds.nasa.gov/pds4/geom/v1 "
            "https://pds.nasa.gov/pds4/geom/v1/PDS4_GEOM_1J00_1960.xsd "
            "http://psa.esa.int/psa/v1 "
            "https://psa.esa.int/psa/v1/PDS4_PSA_1J00_1301.xsd "
            "http://psa.esa.int/psa/juice/v1 "
            "https://psa.esa.int/psa/juice/v1/PDS4_JUICE_1J00_1000.xsd"
        )
    )
    for key, value in sc_eng['Product_Observational'].item().items():
        dict_to_xml(info_element, {key: value})

        # Generate XML string
        xml_string = ET.tostring(info_element, encoding="UTF-8", method='xml', pretty_print=True)
        # Decode bytes to string with specified encoding (UTF-8)
        xml_string_str = xml_string.decode('UTF-8')
        with open('outputs/output_label.xml', 'w') as file:
            file.write(xml_string_str)

def extract_filename_from_xml(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Navigate to the element containing the filename
    filename_element = root.find('.//psa_file_name')  # Adjust this path according to your XML structure

    if filename_element is not None:
        filename = filename_element.text
        return filename
    else:
        raise ValueError("Filename element not found in the XML file")


