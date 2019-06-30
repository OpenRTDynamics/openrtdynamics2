from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)




class Signal:
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):
        self.sim = sim
        
        # the fixed and final datatype of this signals either as a result of the datatype determination phase
        # or manually fixed.
        self.datatype = datatype

        # datatype proposal that may be filled out during the datatype determination phase
        self.proposedDatatype = None
        # self.proposedDatatypeUpdated = False

        self.sourceBlock = sourceBlock
        self.sourcePort = sourcePort  # counting starts at zero

        # give this signal a unique default name
        self.name = 'signal_' + str(sim.getNewSignalId())

        # the list of destinations this signals goes to
        self.destinationBlocks = []
        self.destinationPorts = []

        # link to myself by defaul
        self.linkedSignal = self

        # used by TraverseGraph as a helper variable to perform a marking of the graph nodes
        self.linkedSignal.graphTraversionMarker = -1

        # notify the creation of this signal
        self.sim.datatypePropagation.notifySignal(self)


    def graphTraversionMarkerReset(self):
        self.linkedSignal.graphTraversionMarker = -1

    def graphTraversionMarkerMarkVisited(self, level):
        if level < 0:
            raise BaseException("level cannot be < 0")

        self.linkedSignal.graphTraversionMarker = level
    
    def graphTraversionMarkerMarkIsVisited(self):
        # check of this node was marked on level or a level below
        return self.linkedSignal.graphTraversionMarker >= 0

    def graphTraversionMarkerMarkIsVisitedOnLevel(self, onLevel):
        # check of this node was marked on level or a level below
        return self.linkedSignal.graphTraversionMarker == onLevel

    # set the name of this signal
    def setName(self, name):
        self.linkedSignal.name = name

        print("-- set name of signql to " + name)

        return self

    def getName(self):
        return self.linkedSignal.name

    def toStr(self):
        ret = ''
        ret += self.linkedSignal.name

        if self.linkedSignal.datatype is not None:
            ret += " (" + self.linkedSignal.datatype.toStr() + ")"
        else:
            ret += " (undef datatype)"


        if self.linkedSignal.proposedDatatype is not None:
            ret += " proposal: (" + self.linkedSignal.proposedDatatype.toStr() + ")"
        else:
            ret += "proposal: (undef datatype)"

        return ret
        

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
        print("== Created a signal link " +  to.getName() + " == "+   self.getName() +  "")

        # merge the list of detination blocks
        for b in self.destinationBlocks:
            to.destinationBlocks.append(b)

        # merge self.destinationBlocks into to.destinationBlocks
        for p in self.destinationPorts:
            to.destinationPorts.append(p)

        # overwrite self
        self.linkedSignal = to

    def getDatatype(self):
        return self.linkedSignal.datatype

    def setDatatype(self, datatype):
        self.linkedSignal.datatype = datatype

        # notify the change of the datatype
        self.sim.datatypePropagation.notifySignal(self)

    def fixDatatype(self):
        # this shall explicitely not trigger a notification!
        self.linkedSignal.datatype = self.linkedSignal.proposedDatatype

    def getProposedDatatype(self):
        return self.linkedSignal.proposedDatatype

    def setProposedDatatype(self, proposedDatatype):
        # only proceed if the datatype of this signals is not already fixed
        if self.linkedSignal.datatype is None:

            # only proceed of the prosed datatype is diffent to the stored one
            # or the stored type is None (not set before)
            if not proposedDatatype.isEqualTo( self.linkedSignal.proposedDatatype ) or self.linkedSignal.proposedDatatype is None:

                self.linkedSignal.proposedDatatype = proposedDatatype
                # self.linkedSignal.proposedDatatypeUpdated = True

                # notify the change of the datatype
                self.sim.datatypePropagation.notify_updateOfProposedDatatype(self)

        else:
            raise BaseException("setProposedDatatype: only possible for signals which datatype are not already fixed!")


    def setNameOfOrigin(self, name):
        if not self.linkedSignal.sourceBlock is None:
            self.linkedSignal.sourceBlock.setName(name)

        return self


    def ShowOrigin(self):
        if not self.linkedSignal.sourcePort is None and not self.linkedSignal.sourceBlock is None:
            print("Signal >" + self.name + "< origin: port " + str(self.linkedSignal.sourcePort) + " of block #" + str(self.linkedSignal.sourceBlock.getId()) )

        else:
            print("Signal >" + self.name + "< origin not defined (so far)")





class BlockOutputSignal(Signal):
    """
        A signal that is the output of a block (normal case)

        TODO: implement and remove code from 'Signal' above
    """

    def __init__(self, sim, port : int, datatype = None):
        pass



class SimulationInputSignal(Signal):
    """
        A special signal that markes an input to a simulation.
    """

    def __init__(self, sim, port : int, datatype = None):
        
        self.port = port

        Signal.__init__(self, sim, datatype=datatype)

