# from SimulationContext import *
# from BlockPrototypes import *

from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)




class Signal(object):
    
    # TODO: remove  sourceBlock = None, sourcePort = None as they are not special to this base class

    def __init__(self, sim, datatype = None):
        self.sim = sim
        
        # the fixed and final datatype of this signals either as a result of the datatype determination phase
        # or manually fixed.
        self.datatype = datatype

        # datatype proposal that may be filled out during the datatype determination phase
        self.proposedDatatype = None
        # self.proposedDatatypeUpdated = False

        #self.sourceBlock = sourceBlock
        #self.sourcePort = sourcePort  # counting starts at zero

        # give this signal a unique default name
        # (NOTE: the name will be set by the derived classes)
        # self.name = None # 's' + str(sim.getNewSignalId())

        self._nameIsDefault = True

        # the list of destinations this signals goes to
        self.destinationBlocks = []
        self.destinationPorts = []

        # used by TraverseGraph as a helper variable to perform a marking of the graph nodes
        self.graphTraversionMarker = -1

        # notify the creation of this signal
        self.sim.datatypePropagation.notifySignal(self)

    @property
    def nameIsDefault(self):
        return self._nameIsDefault

    def lookupSource(self):
        return self

    def graphTraversionMarkerReset(self):
        self.lookupSource().graphTraversionMarker = -1

    def graphTraversionMarkerMarkVisited(self, level):
        if level < 0:
            raise BaseException("level cannot be < 0")

        self.lookupSource().graphTraversionMarker = level
    
    def graphTraversionMarkerMarkIsVisited(self):
        # check of this node was marked on level or a level below
        return self.lookupSource().graphTraversionMarker >= 0

    def graphTraversionMarkerMarkIsVisitedOnLevel(self, onLevel):
        # check of this node was marked on level or a level below
        return self.lookupSource().graphTraversionMarker == onLevel

    # set the name of this signal
    def setName(self, name):
        self.lookupSource().name = name

        # indicate that this Signal has a specified name (not a default/auto-generated name)
        self._nameIsDefault = False

        return self

    def getName(self):
        return self.lookupSource().name

    def toStr(self):
        ret = ''
        ret += self.lookupSource().name

        if self.lookupSource().datatype is not None:
            ret += " (" + self.lookupSource().datatype.toStr() + ")"
        else:
            ret += " (undef datatype)"


        if self.lookupSource().proposedDatatype is not None:
            ret += " proposal: (" + self.lookupSource().proposedDatatype.toStr() + ")"
        else:
            ret += "proposal: (undef datatype)"

        return ret
        

    def addDestination(self, block , port : int):
        # add this destination to the list
        self.lookupSource().destinationBlocks.append( block )
        self.lookupSource().destinationPorts.append( port )

    def getDestinationBlocks(self):
        return self.lookupSource().destinationBlocks

    def getDatatype(self):
        return self.lookupSource().datatype

    def setDatatype(self, datatype):
        self.lookupSource().datatype = datatype

        # notify the change of the datatype
        self.sim.datatypePropagation.notifySignal(self)

    def fixDatatype(self):
        # this shall explicitely not trigger a notification!
        self.lookupSource().datatype = self.lookupSource().proposedDatatype

    def getProposedDatatype(self):
        return self.lookupSource().proposedDatatype

    def setProposedDatatype(self, proposedDatatype):
        # only proceed if the datatype of this signals is not already fixed
        if self.lookupSource().datatype is None:

            # only proceed of the prosed datatype is diffent to the stored one
            # or the stored type is None (not set before)
            if not proposedDatatype.isEqualTo( self.lookupSource().proposedDatatype ) or self.lookupSource().proposedDatatype is None:

                self.lookupSource().proposedDatatype = proposedDatatype
                # self.lookupSource().proposedDatatypeUpdated = True

                # notify the change of the datatype
                self.sim.datatypePropagation.notify_updateOfProposedDatatype(self)

        else:
            raise BaseException("setProposedDatatype: only possible for signals which datatype are not already fixed!")


    # move to derived classes below
    def getSourceBlock(self):
        return self.lookupSource().sourceBlock


    def setNameOfOrigin(self, name):
        if not self.lookupSource().sourceBlock is None:
            self.lookupSource().sourceBlock.setName(name)

        return self

    def ShowOrigin(self):
        if not self.lookupSource().sourcePort is None and not self.lookupSource().sourceBlock is None:
            print("Signal >" + self.name + "< origin: port " + str(self.lookupSource().sourcePort) + " of block #" + str(self.lookupSource().sourceBlock.getId()) )

        else:
            print("Signal >" + self.name + "< origin not defined (so far)")






class UndeterminedSignal(Signal):
    """
        A signal that serves as a placeholder and will be connected later on by
        calling connect(). As long as no connection to a real source is present
        the blocks that are connected to this signal are colleted in a list. Once
        this signal is conneted, the source's signal lists are merged.

        NOTE: undetermined singlas must be connected to a block's output i.e. they
        cannot be simulation inputs

    """

    def __init__(self, sim):
        
        # link to myself by default to be able to colltect the blocks that are connected to
        # this fake-signal

        # name undefined. Once connected to a block output the name is defined
        self.name = 'anonymous'
        self.linkedSignal = self
        self.nameProposal = None

        Signal.__init__(self, sim)

    def toStr(self):
        if self is self.linkedSignal:
            return Signal.toStr(self) + ' (ANONYMOUS)'
        else:
            return Signal.toStr(self)

    # connect to source
    def setequal(self, to):
        if self is to:
            raise BaseException("Cannot connect to the same signal.")

        # check if to is a BlockOutputSignal
        if not isinstance(to.lookupSource(), BlockOutputSignal):
            raise BaseException("An anonymous signal can only be connected to a block output.")

        # build a link to the already existing signal 'to'
        print("== Created a signal link " +  to.getName() + " == "+   self.getName() +  "")

        # merge the list of detination blocks
        for b in self.destinationBlocks:
            to.destinationBlocks.append(b)

        # merge self.destinationBlocks into to.destinationBlocks
        for p in self.destinationPorts:
            to.destinationPorts.append(p)

        # merge name
        if self.nameProposal is not None and not to.nameIsDefault:
            # TODO: check if to holds just the default name. If so update it with the proposal

            to.setName(self.nameProposal)
            
        # overwrite self
        self.linkedSignal = to

    def isConnectedToSth(self):
        if self is self.linkedSignal:
            return False
        else:
            return True

    # set the name of this signal
    def setName(self, name):
        if not self.isConnectedToSth():
            # not connected
            self.nameProposal = name

        else:
            self.linkedSignal.lookupSource().setName(name)


    def lookupSource(self):

        if not self.isConnectedToSth():
            # Note at this point the anonymous signal does not have a proper
            # source. return itself as a placeholder until sth. is connected 
            # by calling setequal().
            return self

        else:

            return self.linkedSignal.lookupSource()






class BlockOutputSignal(Signal):
    """
        A signal that is the output of a block (normal case)

        TODO: implement and remove code from 'Signal' above
    """

    def __init__(self,  sim, datatype = None, sourceBlock = None, sourcePort = None):

        # give this signal a unique default name
        self.name = 's' + str(sim.getNewSignalId())
        
        self.sourceBlock = sourceBlock
        self.sourcePort = sourcePort  # counting starts at zero

        Signal.__init__(self, sim, datatype)

    def lookupSource(self):
        return self



class SimulationInputSignal(Signal):
    """
        A special signal that markes an input to a simulation.
    """

    def __init__(self, sim, datatype = None):

        self.port = sim.simulationInputSignalCounter
        sim.simulationInputSignalCounter += 1

        # give this signal a unique default name
        # TODO: This shall be overwritten anyways by the user, so maybe this can be removed (or maybe not in case it is 
        # used to auto-generate sub-systems)
        self.name = 's' + str(sim.getNewSignalId())

        Signal.__init__(self, sim, datatype=datatype)

    def lookupSource(self):
        return self
