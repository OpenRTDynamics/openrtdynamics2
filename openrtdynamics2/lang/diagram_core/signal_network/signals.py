from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)




class Signal(object):
    
    def __init__(self, system, autogeneratedName : str, datatype = None ):
        self._system = system
        
        # the fixed and final datatype of this signals either as a result of the datatype determination phase
        # or manually fixed.
        self._datatype = datatype

        # datatype proposal that may be filled out during the datatype determination phase
        self.proposedDatatype = None

        # indicates a signal that is not computed by a set of instructions but points to a memory containing the value
        self._is_referencing_memory = False

        # give this signal a unique default name
        self._name = autogeneratedName
        self._nameIsDefault = True

        # the list of destinations this signals goes to
        self.destinationBlocks = []
        self.destinationPorts = []

        # the list of signals to which the datatype of this signal is inherited
        self._inherit_datatype_to_list = []

        # used by dependency tree alg as a helper variable to perform a marking of the graph nodes
#        self.graphTraversionMarker = -1

        self.dependency_tree_node = None

        # inherit the datatype for this anonymous signals from the signal referred to by inherit_datatype_of_signal
        self.inherit_datatype_of_signal = None

        # In case not None: the data/value of the signal are obtained from the given signal
        # NOTE: not used so far.
        self._data_link = None

        # NOTE: this mus be the last in the list
        # notify the creation of this signal
        self._system.datatype_propagation_instance.notifySignal(self)

        # properties (user)
        self.properties = {}

        # properties (internal, controlled by block prototypes)
        self.properties_internal = {}

        # optional: port number of input / output w.r.t. the system 'sim'
        self.port = None


    # TODO: remove
    def getDatatype(self):
        return self.lookupSource()._datatype

    @property
    def datatype(self):
        return self.lookupSource()._datatype
    
    def update_datatype_config(self, datatype):
        """
            set the datatype in case it was not defined in the constructor
        """
        if self.lookupSource()._datatype is not None:
            raise BaseException("datatype already defined")
        
        self.lookupSource()._datatype = datatype


    @property
    def is_referencing_memory(self):
        return self._is_referencing_memory

    def set_is_referencing_memory(self, val : bool):
        self._is_referencing_memory = val

    @property
    def nameIsDefault(self):
        return self._nameIsDefault

    @property
    def system(self):
        # system == simulation
        return self._system

    # in case resolveUndeterminedSignals becomes obsolete, those 3 fns might be important
    # otherwise TODO: remove them
    def is_proxy(self):
        return self.lookupSource().is_proxy()

    def is_block_output(self):
        return self.lookupSource().is_block_output()

    def is_simulation_input(self):
        return self.lookupSource().is_simulation_input()


    def is_crossing_system_boundary(self, system):

        """
            test if fot the given system this signals comes from an outer/higher level
            system.
        """

        if self._system == system:
            return False

        # check if this signal is coming from an upper/outer system 
        # (if not it comes from a parallel system that cannot be accessed: this is an error)

        # go up in the system-nesting hierarchy starting at system
        system_iter = system

        while system_iter.parent_system is not None:

            if system_iter.parent_system == self.system:
                return True

            system_iter = system_iter.parent_system

        raise BaseException("Bad access to signal " + Fore.YELLOW + self.name + Fore.RESET + ": did you access a signal from another subsystem that cannot be reached?")

    def lookupSource(self):
        return self

    # def graphTraversionMarkerReset(self):
    #     self.lookupSource().graphTraversionMarker = -1

    # def graphTraversionMarkerMarkVisited(self, level):
    #     if level < 0:
    #         raise BaseException("level cannot be < 0")

    #     self.lookupSource().graphTraversionMarker = level
    
    # def graphTraversionMarkerMarkIsVisited(self):
    #     # check of this node was marked on level or a level below
    #     return self.lookupSource().graphTraversionMarker >= 0

    # def graphTraversionMarkerMarkIsVisitedOnLevelLowerThan(self, onLevel):
    #     # check of this node was marked on level or a level below
    #     return self.graphTraversionMarkerMarkIsVisited() and self.lookupSource().graphTraversionMarker < onLevel

    # set the name of this signal
    def set_name(self, name):
        self.lookupSource()._name = name

        # indicate that this Signal has a specified name (not a default/auto-generated name)
        self._nameIsDefault = False

        return self

    # set the name of this signal (this method shall not be overwritten)
    def set_name_raw(self, name):
        self.lookupSource()._name = name

        # indicate that this Signal has a specified name (not a default/auto-generated name)
        self._nameIsDefault = False

        return self

        


    @property
    def name(self):
        return self.lookupSource()._name

    def toStr(self):
        ret = ''
        ret += self.name

        if self.datatype is not None:
            ret += " (" + self.datatype.toStr() + ")"
        else:
            # ret += " (undef datatype)"
            pass


        if self.lookupSource().proposedDatatype is not None:
            ret += " type proposal: (" + self.lookupSource().proposedDatatype.toStr() + ")"
        else:
            # ret += "proposal: (undef datatype)"
            pass

        if self.lookupSource().inherit_datatype_of_signal is not None:
            ret = ret + 'type inherit from ' + self.lookupSource().inherit_datatype_of_signal.name

        return ret
        

    def addDestination(self, block , port : int):
        # add this destination to the list
        self.lookupSource().destinationBlocks.append( block )
        self.lookupSource().destinationPorts.append( port )

    def getDestinationBlocks(self):
        return self.lookupSource().destinationBlocks



    def setDatatype_nonotitication(self, datatype):
        self.lookupSource()._datatype = datatype

        # TODO: maybe there should be a notification in the next step in the datatype propagation phase?
        # e.g.:
        # self.lookupSource()._datatype_changed_but_not_notified_so_far = True

    def setDatatype(self, datatype):

        self.setDatatype_nonotitication( datatype )

        # NOTE: should be added lookupSource() here (though effectively no difference)
        # notify the change of the datatype
        self._system.datatype_propagation_instance.notifySignal(self)

    def fixDatatype(self):
        # this shall explicitely not trigger a notification!
        self.lookupSource()._datatype = self.lookupSource().proposedDatatype

    def getProposedDatatype(self):
        return self.lookupSource().proposedDatatype

    def setProposedDatatype(self, proposedDatatype):
        # only proceed if the datatype of this signals is not already fixed
        if self.lookupSource()._datatype is None:

            # only proceed of the prosed datatype is diffent to the stored one
            # or the stored type is None (not set before)
            if not proposedDatatype.is_equal_to( self.lookupSource().proposedDatatype ) or self.lookupSource().proposedDatatype is None:

                self.lookupSource().proposedDatatype = proposedDatatype
                # self.lookupSource().proposedDatatypeUpdated = True

                # notify the change of the datatype
                self._system.datatype_propagation_instance.notify_updateOfProposedDatatype(self)

        else:
            if not self.lookupSource()._datatype.is_equal_to( proposedDatatype ):
                raise BaseException("setProposedDatatype: only possible for signals the datatypes of which is not already fixed!")

    @property
    def proposed_datatype(self):
        return self.lookupSource().proposedDatatype



    def inherit_datatype_from_signal(self, from_signal):
        """
            The datatype of this anonymous signal shall be inherited from the given signal 'from_signal'.
            This creates a bi-directional link in-between the signals self and from_signal
        """
        self.lookupSource().inherit_datatype_of_signal = from_signal

        from_signal.inherit_datatype_to( self )

    def inherit_datatype_to(self, to_signal):
        """
            add to_signal to the list of signals that inherit the datatype of this signal
        """
        # once the datatype of this signal is fixed, inherit it to to_signal
        self.lookupSource()._inherit_datatype_to_list.append( to_signal )

    @property
    def inherit_datatype_to_list(self):
        return self.lookupSource()._inherit_datatype_to_list



    def set_data_link(self, signal):
        """
            The data/value of the signal are based on the given signal

            This is used for:
                1) accessing the output of a subsystem 
        """
        self.lookupSource()._data_link = signal

    @property
    def data_link(self):
        return self.lookupSource()._data_link


    # move to derived classes below
    def getSourceBlock(self):
        return self.lookupSource().sourceBlock


    def set_blockname(self, name):
        if not self.lookupSource().getSourceBlock() is None:
            self.lookupSource().getSourceBlock().set_name(name)

        return self

    def ShowOrigin(self):
        pass
        # if not self.lookupSource().sourcePort is None and not self.lookupSource().sourceBlock is None:
        #     print("Signal >" + self.name + "< origin: port " + str(self.lookupSource().sourcePort) + " of block #" + str(self.lookupSource().sourceBlock.getId()) )

        # else:
        #     print("Signal >" + self.name + "< origin not defined (so far)")




def resolveUndeterminedSignals(signals : List[Signal], ignore_signals_with_datatype_inheritance = False ):
    """
        Go through a list of signals and replace (inplace) all entries of the list
        with their direct source signals, i.e., signals of type UndeterminedSignal
        will become the connected block output of type BlockOutputSignal
    """

    if signals is None:
        return

    for i in range(0,len(signals)):
        signal = signals[i].lookupSource()

        if isinstance(signal, UndeterminedSignal):

            if signal.inherit_datatype_of_signal is not None and ignore_signals_with_datatype_inheritance:

                # there is an anonymous signal in the list. However, its datatype is foreseen to be inherited

                # print("  --------- ignoring anonymous signal "  + signal.toStr() + " as its datatype will be inherited -------  ")
                pass

            else:

                raise BaseException("Could not resolve anonymous singal " + signal.toStr() + ". Please ensure to connect this signal to a block output." )

        signals[i] = signal





class UndeterminedSignal(Signal):
    """
        A signal that serves as a placeholder and will be connected later on by
        calling connect(). As long as no connection to a real source is present
        the blocks that are connected to this signal are colleted in a list. Once
        this signal is connected, the source's signal lists are merged.

        NOTE: undetermined singlas must be connected to a block's output i.e. they
        cannot be simulation inputs

        It is optional to specify a datatype.

    """

    def __init__(self, system, datatype = None):
        
        # link to myself by default to be able to colltect the blocks that are connected to
        # this fake-signal

        # name undefined. Once connected to a block output the name is defined
        self.linkedSignal = self
        self.nameProposal = None

        Signal.__init__(self, system, autogeneratedName = 'anonymous', datatype=datatype)

    def is_proxy(self):
        return True

    def toStr(self):
        string = Signal.toStr(self)

        if self is self.linkedSignal:
            string = string + ' (anon.)'

        return string

    # connect to source
    def setequal(self, to : Signal):
        if self is to:
            raise BaseException("Cannot connect to the same signal.")

        # check if to is a BlockOutputSignal
        if not isinstance(to.lookupSource(), BlockOutputSignal):
            raise BaseException("An anonymous signal can only be connected to a block output.")

        # build a link to the already existing signal 'to'
        # print("== Created a signal link " +  to.name + " == "+   self.name +  "")

        # merge the list of detination blocks
        for b in self.destinationBlocks:
            to.destinationBlocks.append(b)

        # merge self.destinationBlocks into to.destinationBlocks
        for p in self.destinationPorts:
            to.destinationPorts.append(p)

        # merge datatype
        if self.datatype is not None and not to.datatype:
            to.setDatatype_nonotitication(self.datatype)

        # merge name
        if self.nameProposal is not None and not to.nameIsDefault:
            # TODO: check if to holds just the default name. If so update it with the proposal

            to.set_name(self.nameProposal)
            
        # overwrite self
        self.linkedSignal = to




    def isConnectedToSth(self):
        if self is self.linkedSignal:
            return False
        else:
            return True

    # set the name of this signal
    def set_name(self, name):
        if not self.isConnectedToSth():
            # not connected
            self.nameProposal = name

        else:
            self.linkedSignal.lookupSource().set_name(name)

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

    def __init__(self, system, datatype = None, sourceBlock = None, sourcePort = None):
        
        self._sourceBlock = sourceBlock
        self._sourcePort = sourcePort  # counting starts at zero

        # give this signal a unique default name
        Signal.__init__(self, system, autogeneratedName = 's' + str(system.generate_new_signal_id()), datatype = datatype)

    def is_block_output(self):
        return True

    def update_source_config(self, sourceBlock = None, sourcePort = None):
        """
            In the constructor all information is optional. To add information after construction
            of this signal, update config might be used
        """

        if self._sourceBlock is None:
            self._sourceBlock = sourceBlock

        elif sourceBlock is not None:
            raise BaseException("souce block already defined and cannot be changed anymore")
            

        if self._sourcePort is None:
            self._sourcePort = sourcePort

        elif sourcePort is not None:
            raise BaseException("souce port already defined and cannot be changed anymore")
            

    def lookupSource(self):
        return self

    def set_name(self, name):
        # add a prefix to the autogenerated name
        Signal.set_name(self, self.name + '_' + name)

    @property
    def sourceBlock(self):
        return self._sourceBlock

    def sourcePort(self):
        return self._sourcePort

    def redefine_source(self, sourceBlock, sourcePort):
        self._sourceBlock = sourceBlock
        self._sourcePort = sourcePort


class SimulationInputSignal(Signal):
    """
        A special signal that describes an input to a system.
    """

    def __init__(self, system, datatype = None):

        # give this signal a unique default name
        Signal.__init__(self, system, autogeneratedName = 'signal' + str(system.generate_new_signal_id()), datatype = datatype)

        self.port = system.simulation_input_signal_counter
        system.simulation_input_signal_counter += 1

        # # add to the list of system inputs of system
        # system.append_input_signal( input_signal )


    def is_simulation_input(self):
        return True

    def is_crossing_system_boundary(self, system):
        # as an input to a system the signal crosses the boundaries of the system
        return True

    def lookupSource(self):
        return self
