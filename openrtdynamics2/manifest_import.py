



def get_all_inputs( manifest, only_inputs_with_default_values = True ):
    """
        return a key-value struct containing all inputs which have a default value
    """
    ret = {}

    manifest_in_o = manifest['io']['inputs']['calculate_output']
    manifest_in_u = manifest['io']['inputs']['state_update']

    def fill_in(manifest_in):

        for i in range(len(manifest_in['names'])):

            # introduce new struct
            s = {}

            k = manifest_in['names'][i]

            s['cpptype'] =  manifest_in['cpptypes'][i]

            if 'properties' in manifest_in:
    
                properties = manifest_in['properties'][i]
                s['properties']    = properties

                if not 'default_value' in properties and only_inputs_with_default_values:
                    break

            # fill in struct
            ret[k] = s

    fill_in(manifest_in=manifest_in_o)
    fill_in(manifest_in=manifest_in_u)

    return ret
