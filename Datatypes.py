from typing import Dict, List

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




class DataType:
    #
    # TODO: feature: add type of datype: 1) 'C++', 'ORTD (old)', 'ORTD (V2)' + optional 'is reference flag' 
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


#
# numeric types
#

class DataTypeNumeric(DataType):
    def __init__(self, size : int):
        DataType.__init__(self, type=ORTD_DATATYPE_FLOAT, size=size)


class DataTypeFloat(DataTypeNumeric):

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
            if isinstance(t, DataTypeFloat):
                returnType = DataTypeFloat(1)

    return returnType
        
