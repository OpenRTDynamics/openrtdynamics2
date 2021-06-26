from typing import Dict, List

from . import lang as dy
from . import block_prototypes as bp
from . import signal_interface as si
from .system_context import generate_subsystem_name, enter_subsystem
from .diagram_core.signal_network.signals import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal

"""
    User interface for subsystems 
"""




class sub_if:
    """

        NOTE: in case the if condition is false, the outputs are hold. Eventally uninitialized.
    """


    def __init__(
            self, 
            condition_signal : dy.SignalUserTemplate, 
            subsystem_name              = None, 
            prevent_output_computation  = False
        ):

        if subsystem_name is not None:
            self._subsystem_name = generate_subsystem_name() + '_' + subsystem_name
        else:
            self._subsystem_name = generate_subsystem_name()

        self._condition_signal = condition_signal
        self._prevent_output_computation = prevent_output_computation

        # 
        self._outputs_of_embedded_subsystem = []

        # outputs (links to the subsystem outputs) to be used by the user
        self._output_links = None


    def set_outputs(self, signals):
        self._outputs_of_embedded_subsystem = signals.copy()

    def __enter__(self):
        self._system = enter_subsystem(self._subsystem_name )

        return self


    def __exit__(self, type, value, traceback):

        embedded_subsystem = dy.get_current_system()

        # set the outputs of the system
        embedded_subsystem.set_primary_outputs( si.unwrap_list( self._outputs_of_embedded_subsystem ) )


        self._subsystem_wrapper = bp.SystemWrapper(embedded_subsystem)

        # leave the context of the subsystem
        dy.leave_system()

        #
        # now in the system in which the embeding block (including the logic) shall be placed.
        #

        # create the embedder prototype
        embeddedingBlockPrototype = bp.TriggeredSubsystem( 
            system=dy.get_current_system(), 
            control_input=si.unwrap( self._condition_signal ), 
            subsystem_wrapper=self._subsystem_wrapper,
            prevent_output_computation = self._prevent_output_computation
        )


        # connect the normal outputs via links
        self._output_links = si.wrap_signal_list( embeddedingBlockPrototype.outputs )

        # connect the additional (control) outputs
        # self._state_output = si.wrap_signal( embeddedingBlockPrototype.state_output )

    @property
    def outputs(self):

        if self._output_links is None:
            BaseException("Please close the subsystem before querying its outputs: Maybe one less tab when calling this function?")
        
        return self._output_links
    






class sub_loop:
    """

    """


    def __init__(self, max_iterations : int, subsystem_name = None ):

        if subsystem_name is not None:
            self._subsystem_name = generate_subsystem_name() + '_' + subsystem_name
        else:
            self._subsystem_name = generate_subsystem_name()

        self._max_iterations = max_iterations

        # control outputs of the embedded subsystem
        self._until_signal = None
        self._yield_signal = None

        # 
        self._outputs_of_embedded_subsystem = []

        # outputs (links to the subsystem outputs) to be used by the user
        self._output_links = None


    def set_outputs(self, signals):
        self._outputs_of_embedded_subsystem = si.unwrap_list( signals.copy() )

    def loop_until(self, condition_signal):
        self._until_signal = condition_signal.unwrap

    def loop_yield(self, condition_signal):
        self._yield_signal = condition_signal.unwrap

    def __enter__(self):

        self._system = enter_subsystem(self._subsystem_name )

        return self


    def __exit__(self, type, value, traceback):

        embedded_subsystem = dy.get_current_system()

        if self._until_signal is None and self._yield_signal is None:
            raise BaseException('sub_loop: Please specify either an abort or a yield condition. This can be achieved by the methods system.loop_until(condition) or system.loop_yield(condition).')

        # collect all outputs
        all_output_signals = []
        all_output_signals.extend(self._outputs_of_embedded_subsystem)
        if self._until_signal is not None:
            all_output_signals.append(self._until_signal)
        if self._yield_signal is not None:
            all_output_signals.append(self._yield_signal)

        # set the outputs of the system
        embedded_subsystem.set_primary_outputs(  all_output_signals  )

        self._subsystem_wrapper = bp.SystemWrapper(embedded_subsystem)

        # leave the context of the subsystem
        dy.leave_system()

        #
        # now in the system in which the embedder block (including the logic) shall be placed.
        #

        # create the embedder prototype
        embeddedingBlockPrototype = bp.LoopUntilSubsystem( system=dy.get_current_system(), 
                max_iterations=self._max_iterations, 
                subsystem_wrapper=self._subsystem_wrapper,
                add_until_control=self._until_signal is not None,
                add_yield_control=self._yield_signal is not None)

        # connect the normal outputs via links
        self._output_links = si.wrap_signal_list( embeddedingBlockPrototype.outputs )


    @property
    def outputs(self):

        if self._output_links is None:
            BaseException("Please close the subsystem before querying its outputs")
        
        return self._output_links
    









#
# new stuff
#





class SwitchPrototype:
    """
        a switch for subsystems that are implemented by SwitchedSubsystemPrototype (class to be derived)

        switch_subsystem_name        - the name of the switch
        number_of_control_outputs - the number of system outputs in addition to the embedded systems outputs
                                       i.e. control outputs of a switch/statemaching/...

        - member variables -

        self._switch_output_links    - overwrite by derived class when calling on_exit()
        self.outputs                 - a list of output signals as defined by self._switch_output_links

        - methods to be defined -

        on_exit(subsystem_wrapper)  - callback once all subsystems were defined
                                         during this callback self._switch_output_links must be defined

    """

    # NOTE: in case of an exception, nothing happens just __exit__ is called silently which then aborts

    def __init__(self, switch_subsystem_name, number_of_control_outputs=0):

        self._switch_subsystem_name = switch_subsystem_name
        self._total_number_of_subsystem_outputs = None
        self._switch_output_links = None
        self._switch_system = None
        self._number_of_control_outputs = number_of_control_outputs
        self._number_of_switched_outputs = None

        # List [ bp.SystemWrapper ]
        self._subsystem_wrapper = None

        # List [ switch_single_sub ]
        self._subsystem_list = None


    def new_subsystem(self, subsystem_name = None):
        raise BaseException("to be implemented")

    def __enter__(self):

        self._subsystem_list = []
        self._subsystem_wrapper = []

        return self

    def on_exit(self, subsystem_wrapper):
        """
            called when all subsystems have been added to the switch

            subsystem_wrapper - the list of subsystem wrappers of type bp.SystemWrapper
        """
        raise BaseException("to be implemented")

    def __exit__(self, type, value, traceback):
        # collect all prototyes that embed the subsystems
        for system in self._subsystem_list:
            self._subsystem_wrapper.append( system.subsystem_prototype )

        # analyze the default subsystem (the first) to get the output datatypes to use
        for subsystem in [ self._subsystem_list[0] ]:

            # get the outputs that will serve as reference points for datatype inheritance
            number_of_normal_outputs = len( subsystem.outputs ) - self._number_of_control_outputs
            self._reference_outputs = subsystem.outputs[0:number_of_normal_outputs]
            self._total_number_of_subsystem_outputs = len(subsystem.outputs)

            self._number_of_switched_outputs = self._total_number_of_subsystem_outputs - self._number_of_control_outputs

        self.on_exit( self._subsystem_wrapper )

    @property
    def outputs(self):

        if self._switch_output_links is None:
            BaseException("Please close the switch subsystem before querying its outputs")
        
        return self._switch_output_links
    


class SwitchedSubsystemPrototype:
    """
        A single subsystem as part of a switch (implemented by SwitchPrototype) in between multiple subsystems

        - methods to called by the user -

        set_switched_outputs(signals)  - connect a list of signals to the output of the switch
    """

    # NOTE: in case of an exception, nothing happens just __exit__ is called silently which then aborts

    def __init__(self, subsystem_name = None ):

        if subsystem_name is not None:
            self._subsystem_name = generate_subsystem_name() + '_' + subsystem_name
        else:        
            self._subsystem_name = generate_subsystem_name()

        self._outputs_of_embedded_subsystem = None

        self._system = None
        self._anonymous_output_signals = None
        self._subsystem_wrapper = None

    @property
    def system(self):
        return self._system

    @property
    def name(self):
        return self._subsystem_name

    @property
    def outputs(self):
        return self._outputs_of_embedded_subsystem

    def set_switched_outputs(self, signals):
        """
            connect a list of outputs to the switch that switches between multiple subsystems of this kind

            use self.set_switched_outputs_prototype in the derived classes to set this
        """
        
        BaseException("to be implemented")

    def set_switched_outputs_prototype(self, signals):
        """
            connect a list of outputs to the switch that switches between multiple subsystems of this kind
        """

        if self._outputs_of_embedded_subsystem is None:
            self._outputs_of_embedded_subsystem = signals.copy()
        else:
            raise BaseException("tried to overwrite previously set output")





    def __enter__(self):
        self._system = enter_subsystem(self._subsystem_name )

        return self


    def __exit__(self, type, value, traceback):
        embedded_subsystem = dy.get_current_system()

        # set the outputs of the system
        embedded_subsystem.set_primary_outputs( si.unwrap_list( self._outputs_of_embedded_subsystem ) )

        self._subsystem_wrapper = bp.SystemWrapper(embedded_subsystem)

        # leave the context of the subsystem
        dy.leave_system()

    @property
    def subsystem_prototype(self):
        return self._subsystem_wrapper


##
##
## Derivatives of SwitchedSubsystemPrototype
##
##




#
# Switch among subsystems i.e. similar to select/case
#

class SwitchedSubsystem(SwitchedSubsystemPrototype):
    """
        A single subsystem as part of a switch (implemented by SwitchPrototype) in between multiple subsystems

        - methods to be called by the user -

        set_switched_outputs(signals)  - connect a list of signals to the output of the switch
    """
    def __init__(self, subsystem_name = None ):

        SwitchedSubsystemPrototype.__init__(self, subsystem_name)


    def set_switched_outputs(self, signals):
        """
            connect a list of outputs to the switch that switches between multiple subsystems of this kind
        """

        self.set_switched_outputs_prototype(signals)


class sub_switch(SwitchPrototype):
    def __init__(self, switch_subsystem_name, select_signal : dy.SignalUserTemplate ):

        self._select_signal = select_signal
        SwitchPrototype.__init__(self, switch_subsystem_name, number_of_control_outputs=0)

    def new_subsystem(self, subsystem_name = None):

        system = SwitchedSubsystem(subsystem_name=subsystem_name)
        self._subsystem_list.append(system)

        return system


    def on_exit(self, subsystem_wrappers):

        # create the embedding prototype
        embeddedingBlockPrototype = bp.SwitchSubsystems( system=dy.get_current_system(), 
                control_input=self._select_signal.unwrap, 
                subsystem_wrappers=subsystem_wrappers, 
                reference_outputs=  si.unwrap_list( self._reference_outputs ) )

        # connect the normal outputs via links
        self._switch_output_links = si.wrap_signal_list( embeddedingBlockPrototype.switched_normal_outputs )

        # connect the additional (control) outputs
        # -- None --



#
# State machines
#

class state_sub(SwitchedSubsystemPrototype):
    """
        A single subsystem as part of a state machine (implemented by sub_statemachine)

        - methods to called by the user -

        set_switched_outputs(signals, state_signal)  - connect a list of signals to the output of the state machine
    """

    def __init__(
            self, 
            subsystem_name = None
        ):
        SwitchedSubsystemPrototype.__init__(self, subsystem_name)

        self._output_signals = None
        self._state_signal = None


    def set_switched_outputs(self, signals, state_signal):
        """
            set the output signals of a subsystem embedded into the state machine

            - signals      - normal system output that are forwarded using a switch
            - state_signal - control signal indicating the next state the state machine enters
        """
        self._output_signals = signals
        self._state_signal = state_signal

        self.set_switched_outputs_prototype( signals +  [state_signal] )

    @property
    def state_control_output(self):
         return self._state_signal

    @property
    def subsystem_outputs(self):
        return self._output_signals



class sub_statemachine(SwitchPrototype):
    """
        A state machine subsystem

        - properties -

        self.state - status signal of the state machine (available after 'with sub_statemachine' has findished)
    """
    def __init__(
            self, 
            switch_subsystem_name  : str,
            immediate_state_switch : bool         = False            
        ):

        self._immediate_state_switch = immediate_state_switch

        number_of_control_outputs = 1 # add one control output to inform about the current state

        SwitchPrototype.__init__(self, switch_subsystem_name, number_of_control_outputs )

        # state output signal undefined until defined by on_exit() 
        self._state_output = None

    @property
    def state(self):
        """
            get the signal describing the current state
        """
        return self._state_output

    def new_subsystem(self, subsystem_name = None):

        system = state_sub(subsystem_name=subsystem_name)
        self._subsystem_list.append(system)

        return system

    def on_exit(self, subsystem_prototypes):

        # create the embedding prototype
        embeddedingBlockPrototype = bp.StatemachineSwitchSubsystems( 
            system                 = dy.get_current_system(), 
            subsystem_wrappers     = subsystem_prototypes, 
            reference_outputs      = si.unwrap_list( self._reference_outputs ),
            immediate_state_switch = self._immediate_state_switch
        )

        # connect the normal outputs via links
        self._switch_output_links = si.wrap_signal_list( embeddedingBlockPrototype.switched_normal_outputs )

        # connect the additional (control) outputs
        self._state_output = si.wrap_signal( embeddedingBlockPrototype.state_control )

