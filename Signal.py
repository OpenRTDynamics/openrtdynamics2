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
    def __init__(self, type : int, size : int):
        self.type = type
        self.size = size

    def isEqualTo(self, otherType):
        #print("DataType:isEqualTo " + str(self.size) + "==" + str(otherType.size) + " -- " + str(self.type) + " == " + str(otherType.type) )

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
        print("Datatype: type=" + str(self.type) + " size=" + str(self.size) )


class Signal:
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):
        self.sim = sim
        self.datatype = datatype
        self.sourceBlock = sourceBlock
        self.sourcePort = sourcePort  # counting starts at zero

        #if sourceBlock == None:
            # create a signal without any specified origin

    def setequal(self, From ):
        #if self.sim != From.sim:
        #    throw("setequal: From signal must be from the same simulation")

        if self.datatype == None:
            self.datatype = From.datatype
        elif not self.datatype.isEqualTo( From.datatype ):
            raise("setqual: datatype missmatch")
        else:
            self.datatype = From.datatype

        self.sourceBlock = From.sourceBlock
        self.sourcePort = From.sourcePort

    def getDatatype(self):
        return self.datatype

    def ShowOrigin(self):
        if not self.sourcePort is None and not self.sourceBlock is None:
            print("Signal origin: port " + str(self.sourcePort) + " of block #" + str(self.sourceBlock.getId()) )

        else:
            print("Signal origin not defined (so far)")

