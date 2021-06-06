



def get_all_inputs( 
        manifest, 
        only_inputs_with_default_values    = True, 
        return_inputs_to_update_states     = True,
        return_inputs_to_calculate_outputs = True,
        return_inputs_to_reset_states      = True
    ):
    """
        return a key-value struct containing all inputs
    """
    ret = {}


    def fill_in(manifest_in):

        for i in range(len(manifest_in['names'])):

            # introduce new struct
            s = {}

            k = manifest_in['names'][i]

            s['cpptype'] =  manifest_in['cpptypes'][i]
            s['printf_pattern'] =  manifest_in['printf_patterns'][i]

            if 'properties' in manifest_in:
    
                properties = manifest_in['properties'][i]
                s['properties']    = properties

                if not 'default_value' in properties and only_inputs_with_default_values:
                    break

            # fill in struct
            ret[k] = s

    if return_inputs_to_calculate_outputs:
        manifest_in_o = manifest['io']['inputs']['calculate_output']
        fill_in(manifest_in=manifest_in_o)
    
    if return_inputs_to_update_states:
        manifest_in_u = manifest['io']['inputs']['state_update']
        fill_in(manifest_in=manifest_in_u)

    if return_inputs_to_reset_states:
        manifest_in_r = manifest['io']['inputs']['reset']
        fill_in(manifest_in=manifest_in_r)

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


    def fill_in(manifest_in):

        for i in range(len(manifest_in['names'])):

            # introduce new struct
            s = {}

            k = manifest_in['names'][i]

            s['cpptype'] =  manifest_in['cpptypes'][i]
            s['printf_pattern'] =  manifest_in['printf_patterns'][i]

            if 'properties' in manifest_in:
    
                properties = manifest_in['properties'][i]
                s['properties']    = properties


            # fill in struct
            ret[k] = s

    # fill_in(manifest['io']['outputs']['calculate_output'])

    if return_inputs_to_calculate_outputs:
        manifest_in_o = manifest['io']['outputs']['calculate_output']
        fill_in(manifest_in=manifest_in_o)
    
    if return_inputs_to_update_states:
        manifest_in_u = manifest['io']['outputs']['state_update']
        fill_in(manifest_in=manifest_in_u)

    if return_inputs_to_reset_states:
        manifest_in_r = manifest['io']['outputs']['reset']
        fill_in(manifest_in=manifest_in_r)

    return ret
