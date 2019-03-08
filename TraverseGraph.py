
from typing import Dict, List
from Signal import *
from Block import *


class Node:
    def __init__(self, block : Block ):
        self.block = block

    def next(self):
        pass






class TraverseTree:
    def __init__(self, blockList : List[ Block ]):

        # build a list of nodes
        self.nodeList = []

        for block in blockList:

            self.nodeList.append( Node(block) )

