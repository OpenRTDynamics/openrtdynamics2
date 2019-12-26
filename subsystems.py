

# from BlockPrototypes import Operator1
from typing import Dict, List

import dynamics as dy
import BlockPrototypes as block_prototypes

from Signal import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal



class sub:
    def __init__(self):

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

        print("Entering subsystem")

        dy.enter_subsystem('subsystem')

        return self


    def __exit__(self, type, value, traceback):

        print("leave subsystem")

        # set the outputs of the system
        dy.get_simulation_context().setPrimaryOutputs( dy.unwrap_list( self._outputs_inside_subsystem ) )

        # Please note: in case it is really necessary to specify a system != None here, use the upper-level system
        # not the embedded one.

        # store an embeeder prototype (as generated by dy.GenericSubsystem) into the date structure of the subsystem
        embeddedingBlockPrototype = dy.GenericSubsystem( sim=dy.get_simulation_context().UpperLevelSim, inputSignals=None, manifest=None, additionalInputs=None )

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


    def __init__(self, condition_signal : dy.SignalUserTemplate):
        self._condition_signal = condition_signal

        self._outputs_inside_subsystem = []
        self._outputs_of_embedding_block = []

    def add_output(self, output_signal : dy.SignalUserTemplate):

        print("added output signal " + output_signal.name)

        self._outputs_inside_subsystem.append(output_signal)


        # use SubsystemOutputLink to generate a new signal to be used outside of the subsystem
        # This creates a link output_signal_of_embedding_system --> output_signal
        output_signal_of_embedding_system = dy.SubsystemOutputLinkUser( dy.get_simulation_context().UpperLevelSim, output_signal )

        # inherit datatype from output_signal
        output_signal_of_embedding_system.inherit_datatype( output_signal )


        self._outputs_of_embedding_block.append( output_signal_of_embedding_system.unwrap )



        return output_signal_of_embedding_system


    def __enter__(self):

        print("Entering if subsystem")

        dy.enter_subsystem('if_subsystem')

        return self


    def __exit__(self, type, value, traceback):

        print("leave if subsystem")

        # set the outputs of the system
        dy.get_simulation_context().setPrimaryOutputs( dy.unwrap_list( self._outputs_inside_subsystem ) )

        # Please note: in case it is really necessary to specify a system != None here, use the upper-level system
        # not the embedded one.

        # store an embeeder prototype (as generated by dy.GenericSubsystem) into the date structure of the subsystem
        embeddedingBlockPrototype = dy.TruggeredSubsystem( sim=dy.get_simulation_context().UpperLevelSim, inputSignals=None, manifest=None, trigger=self._condition_signal.unwrap )

        dy.get_simulation_context().embeddedingBlockPrototype = embeddedingBlockPrototype

        #
        # Link output_signal_of_embedding_system to the outputs created by dy.GenericSubsystem
        #

        embeddedingBlockPrototype.set_anonymous_output_signal_to_connect(   self._outputs_of_embedding_block  )


        # TODO: add a system wrapper/embedded (e.g. this if-block) to leave_system
        dy.leave_system()

