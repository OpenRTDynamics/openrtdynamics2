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

def signalListHelper_CppVarDefStr(signals):
    vardefStr = []  # e.g. double y

    for s in signals:
        # e.g.: double y;
        vardefStr.append( s.getDatatype().cppDataType + ' ' + s.name )

    return vardefStr


def asign( from_signal_name, to_signal_name ):
    return to_signal_name + ' = ' + from_signal_name + ';\n'

def signalListHelper_CppVarDefStr_string(signals):
    return '; '.join( signalListHelper_CppVarDefStr(signals)  ) + ';'

def defineVariables( signals ):
    """
        create a sting containing e.g.

        'double signalName1;\n
         double signalName2;\n'
    """
    elements = signalListHelper_CppVarDefStr(signals)

    return ';\n'.join( elements ) + ';\n'

def defineVariable( signal ):
    """
        create a sting containing e.g.

        'double signalName;'
    """
    element = signalListHelper_CppVarDefStr([signal])

    return element[0] + ';\n'

def defineVariableLine( signal ):
    """
        create a sting containing e.g.

        'double signalName;\n'
    """
    element = signalListHelper_CppVarDefStr([signal])

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

