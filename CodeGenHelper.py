#
# Helper functions related to c++ code generation
#

def tabs(N):
    t = ''
    for i in range(0,N):
        t += '  '
    
    return t




#
#
#


def signalListHelper_names(signals):
    names = []

    for s in signals:
        names.append( s.getName() )

    return names

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
        vardefStr.append( s.getDatatype().cppDataType + ' ' + s.getName() )

    return vardefStr


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

    return element[0] + ';'

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
        lines += structVarname + '.' + s.getName() + ' = ' + s.getName() + ';\n'

    return lines

def getStructElements( structVarname, signals ):
    # get list of e.g. 'outputs.y1', 'outputs.y2'

    structElements = []

    for s in signals:
        structElements.append( structVarname + '.' + s.getName()  )

    return structElements

