import xml.etree.ElementTree as ET

# Load the XML content
xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1"
                       xmlns:geom="http://pds.nasa.gov/pds4/geom/v1"
                       xmlns:juice="http://psa.esa.int/psa/juice/v1"
                       xmlns:psa="http://psa.esa.int/psa/v1"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1J00.xsd http://pds.nasa.gov/pds4/geom/v1 https://pds.nasa.gov/pds4/geom/v1/PDS4_GEOM_1J00_1960.xsd http://psa.esa.int/psa/v1 https://psa.esa.int/psa/v1/PDS4_PSA_1J00_1301.xsd http://psa.esa.int/psa/juice/v1 https://psa.esa.int/psa/juice/v1/PDS4_JUICE_1J00_1000.xsd">
   <Identification_Area>
      <logical_identifier></logical_identifier>
      <version_id></version_id>
      <title></title>
      <information_model_version></information_model_version>
      <product_class>Product_Observational</product_class>
      <Citation_Information>
         <author_list>Umberto De Filippis</author_list>
         <publication_year></publication_year>
         <keyword>Accelerometer</keyword>
         <keyword>Sloshing</keyword>
         <keyword>JUICE</keyword>
         <keyword>Jupiter</keyword>
         <keyword>Solar System</keyword>
         <description>Cal science product. Records the position and temperature of each accelerometer</description>
      </Citation_Information>
      <Modification_History>
         <Modification_Detail>
            <modification_date></modification_date>
            <version_id></version_id>
            <description></description>
         </Modification_Detail>
      </Modification_History>
   </Identification_Area>
</Product_Observational>'''

# Parse the XML content
root = ET.fromstring(xml_content)

# Function to remove namespaces from the element tags
def remove_ns(tag):
    return tag.split('}', 1)[-1] if '}' in tag else tag

# Traverse the tree and update the tag names
for elem in root.iter():  # Using iter() instead of getiterator()
    elem.tag = remove_ns(elem.tag)

# Populate elements with sample data
logical_identifier = root.find('.//logical_identifier')
if logical_identifier is not None:
    logical_identifier.text = "urn:example:logical_identifier"

version_id = root.find('.//version_id')
if version_id is not None:
    version_id.text = "1.0"

publication_year = root.find('.//publication_year')
if publication_year is not None:
    publication_year.text = "2024"

modification_date = root.find('.//modification_date')
if modification_date is not None:
    modification_date.text = "2024-11-15"

# Convert the updated XML back to a string
updated_xml_content = ET.tostring(root, encoding='unicode', method='xml')

# Save or print the updated XML
print(updated_xml_content)