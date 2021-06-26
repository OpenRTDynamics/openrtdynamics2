from prettytable import PrettyTable


# TODO: rename to 'get_inputs'
def get_all_inputs( 
        manifest, 
        only_inputs_with_default_values    = False, 
        return_inputs_to_update_states     = True,
        return_inputs_to_calculate_outputs = True,
        return_inputs_to_reset_states      = True
    ):
    """
        Return a key-value structure containing the inputs that are needed to run
        the system the manifest is referring to.

        Please note, that some inputs that are defined might not appear in
        in case they are not used or needed in the system.
        The list manifest['io']['all_inputs_by_port_number'] contains the full
        list of system inputs.
    """
    ret = {}


    def fill_in(ports):

        for i in range(len(ports['names'])):

            # introduce new structure
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

            # fill in structure
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

# TODO: rename to 'get_outputs'
def get_all_outputs(
        manifest,
        return_inputs_to_update_states     = True,
        return_inputs_to_calculate_outputs = True,
        return_inputs_to_reset_states      = True
    ):
    """
        return a key-value structure containing the system outputs
    """
    ret = {}


    def fill_in(ports):

        for i in range(len(ports['names'])):

            # introduce new structure
            s = {}

            k = ports['names'][i]

            s['cpptype']        =  ports['cpptypes'][i]
            s['printf_pattern'] =  ports['printf_patterns'][i]
            s['port_number']    =  ports['port_numbers'][i]

            if 'properties' in ports:
                properties         = ports['properties'][i]
                s['properties']    = properties

            # fill in structure
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



def show_inputs(manifest, show_description = True, do_not_print = False):
    """
        Print a table containing all input signals as required by the simulator functions
        of the implemented system.

        manifest     - the exported manifest
        do_not_print - in case of True, the a string containing the table is returned 
    """

    s_o_1 = manifest['io']['inputs']['calculate_output']['port_numbers']
    s_u   = manifest['io']['inputs']['state_update']['port_numbers']
    s_r   = manifest['io']['inputs']['reset']['port_numbers']

    all_signals = manifest['io']['all_inputs_by_port_number']

    table_rows = []
    index = 0
    for k in all_signals:

        o_1, u, r = '', '', ''

        if index in s_o_1:
            o_1 = 'X'

        if index in s_u:
            u = 'X'

        if index in s_r:
            r = 'X'

        row = [ index, k['name'], o_1, u, r, k['cpptype'] ]
        if show_description:
            if 'properties' in k:
                if 'title' in k['properties']:
                    row.append( k['properties']['title'] )

        table_rows.append(row)
        
        index += 1


    x = PrettyTable()
    field_names = ["#port", "input signal,  to -->", "outputs", "update", "reset", "datatype (c++)"]
    
    if show_description:
        field_names.append("description")
        
    x.field_names = field_names

    if show_description:
        x.align["description"] = "l"

    x.add_rows(table_rows)

    if not do_not_print:
        print(x)
        return
    
    return x.get_string()
    


def show_outputs(manifest, show_description = False, do_not_print = False):
    """
        Print a table containing all output signals

        manifest     - the exported manifest
        do_not_print - in case of True, the a string containing the table is returned 
    """

    outputs = manifest['io']['outputs']['calculate_output']
    
    n_outputs = len(outputs['names'])

    table_rows = []

    for index in range(0, n_outputs):

        row = [ index, outputs['names'][index], outputs['cpptypes'][index] ]
        
        if show_description:
                if 'title' in outputs['properties']:
                    row.append( outputs['properties']['title'] )

        table_rows.append(row)
        
        index += 1


    x = PrettyTable()
    field_names = ["#port", "input signal", "datatype (c++)"]
    
    if show_description:
        field_names.append("description")
        
    x.field_names = field_names

    if show_description:
        x.align["description"] = "l"

    x.add_rows(table_rows)

    if not do_not_print:
        print(x)
        return
    
    return x.get_string()
    