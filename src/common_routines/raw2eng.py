import re
def raw2eng(par_data, calibration, product_type, dyn):
    for key, par in par_data.items():
        name_text = par['name']['Text']
        if product_type == 'sc' and name_text == 'TIME_UTC':
            par['data'] = [value  for value in par['data']]
        if product_type == 'sc' and name_text == 'TIME_OBT':
            par['data'] = [value  for value in par['data']]
        if product_type == 'sc' and name_text in ['MAX_POS_ACC_X_HAA_URF_DIRECTED', 'MAX_POS_ACC_Y_HAA_URF_DIRECTED', 'MAX_POS_ACC_Z_HAA_URF_DIRECTED']:
            par['data'] = [value  for value in par['data']]   #TBD (Chiedere a Max!!)
        if product_type == 'sc' and name_text in ['TEMP_X_HAA_URF_DIRECTED', 'TEMP_Y_HAA_URF_DIRECTED', 'TEMP_Z_HAA_URF_DIRECTED']:
            masstring = str(calibration['ICE']['channel_Mapping']['data'])
            mass = re.search('_([XYZ])_', name_text).group(1)
            par['data'] = [value * calibration[f'Acc{mass}']['temp_a']['data'] + calibration[f'Acc{mass}']['temp_offset']['data'] for value in par['data']]

        if product_type == 'sc' and name_text in ['ACC_X_HAA_URF_DIRECTED', 'ACC_Y_HAA_URF_DIRECTED', 'ACC_Z_HAA_URF_DIRECTED']:
            masstring = str(calibration['ICE']['channel_Mapping']['data'])
            mass = re.search('_([XYZ])_', name_text).group(1)
            acc = par['data']

#### TBC ####

        if product_type == 'sc_hr' and name_text == 'TIME_UTC':
            par['data'] = [value  for value in par['data']]
        if product_type == 'sc_hr' and name_text == 'TIME_OBT':
            par['data'] = [value  for value in par['data']]
        if product_type == 'sc_hr' and name_text == 'ACC_ACQUIRED':
            par['data'] = [value  for value in par['data']]
        if product_type == 'sc_hr' and name_text in ['POS']:
            axes = [str(a) for a in par_data['ACC_ACQUIRED']['data']]
            print("DEBUG calibration keys:", [calibration[f'Acc{axis.lower()}']['alpha']['data'] for axis in axes])            
            par['data'] = [
                value
                * calibration[f'Acc{axis.lower()}']['alpha']['data']
                * calibration['HR']['alpha']['data']
                for value, axis in zip(par['data'], axes)
            ]
            print(par['data'])
        if product_type == 'sc_hr' and name_text == 'INTERPOLATED':
            par['data'] = [value  for value in par['data']]
#### TBC ####
        
        if product_type == 'sc':
            par['data'] = [value  for value in par['data']]
        """
        if len(*args) > 0 and name_text in ['ACC_X_HAA_URF_DIRECTED', 'ACC_Y_HAA_URF_DIRECTED', 'ACC_Z_HAA_URF_DIRECTED']:
            if 'nominal' in args:
                par['data'] = [value * calibration[f'Acc{mass}']['alpha']['data']/10 for value in par['data']]
            elif 'extended' in args:
                par['data'] = [value * calibration[f'Acc{mass}']['alpha']['data']for value in par['data']]
            else:
                par['data'] = [value * calibration[f'Acc{mass}']['alpha']['data'] for value in par['data']]
        """
        if name_text in ['ACC_X_HAA_URF_DIRECTED', 'ACC_Y_HAA_URF_DIRECTED', 'ACC_Z_HAA_URF_DIRECTED']:        
            par['data'] = [value * calibration[f'Acc{mass}']['alpha']['data'] / int(dyn[i]) for i, value in enumerate(par['data'])]

        if product_type == 'hk' and name_text in ['TEMP_ACC_0', 'TEMP_ACC_1', 'TEMP_ACC_2', 'TEMP_FEE']:
            par['data'] = [value / 100 for value in par['data']]
        if product_type == 'hk' and name_text =='PWR_TEMP':
            par['data'] = [((calibration['PWR_TEMP']['Polynomia']['P_N1']['data'] * value + calibration['PWR_TEMP']['Polynomia']['P_N2']['data']) * value + calibration['PWR_TEMP']['Polynomia']['P_N3']['data']) * value + calibration['PWR_TEMP']['Polynomia']['P_N4']['data'] for value in par['data']]
        if product_type == 'hk' and name_text in ['DELTA_TEMP_FEE', 'DELTA_TEMP_ACC_0', 'DELTA_TEMP_ACC_1', 'DELTA_TEMP_ACC_2']:
            par['data'] = [value / 10 for value in par['data']]
        if product_type == 'hk'and name_text == 'TEMP_IDA_FEE_HOTSPOT':
            par['data'] = [value**3 * calibration['TEMP_IDA_FEE_HOTSPOT_poli']['Polynomia']['P_N1']['data'] + \
                           value**2 * calibration['TEMP_IDA_FEE_HOTSPOT_poli']['Polynomia']['P_N2']['data'] + \
                           value    * calibration['TEMP_IDA_FEE_HOTSPOT_poli']['Polynomia']['P_N3']['data'] + \
                                      calibration['TEMP_IDA_FEE_HOTSPOT_poli']['Polynomia']['P_N4']['data'] for value in par['data']]
        if product_type == 'hk'and name_text == 'TEMP_IDA_FEE_DIGITAL':
            par['data'] = [value**3 * calibration['TEMP_IDA_FEE_DIGITAL_poli']['Polynomia']['P_N1']['data'] + \
                           value**2 * calibration['TEMP_IDA_FEE_DIGITAL_poli']['Polynomia']['P_N2']['data'] + \
                           value    * calibration['TEMP_IDA_FEE_DIGITAL_poli']['Polynomia']['P_N3']['data'] + \
                                      calibration['TEMP_IDA_FEE_DIGITAL_poli']['Polynomia']['P_N4']['data'] for value in par['data']]
        if product_type == 'hk'and name_text == 'TEMP_IDA_BOUNDARY':
            par['data'] = [value**3 * calibration['TEMP_IDA_BOUNDARY_poli']['Polynomia']['P_N1']['data'] + \
                           value**2 * calibration['TEMP_IDA_BOUNDARY_poli']['Polynomia']['P_N2']['data'] + \
                           value    * calibration['TEMP_IDA_BOUNDARY_poli']['Polynomia']['P_N3']['data'] + \
                                      calibration['TEMP_IDA_BOUNDARY_poli']['Polynomia']['P_N4']['data'] for value in par['data']]                              

        if product_type == 'hk' and name_text == 'TR_FEE':
            par['name']['Text'] = 'TEMP_REACH_FEE'
        if product_type == 'hk' and name_text == 'TEMP_REACH_ACC0':
            par['name']['Text'] = 'TEMP_REACH_ACC0'
        if product_type == 'hk' and name_text == 'TEMP_REACH_ACC1':
            par['name']['Text'] = 'TEMP_REACH_ACC1'
        if product_type == 'hk' and name_text == 'TEMP_REACH_ACC2':
            par['name']['Text'] = 'TEMP_REACH_ACC2'
        if product_type == 'hk' and name_text == 'HEAT_STAT_FEE':
            par['name']['Text'] = 'HEAT_STAT_FEE'
        if product_type == 'hk' and name_text == 'HEAT_STAT_ACC0':
            par['name']['Text'] = 'HEAT_STAT_ACC0'
        if product_type == 'hk' and name_text == 'HEAT_STAT_ACC1':
            par['name']['Text'] = 'HEAT_STAT_ACC1'
        if product_type == 'hk' and name_text == 'HEAT_STAT_ACC2':
            par['name']['Text'] = 'HEAT_STAT_ACC2'            
        if product_type == 'hk' and name_text in ['HEAT_CURR_ACC0', 'HEAT_CURR_ACC1', 'HEAT_CURR_ACC2']:     #Miss the calibration coeff.
            masstring = str(calibration['ICE']['channel_Mapping']['data'])
            mass = masstring[int(name_text[-1])]
            par['data'] = [value * calibration[f'Acc{mass}']['heater_current']['data'] for value in par['data']]  
            par['name']['Text'] = f'HEAT_POWER_ACC{mass}'
        if product_type == 'hk' and name_text == 'HEAT_CURR_FEE':                                            
            par['data'] = [value**4 * calibration['FEE']['heater_current5']['data']+value**3 * calibration['FEE']['heater_current4']['data']+value**2 * calibration['FEE']['heater_current3']['data']+value * calibration['FEE']['heater_current2']['data']+ calibration['FEE']['heater_current1']['data'] for value in par['data']]
            par['name']['Text'] = 'HEAT_POWER_FEE'
        if product_type == 'hk'and name_text == 'PRIM_CURR':
            par['data'] = [value * calibration['ICE']['supplyCurr']['data']+ calibration['ICE']['supplyCurr_offset']['data'] for value in par['data']]
        if product_type == 'hk' and name_text == 'MODE':
            par['data'] = opModeTran(par['data'])
        if product_type == 'hk' and name_text == 'LOW_RATE':
            r = ['2.5','10']
            par['data'] = [r[value + 1] for value in par['data']]
        if product_type == 'hk' and name_text == 'ICE_140V':
            par['data'] = [value * calibration['ICE']['highVolt_bus']['data']+calibration['ICE']['highVolt_bus_offset']['data'] for value in par['data']]
        if product_type == 'hk' and name_text == 'ICE_3V':
            par['data'] = [value * calibration['ICE']['lowVolt_bus']['data']+calibration['ICE']['lowVolt_bus_offset']['data'] for value in par['data']]
    return par_data

def opModeTran(hex_op_mode):
    operative_modes = []
    for hex_value in hex_op_mode:
        op = ''
        if hex_value == 1:
            op = 'S/C Assisted Calibration'
        elif hex_value == 2:
            op = 'Chain Calibration'
        elif hex_value == 4:
            op = 'Self Calibration'
        elif hex_value == 8:
            op = 'High Rate Observation'
        elif hex_value == 16:
            op = 'Observation'
        elif hex_value == 32:
            op = 'Configuration'
        elif hex_value == 64:
            op = 'Stand-By'
        elif hex_value == 128:
            op = 'Safe'
        elif hex_value == 256:
            op = 'Diagnostic'
        elif hex_value == 512:
            op = 'Maintenance'
        elif hex_value == 1024:
            op = 'Boot'
        else:
            op = 'NA'
        operative_modes.append(op)
    return operative_modes




    
