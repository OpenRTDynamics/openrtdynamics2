from typing import Dict, List

#from Block import * 

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


class Signal:
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):
        self.sim = sim
        self.datatype = datatype
        self.sourceBlock = sourceBlock
        self.sourcePort = sourcePort  # counting starts at zero
        self.name = "--"

        # the list of destinations this signals goes to
        self.destinationBlocks = []
        self.destinationPorts = []

        # link to myself by defaul
        self.linkedSignal = self

        #self.graphTraverseMarker = False

        #if sourceBlock == None:
            # create a signal without any specified origin

    # set the name of this signal
    def setName(self, name):
        self.name = name

        return self

    def getName(self):
        return self.name
        

    def addDestination(self, block , port : int):
        # add this destination to the list
        self.linkedSignal.destinationBlocks.append( block )
        self.linkedSignal.destinationPorts.append( port )

    def getDestinationBlocks(self):
        return self.linkedSignal.destinationBlocks

    def getSourceBlock(self):
        return self.linkedSignal.sourceBlock

    def setequal(self, to):
        # build a link to the already existing signal 'to'
        self.linkedSignal = to

        print("== Created a signal link ==")

    def getDatatype(self):
        return self.linkedSignal.datatype

    def setDatatype(self, datatype  ):
        self.linkedSignal.datatype = datatype

    def setNameOfOrigin(self, name):
        if not self.linkedSignal.sourceBlock is None:
            self.linkedSignal.sourceBlock.setName(name)

        return self


    def ShowOrigin(self):
        if not self.linkedSignal.sourcePort is None and not self.linkedSignal.sourceBlock is None:
            print("Signal >" + self.name + "< origin: port " + str(self.linkedSignal.sourcePort) + " of block #" + str(self.linkedSignal.sourceBlock.getId()) )

        else:
            print("Signal >" + self.name + "< origin not defined (so far)")

