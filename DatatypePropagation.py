from typing import Dict, List
from Signal import *
from Block import *

from colorama import init,  Fore, Back, Style
init(autoreset=True)



class DatatypePropagation:

    # TODO: implement this -- stopped here (XXX)

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
        # a new singals has been created

        print("DatatypePropagation: new signal " + signal.toStr( ))

        # fill in to self.signalsWithUpdatedDeterminedTypes or self.signalsWithUpdatedProposedTypes

        if signal.getDatatype() is None:
            
            self.signalsWithUnderminedTypes.append( signal )
        else:
            self.signalsWithUpdatedDeterminedTypes.append( signal )

        self.updateCounter += 1



    def notify_updateOfProposedDatatype(self, signal : Signal):
        # a proposal for a datatype has been updated

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

        for i in range(0,10):


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

            # print("update counter is before " + str(self.updateCounter))

            updateCounterBefore = self.updateCounter

            # at fitst ask all blocks who have a signal with an already fixed datatype connected to their inputs 
            for s in signalsWithUpdatedDeterminedTypes:
                # ask all blocks connected to s to update their output type proposal or fix their type

                # ask each block connected to the signal s to update its output type (proposals)
                for destBlock in s.getDestinationBlocks():

                    print("  asking block " + destBlock.toStr())

                    destBlock.configDefineOutputTypes()


            # forward the datatype proposals to the connected blocks
            for s in self.signalsWithUpdatedProposedTypes:
                # ask all blocks connected to s to update their output type proposal or fix their type
                
                # ask each block connected to the signal s to update its output type (proposals)
                for destBlock in s.getDestinationBlocks():

                    print("  asking block " + destBlock.toStr())
                    destBlock.configDefineOutputTypes()

            # print("update counter is after " + str(self.updateCounter))


            if updateCounterBefore == self.updateCounter:

                print("nothing changed -- abort")

                print("signals with fixed types:")
                for s in self.signalsWithDeterminedTypes:
                    print('  - ' + s.toStr())

                print("signals with proposed types:")
                for s in self.signalsWithProposedTypes:
                    print('  - ' + s.toStr())

                print("signals with undetermined types:")
                for s in self.signalsWithProposedTypes:
                    print('  - ' + s.toStr())

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

            print('  - fix - ' + s.toStr())

            # fixate datatype of s
            s.fixDatatype()

            # remove from
            self.signalsWithUnderminedTypes.remove( s )

        print("signals with undetermined types:")  # TODO: investigate why this list contains some leftovers...
        for s in self.signalsWithUnderminedTypes:
            print('  - ' + s.toStr())


