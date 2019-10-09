from typing import Dict, List

import Signal as sig

ORTD_DATATYPE_UNCONFIGURED = 0
ORTD_DATATYPE_FLOAT = (1 | (8 << 5))
ORTD_DATATYPE_SHORTFLOAT = 4
ORTD_DATATYPE_INT32 = 2
ORTD_DATATYPE_BOOLEAN = 3
ORTD_DATATYPE_EVENT = 5
ORTD_DATATYPE_BINARY = 6
ORTD_DATATYPE_UINT32 = 7
ORTD_DATATYPE_INT16 = 8
ORTD_DATATYPE_UINT16 = 9
ORTD_DATATYPE_INT8 = 10
ORTD_DATATYPE_UINT8 = 11


def extract_datatypes_from_signals(signals : List[sig.Signal]):
    """
        extract the datatytes for each element of a list of signals and return them in a list 
    """

    datatypes = []
    for s in signals:
        datatypes.append( s.getDatatype() )

    return datatypes

class DataType(object):
    #
    # TODO: feature: add type of datype: 1) 'C++', 'ORTD (V2)' + optional 'is reference flag' 
    #
    #
    #
    #



    def __init__(self, type : int, size : int):
        self.type = type
        self.size = size

    def isEqualTo(self, otherType):
        # output types
        # -1 undefined, 1 equal types, 0 type missmatch

        #print("DataType:isEqualTo " + str(self.size) + "==" + str(otherType.size) + " -- " + str(self.type) + " == " + str(otherType.type) )
        if otherType is None:
            return -1

        if not self.isDefined():
            return -1

        if not otherType.isDefined():
            return -1

        if self.size == otherType.size and self.type == otherType.type:
            return 1
        else:
            return 0

    def isDefined(self):
        if self.type is None:
            return False

        if self.size is None:
            return False

        return True

    def show(self):
        print("Datatype: type=" + self.toStr())

    def toStr(self):
        return "type=" + str(self.type) + " size=" + str(self.size) + ' (' + self.cppDataType + ')'

    @property
    def cppDataType(self):
        return 'UNDEF (prototype)'


    @property
    def cppPrintfPattern(self):
        return None


class DataTypeBoolean(DataType):

    def __init__(self, size : int):
        DataType.__init__(self, type=ORTD_DATATYPE_BOOLEAN, size=size)

    @property
    def cppDataType(self):
        return 'bool'

    @property
    def cppPrintfPattern(self):
        return '%d'



#
# numeric types
#

class DataTypeNumeric(DataType):
    def __init__(self, size : int):
        DataType.__init__(self, type=ORTD_DATATYPE_FLOAT, size=size)


class DataTypeFloat64(DataTypeNumeric):

    def __init__(self, size : int):
        DataType.__init__(self, type=ORTD_DATATYPE_FLOAT, size=size)

    @property
    def cppDataType(self):
        return 'double'

    @property
    def cppPrintfPattern(self):
        return '%f'




class DataTypeInt32(DataTypeNumeric):

    def __init__(self, size : int):

        DataType.__init__(self, type=ORTD_DATATYPE_INT32, size=size)

    @property
    def cppDataType(self):
        return 'int32_t'

    @property
    def cppPrintfPattern(self):
        return '%d'


def areAllTypesDefined( datatypes : List[ DataType ] ):
    """
        check of all given types are defined i.e. none of them is None
    """
    for t in datatypes:
        if t is None:
            return False

    return True


def computeResultingNumericType( datatypes : List[ DataTypeNumeric ] ):
    """
        return the type with the highest numerical precission
    """
    returnType = DataTypeInt32(1)

    for t in datatypes:
        # ignore undefined types
        if t is not None:
            if isinstance(t, DataTypeFloat64):
                returnType = DataTypeFloat64(1)

    return returnType
        

def autoDatatype_Nto1(outputSignal : DataType, inputSignal : List[DataType] ):
    """
        Verifies that the datatypes for the given signalstype match and returns
        that that datatype. 
    """
    
    referenceDatatype = None

    # if the output is defined, use its datatype
    if outputSignal is not None:
        referenceDatatype = outputSignal

    # otherwise, look for a defined input signal und use its datatype as the reference type
    else:
        for s in inputSignal:
            if s is not None:
                referenceDatatype = s

                break

    # if no reference datatype could be found return nothing
    if referenceDatatype is None:
        return None

    # check if all inputs have the refernce type
    for s in inputSignal:
        if s.isEqualTo( referenceDatatype ) == 0:
            raise BaseException('Type error: input do not match to the output datatype')

    return referenceDatatype