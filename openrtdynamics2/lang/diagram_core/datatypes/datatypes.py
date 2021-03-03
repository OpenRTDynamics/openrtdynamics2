from typing import Dict, List

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


# def extract_datatypes_from_signals(signals : List[sig.Signal]):
#     """
#         extract the datatypes for each element of a list of signals and return them in a list 
#     """

#     datatypes = []
#     for s in signals:
#         datatypes.append( s.getDatatype() )

#     return datatypes

class DataType(object):

    def __init__(self, type_id : int, size : int):
        self._type = type_id
        self._size = size

    def is_equal_to(self, other_type):
        # output types
        # -1 undefined, 1 equal types, 0 type missmatch

        if other_type is None:
            return -1

        if not self.is_defined():
            return -1

        if not other_type.is_defined():
            return -1

        if self._size == other_type._size and self._type == other_type._type:
            return 1
        else:
            return 0

    def is_defined(self):
        if self._type is None:
            return False

        if self._size is None:
            return False

        return True

    def show(self):
        print("datatype: " + self.cpp_datatype_string)

    def toStr(self):
        return self.cpp_datatype_string + " [" + str(self._size) + "]"

    @property
    def cpp_datatype_string(self):
        return 'UNDEF'

    def cpp_define_variable(self, variable_name, make_a_reference = False):
        if make_a_reference:
            variable_name_ = '&' + variable_name + ''
        else:
            variable_name_ = variable_name

        return self.cpp_datatype_string + ' ' + variable_name_

    @property
    def cpp_printf_pattern(self):
        return None

    @property
    def cpp_zero_element(self):
        return 'UNDEF'




class DataTypePointer(DataType):
    """
    Create a pointer pointing to an instance of a given class

    Example:
    --------

        cpp_type_name_class = 'SomeClass' 

    In the source code of the class, the following definition is required

        typedef SomeClass *SomeClassPtr

    """

    def __init__(self, cpp_type_name_class : str ):
        DataType.__init__(self, type_id=None, size=1)

        self._cpp_ptr_type_name   = cpp_type_name_class + 'Ptr' # cpp_ptr_type_name
        self._cpp_type_name_class = cpp_type_name_class

    @property
    def cpp_datatype_string(self):
        """
        return the c++ datatype string of the pointer to the class instance 
        """
        return self._cpp_ptr_type_name

    @property
    def cpp_datatype_string_class(self):
        """
        return the c++ datatype string of the class
        """
        return self._cpp_type_name_class

    def is_equal_to(self, other_type):

        result = DataType.is_equal_to(self, other_type)

        if result == 1:
            if self._cpp_ptr_type_name == other_type._cpp_ptr_type_name:
                return 1
        else:
            return result





class DataTypeArray(DataType):

    def __init__(self, length : int, datatype : DataType ):
        DataType.__init__(self, type_id=None, size=1)

        self._array_element_datatype = datatype
        self._length    = length

    @property
    def cpp_datatype_string(self):
        return self._array_element_datatype.cpp_datatype_string + ' [' + str(self._length) + ']'
    
    @property
    def datatype_of_elements(self):
        return self._array_element_datatype

    def cpp_define_variable(self, variable_name, make_a_reference = False):

        if make_a_reference:
            variable_name_ = ' (&' + variable_name + ')'
        else:
            variable_name_ = variable_name

        return self._array_element_datatype.cpp_datatype_string + ' ' + variable_name_ + '[' + str(self._length) + ']'




class DataTypeBoolean(DataType):

    def __init__(self, size : int):
        DataType.__init__(self, type_id=ORTD_DATATYPE_BOOLEAN, size=size)

    @property
    def cpp_datatype_string(self):
        return 'bool'

    @property
    def cpp_printf_pattern(self):
        return '%d'

    @property
    def cpp_zero_element(self):
        return 'false'


#
# numeric types
#

class DataTypeNumeric(DataType):
    def __init__(self, size : int):
        DataType.__init__(self, type_id=ORTD_DATATYPE_FLOAT, size=size)


class DataTypeFloat64(DataTypeNumeric):

    def __init__(self, size : int):
        DataType.__init__(self, type_id=ORTD_DATATYPE_FLOAT, size=size)

    @property
    def cpp_datatype_string(self):
        return 'double'

    @property
    def cpp_printf_pattern(self):
        return '%f'

    @property
    def cpp_zero_element(self):
        return '0.0'



class DataTypeInt32(DataTypeNumeric):

    def __init__(self, size : int):

        DataType.__init__(self, type_id=ORTD_DATATYPE_INT32, size=size)

    @property
    def cpp_datatype_string(self):
        return 'int32_t'

    @property
    def cpp_printf_pattern(self):
        return '%d'

    @property
    def cpp_zero_element(self):
        return '0'


# def areAllTypesDefined( datatypes : List[ DataType ] ):
#     """
#         check of all given types are defined i.e. none of them is None
#     """
#     for t in datatypes:
#         if t is None:
#             return False

#     return True


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
        

def get_unique_datatype_from_io_types(datatype_of_output_signal : DataType, datatypes_of_input_signals : List[DataType] ):
    """
        Verifies that the datatypes in datatypes_of_input_signals and datatype_of_output_signal match.
        Undefined datatypes are ignored. Returns the datatype.
    """
    
    referenceDatatype = None

    # if the output is defined, use its datatype
    if datatype_of_output_signal is not None:
        referenceDatatype = datatype_of_output_signal

    # otherwise, look for a defined input signal und use its datatype as the reference type
    else:
        for s in datatypes_of_input_signals:
            if s is not None:
                referenceDatatype = s

                break

    # if no reference datatype could be found return nothing
    if referenceDatatype is None:
        return None

    # check if all inputs have the reference type
    for s in datatypes_of_input_signals:
        if s.is_equal_to( referenceDatatype ) == 0:
            raise BaseException('Type error: inputs do not match to the output datatype')

    return referenceDatatype