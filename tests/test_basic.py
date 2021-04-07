#from .context import openrtdynamics2
#from .context import dy

import openrtdynamics2.lang as dy

def test_basic_code_gen():
    # create a new system
    system = dy.enter_system()

    # define system inputs
    input1               = dy.system_input( dy.DataTypeFloat64(1), name='input1', default_value=5.0,  value_range=[0, 25], title="input #1")

    # the diagram
    tmp = input1 * dy.float64(2.0)
    tmp.set_name("some_name")
    output = dy.delay(tmp)

    # define output(s)
    dy.append_output(output, 'outputs')

    # generate code
    code_gen_results = dy.generate_code(template=dy.TargetWasm(), folder="generated/", build=False)
    sourcecode, manifest = code_gen_results['sourcecode'], code_gen_results['manifest']

    # clear workspace
    dy.clear()

    # raise BaseException('testfail')



