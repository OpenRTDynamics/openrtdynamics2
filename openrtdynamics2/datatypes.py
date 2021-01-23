from typing import Dict, List

from openrtdynamics2 import signals as sig

# remove these
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
        print("datatype: type=" + self.toStr())

    def toStr(self):
        return self.cppDataType + " [" + str(self.size) + "]"

    @property
    def cppDataType(self):
        return 'UNDEF (prototype)'

    def cpp_define_variable(self, variable_name, make_a_reference = False):
        if make_a_reference:
            variable_name_ = '&' + variable_name + ''
        else:
            variable_name_ = variable_name

        return self.cppDataType + ' ' + variable_name_

    @property
    def cppPrintfPattern(self):
        return None

    @property
    def cpp_zero_element(self):
        return 'UNDEF'



class DataTypeArray(DataType):

    def __init__(self, length : int, datatype : DataType ):
        DataType.__init__(self, type=None, size=1)

        self._array_element_datatype = datatype
        self._length    = length

    @property
    def cppDataType(self):
        return self._array_element_datatype.cppDataType + ' [' + str(self._length) + ']'
    
    @property
    def datatype_of_elements(self):
        return self._array_element_datatype

    def cpp_define_variable(self, variable_name, make_a_reference = False):

        if make_a_reference:
            variable_name_ = ' (&' + variable_name + ')'
        else:
            variable_name_ = variable_name

        return self._array_element_datatype.cppDataType + ' ' + variable_name_ + '[' + str(self._length) + ']'




class DataTypeBoolean(DataType):

    def __init__(self, size : int):
        DataType.__init__(self, type=ORTD_DATATYPE_BOOLEAN, size=size)

    @property
    def cppDataType(self):
        return 'bool'

    @property
    def cppPrintfPattern(self):
        return '%d'

    @property
    def cpp_zero_element(self):
        return 'false'


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

    @property
    def cpp_zero_element(self):
        return '0.0'



class DataTypeInt32(DataTypeNumeric):

    def __init__(self, size : int):

        DataType.__init__(self, type=ORTD_DATATYPE_INT32, size=size)

    @property
    def cppDataType(self):
        return 'int32_t'

    @property
    def cppPrintfPattern(self):
        return '%d'

    @property
    def cpp_zero_element(self):
        return '0'


def areAllTypesDefined( datatypes : List[ DataType ] ):
    """
        check of all given types are defined i.e. none of them is None
    """
    for t in datatypes:
        if t is None:
            return False

    return True


def common_numeric_type( datatypes : List[ DataTypeNumeric ] ):
    """
        return the type with the highest numerical precission among the given datatypes
    """
    returnType = DataTypeInt32(1)

    # TODO: stupid implementation only valid to choose among int32 and float64
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