# WI_Data_Handling
A tool for data visualization, check and conversion to XML.
# Version 1 capabilites:
## Functionality depends on the input file format
File Type | Preprocessing | Split data to RIH/POOH | Visualization | Check according to the WD requirements | Convert to XML
:---:   | :---:   | :---:  | :---:  |:---:  | :---:  
LAS | Not needed | Yes| Yes| Yes| Yes
CSV | Yes | Yes| Yes| Yes| Yes
DLIS | Not needed | Not needed| Yes (an intermediate step to select a frame is included)| Yes| Yes
XML | Not needed | Yes| Yes| Yes| No
## Configuration
* Classes.py contain classes of functions
* **Configuration** Class:
  * Function **serviceTypeOptions** determines service types available for log names. They are stored in configuration/service type.txt in such a way: 'Well Head Parameters : WH'
  * Function **dataTypeOptions** determines available data type for log names. They are stored in configuration/data type.txt in such a way: 'Operational data : OP'
  * Function **KDIunits** contains a list of the units recognized by SiteCom, a source file is configuration/KDIunits.xlsx
  * All the files in Configuration folder can be updated
* Classes for preprocessing data: **CSVprocessing, IndexType,  DLISprocessing, InputXMLprocessing, LASprocessing**
* Class for check a file according to the WD/KDI requirements: **CheckFunctions**
* Class for XML file generation: **XmlGeneration**
* Class for data visualization: **Configuration**
## Folders
* Folder **configuration** contains files with KDI units, data and service type options
* Folder **errorlog** is where an error log after the check is saved
* Folder **generatedXML** will contain a generated XML file
* Folder **templates** contain HTML templates for the application's interface
* Folder **uploads** is where uploaded files will be stored
# Version 2 capabilites:
Manual input data correction and
File split according to KDI requirements
