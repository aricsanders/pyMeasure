#-----------------------------------------------------------------------------
# Name:        MUFModels
# Purpose:     A module that holds the models associated with the Microwave Uncertainty Framework
# Author:      Aric Sanders
# Created:     3/31/2016
# License:     MIT License
#-----------------------------------------------------------------------------
""" A module that holds the models associated with the Microwave Uncertainty Framework.
Most models are xml based"""

#-----------------------------------------------------------------------------
# Standard Imports
import sys
import os
import datetime
from types import *
#-----------------------------------------------------------------------------
# Third Party Imports
sys.path.append(os.path.join(os.path.dirname( __file__ ), '..','..'))
try:
    from Code.DataHandlers.XMLModels import *
except:
    print("The module pyMeasure.Code.DataHandlers.XMLModels was not found,"
          "please put it on the python path")
    raise ImportError
try:
    import clr
except:
    print("The module clr had an error or was not found. Please check that it is on the path and "
          "working properly")
    raise ImportError
#-----------------------------------------------------------------------------
# Module Constants
SCRIPTABLE_MUF_LOCATION=r"C:\Share\MUF-develop\VNAUncertainty\bin\Debug"
"""Location of the MUF executable with modifications to make it scriptable."""
MODEL_UNIT_LIST=["Unitless","cm","mm","um","GHz","pf","nH","ohm","mho","pf/cm","ns","ps","mV","mA"]
MODEL_DISTRIBUTION_LIST=["Rectangular","Arc-sine","Bernoulli (binary)","Gaussain",
                         "2-D Uniform-Distribution Radius","2-D Gaussian-Distribution Radius"]

#-----------------------------------------------------------------------------
# Module Functions

#-----------------------------------------------------------------------------
# Module Classes
class MUFParameter(XMLBase):
    def get_value(self):
        """Returns the value of the parameter"""
        mechanism_value=self.etree.findall(".//MechanismValue")[0]
        value=mechanism_value.attrib["ControlText"]
        return float(value)

    def set_value(self,value):
        """Sets the value (center of distribution)"""
        mechanism_value=self.etree.findall(".//MechanismValue")[0]
        mechanism_value.attrib["ControlText"]=str(value)
        self.update_document()

    def get_distribution_type(self):
        """Returns the type of Distribution. The choices are held in  DistributionType/Item."""
        distribution_type=self.etree.findall(".//DistributionType")[0]
        text=distribution_type.attrib["ControlText"]
        return text

    def set_distribution_type(self,distribution_type):
        """Sets the distribution type, accepts an integer or text value.
        See the constant MODEL_DISTRIBUTION_LIST for possibilities. Rectangular is 0, Gaussian is 3. """
        if type(distribution_type) in [IntType,FloatType]:
            type_number=distribution_type
            type_name=MODEL_DISTRIBUTION_LIST[distribution_type]
        elif distribution_type in MODEL_DISTRIBUTION_LIST:
            type_number=MODEL_DISTRIBUTION_LIST.index(distribution_type)
            type_name=distribution_type
        else:
            print("Could not set the type {0} please choose a"
                  " type or index from {1}".format(distribution_type,MODEL_DISTRIBUTION_LIST))
            return
        distribution_type_tag = self.etree.findall(".//DistributionType")[0]
        distribution_type_tag.attrib["ControlText"]=type_name
        distribution_type_tag.attrib["SelectedIndex"]=type_number
        self.update_document()

    def get_distribution_width(self):
        """Returns the wdith of the distribution."""
        distribution_width=self.etree.findall(".//DistributionLimits")[0]
        text=distribution_width.attrib["ControlText"]
        return text

    def set_distribution_width(self,distribution_width):
        """Sets the distribution width"""
        distribution_width = self.etree.findall(".//DistributionLimits")[0]
        distribution_width.attrib["ControlText"]=str(distribution_width)
        self.update_document()

    def get_units(self):
        """Returns the units of the parameter"""
        units=self.etree.findall(".//Units")[0]
        text=units.attrib["ControlText"]
        return text

    def set_units(self,units):
        """Sets the units of the parameter can accept either an index or value. Look at
        MODEL_UNIT_LIST for complete set of possibilities"""
        if type(units) in [IntType,FloatType]:
            unit_number=units
            unit_name=MODEL_DISTRIBUTION_LIST[units]
        elif units in MODEL_DISTRIBUTION_LIST:
            unit_number=MODEL_DISTRIBUTION_LIST.index(units)
            unit_name=units
        else:
            print("Could not set the units {0} please choose a"
                  " type or index from {1}".format(units,MODEL_UNIT_LIST))
            return
        unit_tag = self.etree.findall(".//Units")[0]
        unit_tag.attrib["ControlText"]=unit_name
        unit_tag.attrib["SelectedIndex"]=unit_number
        self.update_document()

    def get_mechanism_name(self):
        """Returns the mechanism name"""
        units=self.etree.findall(".//MechanismName")[0]
        text=units.attrib["ControlText"]
        return text

class MUFModel(XMLBase):
    pass
class MUFVNAUncert(XMLBase):
    def get_results_directory(self):
        "Returns the results directory"
        results_directory=self.etree.findall(".//MenuStripTextBoxes/ResultsDirectory")[0].attrib["Text"]
        return results_directory

    def set_results_directory(self,directory=None):
        "Sets the results directory, default is the current working directory"
        if directory is None:
            directory=os.getcwd()
        results_directory = self.document.getElementsByTagName("ResultsDirectory")[0]
        results_directory.setAttribute(attname="Text", value=directory)
        check_box=self.document.getElementsByTagName("SelectResultsDirectoryToolStripMenuItem")[0]
        check_box.setAttribute(attname="Checked", value="True")
        self.update_etree()

    def get_number_standards(self):
        "Returns the number of calibration standards in the before calibration"
        sub_items = self.etree.findall(".//BeforeCalibration/Item")
        return len(sub_items)

    def get_standard_definition(self,standard_number=1):
        "Returns the xml definition of the standard in position standard_number"
        sub_items = self.etree.findall(".//BeforeCalibration/Item")
        return etree.tostring(sub_items[standard_number-1])

    def get_standard_measurement_locations(self):
        """Returns the file locations for the measurement of the standards in a form of a list"""
        standards = self.etree.findall(".//BeforeCalibration/Item/SubItem[@Index='6']")
        locations=[standard.attrib["Text"] for standard in standards]
        return locations

    def set_standard_location(self,standard_location=None,standard_number=1):
        """Sets the location for the measurement of standard_number"""
        standards = self.etree.findall(".//BeforeCalibration/Item/SubItem[@Index='6']")
        standard=standards[standard_number-1]
        standard.attrib["Text"]=standard_location
        self.update_document()

    def get_number_montecarlo(self):
        "Returns the number of montecarlo simulations"
        montecarlo_text_box=self.etree.findall(".//MenuStripTextBoxes/NumberMonteCarloSimulations")[0]
        number_montecarlo=montecarlo_text_box.attrib["Text"]
        return number_montecarlo

    def set_number_montecarlo(self,number_montecarlo=100):
        """Sets the number of montecarlo trials for the menu"""
        montecarlo_text_box = self.etree.findall(".//MenuStripTextBoxes/NumberMonteCarloSimulations")[0]
        montecarlo_text_box.attrib["Text"]=str(number_montecarlo)
        self.update_document()

    def get_DUTs(self):
        "Returns the names and locations of DUTs"
        duts=[]
        names=map(lambda x: x.attrib["Text"],self.etree.findall(".//DUTMeasurements/Item/SubItem[@Index='0']"))
        locations=map(lambda x: x.attrib["Text"],self.etree.findall(".//DUTMeasurements/Item/SubItem[@Index='1']"))
        for index,name in enumerate(names):
            name_location_dictionary={"name":name,"location":locations[index]}
            duts.append(name_location_dictionary)
        return duts

    def add_DUT(self,location,name=None):
        """Adds a DUT to the DUTMeasurements element"""
        # get the name
        if name is None:
            name=os.path.basename(location).split(".")[0]
        # first get the DUTMeasurement element
        dut_measurement=self.etree.findall(".//DUTMeasurements")[0]
        # next add one to the count attribute
        number_standards=int(dut_measurement.attrib["Count"])
        number_standards+=1
        dut_measurement.attrib["Count"]=str(number_standards)
        # create a Item
        item=etree.SubElement(dut_measurement,"Item",attrib={"Count":"2","Index":str(number_standards),"Text":name})
        etree.SubElement(item,"SubItem",attrib={"Index":"0","Text":name})
        etree.SubElement(item,"SubItem",attrib={"Index":"1","Text":location})
        self.update_document()

    def clear_DUTs(self):
        """Removes all DUTs"""
        dut_measurement = self.etree.findall(".//DUTMeasurements")[0]
        items= self.etree.findall(".//DUTMeasurements/Item")
        for item in items:
            dut_measurement.remove(item)
        self.update_document()










class MUFVNAUncertArchive(XMLBase):
    pass
class MUFMeasurement(XMLBase):
    pass
class MUFSolution(XMLBase):
    pass

#-----------------------------------------------------------------------------
# Module Scripts
def run_muf_script(menu_location,timeit=True):
    """Opens a vnauncert or vnauncert_archive and runs it as is."""

    start=datetime.datetime.utcnow()
    sys.path.append(SCRIPTABLE_MUF_LOCATION)
    clr.AddReference("VNAUncertainty")
    import VNAUncertainty
    from System import EventArgs, Object
    event=EventArgs()
    vna =VNAUncertainty.VNAUncertainty()
    vna.OnLoad(event)
    vna.myOpenMenu(menu_location)
    vna.OnLocationChanged(event)
    vna.RunCalibration(0)
    vna.Close()
    if timeit:
        stop=datetime.datetime.utcnow()
        runtime=stop-start
        print("VNAUncertainty finished running  at {0}".format(stop))
        print("The script took {0} seconds to run".format(runtime.seconds))


#-----------------------------------------------------------------------------
# Module Runner
if __name__ == '__main__':
    pass