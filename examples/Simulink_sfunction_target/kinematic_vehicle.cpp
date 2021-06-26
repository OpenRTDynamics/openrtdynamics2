/*  File    : kinematic_vehicle.cpp
 *  Abstract:
 *
 *      Code automatically built from an OpenRTDynamics 2 system
 *      using the Simulink s-function target.
 *
 *      Do not edit manually. Your changes might be lost.
 *
 *
 *  Configured input signals:
 *
 *  +-------+-----------------------+---------+--------+-------+----------------+----------------+
 *  | #port | input signal,  to --> | outputs | update | reset | datatype (c++) | description    |
 *  +-------+-----------------------+---------+--------+-------+----------------+----------------+
 *  |   0   |         delta         |    X    |   X    |       |     double     | steering angle |
 *  |   1   |           v           |    X    |   X    |       |     double     | velocity       |
 *  |   2   |       wheelbase       |    X    |        |       |     double     | wheelbase      |
 *  +-------+-----------------------+---------+--------+-------+----------------+----------------+
 *
 *  Configured output signals:
 *
 *  +-------+--------------+----------------+
 *  | #port | input signal | datatype (c++) |
 *  +-------+--------------+----------------+
 *  |   0   |      x       |     double     |
 *  |   1   |      y       |     double     |
 *  |   2   |     psi      |     double     |
 *  |   3   |   psi_dot    |     double     |
 *  +-------+--------------+----------------+
 *
 */

#include <iostream>

#include <stdio.h>
#include <math.h>

// namespace for simulation {
  // global variables

  class simulation {
    public:


    // state update
    double block_15_mem;
    double block_13_mem;
    double block_11_mem;


    // state update


    //
    // cached output values
    //

    double psi__block_15;
    double s10__block_7;
    double s11__block_8;
    double psi_dot__block_9;
    double y__block_13;
    double x__block_11;

    // API-function resetStates
    void resetStates() { // created by cpp_define_function

      block_15_mem = 0;
      block_13_mem = 0;
      block_11_mem = 0;
    }
    // output signals of  resetStates
    struct Outputs_resetStates{
      ;

    };
    // input signals of resetStates
    struct Inputs_resetStates{
      ;

    };
    // wrapper function for resetStates
    Outputs_resetStates resetStates__(Inputs_resetStates inputs) {
      Outputs_resetStates outputs;

      resetStates();

      return outputs;
    }
    // API-function updateStates
    void updateStates(double v, double delta) { // created by cpp_define_function
      double s17;
      double s7;
      double s8;
      double s9;
      double s15;
      double s4;
      double s5;
      double s6;
      double s13;


      // restoring the signals psi, s10, s11, psi_dot, y, x from the states 
      double &psi = psi__block_15;
      double &s10 = s10__block_7;
      double &s11 = s11__block_8;
      double &psi_dot = psi_dot__block_9;
      double &y = y__block_13;
      double &x = x__block_11;


      // calculating the block outputs in the following order s17, s7, s8, s9, s15, s4, s5, s6, s13
      // that depend on v, delta
      // dependencies that require a state update are  

      s17 = 1 * psi + 0.01 * psi_dot;
      s7 = delta + psi;
      s8 = sin(s7);
      s9 = v * s8;
      s15 = 1 * y + 0.01 * s9;
      s4 = delta + psi;
      s5 = cos(s4);
      s6 = v * s5;
      s13 = 1 * x + 0.01 * s6;

      block_15_mem = s17;
      block_13_mem = s15;
      block_11_mem = s13;

      // calculating the block outputs in the following order 
      // that depend on 
      // dependencies that require a state update are  


    }
    // output signals of  updateStates
    struct Outputs_updateStates{
      ;

    };
    // input signals of updateStates
    struct Inputs_updateStates{
      double v;
      double delta;

    };
    // wrapper function for updateStates
    Outputs_updateStates updateStates__(Inputs_updateStates inputs) {
      Outputs_updateStates outputs;

      updateStates(inputs.v, inputs.delta);

      return outputs;
    }
    // API-function calcResults_1 to compute: x, y, psi, psi_dot
    void calcResults_1(double &x, double &y, double &psi, double &psi_dot, double v, double wheelbase, double delta) { // created by cpp_define_function
      double s10;
      double s11;


      // calculating the block outputs in the following order psi, s10, s11, psi_dot, y, x
      // that depend on v, wheelbase, delta
      // dependencies that require a state update are s17, s15, s13 

      psi = block_15_mem;
      s10 = v / wheelbase;
      s11 = sin(delta);
      psi_dot = s10 * s11;
      y = block_13_mem;
      x = block_11_mem;

      // saving the signals psi, s10, s11, psi_dot, y, x into the states 
      psi__block_15 = psi;
      s10__block_7 = s10;
      s11__block_8 = s11;
      psi_dot__block_9 = psi_dot;
      y__block_13 = y;
      x__block_11 = x;
    }
    // output signals of  calcResults_1
    struct Outputs_calcResults_1{
      double x;
      double y;
      double psi;
      double psi_dot;

    };
    // input signals of calcResults_1
    struct Inputs_calcResults_1{
      double v;
      double wheelbase;
      double delta;

    };
    // wrapper function for calcResults_1
    Outputs_calcResults_1 calcResults_1__(Inputs_calcResults_1 inputs) {
      Outputs_calcResults_1 outputs;

      calcResults_1(outputs.x, outputs.y, outputs.psi, outputs.psi_dot,   inputs.v, inputs.wheelbase, inputs.delta);

      return outputs;
    }
    // all system inputs and outputs combined
    struct Inputs{
      double wheelbase;
      double v;
      double delta;

    };
    struct Outputs{
      double x;
      double y;
      double psi;
      double psi_dot;

    };
    // main step function 
    void step(Outputs & outputs, Inputs const & inputs, int calculate_outputs, bool update_states, bool reset_states) {
      if (reset_states) {
        resetStates();

      }
      if (calculate_outputs==1) {
        calcResults_1(outputs.x, outputs.y, outputs.psi, outputs.psi_dot,   inputs.v, inputs.wheelbase, inputs.delta);

      }
      if (update_states) {
        updateStates(inputs.v, inputs.delta);

      }

    }
  };

// end of namespace for simulation





#define S_FUNCTION_LEVEL 2
#define S_FUNCTION_NAME  kinematic_vehicle

#include "simstruc.h"

#define IS_PARAM_DOUBLE(pVal) (mxIsNumeric(pVal) && !mxIsLogical(pVal) &&!mxIsEmpty(pVal) && !mxIsSparse(pVal) && !mxIsComplex(pVal) && mxIsDouble(pVal))

//
// S-function methods
//

#define MDL_CHECK_PARAMETERS
#if defined(MDL_CHECK_PARAMETERS)  && defined(MATLAB_MEX_FILE)
static void mdlCheckParameters(SimStruct *S)
{

    const mxArray *pVal0 = ssGetSFcnParam(S,0);

    if ( !IS_PARAM_DOUBLE(pVal0)) {
        ssSetErrorStatus(S, "Parameter to S-function must be a double scalar");
        return;
    } 
}
#endif


static void mdlInitializeSizes(SimStruct *S)
{
    ssSetNumSFcnParams(S, 1);  /* Number of expected parameters */
#if defined(MATLAB_MEX_FILE)
    if (ssGetNumSFcnParams(S) == ssGetSFcnParamsCount(S)) {
        mdlCheckParameters(S);
        if (ssGetErrorStatus(S) != NULL) {
            return;
        }
    } else {
        return; /* Parameter mismatch will be reported by Simulink */
    }
#endif
    ssSetSFcnParamTunable(S, 0, 0);

    // number of cont and discrete states
    ssSetNumContStates(S, 0);
    ssSetNumDiscStates(S, 0);

    // number of input ports
    if (!ssSetNumInputPorts(S, 3  )) return;
    
    // set sizes 
    ssSetInputPortWidth(S, 0, 1); // delta 
    ssSetInputPortWidth(S, 1, 1); // v 
    ssSetInputPortWidth(S, 2, 1); // wheelbase 

    // set direct feedthough (for input signals that are needed to compute the system outputs)
    ssSetInputPortDirectFeedThrough(S, 1, 1); // v
    ssSetInputPortDirectFeedThrough(S, 2, 1); // wheelbase
    ssSetInputPortDirectFeedThrough(S, 0, 1); // delta

    // number of output ports
    if (!ssSetNumOutputPorts(S, 4)) return;

    ssSetOutputPortWidth(S, 0, 1); // x
    ssSetOutputPortWidth(S, 1, 1); // y
    ssSetOutputPortWidth(S, 2, 1); // psi
    ssSetOutputPortWidth(S, 3, 1); // psi_dot

    // sample times
    ssSetNumSampleTimes(S, 1);
    
    // define storage
    ssSetNumRWork(S, 0);
    ssSetNumIWork(S, 0);
    ssSetNumPWork(S, 1); // reserve element in the pointers vector
    ssSetNumModes(S, 0); // to store a C++ object
    ssSetNumNonsampledZCs(S, 0);

    // operating point
    ssSetOperatingPointCompliance(S, USE_DEFAULT_OPERATING_POINT);

    // general options
    ssSetOptions(S, 0);         
}




static void mdlInitializeSampleTimes(SimStruct *S)
{
    ssSetSampleTime(S, 0, mxGetScalar(ssGetSFcnParam(S, 0)));
    ssSetOffsetTime(S, 0, 0.0);
    ssSetModelReferenceSampleTimeDefaultInheritance(S);
}

#define MDL_START
#if defined(MDL_START) 
  static void mdlStart(SimStruct *S)
  {
      ssGetPWork(S)[0] = (void *) new simulation; // store new C++ object in the

      simulation *c = (simulation *) ssGetPWork(S)[0];
      
      // ORTD I/O structures
      simulation::Inputs inputs;
      simulation::Outputs outputs;

      // reset system
      c->step( outputs, inputs, false, false, true ); 
  }
#endif /*  MDL_START */

static void mdlOutputs(SimStruct *S, int_T tid)
{
    simulation *c = (simulation *) ssGetPWork(S)[0];
    
    // inputs
    InputRealPtrsType uPtrs1 = ssGetInputPortRealSignalPtrs(S,1);
    InputRealPtrsType uPtrs2 = ssGetInputPortRealSignalPtrs(S,2);
    InputRealPtrsType uPtrs0 = ssGetInputPortRealSignalPtrs(S,0);

    
    // outputs
    real_T  *y0 = ssGetOutputPortRealSignal(S, 0);
    real_T  *y1 = ssGetOutputPortRealSignal(S, 1);
    real_T  *y2 = ssGetOutputPortRealSignal(S, 2);
    real_T  *y3 = ssGetOutputPortRealSignal(S, 3);


    // ORTD I/O structures
    simulation::Inputs inputs;
    simulation::Outputs outputs;

    
    inputs.v = *uPtrs1[0];
    inputs.wheelbase = *uPtrs2[0];
    inputs.delta = *uPtrs0[0];


    // compute the system outputs
    c->step( outputs, inputs, true, false, false ); 
    
    y0[0] = outputs.x;
    y1[0] = outputs.y;
    y2[0] = outputs.psi;
    y3[0] = outputs.psi_dot;

    
    UNUSED_ARG(tid);
}                                                


#define MDL_UPDATE
static void mdlUpdate(SimStruct *S, int_T tid)
{
    InputRealPtrsType uPtrs  = ssGetInputPortRealSignalPtrs(S,0);
    simulation *c = (simulation *) ssGetPWork(S)[0];

    simulation::Inputs inputs;
    simulation::Outputs outputs;

    InputRealPtrsType uPtrs1 = ssGetInputPortRealSignalPtrs(S,1);
    InputRealPtrsType uPtrs0 = ssGetInputPortRealSignalPtrs(S,0);


    UNUSED_ARG(tid); /* not used in single tasking mode */
    
    inputs.v = *uPtrs1[0];
    inputs.delta = *uPtrs0[0];


    // update the states of the system
    c->step( outputs, inputs, false, true, false ); 
}


static void mdlTerminate(SimStruct *S)
{
    simulation *c = (simulation *) ssGetPWork(S)[0]; // retrieve and destroy C++
    delete c;                                  // object in the termination
}                                              // function

/*=============================*
 * Required S-function trailer *
 *=============================*/

#ifdef  MATLAB_MEX_FILE    /* Is this file being compiled as a MEX-file? */
#include "simulink.c"      /* MEX-file interface mechanism */
#else
#include "cg_sfun.h"       /* Code generation registration function */
#endif


        
        