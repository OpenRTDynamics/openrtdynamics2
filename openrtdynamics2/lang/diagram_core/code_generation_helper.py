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
        typeNames.append( s.getDatatype().cpp_datatype_string )

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






def assign( from_signal_name, to_signal_name ):
    """
        generate code to assign a value

        - from_signal_name
        - to_signal_name
    """
    return to_signal_name + ' = ' + from_signal_name + ';\n'

def define_variable_list_string(signals, make_a_reference = False):
    return '; '.join( define_variable_list(signals, make_a_reference)  ) + ';'



def generate_compare_equality_to_constant( language, signal_name, constant ):
    return signal_name + ' == ' + str(constant)


def generate_compare_equality( language, variable_name_1, variable_name_2 ):
    return variable_name_1 + ' == ' + variable_name_2

def generate_and( language, condition1, condition2 ):
    return condition1 + ' && ' + condition2

def define_variable_line( signal, make_a_reference = False ):
    """
        create a string containing e.g.

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
        printfPatterns.append( s.datatype.cpp_printf_pattern )
    
    return printfPatterns

def signalListHelper_printfPattern_string(signals):
    return ' '.join( signalListHelper_printfPattern(signals) )




# brackets
def brackets(code):
    return '{\n' + indent(code) + '\n}\n'

def brackets_no_newline(code):
    return '{\n' + indent(code) + '\n}'



#
#
#


def define_structure( name, signals ):
    """
        define a structure given a name given a list of signals
    """
#    tmp = defineVariables( signals )
#    tmp = indent(tmp, '  ')
#    return f'struct { name }  {{\n{ tmp }}};\n\n'

    return 'struct ' + name + brackets_no_newline( defineVariables( signals )  ) + ';\n'
    

def define_struct_var( structName, structVarname ):
    return structName + ' ' + structVarname + ';\n'

def fillStruct( structName, structVarname, signals ):
    """
        define an instance of a structure and assign values to the elements
    """

    lines = ''

    lines += define_struct_var( structName, structVarname )


    for s in signals:
        lines += structVarname + '.' + s.name + ' = ' + s.name + ';\n'

    return lines

def get_struct_elements( structVarname, signals ):
    # get list of e.g. 'outputs.y1', 'outputs.y2'

    structElements = []

    for s in signals:
        structElements.append( structVarname + '.' + s.name  )

    return structElements

def build_function_arguments_for_signal_io_with_struct(input_signals, output_signals, input_struct_varname, output_struct_varname):

    # build arguments for function call
    if len(output_signals) > 0 or len(input_signals) > 0:

        output_arguments = get_struct_elements( output_struct_varname, output_signals )
        input_arguments = get_struct_elements( input_struct_varname, input_signals )

        arguments_string = ''
        if len(output_arguments) > 0:
            arguments_string += ', '.join( output_arguments )

        if len(output_arguments) > 0 and len(input_arguments) > 0:
            arguments_string += ',   '                    

        if len(input_arguments) > 0:
            arguments_string += ', '.join( input_arguments )

    else:
        arguments_string = ''

    return arguments_string


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


def generate_loop( language, max_iterations, code_to_exec, code_to_exec_on_abort='', counter_variable_name = '_i'  ):
    """
        generate a loop

        - max_iterations        - the maximal number of loop iterations
        - code_to_exec          - the code to execute in the loop
        - code_to_exec_on_abort - the code to exec when the maximal number of iterations is reached
    """


    code_loop = brackets_no_newline( 
        code_to_exec + generate_if_else(
            language, 
            condition_list = [ counter_variable_name+ ' >= ' + str(max_iterations) ] ,
            action_list = [ code_to_exec_on_abort + 'break;' ]
        )
    )

    lines = 'for (int ' +counter_variable_name+ ' = 0; ' + '; ++' +counter_variable_name+ ') ' + code_loop + ';\n'
    return lines




def cpp_define_generic_function(fn_name, return_cpp_type_str, arg_list_str, code):
    """
        generate code for a c++ generic c++ function
    """
    lines = ''
    lines += return_cpp_type_str + ' ' + fn_name + '(' + arg_list_str + ') {\n'

    # inner code to call
    lines += indent(code)

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
    """
    Build c++ code to call a function using the given paramerers 
    """

    lines = ''

    outputs_avail = output_names is not None and len(output_names) != 0
    inputs_avail  = input_names  is not None and len(input_names)  != 0


    lines += fn_name + '(' 
    
    if outputs_avail:  
        output_parameter_string = ', '.join(output_names)
        lines += output_parameter_string  
    
    if outputs_avail and inputs_avail:
        lines +=  ', ' 

    if inputs_avail: 
        input_parameter_string = ', '.join(input_names)
        lines += input_parameter_string 
    
    lines +=  ');\n'

    return lines

def call_function_with_argument_str(fn_name, arguments_str):
    return fn_name + '(' + arguments_str + ');\n'


#
# I/O
#

def create_printf(intro_string, signals):
    """
        generate a code for showing the values of the given signals using printf

        intro_string - a string that is place at the begin of the output
        signals      - a list of signals whose values to print

        NOTE: signals with a datatype that did not define a printf pattern will be ignored. 
    """

    signals_ok_to_print = []
    for s in signals:

        if s.datatype.cpp_printf_pattern is not None:
            signals_ok_to_print.append( s )

    format_str = signalListHelper_printfPattern_string(signals_ok_to_print)
    parameter_str = signal_list_to_names_string(signals_ok_to_print)

    if not 0 == len(signals_ok_to_print):
        code = 'printf("' + intro_string + ':   (' + parameter_str + ') = (' + format_str + ')\\n", ' + parameter_str + ');' + '\n'
    else:
        code = 'printf("' + intro_string +  '\\n");' + '\n'

    return code
