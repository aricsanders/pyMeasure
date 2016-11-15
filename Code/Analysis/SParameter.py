#-----------------------------------------------------------------------------
# Name:        SParameter.py
# Purpose:    Tools to analyze SParameter Data
# Author:      Aric Sanders
# Created:     4/13/2016
# License:     MIT License
#-----------------------------------------------------------------------------
""" Sparameter is a module with tools for analyzing Sparameter data.  """
#-----------------------------------------------------------------------------
# Standard Imports
import os
import re
import datetime
import sys

#-----------------------------------------------------------------------------
# Third Party Imports
sys.path.append(os.path.join(os.path.dirname( __file__ ), '..','..'))
try:
    import numpy as np
except:
    np.ndarray='np.ndarray'
    print("Numpy was not imported")
    pass
try:
    import pandas
except:
    print("Pandas was not imported")
    pass
try:
    #Todo: this could lead to a cyclic dependency, it really should import only the models it analyzes
    #Todo: If analysis is to be in the top import, none of the models should rely on it
    #import pyMeasure.Code.DataHandlers.NISTModels
    from Code.DataHandlers.NISTModels import *
    from Code.DataHandlers.TouchstoneModels import *
    from Code.DataHandlers.GeneralModels import *
    #from pyMeasure import *
except:
    print("The subpackage pyMeasure.Code.DataHandlers did not import properly,"
          "please check that it is on the python path and that unit tests passed")
    raise ImportError
try:
    import matplotlib.pyplot as plt
except:
    print("The module matplotlib was not found,"
          "please put it on the python path")
#-----------------------------------------------------------------------------
# Module Constants

# Does this belong in tests or a Data folder
ONE_PORT_DUT=os.path.join(os.path.dirname(os.path.realpath(__file__)),'Tests')
#-----------------------------------------------------------------------------
# Module Functions
def one_port_robin_comparision_plot(input_asc_file,input_res_file,**options):
    """one_port_robin_comparision_plot plots a one port.asc file against a given .res file,
    use device_history=True in options to show device history"""
    defaults={"device_history":False,"mag_res":False}
    plot_options={}
    for key,value in defaults.iteritems():
        plot_options[key]=value
    for key,value in options.iteritems():
        plot_options[key]=value
    history=np.loadtxt(input_res_file,skiprows=1)
    column_names=["Frequency",'mag','arg','magS11N','argS11N','UmagS11N','UargS11N']
    options={"data":history.tolist(),"column_names":column_names,"column_types":['float' for column in column_names]}
    history_table=AsciiDataTable(None,**options)
    table=OnePortCalrepModel(input_asc_file)
    if plot_options["device_history"]:
        history_frame=pandas.read_csv(ONE_PORT_DUT)
        device_history=history_frame[history_frame["Device_Id"]==table.header[0].rstrip().lstrip()]
    fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)

    ax0.errorbar(history_table.get_column('Frequency'),history_table.get_column('magS11N'),fmt='k--',
                yerr=history_table.get_column('UmagS11N'),label="History")
    ax0.errorbar(table.get_column('Frequency'),table.get_column('mag'),
        yerr=table.get_column('uMg'),fmt='ro',label="Current Measurement",alpha=.3)
    if plot_options["device_history"]:
        ax0.errorbar(device_history['Frequency'].tolist(),device_history['mag'].tolist(),fmt='bs',
                    yerr=device_history['uMg'].tolist(),label="From .asc", alpha=.5)
    if plot_options["mag_res"]:
        ax0.errorbar(history_table.get_column('Frequency'),history_table.get_column('mag'),fmt='gx',
                    yerr=history_table.get_column('UmagS11N'),label="From mag in res")
    ax0.set_title('Magnitude S11')

    ax1.errorbar(history_table.get_column('Frequency'),history_table.get_column('arg'),fmt='k--',
                yerr=history_table.get_column('UargS11N'),label="history")
    ax1.errorbar(table.get_column('Frequency'),table.get_column('arg'),
                 yerr=table.get_column('uAg'),fmt='ro',label="Current Measurement",alpha=.3)
    if plot_options["device_history"]:
        ax1.errorbar(device_history['Frequency'].tolist(),device_history['arg'].tolist(),fmt='bs',
                    yerr=device_history['uAg'].tolist(),label="From .asc", alpha=.5)
    ax1.set_title('Phase S11')
    ax0.legend(loc='lower left', shadow=True)
    plt.show()

def two_port_swap_ports(complex_data):
    """Accepts data in [[frequency, S11, S21, S12, S22]..] format and returns
    [[frequency, S22, S12, S21, S11]..]"""
    out_data=[]
    for row in complex_data:
        [frequency, S11, S21, S12, S22]=row
        new_row=[frequency, S22, S12, S21, S11]
        out_data.append(new_row)
    return out_data

def two_port_complex_to_matrix_form(complex_data):
    """two_port_complex_to_matrix_form takes a list of [[frequency,S11,S21,S12,S22],..] and
    returns a list in the
    form [[frequency,np.matrix([[S11,S12],[S21,S22]])]..], it is meant to prepare data for correction"""
    out_list=[]
    for row in complex_data:
        frequency=row[0]
        [S11,S21,S12,S22]=row[1:]
        m=np.matrix([[S11,S12],[S21,S22]])
        out_list.append([frequency,m])
    #print out_list
    return out_list

def two_port_matrix_to_complex_form(matrix_form_data):
    """two_port_matrix_to_complex_form takes a list of [[frequency,np.matrix([[S11,S12],[S21,S22]])]..]
    and returns a list in the
    form [[frequency,S11,S21,S12,S22],..] , it is meant to undo two_port_complex_to_matrix_form"""
    out_list=[]
    for row in matrix_form_data:
        frequency=row[0]
        m=row[1]
        [S11,S21,S12,S22]=[m[0,0],m[1,0],m[0,1],m[1,1]]
        out_list.append([frequency,S11,S12,S21,S22])
    return out_list

def invert_two_port_matrix_list(two_port_matrix_form):
    """invert_two_port_matrix_list inverts all elements in the list two_port_matrix_form,
    which is in the format [[frequency,np.matrix([[S11,S12],[S21,S22]])]..] and returns a list
    in [[frequency,inv(np.matrix([[S11,S12],[S21,S22]]))]..] format works on any list in the form [value, matrix]
    """
    out_list=[]
    for row in two_port_matrix_form:
        frequency=row[0]
        m=row[1]
        m_inv=np.linalg.inv(m)
        out_list.append([frequency,m_inv])
    return out_list

def polar_average(complex_number_1,complex_number_2):
    """Averages 2 complex numbers in polar coordinates and returns a single complex number"""
    polar_number_1=cmath.polar(complex_number_1)
    polar_number_2=cmath.polar(complex_number_2)
    average_length=(polar_number_1[0]+polar_number_2[0])/2.
    average_phase=(polar_number_1[1]+polar_number_2[1])/2.
    out_value=cmath.rect(average_length,average_phase)
    return out_value

def polar_geometric_average(complex_number_1,complex_number_2):
    """Averages 2 complex numbers in polar coordinates and returns a single complex number"""
    polar_number_1=cmath.polar(complex_number_1)
    polar_number_2=cmath.polar(complex_number_2)
    average_length=(polar_number_1[0]*polar_number_2[0])**.5
    average_phase=(polar_number_1[1]+polar_number_2[1])/2
    out_value=cmath.rect(average_length,average_phase-math.pi)
    return out_value

def S_to_T(S_list):
    """Converts S-parameters into a T Matrix. Input form should be in frequency, np.matrix([[S11,S12],[S21,S22]])
    format. Returns a list in [frequency, np.matrix] format """
    t_complex_list=[]
    t_matrix=[]
    for row in S_list:
        frequency=row[0]
        m=row[1]
        T11=-np.linalg.det(m)/m[1,0]
        T12=m[0,0]/m[1,0]
        T21=-m[1,1]/m[1,0]
        T22=1/m[1,0]
        t_matrix.append([frequency,np.matrix([[T11,T12],[T21,T22]])])
        t_complex_list.append([frequency,T11,T12,T21,T22])
    return t_matrix

def T_to_S(T_list):
    """Converts T Matrix into S parameters. Input form should be in frequency, np.matrix([[T11,T12],[T21,T22]])
    format. Returns a list in [frequency, np.matrix] format."""
    S_list=[]
    for row in T_list:
        frequency=row[0]
        m=row[1]
        S11=m[0,1]/m[1,1]
        S12=np.linalg.det(m)/m[1,1]
        S21=1/m[1,1]
        S22=-m[1,0]/m[1,1]
        S_list.append([frequency,np.matrix([[S11,S12],[S21,S22]])])
    return S_list

def unwrap_phase(phase_list,min_phase=0,units='degree'):
    """unwrap_phase returns an unwraped phase list given a wraped phase list, the beginning value can be specified
    by min_phase and radians or degrees can be specified by units"""
    unwrapped_phase_list=[]
    pass



def correct_sparameters_eight_term(sparameters_complex,eight_term_correction,reciprocal=True):
    """Applies the eight term correction to sparameters_complex and returns
    a correct complex list in the form of [[frequency,S11,S21,S12,S22],..]. The eight term
    correction should be in the form [[frequency,S1_11,S1_21,S1_12,S1_22,S2_11,S2_21,S2_12,S2_22]..]
    Use s2p.sparameter_complex as input."""
    # first transform both lists to matrices
    s2p_matrix_list=two_port_complex_to_matrix_form(sparameters_complex)
    s1_list=[[row[0],row[1],row[2],row[3],row[4]] for row in eight_term_correction]
    s2_list=[[row[0],row[5],row[6],row[7],row[8]] for row in eight_term_correction]
    s1_matrix_list=two_port_complex_to_matrix_form(s1_list)
    s2_matrix_list=two_port_complex_to_matrix_form(s2_list)
    # now transform to T matrices
    t_matrix_list=S_to_T(s2p_matrix_list)
    x_matrix_list=S_to_T(s1_matrix_list)
    y_matrix_list=S_to_T(s2_matrix_list)
    # now invert x
    x_inverse_matrix_list=invert_two_port_matrix_list(x_matrix_list)
    y_inverse_matrix_list=invert_two_port_matrix_list(y_matrix_list)
    # now apply the correction
    t_corrected_list=[]
    for index,row in enumerate(t_matrix_list):
        frequency=row[0]
        t_corrected=x_inverse_matrix_list[index][1]*row[1]*y_inverse_matrix_list[index][1]
        t_corrected_list.append([frequency,t_corrected])
    # now transform back to S
    s_corrected_matrix_list =T_to_S(t_corrected_list)
    # now put back into single row form
    s_corrected_list=two_port_matrix_to_complex_form(s_corrected_matrix_list)
    # now we take the geometric average and replace S12 and S21 with it
    if reciprocal:
        s_averaged_corrected=[]
        phase_last=0
        for row in s_corrected_list:
            [frequency,S11,S21,S12,S22]=row
            # S12 and S21 are averaged together in a weird way that makes phase continuous
            geometric_mean=cmath.sqrt(S21*S12)
            root_select=1
            phase_new=cmath.phase(geometric_mean)
            # if the phase jumps by >180 but less than 270, then pick the other root
            if abs(phase_new-phase_last)>math.pi/2 and abs(phase_new-phase_last)<3*math.pi/2:
                root_select=-1
            mean_S12_S21=root_select*cmath.sqrt(S21*S12)
            s_averaged_corrected.append([frequency,S11,mean_S12_S21,mean_S12_S21,S22])
            phase_last=cmath.phase(mean_S12_S21)
        s_corrected_list=s_averaged_corrected
    else:
        pass

    return s_corrected_list

def correct_sparameters_sixteen_term(sparameters_complex,sixteen_term_correction):
    """Applies the sixteen term correction to sparameters and returns a new sparameter list.
    The sparameters should be a list of [frequency, S11, S21, S12, S22] where S terms are complex numbers.
    The sixteen term correction should be a list of
    [frequency, S11, S12, S13,S14,S21, S22,S23,S24,S31,S32,S33,S34,S41,S42,S43,S44], etc are complex numbers
    Designed to use S2P.sparameter_complex and SNP.sparameter_complex"""

    # first create 4 separate matrix lists for 16 term correction
    s1_matrix_list=[]
    s2_matrix_list=[]
    s3_matrix_list=[]
    s4_matrix_list=[]
    # Then populate them with the right values
    for index,correction in enumerate(sixteen_term_correction):
        [frequency, S11, S12, S13,S14,S21, S22,S23,S24,S31,S32,S33,S34,S41,S42,S43,S44]=correction
        s1_matrix_list.append([frequency,np.matrix([[S11,S12],[S21,S22]])])
        s2_matrix_list.append([frequency,np.matrix([[S13,S14],[S23,S24]])])
        s3_matrix_list.append([frequency,np.matrix([[S31,S32],[S41,S42]])])
        s4_matrix_list.append([frequency,np.matrix([[S33,S34],[S43,S44]])])
    sparameter_matrix_list=two_port_complex_to_matrix_form(sparameters_complex)
    # Apply the correction
    sparameter_out=[]
    for index,sparameter in enumerate(sparameter_matrix_list):
        frequency=sparameter[0]
        s_matrix=sparameter[1]
        [s11_matrix,s12_matrix,s21_matrix,s22_matrix]=[s1_matrix_list[index][1],s2_matrix_list[index][1],
                                                   s3_matrix_list[index][1],s4_matrix_list[index][1]]
        corrected_s_matrix=np.linalg.inv(s21_matrix*np.linalg.inv(s_matrix-s11_matrix)*s12_matrix+s22_matrix)
        # This flips S12 and S21
        sparameter_out.append([frequency,corrected_s_matrix[0,0],corrected_s_matrix[1,0],
                                corrected_s_matrix[0,1],corrected_s_matrix[1,1]])
    return sparameter_out

def correct_sparameters_twelve_term(sparameters_complex,twelve_term_correction,reciprocal=True):
    """Applies the twelve term correction to sparameters and returns a new sparameter list.
    The sparameters should be a list of [frequency, S11, S21, S12, S22] where S terms are complex numbers.
    The twelve term correction should be a list of
    [frequency,Edf,Esf,Erf,Exf,Elf,Etf,Edr,Esr,Err,Exr,Elr,Etr] where Edf, etc are complex numbers"""
    if len(sparameters_complex) != len(twelve_term_correction):
        raise TypeError("s parameter and twelve term correction must be the same length")
    sparameter_out=[]
    phase_last=0.
    for index,row in enumerate(sparameters_complex):
        frequency=row[0]
        Sm=np.matrix(row[1:]).reshape((2,2))
        [frequency,Edf,Esf,Erf,Exf,Elf,Etf,Edr,Esr,Err,Exr,Elr,Etr]=twelve_term_correction[index]
        #        frequency Edf Esf Erf Exf Elf Etf Edr Esr Err Exr Elr Etr.
#         print [frequency,Edf,Esf,Erf,Exf,Elf,Etf,Edr,Esr,Err,Exr,Elr,Etr]
#         print Sm[0,0]
        D =(1+(Sm[0,0]-Edf)*(Esf/Erf))*(1+(Sm[1,1]-Edr)*(Esr/Err))-(Sm[0,1]*Sm[1,0]*Elf*Elr)/(Etf*Etr)
#         print D
        S11 =(Sm[0,0]-Edf)/(D*Erf)*(1+(Sm[1,1]-Edr)*(Esr/Err))-(Sm[0,1]*Sm[1,0]*Elf)/(D*Etf*Etr)
        S21 =((Sm[1,0]-Exr)/(D*Etf))*(1+(Sm[1,1]-Edr)*(Esr-Elf)/Err)
        S12 = ((Sm[0,1]-Exf)/(D*Etr))*(1+(Sm[0,0]-Edf)*(Esf-Elr)/Erf)
        S22 = (Sm[1,1]-Edr)/(D*Err)*(1+(Sm[0,0]-Edf)*(Esf/Erf))-(Sm[0,1]*Sm[1,0]*Elr)/(D*Etf*Etr)
        # S12 and S21 are averaged together in a weird way that makes phase continuous
        geometric_mean=cmath.sqrt(S21*S12)
        root_select=1
        phase_new=cmath.phase(geometric_mean)
        # if the phase jumps by >180 but less than 270, then pick the other root
        if abs(phase_new-phase_last)>math.pi/2 and abs(phase_new-phase_last)<3*math.pi/2:
            root_select=-1
        mean_S12_S21=root_select*cmath.sqrt(S21*S12)
        if reciprocal:
            sparameter_out.append([frequency,S11,mean_S12_S21,mean_S12_S21,S22])
        else:
            sparameter_out.append([frequency,S11,S21,S12,S22])
        phase_last=cmath.phase(mean_S12_S21)
    return sparameter_out
def correct_sparameters(sparameters,correction,**options):
    """Correction sparamters trys to return a corrected set of sparameters given uncorrected sparameters
    and a correction. Correct sparameters will accept file_name's, pyMeasure classes,
    complex lists or a mixture, returns value in the form it was entered. Correction is assumed reciprocal
    unless reciprocal=False"""
    defaults={"reciprocal":True,"output_type":None,"file_path":None}
    correction_options={}
    for key,value in defaults.iteritems():
        correction_options[key]=value
    for key,value in options.iteritems():
        correction_options[key]=value
    try:
        # import and condition sparameters and correction
        if type(sparameters) is StringType:
            # Assume sparameters is given by file name
            sparameters_table=S2PV1(sparameters)
            sparameters=sparameters_table.sparameter_complex
            output_type='file'
        elif re.search('S2PV1',type(sparameters)):
            output_type='S2PV1'
            sparameters=sparameters.sparameter_complex
        elif type(sparameters) is ListType:
            # check to see if it is a list of complex variables or matrix
            if type(sparameters[1]) is ComplexType:
                output_type='complex_list'
            # Handle frequency, matrix lists
            elif type(sparameters[1]) in ['np.array','np.matrix'] and type(sparameters) is FloatType :
                output_type='matrix_list'
                sparameters=two_port_matrix_to_complex_form(sparameters)
            # handle matrix
        elif type(sparameters) in ['np.array','np.matrix']:
            output_type='matrix'
            raise
        # Handle the correction types
        if len(correction) is 13:
            corrected_sparameters=correct_sparameters_twelve_term(sparameters,correction)
        elif len(correction) is 17:
            corrected_sparameters=correct_sparameters_sixteen_term(sparameters,correction)
        elif len(correction) is 9:
            corrected_sparameters=correct_sparameters_eight_term(sparameters,correction)
        # Handle the output type using the derived one or the one entered as an option
        if correction_options["output_type"] is None:
            pass
        else:
            output_type=correction_options["output_type"]
        if re.match('file',output_type, re.IGNORECASE):
            output_table=S2PV1(correction_options["file_path"],sparameter_complex=corrected_sparameters)
            output_table.save()
            print("Output was saved as {0}".format(output_table.path))
        elif re.search("complex",output_type,re.IGNORECASE):
            return corrected_sparameters
        elif re.search("matrix_list",output_type,re.IGNORECASE):
            return two_port_complex_to_matrix_form(corrected_sparameters)
        elif re.search("matrix",output_type,re.IGNORECASE):
            raise

    except:
        print("Could not correct sparameters")
        raise

def average_one_port_sparameters(table_list,**options):
    """Returns a table that is the average of the Sparameters in table list. The new table will have all the unique
    frequency values contained in all of the tables. Tables must be in Real-Imaginary format or magnitude-angle format
    do not try to average db-angle format. """
    #This will work on any table that the data is stored in data, need to add a sparameter version
    defaults={"frequency_selector":0,"frequency_column_name":"Frequency"}
    average_options={}
    for key,value in defaults.iteritems():
        average_options[key]=value
    for key,value in options.iteritems():
        average_options[key]=value
    frequency_list=[]
    average_data=[]
    for table in table_list:
        frequency_list=frequency_list+table.get_column("Frequency")
    unique_frequency_list=sorted(list(set(frequency_list)))
    for frequency in unique_frequency_list:
        new_row=[]
        for table in table_list:
            data_list=filter(lambda x: x[average_options["frequency_selector"]]==frequency,table.data)
            table_average=np.mean(np.array(data_list),axis=0)
            new_row.append(table_average)
            #print new_row
        average_data.append(np.mean(new_row,axis=0).tolist())
    return average_data

def two_port_comparision_plot_with_residuals(two_port_raw,mean_frame,difference_frame):
    """Creates a comparision plot given a TwoPortRawModel object and a pandas.DataFrame mean frame"""
    fig, axes = plt.subplots(nrows=3, ncols=2, sharex='col',figsize=(8,6),dpi=80)
    measurement_date=two_port_raw.metadata["Measurement_Date"]
    ax0,ax1,ax2,ax3,ax4,ax5 = axes.flat
    compare_axes=[ax0,ax1,ax2,ax3,ax4,ax5]
    diff_axes=[]
    for ax in compare_axes:
        diff_axes.append(ax.twinx())
    #diff_axes=[diff_ax0,diff_ax1,diff_ax2,diff_ax3,diff_ax4,diff_ax5]
    column_names=['Frequency','magS11','argS11','magS21','argS21','magS22','argS22']
    for index,ax in enumerate(diff_axes):
        ax.plot(difference_frame['Frequency'].tolist(),difference_frame[column_names[index+1]].tolist(),'r-x')
        ax.set_ylabel('Difference',color='red')
        if re.search('mag',column_names[index+1]):
            ax.set_ylim(-.02,.02)
        #ax.legend_.remove()
    for index, ax in enumerate(compare_axes):
        ax.plot(two_port_raw.get_column('Frequency'),two_port_raw.get_column(column_names[index+1]),
                'k-o',label=measurement_date)
        ax.plot(mean_frame['Frequency'].tolist(),mean_frame[column_names[index+1]].tolist(),'gs',label='Mean')
        ax.set_title(column_names[index+1])
        ax.legend(loc=1,fontsize='8')
        #ax.xaxis.set_visible(False)
        if re.search('arg',column_names[index+1]):
            ax.set_ylabel('Phase(Degrees)',color='green')
        elif re.search('mag',column_names[index+1]):
            ax.set_ylabel(r'|${\Gamma} $|',color='green')
        #ax.sharex(diff_axes[index])
    ax4.set_xlabel('Frequency(GHz)',color='k')
    ax5.set_xlabel('Frequency(GHz)',color='k')
    fig.subplots_adjust(hspace=0)
    fig.suptitle(two_port_raw.metadata["Device_Id"]+"\n",fontsize=18,fontweight='bold')
    plt.tight_layout()
    plt.show()

def two_port_difference_frame(two_port_raw,mean_frame):
    """Creates a difference pandas.DataFrame given a two port raw file and a mean pandas.DataFrame"""
    difference_list=[]
    for row in two_port_raw.data[:]:
        #print row[0]
        mean_row=mean_frame[abs(mean_frame["Frequency"]-row[0])<abs(.01)].as_matrix()
        #print mean_row
        try:
            mean_row=mean_row[0]
            difference_row=[row[i+2]-mean_row[i] for i in range(1,len(mean_row))]
            difference_row.insert(0,row[0])
            difference_list.append(difference_row)
        except:pass
    column_names=['Frequency','magS11','argS11','magS21','argS21','magS22','argS22']
    diff_data_frame=pandas.DataFrame(difference_list,columns=column_names)
    return diff_data_frame

def two_port_mean_frame(device_id,system_id=None,history_data_frame=None):
    """Given a Device_Id and a pandas data frame of the history creates a mean data_frame"""
    device_history=history_data_frame[history_data_frame["Device_Id"]==device_id]
    if system_id is not None:
        device_history=device_history[device_history["System_Id"]==system_id]
    column_names=['Frequency','magS11','argS11','magS21','argS21','magS22','argS22']
    unique_frequency_list=device_history["Frequency"].unique()
    mean_array=[]
    for index,freq in enumerate(unique_frequency_list):
        row=[]
        for column in column_names:
            values=np.mean(device_history[device_history["Frequency"]==unique_frequency_list[index]][column].as_matrix())
            #print values
            mean_value=np.mean(values)
            row.append(mean_value)
        mean_array.append(row)
    mean_frame=pandas.DataFrame(mean_array,columns=column_names)
    return mean_frame

def mean_from_history(history_frame,**options):
    """mean_from_history creates a mean_frame given a full history frame (pandas.DataFrame object),
    by setting options it selects column names
    to output and input values to filter on. Returns a pandas.DataFrame object with column names = column_names,
    and filtered by any of the following: "Device_Id","System_Id","Measurement_Timestamp",
    "Connector_Type_Measurement", "Measurement_Date" or "Measurement_Time" """

    defaults={"Device_Id":None, "System_Id":None,"Measurement_Timestamp":None,
              "Connector_Type_Measurement":None,
             "Measurement_Date":None,"Measurement_Time":None,
              "column_names":['Frequency','magS11','argS11']}
    mean_options={}
    for key,value in defaults.iteritems():
        mean_options[key]=value
    for key,value in options.iteritems():
            mean_options[key]=value

    filters=["Device_Id","System_Id","Measurement_Timestamp","Connector_Type_Measurement",
             "Measurement_Date","Measurement_Time"]
    temp_frame=history_frame.copy()
    for index,filter_type in enumerate(filters):
        if mean_options[filter_type] is not None:
            temp_frame=temp_frame[temp_frame[filter_type]==mean_options[filter_type]]
#     temp_frame=temp_frame[temp_frame["Device_Id"]==mean_options["Device_Id"]]
#     temp_frame=temp_frame[temp_frame["System_Id"]==mean_options["System_Id"]]
    unique_frequency_list=temp_frame["Frequency"].unique()
    mean_array=[]
    for index,freq in enumerate(unique_frequency_list):
        row=[]
        for column in mean_options["column_names"]:
            values=np.mean(temp_frame[temp_frame["Frequency"]==unique_frequency_list[index]][column].as_matrix())
            mean_value=np.mean(values)
            row.append(mean_value)
        mean_array.append(row)
    mean_frame=pandas.DataFrame(mean_array,columns=mean_options["column_names"])
    return mean_frame

def raw_difference_frame(raw_model,mean_frame,**options):
    """Creates a difference pandas.DataFrame given a raw NIST model and a mean pandas.DataFrame"""
    defaults={"column_names":mean_frame.columns.tolist()}
    difference_options={}
    for key,value in defaults.iteritems():
        difference_options[key]=value
    for key,value in options.iteritems():
        difference_options[key]=value
    difference_list=[]
    for row in raw_model.data[:]:
        #print row[0]
        mean_row=mean_frame[abs(mean_frame["Frequency"]-row[0])<abs(.01)].as_matrix()
        #print mean_row
        try:
            mean_row=mean_row[0]
            difference_row=[row[i+2]-mean_row[i] for i in range(1,len(mean_row))]
            difference_row.insert(0,row[0])
            difference_list.append(difference_row)
        except:pass
    difference_data_frame=pandas.DataFrame(difference_list,columns=difference_options["column_names"])
    return difference_data_frame

def return_history_key(calrep_model):
    "Returns a key for the history dictionary given a calrep model"
    model=calrep_model.__class__.__name__
    #print model
    if re.search('Calrep|DUT',model):
        if re.search('OnePortCalrep',model):
            return '1-port calrep'
        elif re.search('TwoPortCalrep',model):
            return '2-port calrep'
        elif re.search('PowerCalrep',model):
            if calrep_model.options["column_names"]==POWER_3TERM_COLUMN_NAMES:
                return 'power 3term calrep'
            elif calrep_model.options["column_names"]==POWER_4TERM_COLUMN_NAMES:
                return 'power 4term calrep'
        elif re.search('OnePortDUT',model):
            return 'power 3term calrep'
    else:
        raise TypeError("Must be a calrep model, such as OnePortCalrepModel, etc. ")

def raw_comparision_plot_with_residuals(raw_nist,mean_frame,difference_frame,**options):
    """Creates a comparision plot given a RawModel object and a pandas.DataFrame mean frame and difference frame"""
    defaults={"display_mean":True,
              "display_difference":True,
              "display_raw":True,
              "display_legend":True,
              "save_plot":False,
              "directory":None,
              "specific_descriptor":raw_nist.metadata["Device_Id"]+"_Check_Standard",
              "general_descriptor":"Plot","file_name":None}
    comparison_plot_options={}
    for key,value in defaults.iteritems():
        comparison_plot_options[key]=value
    for key,value in options.iteritems():
        comparison_plot_options[key]=value
    column_names=mean_frame.columns.tolist()
    number_rows=len(column_names)/2
    fig, compare_axes = plt.subplots(nrows=number_rows, ncols=2, sharex='col',figsize=(8,6),dpi=80)
    measurement_date=raw_nist.metadata["Measurement_Date"]
    diff_axes=[]
    for ax in compare_axes.flat:
        diff_axes.append(ax.twinx())
    #diff_axes=[diff_ax0,diff_ax1,diff_ax2,diff_ax3,diff_ax4,diff_ax5]
    if comparison_plot_options["display_difference"]:
        for index,ax in enumerate(diff_axes):
            ax.plot(difference_frame['Frequency'].tolist(),difference_frame[column_names[index+1]].tolist(),'r-x')
            ax.set_ylabel('Difference',color='red')
            if re.search('mag',column_names[index+1]):
                ax.set_ylim(-.02,.02)
            #ax.legend_.remove()
    for index, ax in enumerate(compare_axes.flat):
        if comparison_plot_options["display_raw"]:
            ax.plot(raw_nist.get_column('Frequency'),raw_nist.get_column(column_names[index+1]),
                    'k-o',label=measurement_date)
        if comparison_plot_options["display_mean"]:
            ax.plot(mean_frame['Frequency'].tolist(),mean_frame[column_names[index+1]].tolist(),'gs',label='Mean')
        ax.set_title(column_names[index+1])
        if comparison_plot_options["display_legend"]:
            ax.legend(loc=1,fontsize='8')
        #ax.xaxis.set_visible(False)
        if re.search('arg',column_names[index+1]):
            ax.set_ylabel('Phase(Degrees)',color='green')
        elif re.search('mag',column_names[index+1]):
            ax.set_ylabel(r'|${\Gamma} $|',color='green')
        #ax.sharex(diff_axes[index])
    compare_axes.flat[-2].set_xlabel('Frequency(GHz)',color='k')
    compare_axes.flat[-1].set_xlabel('Frequency(GHz)',color='k')
    fig.subplots_adjust(hspace=0)
    fig.suptitle(raw_nist.metadata["Device_Id"]+"\n",fontsize=18,fontweight='bold')
    plt.tight_layout()
    if comparison_plot_options["file_name"] is None:
        file_name=auto_name(specific_descriptor=comparison_plot_options["specific_descriptor"],
                            general_descriptor=comparison_plot_options["general_descriptor"],
                            directory=comparison_plot_options["directory"],extension='png',padding=3)
    else:
        file_name=comparison_plot_options["file_name"]
    if comparison_plot_options["save_plot"]:
        #print file_name
        plt.savefig(os.path.join(comparison_plot_options["directory"],file_name))
    else:
        plt.show()

def calrep_history_plot(calrep_model,history_frame,**options):
    """Given a calrep_model and a history frame calrep_history_plot plots the file against any other in history
    frame  (pandas.DataFrame) with dates"""
    defaults={"display_legend":True,
              "save_plot":False,
              "directory":None,
              "specific_descriptor":calrep_model.metadata["Device_Id"]+"_Device_Measurement",
              "general_descriptor":"Plot",
              "file_name":None,
              "min_num":0,
              "max_num":None,
              "error_style":"area"}
    history_plot_options={}
    for key,value in defaults.iteritems():
        history_plot_options[key]=value
    for key,value in options.iteritems():
        history_plot_options[key]=value
    # The way we plot depends on the models
    model=calrep_model.__class__.__name__
    device_history=history_frame[history_frame["Device_Id"]==calrep_model.metadata["Device_Id"]]
    unique_analysis_dates=sorted(device_history["Analysis_Date"].unique().tolist())
    print("{0} are {1}".format("unique_analysis_dates",unique_analysis_dates))
    if re.search('Power',model):
        number_rows=2
        column_names=['mag','arg','Efficiency','Calibration_Factor']
        if calrep_model.options["column_names"]==POWER_3TERM_COLUMN_NAMES:
            error_names=['uMg','uAg','uEe','uCe']
        elif calrep_model.options["column_names"]==POWER_4TERM_COLUMN_NAMES:
            error_names=['uMg','uAg','uEg','uCg']
        table=calrep_model.joined_table

    elif re.search('OnePort',model):
        number_rows=1
        column_names=['mag','arg']
        error_names=['uMg','uAg']
        table=calrep_model

    elif re.search('TwoPort',model):
        number_rows=3
        column_names=['magS11','argS11','magS21','argS21','magS22','argS22']
        error_names=['uMgS11','uAgS11','uMgS21','uAgS21','uMgS22','uAgS22']
        table=calrep_model.joined_table

    fig, compare_axes = plt.subplots(nrows=number_rows, ncols=2, sharex='col',figsize=(8,6),dpi=80)
    for index, ax in enumerate(compare_axes.flat):

        #ax.xaxis.set_visible(False)
        if re.search('arg',column_names[index]):
            ax.set_ylabel('Phase(Degrees)',color='green')
        elif re.search('mag',column_names[index]):
            ax.set_ylabel(r'|${\Gamma} $|',color='green')
        ax.set_title(column_names[index])
        # initial plot of
        x=table.get_column('Frequency')
        y=np.array(table.get_column(column_names[index]))
        error=np.array(table.get_column(error_names[index]))
        if re.search('bar',history_plot_options["error_style"],re.IGNORECASE):
            ax.errorbar(x,y,yerr=error,fmt='k--')

            for date_index,date in enumerate(unique_analysis_dates[history_plot_options["min_num"]:history_plot_options["max_num"]]):
                number_lines=len(unique_analysis_dates[history_plot_options["min_num"]:history_plot_options["max_num"]])
                date_device_history=device_history[device_history["Analysis_Date"]==date]
                if not date_device_history.empty:
                    x_date=date_device_history['Frequency']
                    y_date=np.array(date_device_history[column_names[index]].tolist())
                    error_date=np.array(date_device_history[error_names[index]].tolist())
                    #print("{0} is {1}".format("date_device_history",date_device_history))
                    #print("{0} is {1}".format("y_date",y_date))
                    #print("{0} is {1}".format("date",date))
                    date_color=(1-float(date_index+1)/number_lines,0,float(date_index+1)/number_lines,.5)
                    ax.errorbar(x_date,y_date,
                         yerr=error_date,color=date_color,label=date)
        elif re.search('area',history_plot_options["error_style"],re.IGNORECASE):
            ax.plot(x,y,'k--')
            ax.fill_between(x,y-error,y+error,edgecolor=(0,.0,.0,.25), facecolor=(.25,.25,.25,.1),
                            linewidth=1)
            for date_index,date in enumerate(unique_analysis_dates[history_plot_options["min_num"]:history_plot_options["max_num"]]):
                number_lines=float(len(unique_analysis_dates[history_plot_options["min_num"]:history_plot_options["max_num"]]))
                #print("{0} is {1}".format("number_lines",number_lines))
                #print("{0} is {1}".format("index",index))
                #print("{0} is {1}".format("date_index",date_index))
                date_color=(1-float(date_index+1)/number_lines,0,float(date_index+1)/number_lines,.5)
                #print("{0} is {1}".format("date_color",date_color))

                date_device_history=device_history[device_history["Analysis_Date"]==date]
                x_date=date_device_history['Frequency']
                y_date=np.array(date_device_history[column_names[index]].tolist())
                error_date=np.array(date_device_history[error_names[index]].tolist())


                ax.plot(x_date,y_date,
                        color=date_color,label=date)
        #ax.sharex(diff_axes[index])
        if history_plot_options["display_legend"]:
            ax.legend(loc=1,fontsize='8')
    compare_axes.flat[-2].set_xlabel('Frequency(GHz)',color='k')
    compare_axes.flat[-1].set_xlabel('Frequency(GHz)',color='k')
    fig.subplots_adjust(hspace=0)
    fig.suptitle(calrep_model.metadata["Device_Id"]+"\n",fontsize=18,fontweight='bold')
    plt.tight_layout()

    # Dealing with the save option
    if history_plot_options["file_name"] is None:
        file_name=auto_name(specific_descriptor=history_plot_options["specific_descriptor"],
                            general_descriptor=history_plot_options["general_descriptor"],
                            directory=history_plot_options["directory"],extension='png',padding=3)
    else:
        file_name=history_plot_options["file_name"]
    if history_plot_options["save_plot"]:
        #print file_name
        plt.savefig(os.path.join(history_plot_options["directory"],file_name))
    else:
        plt.show()

def compare_s2p_plots(list_S2PV1,**options):
    """compare_s2p_plot compares a list of s2p files plotting each on the same axis for all
    8 possible components. The format of plots can be changed by passing options as key words in a
    key word dictionary. """
    defaults={"format":"MA",
              "display_legend":True,
              "save_plot":False,
              "directory":None,
              "specific_descriptor":"Comparision_Plot",
              "general_descriptor":"Plot",
              "file_name":None,
              "labels":None}
    comparision_plot_options={}
    for key,value in defaults.iteritems():
        comparision_plot_options[key]=value
    for key,value in options.iteritems():
        comparision_plot_options[key]=value

    # create a set of 8 subplots
    fig, compare_axes = plt.subplots(nrows=4, ncols=2, figsize=(8,6),dpi=80)
    if comparision_plot_options["labels"] is None:
        labels=[s2p.path for s2p in list_S2PV1]
    else:
        labels=comparision_plot_options["labels"]
    for s2p_index,s2p in enumerate(list_S2PV1):
        # start by changing the format of all the s2p
        s2p.change_data_format(comparision_plot_options["format"])
        column_names=s2p.column_names[1:]
        for index, ax in enumerate(compare_axes.flat):
            #ax.xaxis.set_visible(False)
            if re.search('arg',column_names[index]):
                ax.set_ylabel('Phase(Degrees)',color='green')
            elif re.search('mag',column_names[index]):
                ax.set_ylabel(r'|${\Gamma} $|',color='green')
            ax.set_title(column_names[index])
            # initial plot of
            x=s2p.get_column('Frequency')
            y=np.array(s2p.get_column(column_names[index]))
            ax.plot(x,y,label=labels[s2p_index])
            if comparision_plot_options["display_legend"]:
                ax.legend(loc=1,fontsize='8')

    compare_axes.flat[-2].set_xlabel('Frequency(GHz)',color='k')
    compare_axes.flat[-1].set_xlabel('Frequency(GHz)',color='k')
    fig.subplots_adjust(hspace=0)
    plt.tight_layout()
    # Dealing with the save option
    if comparision_plot_options["file_name"] is None:
        file_name=auto_name(specific_descriptor=comparision_plot_options["specific_descriptor"],
                            general_descriptor=comparision_plot_options["general_descriptor"],
                            directory=comparision_plot_options["directory"]
                            ,extension='png',padding=3)
    else:
        file_name=comparision_plot_options["file_name"]
    if comparision_plot_options["save_plot"]:
        #print file_name
        plt.savefig(os.path.join(comparision_plot_options["directory"],file_name))
    else:
        plt.show()
#-----------------------------------------------------------------------------
# Module Classes

#-----------------------------------------------------------------------------
# Module Scripts
def test_average_one_port_sparameters():
    os.chdir(TESTS_DIRECTORY)
    table_list=[OnePortRawModel('OnePortRawTestFileAsConverted.txt') for i in range(3)]
    out_data=average_one_port_sparameters(table_list)
    out_table=OnePortRawModel(None,**{"data":out_data})
    #table_list[0].show()
    #out_table.show()
    fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
    ax0.plot(out_table.get_column('Frequency'),out_table.get_column('magS11'),'k--')
    ax0.plot(table_list[0].get_column('Frequency'),table_list[0].get_column('magS11'),'bx')
    ax0.set_title('Magnitude S11')
    ax1.plot(out_table.get_column('Frequency'),out_table.get_column('argS11'),'ro')
    ax1.plot(table_list[0].get_column('Frequency'),table_list[0].get_column('argS11'),'bx')
    ax1.set_title('Phase S11')
    plt.show()
    print out_table

def test_comparison(input_file=None):
    """test_comparision tests the raw_mean,difference and comparison plot functionality"""
    # Data sources, to be replaced as project_files in Django
    # Todo: These are not robust tests fix them?
    TWO_PORT_NR_CHKSTD_CSV=r"C:\Share\Converted_Check_Standard\Two_Port_NR_Check_Standard.csv"
    COMBINED_ONE_PORT_CHKSTD_CSV=r"C:\Share\Converted_Check_Standard\Combined_One_Port_Check_Standard.csv"
    COMBINED_TWO_PORT_CHKSTD_CSV=r"C:\Share\Converted_Check_Standard\Combined_Two_Port_Check_Standard.csv"
    COMBINED_POWER_CHKSTD_CSV=r"C:\Share\Converted_Check_Standard\Combined_Power_Check_Standard.csv"
    ONE_PORT_CALREP_CSV=r"C:\Share\Converted_DUT\One_Port_DUT.csv"
    TWO_PORT_CALREP_CSV=r"C:\Share\Converted_DUT\Two_Port_DUT.csv"
    POWER_3TERM_CALREP_CSV=r"C:\Share\Converted_DUT\Power_3Term_DUT.csv"
    POWER_4TERM_CALREP_CSV=r"C:\Share\Converted_DUT\Power_4Term_DUT.csv"
    history_dict={'1-port':pandas.read_csv(COMBINED_ONE_PORT_CHKSTD_CSV),
         '2-port':pandas.read_csv(COMBINED_TWO_PORT_CHKSTD_CSV),
         '2-portNR':pandas.read_csv(TWO_PORT_NR_CHKSTD_CSV),'power':pandas.read_csv(COMBINED_POWER_CHKSTD_CSV)}
    if input_file is None:
        #input_file=r"C:\Share\Ck_Std_raw_ascii\C07207.D1_030298"
        input_file=r"C:\Share\Ck_Std_raw_ascii\C07207.D9_042500"
        #input_file=r"C:\Share\Ck_Std_raw_ascii\C07208.A10_081507"
        #input_file=r"C:\Share\Ck_Std_raw_ascii\CTNP20.R1_032310"
        #input_file=r"C:\Share\Ck_Std_raw_ascii\CN49.K2_050608"
        #input_file=r"C:\Share\Ck_Std_raw_ascii\C22P13.H4_043015"
        #input_file=r"C:\Share\Ck_Std_raw_ascii\C24N07.L1_070998"
        #input_file=r"C:\Share\Ck_Std_raw_ascii\CTN208.A1_011613"
    start_time=datetime.datetime.now()
    file_model=sparameter_power_type(input_file)
    model=globals()[file_model]
    table=model(input_file)
    #print table
    #table.metadata["System_Id"]
    options={"Device_Id":table.metadata["Device_Id"], "System_Id":table.metadata["System_Id"],"Measurement_Timestamp":None,
                  "Connector_Type_Measurement":table.metadata["Connector_Type_Measurement"],
                 "Measurement_Date":None,"Measurement_Time":None}
    if re.search('2-port',table.metadata["Measurement_Type"],re.IGNORECASE) and not re.search('2-portNR',table.metadata["Measurement_Type"],re.IGNORECASE):
        history_key='2-port'
        options["column_names"]=['Frequency','magS11','argS11','magS21','argS21','magS22','argS22']
    elif re.search('2-portNR',table.metadata["Measurement_Type"],re.IGNORECASE):
        history_key='2-portNR'
        options["column_names"]=['Frequency','magS11','argS11','magS12','argS12','magS21','argS21','magS22','argS22']
    elif re.search('1-port',table.metadata["Measurement_Type"],re.IGNORECASE):
        history_key='1-port'
        if COMBINE_S11_S22:
             options["column_names"]=['Frequency','mag','arg']
        else:
            options["column_names"]=['Frequency','magS11','argS11','magS22','argS22']
    elif re.search('Dry Cal|Thermistor|power',table.metadata["Measurement_Type"],re.IGNORECASE):
        history_key='power'
        options["column_names"]=['Frequency','magS11','argS11','Efficiency','Calibration_Factor']
    #print history[history_key][:5]
    print history_key
    mean_frame=mean_from_history(history_dict[history_key].copy(),**options)
    #print mean_frame
    difference_frame=raw_difference_frame(table,mean_frame)
    #print difference_frame
    stop_time=datetime.datetime.now()
    plot_options={"display_difference":False,"display_mean":True,"display_raw":True,"display_legend":False}
    raw_comparision_plot_with_residuals(table,mean_frame,difference_frame,**plot_options)
    #stop_time=datetime.datetime.now()
    diff=stop_time-start_time
    print("It took {0} seconds to process".format(diff.total_seconds()))

def test_compare_s2p_plots(file_list=["thru.s2p",'20160301_30ft_cable_0.s2p','TwoPortTouchstoneTestFile.s2p']):
    """Tests the compare_s2p_plots function"""
    os.chdir(TESTS_DIRECTORY)
    tables=[S2PV1(file_name) for file_name in file_list]
    format="MA"
    compare_s2p_plots(tables,format=format)
    format="DB"
    compare_s2p_plots(tables,format=format,display_legend=False)
#-----------------------------------------------------------------------------
# Module Runner
if __name__ == '__main__':
    #test_average_one_port_sparameters()
    #test_comparison()
    test_compare_s2p_plots()