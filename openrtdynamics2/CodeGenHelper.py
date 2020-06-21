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


def signalListHelper_names(signals):
    names = []

    for s in signals:
        names.append( s.name )

    return names


# TODO: rename to comma_separated_names_string
def signalListHelper_names_string(signals):
    return ', '.join( signalListHelper_names(signals)  )





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




def asign( from_signal_name, to_signal_name ):
    return to_signal_name + ' = ' + from_signal_name + ';\n'

def define_variable_list_string(signals, make_a_reference = False):
    return '; '.join( define_variable_list(signals, make_a_reference)  ) + ';'

def defineVariables( signals, make_a_reference = False ):
    """
        create a string containing e.g.

        'double signalName1;\n
         double signalName2;\n'
    """
    elements = define_variable_list(signals, make_a_reference )

    return ';\n'.join( elements ) + ';\n'








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
        lines += '\n} else {\n' + indent( action_list[ N ] ) + '\n}'

    elif len(action_list) == N:
        lines += '\n}\n'

    else:
        raise BaseException("missmatch of the number of actions and conditions")

    return lines

def generate_compare_equality_to_constant( language, signal_name, constant ):
    return signal_name + ' == ' + str(constant)



