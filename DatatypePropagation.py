from typing import Dict, List
from Signal import *
from Block import *

from colorama import init,  Fore, Back, Style
init(autoreset=True)



class DatatypePropagation:


    def __init__(self, sim ):

        self.signalsWithDeterminedTypes = []

        self.signalsWithUpdatedDeterminedTypes = []

        self.signalsWithProposedTypes = []

        self.signalsWithUpdatedProposedTypes = []

        self.signalsWithUnderminedTypes = []


        self.updateCounter = 0

    def notifyBlock(self, block : Block):
        # a new singals has been created
        # once a new block is added or one of the input signals change

        # trigger the block to define its output signals or give a proposal
        block.configDefineOutputTypes()

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

        print("DatatypePropagation: new/updated signal " + signal.toStr() )

        # fill in to self.signalsWithUpdatedDeterminedTypes or self.signalsWithUnderminedTypes

        if signal.getDatatype() is None:

            # put to the list of signals with undetermined datatypes
            self.signalsWithUnderminedTypes.append( signal )

        else:

            # put on the list of signals with already fixed datatypes
            self.signalsWithUpdatedDeterminedTypes.append( signal )


            # inherit the type of signal to the signals that inherit from
            
            # set datatypes of block that inherit this datatype
            for to_signal in signal.inherit_datatype_to_list:

                print("inherit datatype of " + signal.toStr() + " to --> " + to_signal.toStr() )

                # NOTE: running setDatatype_nonotitication prevents a callback to notifySignal (This function)
                # and, hence, possible infinite loops
                to_signal.setDatatype_nonotitication( signal.datatype )

                # put on the list of signals with already fixed datatypes
                self.signalsWithUpdatedDeterminedTypes.append( to_signal )



        self.updateCounter += 1



    def notify_updateOfProposedDatatype(self, signal : Signal):
        # a proposal for the datatype of signal was updated

        print("DatatypePropagation: datatype proposol for signal updated " + signal.toStr( ))


        # add to ..
        self.signalsWithUpdatedProposedTypes.append( signal )

        self.updateCounter += 1

        # remove from other lists..



    def updateTypes(self):

        print("DatatypePropagation: update types " )

        # while-loop around the following (think about when it is finished.. e.g. )
        # signalsWithProposedTypes and signalsWithUpdatedProposedTypes are empty
        # or nothing chanegs any more (no notifications arrive within a loop-cycle)

        while True:

            # during the call of .configDefineOutputTypes() the lists might be updated
            # by hereby triggered calls to the notify_* funcrions of this class
            # Hence, make copies of these lists before

            signalsWithUpdatedDeterminedTypes = self.signalsWithUpdatedDeterminedTypes
            signalsWithUpdatedProposedTypes = self.signalsWithUpdatedProposedTypes

            # clear that list as it is about to be processed now
            self.signalsWithUpdatedDeterminedTypes = [] 
            self.signalsWithUpdatedProposedTypes = [] 

            # concat signalsWithUpdatedDeterminedTypes to self.signalsWithDeterminedTypes
            self.signalsWithDeterminedTypes.extend( signalsWithUpdatedDeterminedTypes )
            self.signalsWithProposedTypes.extend( signalsWithUpdatedProposedTypes )

            # a counter that counts the number of signal datatype updates within this loop
            # Please note, that this counter is increased in external functions
            # triggered by the calls 'destBlock.configDefineOutputTypes()'
            updateCounterBefore = self.updateCounter

            # at first ask all blocks who have a signal with an already fixed datatype connected to their inputs 
            for s in signalsWithUpdatedDeterminedTypes:
                # ask all blocks connected to s to update their output type proposal or fix their type

                # ask each block connected to the signal s to update its output type (proposals)
                for destBlock in s.getDestinationBlocks():

                    # print("  asking block " + destBlock.toStr())

                    destBlock.configDefineOutputTypes()


            # forward the datatype proposals to the connected blocks
            for s in self.signalsWithUpdatedProposedTypes:
                # ask all blocks connected to s to update their output type proposal or fix their type
                
                # ask each block connected to the signal s to update its output type (proposals)
                for destBlock in s.getDestinationBlocks():

                    # print("  asking block " + destBlock.toStr())
                    destBlock.configDefineOutputTypes()

            if updateCounterBefore == self.updateCounter and len(self.signalsWithUpdatedProposedTypes) == 0:

                print("resolved all datatypes as far as possible in this update-run")

                print("signals with fixed types:")
                for s in self.signalsWithDeterminedTypes:
                    print('  - ' + s.toStr())

                print("signals with proposed types:")
                for s in self.signalsWithProposedTypes:
                    print('  - ' + s.toStr())

                print("signals with undetermined types:")
                for s in self.signalsWithProposedTypes:
                    print('  - ' + s.toStr())

                # leave the - while True - loop
                break


    def fixateTypes(self):

        # discover datatype
        self.updateTypes()

        # check if something is missing.. TODO
        for s in self.signalsWithDeterminedTypes:

            # remove from
            if s in self.signalsWithUnderminedTypes:
                self.signalsWithUnderminedTypes.remove( s )

        # turn the proposal datatypes into fixed types
        for s in self.signalsWithProposedTypes:

            print('  - turning proposed type into fixed - ' + s.toStr())

            # fixate datatype of s
            s.fixDatatype()

            # remove from
            self.signalsWithUnderminedTypes.remove( s )

        print("signals with undetermined types:")  # TODO: investigate why this list contains some leftovers...
        for s in self.signalsWithUnderminedTypes:
            print('  - ' + s.toStr())

        # TODO: notify the fixation of the datatypes using compile_callback_all_datatypes_defined() of the block prototypes


