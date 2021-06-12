



def get_all_inputs( 
        manifest, 
        only_inputs_with_default_values    = False, 
        return_inputs_to_update_states     = True,
        return_inputs_to_calculate_outputs = True,
        return_inputs_to_reset_states      = True
    ):
    """
        return a key-value struct containing all inputs
    """
    ret = {}


    def fill_in(ports):

        for i in range(len(ports['names'])):

            # introduce new struct
            s = {}

            k = ports['names'][i]

            s['cpptype']        =  ports['cpptypes'][i]
            s['printf_pattern'] =  ports['printf_patterns'][i]
            s['port_number']    =  ports['port_numbers'][i]

            if 'properties' in ports:
    
                properties         = ports['properties'][i]
                s['properties']    = properties

                if not 'default_value' in properties and only_inputs_with_default_values:
                    break

            # fill in struct
            ret[k] = s

    if return_inputs_to_calculate_outputs:
        manifest_in_o = manifest['io']['inputs']['calculate_output']
        fill_in(ports=manifest_in_o)
    
    if return_inputs_to_update_states:
        manifest_in_u = manifest['io']['inputs']['state_update']
        fill_in(ports=manifest_in_u)

    if return_inputs_to_reset_states:
        manifest_in_r = manifest['io']['inputs']['reset']
        fill_in(ports=manifest_in_r)

    return ret


def get_all_outputs(
        manifest,
        return_inputs_to_update_states     = True,
        return_inputs_to_calculate_outputs = True,
        return_inputs_to_reset_states      = True
    ):
    """
        return a key-value struct containing all outputs
    """
    ret = {}


    def fill_in(ports):

        for i in range(len(ports['names'])):

            # introduce new struct
            s = {}

            k = ports['names'][i]

            s['cpptype']        =  ports['cpptypes'][i]
            s['printf_pattern'] =  ports['printf_patterns'][i]
            s['port_number']    =  ports['port_numbers'][i]

            if 'properties' in ports:
    
                properties         = ports['properties'][i]
                s['properties']    = properties


            # fill in struct
            ret[k] = s

    if return_inputs_to_calculate_outputs:
        manifest_in_o = manifest['io']['outputs']['calculate_output']
        fill_in(ports=manifest_in_o)
    
    if return_inputs_to_update_states:
        manifest_in_u = manifest['io']['outputs']['state_update']
        fill_in(ports=manifest_in_u)

    if return_inputs_to_reset_states:
        manifest_in_r = manifest['io']['outputs']['reset']
        fill_in(ports=manifest_in_r)

    return ret
