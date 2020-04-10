

# from BlockPrototypes import Operator1
from typing import Dict, List

import dynamics as dy
import BlockPrototypes as block_prototypes

from CodeGenHelper import *
import SignalInterface as si

from Signal import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal



class sub:
    def __init__(self, subsystem_name = None ):

        if subsystem_name is not None:
            self._subsystem_name = subsystem_name
        else:
            self._subsystem_name = dy.generate_subsystem_name()

        self._outputs_inside_subsystem = []
        self._outputs_of_embedding_block = []

    def add_output(self, output_signal : dy.SignalUserTemplate):

        self._outputs_inside_subsystem.append(output_signal)


        # use SubsystemOutputLink to generate a new signal to be used outside of the subsystem
        # This creates a link output_signal_of_embedding_system --> output_signal
        output_signal_of_embedding_system = dy.SubsystemOutputLinkUser( dy.get_simulation_context().UpperLevelSim, output_signal )

        # inherit datatype from output_signal
        output_signal_of_embedding_system.inherit_datatype( output_signal )


        self._outputs_of_embedding_block.append( output_signal_of_embedding_system.unwrap )

        return output_signal_of_embedding_system

    def set_outputs(self, signals):
        """
            connect the list of outputs
        """
        return_signals = []

        for s in signals:
            return_signals.append( self.add_output( s ) )

        return return_signals




    def __enter__(self):

        print("enterq subsystem " + self._subsystem_name )
        dy.enter_subsystem(self._subsystem_name )

        return self


    def __exit__(self, type, value, traceback):

        print("leave subsystem " + self._subsystem_name )

        # set the outputs of the system
        dy.get_simulation_context().setPrimaryOutputs( dy.unwrap_list( self._outputs_inside_subsystem ) )

        # Please note: in case it is really necessary to specify a system != None here, use the upper-level system
        # not the embedded one.

        # store an embeeder prototype (as generated by dy.GenericSubsystem) into the date structure of the subsystem
        embeddedingBlockPrototype = dy.GenericSubsystem( sim=dy.get_simulation_context().UpperLevelSim, 
                                                        inputSignals=None, manifest=None, 
                                                        additionalInputs=None )

        dy.get_simulation_context().embeddedingBlockPrototype = embeddedingBlockPrototype

        #
        # Link output_signal_of_embedding_system to the outputs created by dy.GenericSubsystem
        #

        embeddedingBlockPrototype.set_anonymous_output_signal_to_connect(   self._outputs_of_embedding_block  )


        # TODO: add a system wrapper/embedded (e.g. this if-block) to leave_system
        dy.leave_system()









class sub_if:
    """

        NOTE: in case the if condition is false, the outputs are hold. Eventally uninitialized.
    """


    def __init__(self, condition_signal : dy.SignalUserTemplate, subsystem_name = None, prevent_output_computation = False ):

        if subsystem_name is not None:
            self._subsystem_name = subsystem_name
        else:
            self._subsystem_name = dy.generate_subsystem_name()

        self._condition_signal = condition_signal
        self._prevent_output_computation = prevent_output_computation

        self._outputs_inside_subsystem = []
        self._outputs_of_embedding_block = []

    def add_output(self, output_signal : dy.SignalUserTemplate):

        self._outputs_inside_subsystem.append(output_signal)

        # use SubsystemOutputLink to generate a new signal to be used outside of the subsystem
        # This creates a link output_signal_of_embedding_system --> output_signal
        output_signal_of_embedding_system = dy.SubsystemOutputLinkUser( dy.get_simulation_context().UpperLevelSim, output_signal )

        # inherit datatype from output_signal
        output_signal_of_embedding_system.inherit_datatype( output_signal )

        self._outputs_of_embedding_block.append( output_signal_of_embedding_system.unwrap )

        return output_signal_of_embedding_system


    def __enter__(self):

        print("enter triggered subsystem " + self._subsystem_name )
        dy.enter_subsystem(self._subsystem_name )

        return self


    def __exit__(self, type, value, traceback):

        print("leave triggered subsystem " + self._subsystem_name )

        # set the outputs of the system
        dy.get_simulation_context().setPrimaryOutputs( dy.unwrap_list( self._outputs_inside_subsystem ) )

        # Please note: in case it is really necessary to specify a system != None here, use the upper-level system
        # not the embedded one.

        # store an embeeder prototype (as generated by dy.GenericSubsystem) into the date structure of the subsystem
        embeddedingBlockPrototype = dy.TruggeredSubsystem( sim=dy.get_simulation_context().UpperLevelSim, 
            inputSignals=None, 
            N_outputs=len(self._outputs_inside_subsystem),
            manifest=None, 
            trigger=self._condition_signal.unwrap,
            prevent_output_computation=self._prevent_output_computation )

        
        for i in range(0, len( embeddedingBlockPrototype.outputs )):
            embeddedingBlockPrototype.outputs[i].inherit_datatype_from_signal( self._outputs_inside_subsystem[i].unwrap() )

        #dy.get_simulation_context().embeddedingBlockPrototype = embeddedingBlockPrototype

        #
        # Link output_signal_of_embedding_system to the outputs created by dy.GenericSubsystem
        #

        #embeddedingBlockPrototype.set_anonymous_output_signal_to_connect(   self._outputs_of_embedding_block  )


        # TODO: add a system wrapper/embedded (e.g. this if-block) to leave_system
        dy.leave_system()














class switch_single_sub:
    """
        A subsystem contained among others e.g. in a switch
    """
    def __init__(self, subsystem_name = None ):

        if subsystem_name is not None:
            self._subsystem_name = subsystem_name
        else:
            self._subsystem_name = dy.generate_subsystem_name()

        self._outputs_inside_subsystem = None

        self._system = None
        self._anonymous_output_signals = None
        self._embeddedingBlockPrototype = None

    @property
    def system(self):
        return self._system

    @property
    def name(self):
        return self._subsystem_name

    @property
    def outputs(self):
        return self._outputs_inside_subsystem


    def set_switched_outputs(self, signals):
        """
            connect a list of outputs to the switch that switches between multple subsystems of this kind
        """

        if self._outputs_inside_subsystem is None:
            
            self._outputs_inside_subsystem = []
            for s in signals:
                self._outputs_inside_subsystem.append( s )

        else:
            raise BaseException("tried to overwrite previously set outputs")


    def __enter__(self):

        print("enter system " + self._subsystem_name)

        self._system = dy.enter_subsystem(self._subsystem_name )

        return self


    def __exit__(self, type, value, traceback):
        #
        number_of_subsystem_ouputs = len(self._outputs_inside_subsystem)

        # set the outputs of the system
        dy.get_simulation_context().setPrimaryOutputs( dy.unwrap_list( self._outputs_inside_subsystem ) )

        # create generic subsystem prototype
        self._embeddedingBlockPrototype = dy.GenericSubsystem( sim=dy.get_simulation_context().UpperLevelSim, 
                                                    manifest=None, inputSignals=None, 
                                                    additionalInputs=None, 
                                                    embedded_subsystem=dy.get_simulation_context(),
                                                    N_outputs=number_of_subsystem_ouputs )

        for i in range(0, len( self._embeddedingBlockPrototype.outputs )):

            output_signal_of_embedding_block = self._embeddedingBlockPrototype.outputs[i]
            output_signal_of_subsystem = self._outputs_inside_subsystem[i].unwrap

            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )


        dy.leave_system()

    @property
    def subsystem_prototype(self):
        return self._embeddedingBlockPrototype




class sub_switch:
    """
        a switch for subsystems
    """


    def __init__(self, switch_subsystem_name, select_signal : dy.SignalUserTemplate ):

        self._select_signal = select_signal
        self._switch_subsystem_name = switch_subsystem_name
        self._number_of_outputs = None
        self._switch_output_links = None
        self._switch_system = None

        # List [ dy.GenericSubsystem ]
        self._subsystem_prototypes = None

        # List [ switch_single_sub ]
        self._subsystem_list = None


    def new_subsystem(self, subsystem_name = None):

        # system = None # TODO

        system = switch_single_sub(subsystem_name=subsystem_name)

        self._subsystem_list.append(system)

        return system


    def __enter__(self):

        self._subsystem_list = []
        self._subsystem_prototypes = []

        # self._switch_system = dy.enter_subsystem( self._switch_subsystem_name )

        return self


    def __exit__(self, type, value, traceback):

        # 

        # collect all prototyes thet embedd the subsystems
        for system in self._subsystem_list:
            self._subsystem_prototypes.append( system.subsystem_prototype )

        # analyze the default subsystem (the first) to get the output datatypes to use
        for subsystem in [ self._subsystem_list[0] ]:

            # print("The reference outputs are: " + signalListHelper_names_string( subsystem.outputs ) )

            # get the outputs that will serve as reference points for datatype inheritance
            self._reference_outputs = subsystem.outputs
            self._number_of_outputs = len(subsystem.outputs)


        # create the  embeeder prototype
        embeddedingBlockPrototype = dy.MultiSubsystemEmbedder( sim=dy.get_simulation_context(), 
                additional_inputs=[ self._select_signal.unwrap ], subsystem_prototypes=self._subsystem_prototypes, N_outputs=self._number_of_outputs )

        for i in range(0, len( embeddedingBlockPrototype.outputs )):

            output_signal_of_embedding_block = embeddedingBlockPrototype.outputs[i]
            output_signal_of_subsystem = self._reference_outputs[i].unwrap
            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )

        #
        self._switch_output_links = si.wrap_signal_list( embeddedingBlockPrototype.outputs )


    @property
    def outputs(self):

        if self._switch_output_links is None:
            BaseException("Please close the swicth subsystem before querying its outputs")
        
        return self._switch_output_links
    