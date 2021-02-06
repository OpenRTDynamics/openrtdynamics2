from typing import Dict, List


class irparElement:
    def __init__(self, id : int, typ : int, ipar : List[int], rpar : List[float]):
        self.id = id
        self.typ = typ
        self.ipar = ipar
        self.rpar = rpar

class irparElement_rpar(irparElement):
    def __init__(self, id : int, rpar : List[float] ):
        irparElement.__init__(self, id, 1, [len(rpar)], rpar )

class irparElement_ipar(irparElement):
    def __init__(self, id : int, ipar : List[int] ):
        irparElement.__init__(self, id, 4, [len(ipar)] + ipar, [] )

class irparElement_container(irparElement):
    def __init__(self, id : int, ipar : List[int], rpar : List[float] ):
        irparElement.__init__(self, id, 10, ipar, rpar )


class irparSet:
    def __init__(self):
        self.Elements = []

    def AddElemet(self, element : irparElement):
        # TODO: check if one id appears twice
        self.Elements.append( element )

    def combine_irparam(self):
        # encode

        rpar_ptr = []
        ipar_ptr = []

        rparges = []
        iparges = []

        for i in range(0,len( self.Elements )):
            ipar_ptr.append( len(iparges) )
            iparges += self.Elements[i].ipar

            rpar_ptr.append( len(rparges) )
            rparges += self.Elements[i].rpar

        # build header
        header_entries = len( self.Elements )
        version = 1
        header = [version, header_entries]

        for i in range(0,len( self.Elements )):
            # pip_len = length(parlist(i).ipar(:));
            pip_len = len( self.Elements[i].ipar )
            prp_len = len( self.Elements[i].rpar)

            header += [ self.Elements[i].id, self.Elements[i].typ, ipar_ptr[i], rpar_ptr[i], pip_len, prp_len ]

            #header = [header; parlist(i).id; parlist(i).typ; ipar_ptr(i); rpar_ptr(i); pip_len; prp_len];

        # summ up
        ipar = header + iparges
        rpar = rparges

        return ipar, rpar



class irparEncoder:
    def __init__(self):
        pass


# irpar = irparSet()
# irpar.AddElemet( irparElement( 10, 11, [1,2,3], [0.1,0.2,0.3] ) )
# irpar.AddElemet( irparElement( 20, 21, [100,200,30], [0.22,0.33] ) )
# irpar.AddElemet( irparElement_ipar( 30, [9,8,7,6] ) )
# irpar.AddElemet( irparElement_rpar( 31, [9.9,8.8,7.7,6.6] ) )


# ipar, rpar = irpar.combine_irparam()

# print(ipar)
# print(rpar)


