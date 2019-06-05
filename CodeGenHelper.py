

def tabs(N):
    t = ''
    for i in range(0,N):
        t += '  '
    
    return t



# def signalListHelper(self, signals):
#     #
#     # make strings for the output signals
#     #
#     names = []
#     typeNames = []
#     vardefStr = []  # e.g. double y

#     printfPatterns = [] 

#     for s in signals:
#         names.append( s.getName() )

#         typeNames.append( s.getDatatype().cppDataType )

#         # e.g.: double y;
#         vardefStr.append( s.getDatatype().cppDataType + ' ' + s.getName() + ';' )

#         # e.g. %f
#         printfPatterns.append( s.getDatatype().cppPrintfPattern )

        

#     # str list of output signals. e.g. 'y1, y2, y3' 
#     outputNamesCSVList = ', '.join( names )
#     outputNamesVarDef = ' '.join( vardefStr )
#     outputPrinfPattern = ' '.join( printfPatterns )




def signalListHelper_names(signals):
    names = []

    for s in signals:
        names.append( s.getName() )

    return names



def signalListHelper_typeNames(signals):
    typeNames = []

    for s in signals:
        typeNames.append( s.getDatatype().cppDataType )

    return typeNames


def signalListHelper_CppVarDefStr(signals):
    vardefStr = []  # e.g. double y

    for s in signals:
        # e.g.: double y;
        vardefStr.append( s.getDatatype().cppDataType + ' ' + s.getName() )

    return vardefStr



def signalListHelper_printfPattern(signals):
    printfPatterns = [] 

    for s in signals:

        # e.g. %f
        printfPatterns.append( s.getDatatype().cppPrintfPattern )
    
    return printfPatterns

