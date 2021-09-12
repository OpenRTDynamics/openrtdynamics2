from .signal_network.signals import *
from .signal_network.Block import *
# from .system import * 


from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)








class ExecutionLine():
    """
        This is a data structure
        
        It contains a list 'signalOrder' of signals to be computed in the given order.
        The computation of these signals depends on a list of signals given by
        'dependencySignals'.
    """

    def __init__(
        self,
        signalOrder : List[ Signal ],
        dependencySignalsSimulationInputs : List[ Signal ],
        blocksToUpdateStates : List[ Block ],
        dependencySignalsThroughStates : List[ Signal ]
    ):
        self.signalOrder                       = signalOrder
        self.dependencySignalsSimulationInputs = dependencySignalsSimulationInputs
        self.blocksToUpdateStates              = blocksToUpdateStates
        self.dependencySignalsThroughStates    = dependencySignalsThroughStates

    def printExecutionLine(self):
        print("------ print of execution line -----")

        print(Fore.RED + "dependent sources of any kind:")

        # for s in self.dependencySignals:
        #     print("  - " + s.name )

        print(Fore.RED + "dependent sources (simulation inputs):")
                
        for s in self.dependencySignalsSimulationInputs:
            print("  - " + s.name )

        print(Fore.RED + "dependent sources (through state-dependend blocks):")
        
        for s in self.dependencySignalsThroughStates:
            print("  - " + s.name )

        print(Fore.GREEN + "execution order:")

        for s in self.signalOrder:
            print("  - " + s.name )

        print(Fore.GREEN + "blocks whose states must be updated:")

        for block in self.blocksToUpdateStates:
            print("  - " + block.name )


    def getSignalsToExecute(self):
        l = []

        l.extend( self.signalOrder )

        return l


    def appendExecutionLine(self, executionLineToAppend):

        # merge dependencySignals: only add the elements of executionLineToAppend.dependencySignals
        # to self.dependencySignals that are not part of self.dependencySignals or self.signalOrder

        # TODO: to optimize: use sets to merge

        # for s in executionLineToAppend.dependencySignals:
        #     if not s in self.dependencySignals and not s in self.signalOrder:
        #         self.dependencySignals.append(s)


        for s in executionLineToAppend.dependencySignalsSimulationInputs:
            if not s in self.dependencySignalsSimulationInputs and not s in self.signalOrder:
                self.dependencySignalsSimulationInputs.append(s)

        
        for s in executionLineToAppend.dependencySignalsThroughStates:
            if not s in self.dependencySignalsThroughStates and not s in self.signalOrder:
                self.dependencySignalsThroughStates.append(s)

        
        original_list_tmp = self.signalOrder.copy()

        for s in executionLineToAppend.signalOrder:
            # TODO: (for optimization purposes) 
            # check if there common blocks in the list. (only in case a block has more than one
            # output signals and one of these signals is in the list executionLineToAppend.signalOrder
            # and another one in self.signalOrder  )

            # just append the 
            if not s in original_list_tmp:
                self.signalOrder.append( s )

            else:
                print("appendExecutionLine: skipped to add " + s.name)




        original_list_tmp = self.blocksToUpdateStates.copy()

        for b in executionLineToAppend.blocksToUpdateStates:
            # TODO: (for optimization purposes) 
            # check if there comcon blocks in the list. 

            # just append the 
            if not b in original_list_tmp:
                self.blocksToUpdateStates.append( b )


class Cluster():
    def __init__(self, destination_signal, id):
        self.id = id
        self.destination_signal = destination_signal
        self.required_signals = []

        self.dependency_signals_simulation_inputs = []
        self.dependency_signals_that_are_sources = []
        self.dependency_signals_that_depend_on_a_state_variable = []
        self.dependency_signals_that_are_junctions = []
        self.start_signals = []
        self.execution_line = []


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


        # self.cluster_required_signals = []
        # self.cluster__dependency_signals_simulation_inputs = []
        # self.cluster__dependency_signals_that_are_sources = []
        # self.cluster__dependency_signals_that_depend_on_a_state_variable = []
        # self.cluster__dependency_signals_that_are_junctions = []
        # self.cluster__start_signals = []
        # self.cluster__execution_line = []


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
        dependency_signals_that_depend_on_a_state_variable
    ):

        self.queried_signal                                     = queried_signal
        self.dependency_signals_simulation_inputs               = dependency_signals_simulation_inputs
        self.dependency_signals_that_are_sources                = dependency_signals_that_are_sources
        self.dependency_signals_that_are_junctions              = dependency_signals_that_are_junctions
        self.dependency_signals_that_depend_on_a_state_variable = dependency_signals_that_depend_on_a_state_variable

    def __str__(self):

        str = ''
        str += 'The queried signal is '                     + self.queried_signal.name + '. Its dependencies are:'
        str += '\nsystem intput signals: '                  + ','.join( [ s.name for s in self.dependency_signals_simulation_inputs ] )
        str += '\nsignals that are sources: '               + ','.join( [ s.name for s in self.dependency_signals_that_are_sources ] )
        str += '\njunctions: '                              + ','.join( [ s.name for s in self.dependency_signals_that_are_junctions ] )
        str += '\nsignals that depend on state variables: ' + ','.join( [ s.name for s in self.dependency_signals_that_depend_on_a_state_variable ] )
        str += '\n'

        return str





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
            signals that have been computet in a previous call to determine_execution_order().

            dependency_signals contains all signals that are required to comput signalToCalculate
            and either cross the border of a simulation, 
        """

        # TODO: dependency signals should stay as they are but reachableSignals should not contain signals
        #       that already have been calculated. Further, reachableSignals shall also contain dependency if they 
        #       were not already calculated

        if self._show_print > 0:
            print("determine_execution_order on level " + str(self.currently_queried_level) )

        # compute by traversing the tree
        # execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states = self.backwards_traverse_signals_exec__(start_signal=signal_to_calculate, depth_counter = 0, current_system=current_system)

        queried_signal, execution_line = self._explore_dependencies(signal_to_calculate, current_system, delay_level)

        # the iteration level
        self.currently_queried_level = self.currently_queried_level + 1

        # 
        self.queried_signals_by_level.append( queried_signal )

        return execution_line






    def _explore_dependencies(self, signal_to_calculate, current_system, delay_level : int):
        """
            helper function for determine_execution_order()
        """

        # the list of simulation input signals required for the computation
        dependency_signals_simulation_inputs = []
        dependency_signals_that_are_junctions = []
        dependency_signals_that_depend_on_a_state_variable = []
        dependency_signals_that_are_sources = []

        # TODO: can be removed
        all_signals_that_are_starting_points_of_execution = []

        # For each signgal execution_order there might be a blocks that
        # has an internal memory. It is required to build a list of those blocks
        # that need a state update after their output(s) are calculated.
        blocks_to_update_states = []

        #
        signals_needed_for_state_update_of_involved_blocks = []

        #
        iteration_counter = 0

        iteration_stack_enqueued = []
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
                dependency_signals_simulation_inputs.append( signal )

                # add starting point for execution
                all_signals_that_are_starting_points_of_execution.append( signal )


                continue


            #
            # add signal to the execution line 
            #
            if not is_crossing_simulation_border:
    
                iteration_stack_enqueued.append( signal )



            #
            # request the dynamic/delayed dependencies to compute signal from the block that is having signal as output 
            #
            found_dependencies_via_state_update, block_whose_states_to_update, signals_needed_via_a_state_update = self.find_dependencies_via_a_state_update(signal)
            if found_dependencies_via_state_update:

                # add the signals that are required to perform the state update
                signals_needed_for_state_update_of_involved_blocks.extend( signals_needed_via_a_state_update )
                blocks_to_update_states.append( block_whose_states_to_update )

                dependency_signals_that_depend_on_a_state_variable.append( signal )
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
                dependency_signals_that_are_sources.append( signal )
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

                    dependency_signals_that_are_junctions.append(s)

                    # found a junction: signal s is required to compute more than one signal
                    s.dependency_tree_node.this_node_is_a_junction = True
                    self.signals_that_are_junctions.append( s )

                    # add starting point for execution
                    all_signals_that_are_starting_points_of_execution.append( s )

                    continue
                

                # signal s was not already planned for computation, hence, append a signal to investigate further
                iteration_stack_signal_to_investigate.append( s )




            # continue in loop
            continue


        # the list of signals planned to be computed in the given correct order 
        # in place: iteration_stack_enqueued.reverse()
        #
        #
        execution_order = iteration_stack_enqueued[::-1]


        # if self._show_print > 0:
        #     print('execution_order', [ s.name for s in execution_order ])
        #     print('dependency_signals_simulation_inputs', [ s.name for s in dependency_signals_simulation_inputs ])
        #     print('dependency_signals_through_states', [ s.name for s in signals_needed_for_state_update_of_involved_blocks ])
        #     print('blocks_to_update_states', [ s.name for s in blocks_to_update_states ])


        queried_signal = QueriedSignal(
            signal_to_calculate,
            dependency_signals_simulation_inputs,
            dependency_signals_that_are_sources,
            dependency_signals_that_are_junctions,
            dependency_signals_that_depend_on_a_state_variable
        )

        #
        return queried_signal, ExecutionLine( 
                execution_order,
                #dependency_signals,
                dependency_signals_simulation_inputs,
                blocks_to_update_states,
                signals_needed_for_state_update_of_involved_blocks
            )


    def _step_back_till_junction_or_input_to_create_cluster(self, destination, static_id):
        #
        # finds: 1) dependencies for computing destination 
        # TODO: needs refinement..

        # create new cluster instance
        cluster = Cluster( destination, static_id )
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

            # mark as part of the cluster
            signal.dependency_tree_node.cluster = cluster

            # extract flags
            is_junction                    = signal.dependency_tree_node.this_node_is_a_junction
            is_input                       = signal.dependency_tree_node.this_node_is_an_input
            is_depending_on_state_variable = signal.dependency_tree_node.this_node_depends_on_a_state_variable
            is_source                      = signal.dependency_tree_node.this_node_is_a_source

#            is_nothing_special   = not (is_input or is_junction 

            if is_depending_on_state_variable:
                destination.dependency_tree_node.cluster.dependency_signals_that_depend_on_a_state_variable.append( signal )

            # 
            if is_junction:
                destination.dependency_tree_node.cluster.dependency_signals_that_are_junctions.append( signal )

            elif is_input:
                destination.dependency_tree_node.cluster.dependency_signals_simulation_inputs.append( signal )


            elif is_source:
                destination.dependency_tree_node.cluster.dependency_signals_that_are_sources.append( signal )

            # step backwards
            else:

                iteration_stack_signal_to_investigate.extend( signal.dependency_tree_node.directly_depending_signals )

        return cluster



    def _explore_computation_plan_in_cluster( self, cluster ):

        start_signals = cluster.start_signals


        # vars
        execution_line = []
        iteration_stack_signal_to_investigate = []

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

        execution_line_by_level = {}

        # finish query
        self.number_of_level = self.currently_queried_level
        self.currently_queried_level = None

        #
        # investigate clusters:
        #
        #   - get dependencies for each destination signal and each junction
        #

        # 

        cluster_destinations = [ q.queried_signal for q in self.queried_signals_by_level ]
        cluster_destinations.extend(
            self.signals_that_are_junctions
        )

        clusters = []
        static_cluster_id_counter = 0 # generate a unique id for each cluster
        for cluster_destination in cluster_destinations:
            cluster = self._step_back_till_junction_or_input_to_create_cluster( cluster_destination, static_cluster_id_counter )
            static_cluster_id_counter += 1
            clusters.append(cluster)

            start_signals = set()
            start_signals.update( set(  cluster_destination.dependency_tree_node.cluster.dependency_signals_that_are_junctions  ) )
            start_signals.update( set(  cluster_destination.dependency_tree_node.cluster.dependency_signals_simulation_inputs  ) )
            start_signals.update( set(  cluster_destination.dependency_tree_node.cluster.dependency_signals_that_are_sources  ) )
            cluster_destination.dependency_tree_node.cluster.start_signals = list(start_signals)
            
        #
        # build execution lines for each cluster
        #

        for cluster in clusters:

            execution_line = self._explore_computation_plan_in_cluster( cluster )
            cluster.execution_line = execution_line

        #
        # print clusters
        #

        print('clusters')
        print('--------')
        for cluster in clusters:
            cluster_destination = cluster.destination_signal


            print('cluster id (' + str(cluster.id) + ') with target signal ' + cluster_destination.name + ' requires ')
        
            print('    * junctions: '       + ', '.join( [ s.name + ' (' + str(s.dependency_tree_node.cluster.id) + ') '  for s in cluster.dependency_signals_that_are_junctions ] ) )
            print('    * inputs: '          + ', '.join( [ s.name for s in cluster.dependency_signals_simulation_inputs ] ) )
            print('    * sources: '         + ', '.join( [ s.name for s in cluster.dependency_signals_that_are_sources ] ) )
            print('    . state dependent: ' + ', '.join( [ s.name for s in cluster.dependency_signals_that_depend_on_a_state_variable ] ) )

            print('    computation order: ' + ', '.join( [ s.name for s in cluster.execution_line ] ) )
            print()










#         #
#         # forward graph traverse
#         #

#         # array to collect all junctions
#         junctions = []

#         # replay all queried signals
#         level = 0
#         for q in self.queried_signals_by_level:

# #            for s in q.dependency_signals_simulation_inputs:

#             start_signals = []
#             start_signals.extend( q.dependency_signals_simulation_inputs )
#             start_signals.extend( q.dependency_signals_that_are_sources )
#             start_signals.extend( q.dependency_signals_that_depend_on_a_state_variable )
#             start_signals.extend( q.dependency_signals_that_are_junctions ) 

#             # add junctions
#             junctions.extend( q.dependency_signals_that_are_junctions )           

#             execution_line_by_level[level] = []

#             for start_signal in start_signals:
#                 execution_line, dependency_signals_that_were_newly_found_to_be_junctions = self._explore_computation_plan( start_signal, level )
#                 execution_line_by_level[level].extend( execution_line )

#                 # add junctions
#                 q.dependency_signals_that_are_junctions.extend( dependency_signals_that_were_newly_found_to_be_junctions )
#                 junctions.extend( dependency_signals_that_were_newly_found_to_be_junctions )

#             level += 1




        # build execution plan
        execution_plan = {
            'clusters' : clusters

        }


        return execution_plan
















    # def _explore_computation_plan( self, start_signal, level ):

    #     #
    #     iteration_counter = 0

    #     iteration_stack_enqueued = []
    #     iteration_stack_signal_to_investigate = [start_signal]

    #     execution_line = []
    #     dependency_signals_that_were_newly_found_to_be_junctions = []

    #     while True:

    #         if len(iteration_stack_signal_to_investigate) == 0:
    #             # all signals are planned to be computed --> abort the loop
    #             break

    #         # get latest item (signal) in the stack of signals to compute
    #         # signal = iteration_stack_signal_to_investigate[ -1 ]
    #         signal = iteration_stack_signal_to_investigate.pop()
    #         iteration_counter += 1


    #         if signal.dependency_tree_node.this_node_is_planned_for_computation:

    #             continue

    #         # check if all dependencies to compute signal are satisfied already
    #         signal_is_ready_to_be_computed = True
    #         for s in signal.dependency_tree_node.directly_depending_signals:
    #             if not s.dependency_tree_node.this_node_is_planned_for_computation:

    #                 signal_is_ready_to_be_computed = False

    #                 break 

    #         if not signal_is_ready_to_be_computed:
    #             continue

    #         # Now that all dependencies are available (the check above passed),
    #         # plan to compute this signal; add to execution line.
    #         execution_line.append( signal )
    #         signal.dependency_tree_node.this_node_is_planned_for_computation = True



    #         # check if signal is a junction. If so add the dependency (start_signal) that is needed to
    #         # compute it.
    #         if signal.dependency_tree_node.this_node_is_a_junction:

    #             # add start signals as dependency
    #             signal.dependency_tree_node.required_start_signals.append( start_signal )


    #             # abort the for-loop here?
    #             break





    #         # if level in signal.dependency_tree_node.needed_by_2:
    #         #     signals_step_forward = signal.dependency_tree_node.needed_by_2[ level ]
    #         #     iteration_stack_signal_to_investigate.extend( signals_step_forward )


    #         # step forward only on the same level
    #         if level in signal.dependency_tree_node.needed_by_2:
    #             signals_step_forward = signal.dependency_tree_node.needed_by_2[ level ]
    #             iteration_stack_signal_to_investigate.extend( signals_step_forward )

    #         continue


    #     print('_explore_computation_plan: execution_line', [ s.name for s in execution_line ])
         
    #     # print('_explore_computation_plan: dependency_signals_that_were_newly_found_to_be_junctions', [ s.name for s in dependency_signals_that_were_newly_found_to_be_junctions ])
        

    #     return execution_line, dependency_signals_that_were_newly_found_to_be_junctions












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














    # Start backward traversion starting from the given startSignal
    def backwards_traverse_signals_exec__(self, start_signal : Signal, depth_counter : int, current_system):
        # WARNING: This is a recursive function!

        # the list of signals planned to be computed in the given correct order 
        execution_order = []

        # list of signals the computation depends on (the tips of the execution tree)
        dependency_signals = []

        # the list of simulation input signals required for the computation
        dependency_signals_simulation_inputs = []

        # For each signgal execution_order there might be a blocks that
        # has an internal memory. It is required to build a list of those blocks
        # that need a state update after their output(s) are calculated.
        blocks_to_update_states = []

        #
        dependency_signals_through_states = []




        #
        # check if the datatype of startSignal is defined
        #

        if start_signal.datatype is None:
            raise BaseException('Unknown datatype for signal ' + start_signal.name + ': no datatype has been specified or could be determined automatically.')


        #
        #
        #

        
        tabs = ''
        for i in range(0, depth_counter):
            tabs += '.  '


        if not (isinstance(start_signal, SimulationInputSignal) or isinstance(start_signal, BlockOutputSignal)):
            
            # this case must be an error..                  
            raise BaseException('not implemented or internal error: unexpected type of signal ' + start_signal.name)

        # check if the signal is a system input signal
        is_crossing_simulation_border = start_signal.is_crossing_system_boundary(current_system) #  self.system != startSignal.sim



        # TODO: IMPLEMENT: except when startSignal is a simulation input (in this case it is not computed)
        #  and not isinstance(startSignal, SimulationInputSignal)
        if start_signal.graphTraversionMarkerMarkIsVisitedOnLevelLowerThan(self.level):
            # - a previously computed signal has been reached

            if self._show_print > 1:
                print(Style.DIM + tabs + "has already been calculated in a previous traversion") 

            dependency_signals.append( start_signal )

            # in case startSignal is a simulation input, still add it to the list of simulation input dependencies
            # though it has already been computed
            if is_crossing_simulation_border:

                if self._show_print > 1:
                    print(Style.DIM + tabs + "as it is also a simulation input, adding it to the list of depended inputs")

                # also note down that this is a (actually used) simulation input
                dependency_signals_simulation_inputs.append( start_signal )

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states








        if start_signal.graphTraversionMarkerMarkIsVisited():

            if self._show_print > 1:
                print(Style.DIM + tabs + "has already been calculated in this traversion") 

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states








        if is_crossing_simulation_border:
            # signal is an input to the system
            # add to the list of dependent inputs

            if self._show_print > 1:
                print(Fore.YELLOW + tabs + "  --> crosses system bounds")

            # startSignal is at the top of the tree, so add it to the dependencies
            dependency_signals.append( start_signal )

            # also note down that this is a (actually used) simulation input
            dependency_signals_simulation_inputs.append( start_signal )

            if self._show_print > 1:
                print(Style.DIM + tabs + "added input dependency " + start_signal.toStr())

            # mark the node/signal as being visited (meaning computed)
            self.place_marker(start_signal)

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states








        # get the blocks prototype function to calculate startSignal
        block = start_signal.getSourceBlock()
        blocksPrototype = block.getBlockPrototype()

        #
        # check if the block that yields startSignal uses internal-states to compute startSignal
        #

        inputs_to_update_states_tmp = blocksPrototype.config_request_define_state_update_input_dependencies( start_signal )
        if inputs_to_update_states_tmp is not None:

            if self._show_print > 1:
                print(tabs + "--- signals needed *indirectly* to compute " + start_signal.name + " (through state update) --" )

            # 
            blocks_to_update_states.append( block )

            # please note: blocksPrototype.config_request_define_state_update_input_dependencies might return some undetermined signals that are resolved here
            resolveUndeterminedSignals( inputs_to_update_states_tmp )

            # add the signals that are required to perform the state update
            dependency_signals_through_states.extend( inputs_to_update_states_tmp )

            if self._show_print > 1:
                for signal in inputs_to_update_states_tmp:
                    print(Fore.MAGENTA + tabs + "-> S " + signal.name )






        #
        # find out the links to other signals but only the ones that are 
        # needed to calculate 'startSignal'
        #

        if self._show_print > 1:
            print(tabs + "--- signals needed for " + start_signal.name + " --" )

        dependingSignals = blocksPrototype.config_request_define_feedforward_input_dependencies(start_signal)

        # please note: blocksPrototype.config_request_define_feedforward_input_dependencies might return some undetermined signals that are resolved here
        resolveUndeterminedSignals( dependingSignals )

        if len(dependingSignals) == 0:
            # no dependencies to calculate startSignal (e.g. in case of const blocks or blocks without direct feedthrough)
            if self._show_print > 1:
                print(Style.DIM + tabs + "  (no signals needed) "  )

            # block startSignal.getSourceBlock() --> startSignal is a starting point

            # startSignal is at the top of the tree, so add it to the dependencies
            dependency_signals.append( start_signal )

            #
            if self._show_print > 1:
                print(Style.DIM + tabs + "added " + start_signal.toStr())
    
            execution_order.append( start_signal )

            # mark the node/signal as being visited (meaning computed)
            self.place_marker(start_signal)

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states



        #
        # ITERATE: go through all signals needed to calculate startSignal
        #          only in case there are any, we come to this point
        #

        for signal in dependingSignals:

            if self._show_print > 1:
                print(Fore.MAGENTA + tabs + "-> S " + signal.name )

            if depth_counter > 100:
                raise BaseException('maximal number of iterations reached in system ' + signal.system.name + 'signal ' + signal.name)

            # R E C U R S I O N
            A_execution_order, A_dependency_signals, A_dependency_signals_simulation_inputs, A_blocks_to_update_states, A_dependency_signals_through_states = self.backwards_traverse_signals_exec__( signal, depth_counter = depth_counter + 1, current_system=current_system )

            execution_order.extend(                      A_execution_order )
            dependency_signals.extend(                   A_dependency_signals )
            dependency_signals_simulation_inputs.extend( A_dependency_signals_simulation_inputs )
            blocks_to_update_states.extend(              A_blocks_to_update_states )
            dependency_signals_through_states.extend(    A_dependency_signals_through_states )


        #
        # FINALIZE: now also startSignal can be computed
        #

        #
        # store startSignal as reachable (put it on the execution list)
        # NOTE: if startSignal is the tip of the tree (no dependingSignals) it is excluded
        #       from this list. However, it is still in the list of dependencySignals.
        #

        if self._show_print > 1:
            print(Style.DIM + tabs + "added " + start_signal.toStr())

        execution_order.append( start_signal )

        # mark the node/signal as being visited (meaning computed)
        self.place_marker(start_signal)


        return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states





















class BuildExecutionPath__original:
    """
        Find out the order in which signals have to be computed such that a given signal
        'signal_to_calculate' can be calculated. This means finding out all dependencies of
        'signal_to_calculate'. For each call to 'determine_execution_order' only the signals that
        were not already marked as a dependency in previous calls are returned.
        Each call to 'determine_execution_order' gives an instance 'ExecutionLine'
    """
    def __init__(self, show_print:int=0):

        self._show_print = show_print

        # list of marked signals (important to reset their visited flags)
        self.marked_signals = []

        # number of calls to determine_execution_order()
        self.level = 0

    def __del__(self):
        # reset the markers stored in the signals
        self.reset_markers()


    def determine_execution_order(self, signal_to_calculate : Signal, current_system):

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
            signals that have been computet in a previous call to determine_execution_order().

            dependency_signals contains all signals that are required to comput signalToCalculate
            and either cross the border of a simulation, 
        """

        # TODO: dependency signals should stay as they are but reachableSignals should not contain signals
        #       that already have been calculated. Further, reachableSignals shall also contain dependency if they 
        #       were not already calculated

        if self._show_print > 0:
            print("determine_execution_order on level " + str(self.level) )

        # compute by traversing the tree
        execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states = self.backwards_traverse_signals_exec__(start_signal=signal_to_calculate, depth_counter = 0, current_system=current_system)

        # the iteration level
        self.level = self.level + 1

        return ExecutionLine( execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states )

    def printExecutionLine(self):
        pass

    def reset_markers(self):
        # reset graph traversion markers
        for signal in self.marked_signals:
            signal.graphTraversionMarkerReset()

        # reset status variables
        self.marked_signals = []
        self.level = 0

    def place_marker_for_current_level(self, signal):
        # mark the node/signal as being visited (meaning computed)
        signal.graphTraversionMarkerMarkVisited(self.level)
        self.marked_signals.append(signal)

    # NOTE: unused
    def is_signal_already_computable(self, signal : Signal):
        return signal.graphTraversionMarkerMarkIsVisited()

    # Start backward traversion starting from the given startSignal
    def backwards_traverse_signals_exec__(self, start_signal : Signal, depth_counter : int, current_system):
        # WARNING: This is a recursive function!

        # the list of signals planned to be computed in the given correct order 
        execution_order = []

        # list of signals the computation depends on (the tips of the execution tree)
        dependency_signals = []

        # the list of simulation input signals required for the computation
        dependency_signals_simulation_inputs = []

        # For each signgal execution_order there might be a blocks that
        # has an internal memory. It is required to build a list of those blocks
        # that need a state update after their output(s) are calculated.
        blocks_to_update_states = []

        #
        dependency_signals_through_states = []




        #
        # check if the datatype of startSignal is defined
        #

        if start_signal.datatype is None:
            raise BaseException('Unknown datatype for signal ' + start_signal.name + ': no datatype has been specified or could be determined automatically.')


        #
        #
        #

        
        tabs = ''
        for i in range(0, depth_counter):
            tabs += '.  '


        if not (isinstance(start_signal, SimulationInputSignal) or isinstance(start_signal, BlockOutputSignal)):
            
            # this case must be an error..                  
            raise BaseException('not implemented or internal error: unexpected type of signal ' + start_signal.name)

        # check if the signal is a system input signal
        is_crossing_simulation_border = start_signal.is_crossing_system_boundary(current_system) #  self.system != startSignal.sim

        # TODO: IMPLEMENT: except when startSignal is a simulation input (in this case it is not computed)
        #  and not isinstance(startSignal, SimulationInputSignal)
        if start_signal.graphTraversionMarkerMarkIsVisitedOnLevelLowerThan(self.level):
            # - a previously computed signal has been reached

            if self._show_print > 1:
                print(Style.DIM + tabs + "has already been calculated in a previous traversion") 

            dependency_signals.append( start_signal )

            # in case startSignal is a simulation input, still add it to the list of simulation input dependencies
            # though it has already been computed
            if is_crossing_simulation_border:

                if self._show_print > 1:
                    print(Style.DIM + tabs + "as it is also a simulation input, adding it to the list of depended inputs")

                # also note down that this is a (actually used) simulation input
                dependency_signals_simulation_inputs.append( start_signal )

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states

        if start_signal.graphTraversionMarkerMarkIsVisited():

            if self._show_print > 1:
                print(Style.DIM + tabs + "has already been calculated in this traversion") 

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states

        if is_crossing_simulation_border:
            # signal is an input to the system
            # add to the list of dependent inputs

            if self._show_print > 1:
                print(Fore.YELLOW + tabs + "  --> crosses system bounds")

            # startSignal is at the top of the tree, so add it to the dependencies
            dependency_signals.append( start_signal )

            # also note down that this is a (actually used) simulation input
            dependency_signals_simulation_inputs.append( start_signal )

            if self._show_print > 1:
                print(Style.DIM + tabs + "added input dependency " + start_signal.toStr())

            # mark the node/signal as being visited (meaning computed)
            self.place_marker_for_current_level(start_signal)

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states


        # get the blocks prototype function to calculate startSignal
        block = start_signal.getSourceBlock()
        blocksPrototype = block.getBlockPrototype()

        #
        # check if the block that yields startSignal uses internal-states to compute startSignal
        #

        inputs_to_update_states_tmp = blocksPrototype.config_request_define_state_update_input_dependencies( start_signal )
        if inputs_to_update_states_tmp is not None:

            if self._show_print > 1:
                print(tabs + "--- signals needed *indirectly* to compute " + start_signal.name + " (through state update) --" )

            # 
            blocks_to_update_states.append( block )

            # please note: blocksPrototype.config_request_define_state_update_input_dependencies might return some undetermined signals that are resolved here
            resolveUndeterminedSignals( inputs_to_update_states_tmp )

            # add the signals that are required to perform the state update
            dependency_signals_through_states.extend( inputs_to_update_states_tmp )

            if self._show_print > 1:
                for signal in inputs_to_update_states_tmp:
                    print(Fore.MAGENTA + tabs + "-> S " + signal.name )


        #
        # find out the links to other signals but only the ones that are 
        # needed to calculate 'startSignal'
        #

        if self._show_print > 1:
            print(tabs + "--- signals needed for " + start_signal.name + " --" )

        dependingSignals = blocksPrototype.config_request_define_feedforward_input_dependencies(start_signal)

        # please note: blocksPrototype.config_request_define_feedforward_input_dependencies might return some undetermined signals that are resolved here
        resolveUndeterminedSignals( dependingSignals )

        if len(dependingSignals) == 0:
            # no dependencies to calculate startSignal (e.g. in case of const blocks or blocks without direct feedthrough)
            if self._show_print > 1:
                print(Style.DIM + tabs + "  (no signals needed) "  )

            # block startSignal.getSourceBlock() --> startSignal is a starting point

            # startSignal is at the top of the tree, so add it to the dependencies
            dependency_signals.append( start_signal )

            #
            if self._show_print > 1:
                print(Style.DIM + tabs + "added " + start_signal.toStr())
    
            execution_order.append( start_signal )

            # mark the node/signal as being visited (meaning computed)
            self.place_marker_for_current_level(start_signal)

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states



        #
        # ITERATE: go through all signals needed to calculate startSignal
        #          only in case there are any, we come to this point
        #

        for signal in dependingSignals:

            if self._show_print > 1:
                print(Fore.MAGENTA + tabs + "-> S " + signal.name )

            if depth_counter > 100:
                raise BaseException('maximal number of iterations reached in system ' + signal.system.name + 'signal ' + signal.name)

            # R E C U R S I O N
            A_execution_order, A_dependency_signals, A_dependency_signals_simulation_inputs, A_blocks_to_update_states, A_dependency_signals_through_states = self.backwards_traverse_signals_exec__( signal, depth_counter = depth_counter + 1, current_system=current_system )

            execution_order.extend(                      A_execution_order )
            dependency_signals.extend(                   A_dependency_signals )
            dependency_signals_simulation_inputs.extend( A_dependency_signals_simulation_inputs )
            blocks_to_update_states.extend(              A_blocks_to_update_states )
            dependency_signals_through_states.extend(    A_dependency_signals_through_states )


        #
        # FINALIZE: now also startSignal can be computed
        #

        #
        # store startSignal as reachable (put it on the execution list)
        # NOTE: if startSignal is the tip of the tree (no dependingSignals) it is excluded
        #       from this list. However, it is still in the list of dependencySignals.
        #

        if self._show_print > 1:
            print(Style.DIM + tabs + "added " + start_signal.toStr())

        execution_order.append( start_signal )

        # mark the node/signal as being visited (meaning computed)
        self.place_marker_for_current_level(start_signal)


        return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states
