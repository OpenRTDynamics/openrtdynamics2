# old stuff





# # TODO REMOVE
# def ld_block(sim, operator : str, inlist, par):
#     # lookup operator...
#     Blocktype = BlockDict.lookupOperator(operator)

#     #
#     blk = Block(sim, Blocktype, inlist, par)
#     sim.addBlock(blk)

#     #print("ld_block: new block with id " + str( blk.getId() ) )

#     # create the output signals
#     y1 = blk.GetOutputSignal(0)

#     return y1




# [sim,sum_] = ld_add(sim, events, inp_list, fak_list)
def ld_add(sim : Simulation, inp_list : List[Signal], fak_list : List[float]):

    BT = Blocktype(
        {"operator": "const",
         "btype": 12,
         "intypes": [ORTD_DATATYPE_FLOAT,ORTD_DATATYPE_FLOAT],
         "insizes": [1,1],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    if len(inp_list) != 2:
        raise("inp_list must have exactly 2 elements")

    par = { 'ipar' : [], 'rpar' : fak_list }
    inlist = inp_list

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)

    # create the output signals
    sum = blk.GetOutputSignal(0)

    return sum


# [sim, out] = ld_delay(sim, events, u, N)
def ld_delay(sim : Simulation, u : Signal, N : int):

    BT = Blocktype(
        {"operator": "const",
         "btype": 60001 + 24,
         "intypes": [ORTD_DATATYPE_FLOAT],
         "insizes": [1],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    if N <= 0:
        raise("N <= 0 !")

    par = { 'ipar' : [N], 'rpar' : [] }
    inlist = [u]

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)


    # create the output signals
    y = blk.GetOutputSignal(0)

    return y


def ld_const(sim : Simulation, val : float):

    BT = Blocktype(
        {"operator": "const",
         "btype": 40,
         "intypes": [],
         "insizes": [],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    par = { 'ipar' : [], 'rpar' : [val] }
    inlist = []

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)

    #print("ld_const: new block with id " + str( blk.getId() ) )

    # create the output signals
    y1 = blk.GetOutputSignal(0)

    return y1




def ld_printf(sim : Simulation, u : Signal, name : str):

    vlen = u.datatype.size

    if u.datatype.type != ORTD_DATATYPE_FLOAT:
        raise("u.datatype.type != ORTD_DATATYPE_FLOAT !")


    BT = Blocktype(
        {"operator": "const",
         "btype": 170,
         "intypes": [ORTD_DATATYPE_FLOAT],
         "insizes": [vlen],
         "outtypes": [],
         "outsizes": []})

    # tostr
    strAscii = []
    for code in map(ord, name):
        #print(code)
        strAscii += [code]



    #
    par = { 'ipar' : [vlen, len(strAscii)] + strAscii, 'rpar' : [] }
    inlist = [u]

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)

    #print("ld_printf: new block with id " + str( blk.getId() ) )

    return



#[sim,y] = ld_play_simple(sim, events, r)
def ld_play_simple(sim :Simulation , r : List[float]):

    BT = Blocktype(
        {"operator": "const",
         "btype": 100,
         "intypes": [],
         "insizes": [],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    if len(r) <= 0:
        raise("length(r) <= 0 !")

    initial_play = 1
    hold_last_value = 0
    mute_afterstop = 0

    par = { 'ipar' : [len(r), initial_play, hold_last_value, mute_afterstop], 'rpar' : r }
    inlist = []

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)


    # create the output signals
    y = blk.GetOutputSignal(0)

    return y



# [sim] = ld_savefile(sim, events, fname, source, vlen), libdyn_new_blk_filedump
def ld_savefile(sim : Simulation, fname : str, source : Signal):

    vlen = source.datatype.size

    if source.datatype.type != ORTD_DATATYPE_FLOAT:
        raise("source.datatype.type != ORTD_DATATYPE_FLOAT !")

    BT = Blocktype(
        {"operator": "const",
         "btype": 130,
         "intypes": [ORTD_DATATYPE_FLOAT],
         "insizes": [vlen],
         "outtypes": [],
         "outsizes": []})

    if vlen <= 0:
        raise("vlen <= 0 !")

    # tostr
    strAscii = []
    for code in map(ord, fname):
        #print(code)
        strAscii += [code]

    autostart = 1
    maxlen = 0

    #
    par = { 'ipar' : [maxlen, autostart, vlen, len(strAscii)] + strAscii, 'rpar' : [] }
    inlist = [source]

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)


    return








# blocks
c1 = ld_const(sim, 1.123)
#c2 = ld_const(sim, 1.23124)

c2 = ld_play_simple(sim, r=[1,2,3,4,5,6,7,8,9])

# a feedback
feedback = Signal(sim, DataType( ORTD_DATATYPE_FLOAT, 1 ))

ld_printf(sim, feedback, "feedback value is")

#
sum = ld_add(sim, inp_list=[c1, c2], fak_list=[1,-1])


sum_delayed = ld_delay(sim, u=sum, N=10)

feedback.setequal( sum_delayed )

ld_printf(sim, sum, "value is")
ld_printf(sim, sum_delayed, "delayed value is")

ld_printf(sim, c2, "another print..")
ld_printf(sim, c2, "and a 3rd one")

ld_savefile(sim, fname="SimulationOutput.dat", source=c2)


print(sim)

with ld_subsim(sim) as sim2:
    ld_printf(sim2, sum, "This is a printf in a sub-simulation")

    ret = ld_delay(sim2, u=sum, N=1)

    sim2.Return( [ret] )





if False:
    sim = Simulation(None, 'main')

    c1 = ld_block(sim, 'const', [], 2)
    c2 = ld_block(sim, 'const', [], 3)

    i_int32 = ld_block(sim, 'constInt32', [], 30)

    #print("####")
    #sum2 = ld_block(sim, 'sum', [i_int32, i_int32], [0.3, 2])
    #print("####")


    sum = ld_block(sim, 'sum', [c1, c2], [0.3, 2])

    condition = ld_block(sim, 'compare', [sum], 0)

    # sim.ShowBlocks()

    #blk = Block(sim, 100, [], [])
    #condition = Signal(sim, DataType(1,1), blk, 1 )


    #ipar, rpar = sim.encode_irpar()

    #print(ipar)
    #print(rpar)

    sim.export_ortdrun('RTMain')



#    with ld_IF(sim, condition) as sim:
#        print("define simulation triggered by if")




