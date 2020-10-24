#
# Helper functions related to c++ code generation
#


import textwrap as tw



def tabs(N):
    t = ''
    for i in range(0,N):
        t += '  '
    
    return t


def indent(lines):

    return tw.indent(lines, '  ')



#
#
#


# rename to signal_list_to_name_list
def signal_list_to_name_list(signals):
    names = []

    for s in signals:
        names.append( s.name )

    return names


# TODO: rename to comma_separated_names_string
def signal_list_to_names_string(signals):
    return ', '.join( signal_list_to_name_list(signals)  )





#
#
#


def signalListHelper_typeNames(signals):
    typeNames = []

    for s in signals:
        typeNames.append( s.getDatatype().cppDataType )

    return typeNames


def signalListHelper_types(signals):
    types = []

    for s in signals:
        types.append( s.getDatatype() )

    return types



#
#
#


def defineVariable( signal, make_a_reference = False ):
    """
        create a sting containing e.g.

        'double signalName'
    """

    return signal.getDatatype().cpp_define_variable( signal.name, make_a_reference )



# rename to signalListHelper_CppVarDefStr --> define_variable_list
def define_variable_list(signals, make_a_reference = False):
    vardefStr = []  # e.g. double y

    for s in signals:
        # e.g.: double y;
        vardefStr.append( defineVariable(s, make_a_reference)  )

    return vardefStr

def defineVariables( signals, make_a_reference = False ):
    """
        create a string containing e.g.

        'double signalName1;\n
         double signalName2;\n'
    """
    elements = define_variable_list(signals, make_a_reference )

    return ';\n'.join( elements ) + ';\n'






def asign( from_signal_name, to_signal_name ):
    """
        generate code to asign a value

        - from_signal_name
        - to_signal_name
    """
    return to_signal_name + ' = ' + from_signal_name + ';\n'

def define_variable_list_string(signals, make_a_reference = False):
    return '; '.join( define_variable_list(signals, make_a_reference)  ) + ';'



def generate_compare_equality_to_constant( language, signal_name, constant ):
    return signal_name + ' == ' + str(constant)






def defineVariableLine( signal, make_a_reference = False ):
    """
        create a sting containing e.g.

        'double signalName;\n'
    """
    element = define_variable_list([signal], make_a_reference )

    return element[0] + ';\n'

#
#
#

def signalListHelper_printfPattern(signals):
    printfPatterns = [] 

    for s in signals:

        # e.g. %f
        printfPatterns.append( s.getDatatype().cppPrintfPattern )
    
    return printfPatterns

def signalListHelper_printfPattern_string(signals):
    return ' '.join( signalListHelper_printfPattern(signals) )



#
#
#

def defineStructVar( structName, structVarname ):
    return structName + ' ' + structVarname + ';\n'

def fillStruct( structName, structVarname, signals ):

    lines = ''

    lines += defineStructVar( structName, structVarname )


    for s in signals:
        lines += structVarname + '.' + s.name + ' = ' + s.name + ';\n'

    return lines

def getStructElements( structVarname, signals ):
    # get list of e.g. 'outputs.y1', 'outputs.y2'

    structElements = []

    for s in signals:
        structElements.append( structVarname + '.' + s.name  )

    return structElements



def brackets(code):
    return '{\n' + indent(code) + '\n}\n'

def brackets_no_newline(code):
    return '{\n' + indent(code) + '\n}'

#
# control flow
#
def generate_if_else(language, condition_list, action_list):

    N = len(condition_list)

    lines = 'if (' + condition_list[0] + ') {\n' + indent( action_list[0] )


    if len(action_list) == 1:
        lines += '\n}\n'

        return lines

    else:

        for i in range(1, N):
            lines += '\n} else if (' + condition_list[i] + ') {\n' + indent( action_list[i] )


    if len(action_list) == N + 1:
        lines += '\n} else {\n' + indent( action_list[ N ] ) + '\n}\n'

    elif len(action_list) == N:
        lines += '\n}\n'

    else:
        raise BaseException("missmatch of the number of actions and conditions")

    return lines





def generate_loop_break(language, condition, code_before_break = None):
    """
        break a loop (to be used with generate_loop)

        condition  - the condition to break the loop
    """
    code_to_run = ''
    if code_before_break is not None:
        code_to_run += code_before_break + '\n'

    code_to_run += 'break;'

    abort_code = generate_if_else(language, condition_list=[condition], action_list=[ code_to_run ])

    return abort_code


def generate_loop( language, max_iterations, code_to_exec  ):
    """
        generate a loop

        - max_iterations - the maximal number of loop iterations
        - code_to_exec   - the code to execute in the loop
    """

    lines = 'for (int i = 0; i < ' + max_iterations + '; ++i) ' + brackets_no_newline( code_to_exec ) + ';\n'
    return lines


def embed_subsystem(language, system_prototype, ouput_signals_name=None, calculate_outputs = True, update_states = False ):
    """  
        generate code to call a subsystem (TODO: this is obsolete remove it!)

        - system_prototype   - the block prototype including the subsystem - type: : dy.GenericSubsystem
        - ouput_signals_name - list of variable names to which the output signals of the subsystem are assigned to
        - calculate_outputs  - generate a call to the output computation API function of the subsystem
        - update_states      - generate a call to the state update API function of the subsystem
    """


    lines = '{ // subsystem ' + system_prototype.embedded_subsystem.name + '\n'

    innerLines = ''

    #
    # system_prototype is of type GenericSubsystem. call the code generation routine of the subsystem
    #

    # generate code for calculating the outputs 
    if calculate_outputs:

        innerLines += system_prototype.generate_code_output_list(language, system_prototype.outputs)

        if len(system_prototype.outputs) != len(ouput_signals_name):
            raise BaseException('len(system_prototype.outputs) != len(ouput_signals_name)')

        for i in range( 0, len( ouput_signals_name ) ):
            innerLines += asign( system_prototype.outputs[i].name, ouput_signals_name[i] )

    # generate code for updating the states
    if update_states:
        innerLines += system_prototype.generate_code_update(language)


    lines += indent(innerLines)
    lines += '}\n'

    return lines





def embed_subsystem2(language, system_prototype, ouput_signals_name=None, ouput_signal_names_of_subsystem=None, calculate_outputs = True, update_states = False ):
    """  
        generate code to call a subsystem

        - system_prototype   - the block prototype including the subsystem - type: : dy.GenericSubsystem
        - ouput_signals_name - list of variable names to which the output signals of the subsystem are assigned to
        
        - ouput_signal_names_of_subsystem - ....

        - calculate_outputs  - generate a call to the output computation API function of the subsystem
        - update_states      - generate a call to the state update API function of the subsystem
    """


    lines = '{ // subsystem ' + system_prototype.embedded_subsystem.name + '\n'

    innerLines = ''

    #
    # system_prototype is of type GenericSubsystem. call the code generation routine of the subsystem
    #

    # generate code for calculating the outputs 
    if calculate_outputs:

        innerLines += system_prototype.generate_code_output_list(language, system_prototype.outputs)

        if len(ouput_signal_names_of_subsystem) != len(ouput_signals_name):
            raise BaseException('len(ouput_signal_names_of_subsystem) != len(ouput_signals_name)')

        for i in range( 0, len( ouput_signals_name ) ):
            innerLines += asign( ouput_signal_names_of_subsystem[i], ouput_signals_name[i] )

    # generate code for updating the states
    if update_states:
        innerLines += system_prototype.generate_code_update(language)


    lines += indent(innerLines)
    lines += '}\n'

    return lines





def cpp_define_function(fn_name, input_signals, output_signals, code):
    """
        generate code for a c++ function using in- and output signals
    """
    lines = ''
    lines += 'void ' + fn_name + '('

    # put the parameter list e.g. double & y1, double & y2, u1, u2
    elements = []
    # for s in output_signals:
    #     elements.append( s.getDatatype().cpp_define_variable( s.name, make_a_reference=True ) )
        
    elements.extend( define_variable_list( output_signals, make_a_reference=True ) )
    elements.extend( define_variable_list( input_signals ) )

    lines += ', '.join(elements)
    lines +=  ') { // created by cpp_define_function\n'

    # inner code to call
    lines += indent(code)

    lines += '}\n'

    return lines


def cpp_define_function_from_types(fn_name, input_types, input_names, output_types, output_names, code):
    """
        generate code for a c++ function using types and names for the in- and outputs
    """
    lines = ''
    lines += 'void ' + fn_name + '('

    # put the parameter list e.g. double & y1, double & y2, u1, u2
    elements = []

    for i in range(0, len(output_types)):
        elements.append( output_types[i].cpp_define_variable( output_names[i], make_a_reference=True ) )
        
    for i in range(0, len(input_types)):
        elements.append( input_types[i].cpp_define_variable( input_names[i], make_a_reference=True ) )


    lines += ', '.join(elements)
    lines +=  ') {\n'

    # inner code to call
    lines += indent(code)

    lines += '\n}\n'

    return lines

def call_function_from_varnames(fn_name, input_names, output_names):

    lines = ''
    lines += fn_name + '(' + ', '.join(output_names) + ', ' + ', '.join(input_names) + ');\n'

    return lines


