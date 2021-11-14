from .signal_network.signals import *
from .signal_network.Block import *
# from .system import * 


from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)







class Cluster():
    def __init__(self, destination_signal, id):
        self.id = id
        self.destination_signal = destination_signal
        #self.required_signals = []

        self.dependency_signals_simulation_inputs               = set()
        self.dependency_signals_that_are_sources                = set()
        self.dependency_signals_that_depend_on_a_state_variable = set()
        self.dependency_signals_that_are_junctions              = set()
        self.start_signals                                      = set()
        self.execution_line = [] # the order is important! describes the order in which the signals must be computed inside this cluster

        self.depending_clusters = None

        self.step_back_cluster = None # for graph algs.
        self.is_computed = False # for graph algs.
        self.tmp_i = 0 # for graph algs.

    #
    def update(self):
        self.depending_clusters = [ s.dependency_tree_node.cluster for s in list( self.dependency_signals_that_are_junctions ) ]





class DependencyTreeNode():
    def __init__(self, planned_for_computation_at_level, planned_for_computation_at_delay_level):

        self.this_node_is_a_junction = False
        self.this_node_is_an_input   = False
        self.this_node_is_a_source = False
        self.this_node_depends_on_a_state_variable = False

        self.needed_by = []
        self.needed_by_2 = {} # a map: level -> List of signals
        self.planned_for_computation_at_level       = planned_for_computation_at_level
        self.planned_for_computation_at_delay_level = planned_for_computation_at_delay_level

        self.this_node_is_planned_for_computation = False

        self.directly_depending_signals = []

        self.required_start_signals = []

        # cluster
        self.cluster = None


    def add_needed_by_2(self, level, signal_by_which_this_node_is_needed):

        if level not in self.needed_by_2:
            self.needed_by_2[ level ] = [ signal_by_which_this_node_is_needed ]
        else:    
            self.needed_by_2[ level ].append( signal_by_which_this_node_is_needed )




class QueriedSignal():
    """
        a structure that stores some initial results for a signal to be computed
    """
    def __init__(
        self,
        queried_signal,
        dependency_signals_simulation_inputs,
        dependency_signals_that_are_sources,
        dependency_signals_that_are_junctions,
        dependency_signals_that_depend_on_a_state_variable,

        blocks_to_update_states,  # needed?
        signals_needed_for_state_update_of_involved_blocks

    ):

        self.queried_signal                                     = queried_signal
        self.dependency_signals_simulation_inputs               = dependency_signals_simulation_inputs
        self.dependency_signals_that_are_sources                = dependency_signals_that_are_sources
        self.dependency_signals_that_are_junctions              = dependency_signals_that_are_junctions
        self.dependency_signals_that_depend_on_a_state_variable = dependency_signals_that_depend_on_a_state_variable

        self.blocks_to_update_states                            = blocks_to_update_states
        self.signals_needed_for_state_update_of_involved_blocks = signals_needed_for_state_update_of_involved_blocks

    def __str__(self):

        str = ''
        str += 'The queried signal is '                     + self.queried_signal.name + '. Its dependencies are:'
        str += '\nsystem intput signals: '                  + ','.join( [ s.name for s in self.dependency_signals_simulation_inputs ] )
        str += '\nsignals that are sources: '               + ','.join( [ s.name for s in self.dependency_signals_that_are_sources ] )
        str += '\njunctions: '                              + ','.join( [ s.name for s in self.dependency_signals_that_are_junctions ] )
        str += '\nsignals that depend on state variables: ' + ','.join( [ s.name for s in self.dependency_signals_that_depend_on_a_state_variable ] )
        str += '\n'

        return str


class ExecutionPlan():
    def __init__(
        self,
        clusters
    ):

        self.clusters = clusters
        self.destination_signals = [ c.destination_signal for c in self.clusters ]

        self.reset_plan_builder()


    def reset_plan_builder(self):

        for cluster in self.clusters:
            cluster.is_computed = False
            cluster.tmp_i = 0 # don't know a good name
            #cluster.n_depends_on_other_clusters = len( cluster.dependency_signals_that_are_junctions )

    def get_cluster_from_destination_signal( self, signal ):

        index = self.destination_signals.index( signal )
        return self.clusters[index]


    def print_clusters(self):

        print('clusters')
        print('--------')
        for cluster in self.clusters:

            cluster_destination = cluster.destination_signal

            print('cluster id (' + str(cluster.id) + ') with target signal ' + cluster_destination.name + ' requires ')
        
            print('    * junctions: '       + ', '.join( [ s.name + ' (' + str(s.dependency_tree_node.cluster.id) + ') '  for s in list(cluster.dependency_signals_that_are_junctions) ] ) )
            print('    * inputs: '          + ', '.join( [ s.name for s in list(cluster.dependency_signals_simulation_inputs) ] ) )
            print('    * sources: '         + ', '.join( [ s.name for s in list(cluster.dependency_signals_that_are_sources) ] ) )
            print('    . state dependent: ' + ', '.join( [ s.name for s in list(cluster.dependency_signals_that_depend_on_a_state_variable) ] ) )

            print('    computation order: ' + ', '.join( [ s.name for s in cluster.execution_line ] ) )
            print()

    

    def find_dependencies_of_cluster( self, cluster, reset_plan_builder : bool = False ):
        """
            Computes the input dependencies to compute the given cluster

            For successive calls, only the newly required dependencies are returned.
            The internal states for this behavior can be reset by calling reset_plan_builder().
        """

        input_dependencies = set()
        input_dependencies, cluster_execution_line = self._update_set_of_dependencies_for_cluster( cluster, input_dependencies )

        if reset_plan_builder:
            self.reset_plan_builder()

        return list(input_dependencies), cluster_execution_line


    def find_dependencies_of_clusters( self, clusters, reset_plan_builder : bool = False ):
        """
            Computes the input dependencies needed to compute the given list of clusters

            For successive calls, only the newly required dependencies are returned.
            The internal states for this behavior can be reset by calling reset_plan_builder().
        """

        input_dependencies = set()

        for cluster in clusters:
            input_dependencies, cluster_execution_line = self._update_set_of_dependencies_for_cluster( cluster, input_dependencies )

        if reset_plan_builder:
            self.reset_plan_builder()

        return list(input_dependencies), cluster_execution_line



    def _update_set_of_dependencies_for_cluster( self, cluster, input_dependencies ):

        cluster_execution_line = []

        # init
        current_cluster = cluster

        while True:

            print('at ', current_cluster.destination_signal.name)


            # look for dependencies
            ready_to_compute = True
            #for s in current_cluster.dependency_signals_that_are_junctions:

            tmp_list = list(current_cluster.dependency_signals_that_are_junctions)

            for i in range( current_cluster.tmp_i, len( tmp_list )  ):
                s = tmp_list[i]

                c = s.dependency_tree_node.cluster
                if not c.is_computed:
                    # remember where we stepped at
                    current_cluster.tmp_i = i

                    # step to cluster on which the current one depends on
                    c.step_back_cluster = current_cluster
                    current_cluster = c

                    print('step to ', current_cluster.destination_signal.name)

                    ready_to_compute = False


                    break

            if not ready_to_compute:
                continue

            # cluster can be computed
            cluster_execution_line.append( current_cluster )  #  # NOTE: changed: TODO: adapt c++ implementation accordingly

            # mark cluster as executed
            current_cluster.is_computed = True #  # NOTE: changed: TODO: adapt c++ implementation accordingly

            # add needed input signals
            input_dependencies.update( current_cluster.dependency_signals_simulation_inputs )

            # abort criterion
            if current_cluster == cluster:
                break

            # step back
            current_cluster = current_cluster.step_back_cluster

            print('step back to ', current_cluster.destination_signal.name)


        return input_dependencies, cluster_execution_line




class BuildExecutionPath:
    """
        Find out the order in which signals have to be computed such that a given signal
        'signal_to_calculate' can be calculated. This means finding out all dependencies of
        'signal_to_calculate'. For each call to 'determine_execution_order' only the signals that
        were not already marked as a dependency in previous calls are returned.
        Each call to 'determine_execution_order' gives an instance 'ExecutionLine'
    """
    def __init__(self, system, show_print : int = 1):

        self.system      = system
        self._show_print = show_print

        # list of marked signals (important to reset their visited flags)
        self.signals_involved_in_the_computation = []

        self.signals_that_are_junctions = []

        # query level counter
        self.currently_queried_level = 0

        # list of previously queried signals to compute. 
        # Thus is used to detect algebraic loops:
        # 
        self.queried_signals_by_level = []


        # collect all blocks that are involved and require a state update
        self.blocks_involved_in_a_state_update = set() 
        self.signals_needed_for_state_update_of_involved_blocks = set()



    def __del__(self):
        # reset the markers stored in the signals
        self.reset_markers()

    def printExecutionLine(self):
        pass


    def reset_markers(self):
        # reset all markers / nodes of the dependency graph
        for signal in self.signals_involved_in_the_computation:
            signal.dependency_tree_node = None

        # reset status variables
        self.signals_involved_in_the_computation = []
        self.signals_that_are_junctions = []

        # reset query level counter
        self.currently_queried_level = 0

    def place_marker(self, signal, delay_level):
        # mark the node/signal as being visited (meaning computed)
        
        if signal.dependency_tree_node is None:
            signal.dependency_tree_node = DependencyTreeNode(self.currently_queried_level, delay_level)
            self.signals_involved_in_the_computation.append(signal)

        else:
            # the signal is already marked...
            pass
            #raise BaseException('Internal error: signal ' + signal.name + ' already has a marker')




    def check_if_signal_was_already_planned_in_previous_query(self, signal):

        if signal.dependency_tree_node is not None:
            if signal.dependency_tree_node.planned_for_computation_at_level < self.currently_queried_level:
                return True

        return False


    def check_if_signal_was_already_planned_in_this_query(self, signal):

        if signal.dependency_tree_node is not None:
            if signal.dependency_tree_node.planned_for_computation_at_level == self.currently_queried_level:
                return True

        return False



    def check_if_signal_was_already_planned_in_this_delay_level(self, signal, delay_level):

        if signal.dependency_tree_node is not None:
            if signal.dependency_tree_node.planned_for_computation_at_delay_level == delay_level:
                return True

        return False







    def determine_execution_order(  # rename to query signal
        self, 
        signal_to_calculate : Signal, 
        current_system,         # remove this and replace with self.system
        delay_level : int
    ):

        """
            get the order of computation steps and their order (computation plan) that have
            to be performed to compute 'signal_to_calculate'
            
            For each call to this function, a list is generated that does not contain
            signals that are already part of a previous list (that are already planned to be computed)
            
            This function can be called multiple times and returns only the necessary 
            computations. Computations already planned in previous calls of this function
            are not listed again. (until reset_markers() is called)

            -- results --

            execution_order contains the list of signals to comute in the correct order including
            the target signals. Not included in this list are signals that cross the border to the simulation
            specified by signal_to_calculate.system (coming from an outer system). Further, not included are
            signals that have been computed in a previous call to determine_execution_order().

            dependency_signals contains all signals that are required to comput signalToCalculate
            and either cross the border of a simulation, 
        """

        # TODO: dependency signals should stay as they are but reachableSignals should not contain signals
        #       that already have been calculated. Further, reachableSignals shall also contain dependency if they 
        #       were not already calculated

        if self._show_print > 0:
            print("determine_execution_order on level " + str(self.currently_queried_level) )

        # compute by traversing the tree
        queried_signal = self._explore_dependencies(signal_to_calculate, current_system, delay_level)

        # the iteration level
        self.currently_queried_level = self.currently_queried_level + 1

        # 
        self.queried_signals_by_level.append( queried_signal )

        return queried_signal






    def _explore_dependencies(self, signal_to_calculate, current_system, delay_level : int):
        """
            helper function for determine_execution_order()
        """

        # the list of simulation input signals required for the computation
        dependency_signals_simulation_inputs = set()
        dependency_signals_that_are_junctions = set()
        dependency_signals_that_depend_on_a_state_variable = set()
        dependency_signals_that_are_sources = set()

        # TODO: can be removed
        all_signals_that_are_starting_points_of_execution = []

        # For each signgal execution_order there might be a blocks that
        # has an internal memory. It is required to build a list of those blocks
        # that need a state update after their output(s) are calculated.
        blocks_to_update_states = set()

        #
        signals_needed_for_state_update_of_involved_blocks = set()

        #
        iteration_counter = 0

        iteration_stack_signal_to_investigate = [ signal_to_calculate ]

        # mark the signal
        self.place_marker(signal_to_calculate, delay_level)

        tabs = ''

        while True:

            if len(iteration_stack_signal_to_investigate) == 0:
                # all signals are planned to be computed --> abort the loop
                break

            # get latest item (signal) in the stack of signals to compute
            # signal = iteration_stack_signal_to_investigate[ -1 ]           
            signal = iteration_stack_signal_to_investigate.pop()
            iteration_counter += 1

            # check if the signal is a system input signal
            is_crossing_simulation_border = signal.is_crossing_system_boundary(current_system) #  self.system != startSignal.sim



            if is_crossing_simulation_border:
                # signal is an input to the system
                signal.dependency_tree_node.this_node_is_an_input = True
                dependency_signals_simulation_inputs.add( signal )

                # add starting point for execution
                all_signals_that_are_starting_points_of_execution.append( signal )


                continue


            #
            # request the dynamic/delayed dependencies to compute signal from the block that is having signal as output 
            #
            found_dependencies_via_state_update, block_whose_states_to_update, signals_needed_via_a_state_update = self.find_dependencies_via_a_state_update(signal)
            if found_dependencies_via_state_update:

                # add the signals that are required to perform the state update
                signals_needed_for_state_update_of_involved_blocks.update( signals_needed_via_a_state_update )
                blocks_to_update_states.add( block_whose_states_to_update )

                
                self.blocks_involved_in_a_state_update.add( block_whose_states_to_update )
                self.signals_needed_for_state_update_of_involved_blocks.update( signals_needed_via_a_state_update )   # TODO: This is present twiche, see 5 lines above



                dependency_signals_that_depend_on_a_state_variable.add( signal )
                signal.dependency_tree_node.this_node_depends_on_a_state_variable   = True


                # TODO: mark also as a junction

                # add starting point for execution
                all_signals_that_are_starting_points_of_execution.append( signal )
                



            #
            # request the direct dependencies to compute signal from the block that is having signal as output 
            #

            directly_depending_signals = self.find_dependencies_via_a_direct_feedthrough(signal)

            # store a copy of the results of the function call above
            signal.dependency_tree_node.directly_depending_signals = directly_depending_signals

            if len(directly_depending_signals) == 0:
                # no dependencies to calculate startSignal (e.g. in case of const blocks or blocks without direct feedthrough)
                # Signal is, for example, the output constant block.

                # add starting point for execution
                dependency_signals_that_are_sources.add( signal )
                signal.dependency_tree_node.this_node_is_a_source = True

                all_signals_that_are_starting_points_of_execution.append( signal )
    
                continue


            # put all dependencies on the stack of signals to investigate
            for s in directly_depending_signals:

                # mark the signal
                self.place_marker(s, delay_level)

                s.dependency_tree_node.needed_by.append( signal )
                s.dependency_tree_node.add_needed_by_2(self.currently_queried_level, signal_by_which_this_node_is_needed=signal)

                if self.check_if_signal_was_already_planned_in_this_query( s ):
                    # raise BaseException('detected algebraic loop')

                    pass
                    # continue


                if self.check_if_signal_was_already_planned_in_this_delay_level(s, delay_level):
                    pass



                if self.check_if_signal_was_already_planned_in_previous_query( s ):  # and not simulation input?

                    dependency_signals_that_are_junctions.add(s)

                    # found a junction: signal s is required to compute more than one signal
                    s.dependency_tree_node.this_node_is_a_junction = True
                    self.signals_that_are_junctions.append( s )                # TODO: this is present twiche (see 4 lin4s above)

                    # add starting point for execution
                    all_signals_that_are_starting_points_of_execution.append( s )

                    continue
                

                # signal s was not already planned for computation, hence, append a signal to investigate further
                iteration_stack_signal_to_investigate.append( s )




            # continue in loop
            continue


        # if self._show_print > 0:
        #     print('dependency_signals_simulation_inputs', [ s.name for s in dependency_signals_simulation_inputs ])
        #     print('dependency_signals_through_states', [ s.name for s in signals_needed_for_state_update_of_involved_blocks ])
        #     print('blocks_to_update_states', [ s.name for s in blocks_to_update_states ])


        queried_signal = QueriedSignal(
            signal_to_calculate,
            list( dependency_signals_simulation_inputs ),
            list( dependency_signals_that_are_sources ),
            list( dependency_signals_that_are_junctions ),
            list( dependency_signals_that_depend_on_a_state_variable ),

            list( blocks_to_update_states ),  # needed?
            list( signals_needed_for_state_update_of_involved_blocks )
        )

        return queried_signal


    def _step_back_till_junction_or_input_to_create_cluster(self, destination, static_id):
        #
        # finds: 1) dependencies to compute the given destination 
        # TODO: needs refinement..

        #
        # create new cluster instance
        #

        cluster = Cluster( destination, static_id )
        assert destination.dependency_tree_node.cluster is None
        destination.dependency_tree_node.cluster = cluster

        iteration_stack_signal_to_investigate = [] # .copy()
        iteration_stack_signal_to_investigate.extend( destination.dependency_tree_node.directly_depending_signals )


        while True:

            if len(iteration_stack_signal_to_investigate) == 0:
                # all signals are planned to be computed --> abort the loop
                break

            # get latest item (signal) in the stack of signals to compute
            # signal = iteration_stack_signal_to_investigate[ -1 ]           
            signal = iteration_stack_signal_to_investigate.pop()

            # extract flags
            is_junction                    = signal.dependency_tree_node.this_node_is_a_junction
            is_input                       = signal.dependency_tree_node.this_node_is_an_input
            is_depending_on_state_variable = signal.dependency_tree_node.this_node_depends_on_a_state_variable
            is_source                      = signal.dependency_tree_node.this_node_is_a_source

            # mark as part of the cluster unless it is the target signal of another cluster
            if not is_junction:

                assert signal.dependency_tree_node.cluster is None
                signal.dependency_tree_node.cluster = cluster

#            is_nothing_special   = not (is_input or is_junction 

            if is_depending_on_state_variable:
                destination.dependency_tree_node.cluster.dependency_signals_that_depend_on_a_state_variable.add( signal )

            # 
            if is_junction:
                destination.dependency_tree_node.cluster.dependency_signals_that_are_junctions.add( signal )

            elif is_input:
                destination.dependency_tree_node.cluster.dependency_signals_simulation_inputs.add( signal )


            elif is_source:
                destination.dependency_tree_node.cluster.dependency_signals_that_are_sources.add( signal )

            # step backwards
            else:

                iteration_stack_signal_to_investigate.extend( signal.dependency_tree_node.directly_depending_signals )

        return cluster



    def _explore_computation_plan_in_cluster( self, cluster ):

        start_signals = list( cluster.start_signals )


        # vars
        execution_line = []
        iteration_stack_signal_to_investigate = []

        # handle special case: no start signals. This happens when the cluster target signal is the output of
        # a block only depending on its state (e.g., the delay block)

        if len( start_signals ) == 0:
            execution_line.append( cluster.destination_signal )
            return execution_line

        # initiate iteration
        for start_signal in start_signals:

            # execution_line.append( start_signal )
            start_signal.dependency_tree_node.this_node_is_planned_for_computation = True
            
            # step forward
            signals_step_forward = start_signal.dependency_tree_node.needed_by
            iteration_stack_signal_to_investigate.extend( signals_step_forward )  # TODO: add only signals belonging to the current cluster


        # iterate
        iteration_counter = 0

        while True:

            if len(iteration_stack_signal_to_investigate) == 0:
                # all signals are planned to be computed --> abort the loop
                break

            # get latest item (signal) in the stack of signals to compute
            # signal = iteration_stack_signal_to_investigate[ -1 ]
            signal = iteration_stack_signal_to_investigate.pop()
            iteration_counter += 1

            # if signal is signal.dependency_tree_node.cluster.destination_signal:
            #     # reached the target
            #     execution_line.append( signal )
            #     signal.dependency_tree_node.this_node_is_planned_for_computation = True
            #     break

            if signal.dependency_tree_node.cluster is not cluster:
                # do no step into other clusters than this 'cluster'
                continue

            if signal.dependency_tree_node.this_node_is_planned_for_computation:
                print('already scheduled', signal.name)
                continue

            # check if all dependencies to compute signal are satisfied already
            signal_is_ready_to_be_computed = True
            for s in signal.dependency_tree_node.directly_depending_signals:
                if not s.dependency_tree_node.this_node_is_planned_for_computation:

                    signal_is_ready_to_be_computed = False

                    break 

            if not signal_is_ready_to_be_computed:
                # push back signal to the begin of the list of signals to investigate
                iteration_stack_signal_to_investigate.insert(0, signal)

                continue





            # Now that all dependencies are available (the check above passed),
            # plan to compute this signal; add to execution line.
            execution_line.append( signal )
            signal.dependency_tree_node.this_node_is_planned_for_computation = True

            if signal is signal.dependency_tree_node.cluster.destination_signal:
                # reached the target
                break

            # step forward
            signals_step_forward = signal.dependency_tree_node.needed_by
            iteration_stack_signal_to_investigate.extend( signals_step_forward )

            continue


        print('_explore_computation_plan_in_cluster: execution_line', [ s.name for s in execution_line ], 'start_signals:', [s.name for s in start_signals])
         

        # initiate iteration
        for start_signal in start_signals:

            # undo mark do not confuse other calls of this function
            start_signal.dependency_tree_node.this_node_is_planned_for_computation = False
            


        return execution_line








    def generate_computation_plan(
        self
    ):
        """
            finish and return a plan to compute the signals
        """

        # finish query
        self.number_of_level = self.currently_queried_level
        self.currently_queried_level = None

        #
        # investigate clusters:
        #
        #   - get dependencies for each destination signal and each junction
        #

        cluster_destinations = set( [ q.queried_signal for q in self.queried_signals_by_level ] )
        cluster_destinations.update(
            set( self.signals_that_are_junctions )
        )

        clusters = []
        static_cluster_id_counter = 0 # generate a unique id for each cluster

        for cluster_destination in list(cluster_destinations):

            cluster = self._step_back_till_junction_or_input_to_create_cluster( cluster_destination, static_cluster_id_counter )
            static_cluster_id_counter += 1
            clusters.append( cluster )

            # start_signals = set()
            # start_signals.update(   cluster_destination.dependency_tree_node.cluster.dependency_signals_that_are_junctions  )
            # start_signals.update(   cluster_destination.dependency_tree_node.cluster.dependency_signals_simulation_inputs  )
            # start_signals.update(   cluster_destination.dependency_tree_node.cluster.dependency_signals_that_are_sources  )
            # cluster_destination.dependency_tree_node.cluster.start_signals = list(start_signals)
            

            cluster_destination.dependency_tree_node.cluster.start_signals.update(  
                cluster_destination.dependency_tree_node.cluster.dependency_signals_that_are_junctions
             )
            cluster_destination.dependency_tree_node.cluster.start_signals.update(  
                cluster_destination.dependency_tree_node.cluster.dependency_signals_simulation_inputs
             )
            cluster_destination.dependency_tree_node.cluster.start_signals.update(  
                cluster_destination.dependency_tree_node.cluster.dependency_signals_that_are_sources
             )

        #
        # build execution lines for each cluster
        #

        for cluster in clusters:

            execution_line = self._explore_computation_plan_in_cluster( cluster )
            cluster.execution_line = execution_line


        #
        # build and print execution plan
        #

        for c in clusters:
            c.update()

        execution_plan = ExecutionPlan(clusters)
        execution_plan.print_clusters()


        #
        execution_plan.find_dependencies_of_cluster( clusters[0] )


        return execution_plan









    def find_dependencies_via_a_state_update(self, signal):


        # get the blocks prototype function to calculate startSignal
        block_whose_states_to_update = signal.getSourceBlock()
        blocksPrototype = block_whose_states_to_update.getBlockPrototype()

        #
        # check if the block that yields startSignal uses internal-states to compute startSignal
        #

        signals_needed_via_a_state_update = blocksPrototype.config_request_define_state_update_input_dependencies( signal )
        if signals_needed_via_a_state_update is not None:

            if self._show_print > 1:
                print(tabs + "--- signals needed *indirectly* to compute " + signal.name + " (through state update) --" )

            # 

            # please note: blocksPrototype.config_request_define_state_update_input_dependencies might return some undetermined signals that are resolved here
            resolveUndeterminedSignals( signals_needed_via_a_state_update )

            # add the signals that are required to perform the state update
            #dependency_signals_through_states.extend( inputs_to_update_states_tmp )
            #blocks_to_update_states.append( block )

            if self._show_print > 1:
                for s in signals_needed_via_a_state_update:
                    print(Fore.MAGENTA + tabs + "-> S " + s.name )        


            return True, block_whose_states_to_update, signals_needed_via_a_state_update

        return False, None, None



    def find_dependencies_via_a_direct_feedthrough(self, signal):


        # get the blocks prototype function to calculate startSignal
        blocks_prototype = signal.getSourceBlock().getBlockPrototype()


        #
        # find out the links to other signals but only the ones that are 
        # needed to calculate 'startSignal'
        #


        depending_signals = blocks_prototype.config_request_define_feedforward_input_dependencies(signal)
        resolveUndeterminedSignals( depending_signals )

        if self._show_print > 1:
            
            print(tabs + "--- direct dependencies to calculate " + signal.name + " --" )

            for s in depending_signals:
                print(Fore.MAGENTA + tabs + "-> S " + s.name )        


        return depending_signals


