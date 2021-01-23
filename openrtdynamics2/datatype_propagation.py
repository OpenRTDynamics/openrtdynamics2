from typing import Dict, List
from .signals import *
from openrtdynamics2 import Block

from colorama import init,  Fore, Back, Style
init(autoreset=True)



class DatatypePropagation:


    def __init__(self, sim, show_print:int=0 ):
        # show_print 0: show nothing, 1: how some print, 2: show all
        self._show_print = show_print

        self.signalsWithDeterminedTypes = set()
        self.signalsWithProposedTypes = set()

        self.signalsWithUpdatedDeterminedTypes = []
        self.signalsWithUpdatedProposedTypes = []
        self.signalsWithUnderminedTypes = []


        self.updateCounter = 0

    def notifyBlock(self, block : Block):
        # a new singals has been created
        # once a new block is added or one of the input signals change

        # trigger the block to define its output signals or give a proposal
        block.config_request_define_output_types()

        pass


    def notifySignal(self, signal : Signal):
        """
            This function is called back from the signal instances in Signal.py

            - when a new signal is created
            - when a datatype of a signal has been updated 
              (e.g. indirectly due to an inherited datatype from another signal that was updated)
        """
        # TODO 25.3.20: maybe all notification shall be just put into a line and the processed at the end of update


        # a new singal was created
        # (Note: it might haven been also only updated, meaning it go registered even before)

        if isinstance( signal, UndeterminedSignal ):
            # ignore anonymous signal (there is a signal connected directly to a block (BlockOutputSignal) for each)
            return

        # fill in to self.signalsWithUpdatedDeterminedTypes or self.signalsWithUnderminedTypes

        if signal.getDatatype() is None:

            # put to the list of signals with undetermined datatypes
            self.signalsWithUnderminedTypes.append( signal )

        else:

            # put on the list of signals with already fixed datatypes
            self.signalsWithUpdatedDeterminedTypes.append( signal )

        self.updateCounter += 1



    def notify_updateOfProposedDatatype(self, signal : Signal):
        # a proposal for the datatype of signal was updated

        # add to ..
        self.signalsWithUpdatedProposedTypes.append( signal )

        self.updateCounter += 1

        # remove from other lists..



    def iteration(self, signals_with_updated_determined_types_current, signals_with_updated_proposed_types_current):

        def inherit_fixed_datatype(signal):

            # inherit the type of signal to the signals that inherit from
            if signal.inherit_datatype_to_list is not None:
                for to_signal in signal.inherit_datatype_to_list:
                    
                    if self._show_print > 1:
                        print("inherit fixed datatype " + signal.toStr() + " --> " + to_signal.toStr() )

                    to_signal.setDatatype( signal.datatype )

                    # put on the list of signals with already fixed datatypes
                    # self.signalsWithUpdatedDeterminedTypes.append( to_signal )

        def inherit_proposed_datatype(signal):

            # inherit the type of signal to the signals that inherit from
            if signal.inherit_datatype_to_list is not None:
                for to_signal in signal.inherit_datatype_to_list:
                    
                    # inherit proposed datatype  signal.toStr()  -->  to_signal.toStr()
                    to_signal.setProposedDatatype( signal.proposed_datatype )

                    # put on the list of signals with already fixed datatypes
                    # self.signalsWithUpdatedDeterminedTypes.append( to_signal )


        # at first ask all blocks who have a signal with an already fixed datatype connected to their inputs 
        for s in signals_with_updated_determined_types_current:
            # ask all blocks connected to s to update their output type proposal or fix their type

            # ask each block connected to the signal s to update its output type (proposals)
            for destBlock in s.getDestinationBlocks():
                destBlock.config_request_define_output_types()

            # forward the datatype of s to the signals that use the same datatype
            inherit_fixed_datatype(s)


        # forward the datatype proposals to the connected blocks
        for s in signals_with_updated_proposed_types_current:
            # ask all blocks connected to s to update their output type proposal or fix their type
            
            # ask each block connected to the signal s to update its output type (proposals)
            for destBlock in s.getDestinationBlocks():
                destBlock.config_request_define_output_types()

            # forward the datatype of s to the signals that use the same datatype
            inherit_proposed_datatype(s)
                

        # remove the already fixed signals from the list of undetermined signals
        for s in signals_with_updated_determined_types_current:
            if s in self.signalsWithUnderminedTypes:
                self.signalsWithUnderminedTypes.remove( s )


    def update_types_iterate(self):

        while True:

            signals_with_updated_determined_types_current = self.signalsWithUpdatedDeterminedTypes
            signals_with_updated_proposed_types_current = self.signalsWithUpdatedProposedTypes

            # clear that list as it is about to be processed now
            self.signalsWithUpdatedDeterminedTypes = [] 
            self.signalsWithUpdatedProposedTypes = [] 

            # concat signalsWithUpdatedDeterminedTypes to self.signalsWithDeterminedTypes
            self.signalsWithDeterminedTypes.update(  (signals_with_updated_determined_types_current) )
            self.signalsWithProposedTypes.update( (signals_with_updated_proposed_types_current) )

            #
            updateCounterBefore = self.updateCounter

            # iterate..
            # herein, the lists might fill up yielding new signals to process in the ongoing iteration
            self.iteration(signals_with_updated_determined_types_current, signals_with_updated_proposed_types_current)

            # check if there is sth. left to to
            if updateCounterBefore == self.updateCounter and len(self.signalsWithUpdatedDeterminedTypes) == 0 and len(self.signalsWithUpdatedProposedTypes) == 0:

                if self._show_print > 0:
                    print("resolved all datatypes as far as possible in this update-run")

                    if self._show_print > 1:
                        print(Fore.GREEN + "signals with fixed types:")
                        for s in list(self.signalsWithDeterminedTypes):
                            print('  - ' + s.toStr())

                        print(Fore.YELLOW + "signals with proposed types:")
                        for s in list(self.signalsWithProposedTypes):
                            print('  - ' + s.toStr())

                        if len(self.signalsWithUnderminedTypes) > 0:

                            print(Fore.RED + "signals with undetermined types:")
                            for s in self.signalsWithUnderminedTypes:
                                print('  - ' + s.toStr())
                        
                        else:
                            print(Fore.GREEN + "no undetermined types are left")

                # leave the - while True - loop
                break




    def fixateTypes(self):

        # discover datatype
        self.update_types_iterate()

        # # check if something is missing.. TODO
        # for s in self.signalsWithDeterminedTypes:

        #     # remove from
        #     if s in self.signalsWithUnderminedTypes:
        #         self.signalsWithUnderminedTypes.remove( s )

        # turn the proposal datatypes into fixed types
        for s in list(self.signalsWithProposedTypes):

            # print('  - turning proposed type into fixed - ' + s.toStr())

            # fixate datatype of s
            s.fixDatatype()

            # remove from
            self.signalsWithUnderminedTypes.remove( s )

            
        if self._show_print > 1:
            print("signals with undetermined types:")  # TODO: investigate why this list contains some leftovers...
            for s in self.signalsWithUnderminedTypes:
                print('  - ' + s.toStr())

        # TODO: notify the fixation of the datatypes using compile_callback_all_datatypes_defined() of the block prototypes



