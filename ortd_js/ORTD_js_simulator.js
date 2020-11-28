var inputGUI = require('./inputGUI.js')


function show_loading(simulator_gui_container) {

    var parameterEditorDivs = simulator_gui_container.getElementsByClassName("parameter_editor" ) 
    var plotDivs            = simulator_gui_container.getElementsByTagName('plot')

    for (var i = 0; i < parameterEditorDivs.length; i++) {
        parameterEditorDivs[i].innerHTML = '...'
    }

    for (var i = 0; i < plotDivs.length; i++) {
        plotDivs[i].innerHTML = 'Loading..'
    }

}




function genrateParameterInitValues(manifest) {
    // generate list of properties
    i1 = manifest.io.inputs.state_update.names.concat(manifest.io.inputs.calculate_output.names);
    p1 = manifest.io.inputs.state_update.properties.concat(manifest.io.inputs.calculate_output.properties);

    var initvals = {}
    for (i = 0; i < i1.length; ++i) {

        if ( !(p1[i] === null) && 'default_value' in p1[i]) {
            initvals[i1[i]] = p1[i].default_value

            console.log('found a default value ', p1[i].default_value)
        } else {
            initvals[i1[i]] = 0.1
        }
    }

    return initvals;
}









function initParameterEditor(simulator_gui_container, manifest, initvals, fn) {

    // generate list of properties
    var i1 = manifest.io.inputs.state_update.names.concat(manifest.io.inputs.calculate_output.names);
    var t1 = manifest.io.inputs.state_update.cpptypes.concat(manifest.io.inputs.calculate_output.cpptypes);
    var p1 = manifest.io.inputs.state_update.properties.concat(manifest.io.inputs.calculate_output.properties);
    var ports1 = manifest.io.inputs.state_update.port_numbers.concat(manifest.io.inputs.calculate_output.port_numbers);

    // sort items according to port number
    var i1_sorted = new Array(i1.len); 
    var p1_sorted = new Array(i1.len);
    for (i = 0; i < i1.length; ++i) {
            port = ports1[i]
            if (port===null) {
                console.log('skipping parameter as port number is not given')
            } else {
                i1_sorted[port] = i1[i]
                p1_sorted[port] = p1[i]    
            }
    }

    // set-up GUI
    var value_storage = {} // will be filled in by the input gui on creation

    var editorDiv = simulator_gui_container.getElementsByClassName("parameter_editor" )[0]
    editorDiv.innerHTML = ''
    
    console.log(inputGUI)

    var input_gui = new inputGUI.inputGUI(editorDiv, i1_sorted, p1_sorted, (e) => { value_storage[e.name] = e.val ; fn(value_storage) } )

    return input_gui
}



class Plot {
    constructor(div) {
        this.div = div
    }

    add_trace(arrays_for_output_signals_array, x_name, y_name, tracke_name) {
    }

    set_descriptions( title, xlabel, ylabel ) {
    }

    show () {

    }

    update () {

    }
}



class PlotPlotly extends Plot {
    constructor(div) {
        super(div)

        this.traces = []
    }

    add_trace(arrays_for_output_signals_array, x_name, y_name, trace_name) {
        //
        // TODO: no checking of x_name, y_name is performed
        //

        var trace = {
            x: arrays_for_output_signals_array[x_name],
            y: arrays_for_output_signals_array[y_name],
            type: 'scattergl',
            name: trace_name
        };

        console.log(trace)

        this.traces.push(trace)
    }

    set_descriptions( title, xlabel, ylabel ) {

        this.layout = {
            title: title,
            xaxis: {
              title: xlabel,
              showgrid: true,
              zeroline: true
            },
            yaxis: {
              title: ylabel,
              showline: true
            },
            paper_bgcolor: 'rgba(128, 128, 128, 0 )',
            plot_bgcolor:  'rgba(0.0, 0, 0, 0)',
//            render_mode: 'webgl'
          }

          console.log(this.layout)
    }

    show() {
        Plotly.newPlot(this.div, this.traces, this.layout);
    }

    update () {
        Plotly.redraw(this.div)
    }
}



class PlotChartJS extends Plot {
    constructor(div) {
        super(div)

        this.number_of_traces = 0

        this.data_arrays = []
        this.data_source_arrays = []
        this.x_names = []
        this.y_names = []
        this.Nsamples_list = []

        this.datasets = []
    }

    allocate_array_struct(Nsamples) {
        var dataset_plot = [];
        for (i = 0; i < Nsamples; ++i) {
            dataset_plot.push({ x: 0.0, y: 0.0 });
        }
    
        return dataset_plot;
    }

    copy_trace_data(index) {
        for (var j = 0; j < this.Nsamples_list[index]; ++j) {
            this.data_arrays[index][j].x = this.data_source_arrays[index].x[j]
            this.data_arrays[index][j].y = this.data_source_arrays[index].y[j]
        }
    }

    copy_data() {
        for (var i = 0; i < this.number_of_traces; ++i) {
            this.copy_trace_data(i)
        }
    }

    add_trace(arrays_for_output_signals_array, x_name, y_name, tracke_name) {
        //
        // TODO: no checking of x_name, y_name is performed
        //



        // default colors
        var colorList = ['black', 'red', 'green', 'blue', 'yellow', 'grey'];

        // prepare datasets and pre alloc memory for each to fill in data
        var Nsamples = arrays_for_output_signals_array[x_name].length
        this.Nsamples_list.push(Nsamples)

        var data = this.allocate_array_struct( Nsamples )

        this.data_arrays.push(data)
        this.data_source_arrays.push( {x: arrays_for_output_signals_array[x_name], y: arrays_for_output_signals_array[y_name] } )

        var color;
        if (this.number_of_traces < colorList.length) {
            color = colorList[this.number_of_traces];
        } else {
            color = 'black'
        }

        var dataset = {
            label: tracke_name,
            borderColor: color,
            data: data
        };

        this.datasets.push(dataset);


        this.number_of_traces++
    }

    set_descriptions( title, xlabel, ylabel ) {

        this.layout = {
        }
    }

    show() {


        var datasets = this.datasets

        this.copy_data()

        // plot
        this.div.innerHTML = 'Chartjs'

        this.subdiv = document.createElement('div')
        this.div.appendChild(this.subdiv)

        // create canvas
        this.canvas = document.createElement('canvas')
        this.canvas.setAttribute('width', '340')
        this.canvas.setAttribute('heigth', '200')

        this.subdiv.appendChild(this.canvas)

        this.myLineChart = new Chart(this.canvas, {
            type: "scatter",
            data: { datasets },
            options: {
                animation: {
                    duration: 1 // general animation time
                },
                hover: {
                    animationDuration: 0 // duration of animations when hovering an item
                },
                responsiveAnimationDuration: 0 // animation duration after a resize
            }
        });

    }

    update () {
        this.copy_data()
        this.myLineChart.update()
    }
}




class PlotManager {
    constructor(simulator_gui_container, manifest, arrays_for_output_signals_array) {
        this.simulator_gui_container = simulator_gui_container
        this.plots = []
        this.preparePlots(simulator_gui_container, manifest, arrays_for_output_signals_array)
    }

    update() {
        for (var i = 0; i < this.plots.length; i++) {
            this.plots[i].update()
        }
    }

    preparePlots(simulator_gui_container, manifest, arrays_for_output_signals_array) {

        var plotDivs = simulator_gui_container.getElementsByTagName('plot');
        var N = plotDivs.length

        for (var i = 0; i < N; i++) {

                var graphDiv = plotDivs[i]
                graphDiv.innerHTML = '' //'Plot ' + i + ' to appear...'

                // new plot
                // console.log('new plot', i, graphDiv)

                var plot

                if (graphDiv.hasAttribute('type')) {

                    var type = graphDiv.getAttribute('type')

                    if (type == 'plotly') {
                        plot = new PlotPlotly(graphDiv)
                    }
                    else if (type == 'chartjs') {
                        plot = new PlotChartJS(graphDiv)
                    }

                } else {
                    plot = new PlotPlotly(graphDiv)
                }

                if (graphDiv.hasAttribute('x') && graphDiv.hasAttribute('y')) {

                    var x_names = graphDiv.getAttribute('x').split(" ")
                    var y_names = graphDiv.getAttribute('y').split(" ")

                    // TODO: handle unknown names
                    if (x_names.length == 1) {
                        // Create plot(s) over one x-variable (e.g. a time-series plot)

                        var x_name = x_names[0]
                        if (x_name != "time" && !manifest.io.outputs.calculate_output.names.includes(x_name)) {
                            console.log(x_name, 'is not part of the systems outputs')
                            continue
                        }

                        y_names.forEach(function (y_name) {
                            // check if y_name is in part of the system outpus manifest.io.outputs.calculate_output.names
                            if ( !manifest.io.outputs.calculate_output.names.includes( y_name )) {
                                console.log(y_name, 'is not part of the systems outputs')
                            } else {
                                plot.add_trace( arrays_for_output_signals_array, x_name, y_name, y_name )
                            }

                        })
            
                    } else if ( x_names.length == y_names.length ) {
                        // create scatterplot(s)

                        for (var j=0; j < x_names.length; ++j) {
                            plot.add_trace( arrays_for_output_signals_array, x_names[j], y_names[j], x_names[j] + '/' + y_names[j] )
                        }

                    } else {
                        console.log('error in setting-up plot: number of x vs. y signals is not matching')
                    }

                } else {
            
                    console.log('no special atrributes found -- creating default plot')
            
                    // put all output signal into one plot
                    manifest.io.outputs.calculate_output.names.forEach(function (outputName) {
                        plot.add_trace( arrays_for_output_signals_array, "time", outputName, outputName )
                    });
                    
                }
            
                // get some comming plot labels
                var title, xlabel, ylabel
                if (graphDiv.hasAttribute('title')) {
                    title = graphDiv.getAttribute('title')
                } else {
                    title = ''
                }
                if (graphDiv.hasAttribute('xlabel')) {
                    xlabel = graphDiv.getAttribute('xlabel')
                } else {
                    xlabel = ''
                }
                if (graphDiv.hasAttribute('ylabel')) {
                    ylabel = graphDiv.getAttribute('ylabel')
                } else {
                    ylabel = ''
                }

                // new
                plot.set_descriptions( title, xlabel, ylabel )

                this.plots.push(plot)

                // new
                plot.show()
        }
    }

}



function compileSimulator(source_code, compile_service_url, secret_token) {

    var compile_request = new Promise(
        function (resolve, reject) {

            var myHeaders = new Headers();
            myHeaders.append("Content-Type", "application/json");

            var raw = JSON.stringify({"source_code" : source_code , "secret_token" : secret_token });

            var requestOptions = {
                method: 'POST',
                headers: myHeaders,
                body: raw,
                redirect: 'follow'
            };

            fetch(compile_service_url, requestOptions)
                .then(response => response.text())
                .then(result => {

                    resolve( JSON.parse( result ) )

                })
                .catch(error => console.log('error', error));

    });

    function _base64ToArrayBuffer(base64) {
        // https://stackoverflow.com/questions/21797299/convert-base64-string-to-arraybuffer/21797381
        var binary_string = window.atob(base64);
        var len = binary_string.length;
        var bytes = new Uint8Array(len);
        for (var i = 0; i < len; i++) {
            bytes[i] = binary_string.charCodeAt(i);
        }
        return bytes.buffer;
    }

    var p_rawWebAssembly = new Promise(
        function (resolve, reject) {
            compile_request.then(function (result) {
                resolve(  _base64ToArrayBuffer(result.rawWebAssembly) )
            })
        });

    var jscode = new Promise(
        function (resolve, reject) {
            compile_request.then(function (result) {
                resolve( window.atob(result.jscode) )
            })
        });

    return {p_rawWebAssembly : p_rawWebAssembly, p_jscode : jscode};

}



// load wasm file files = { manifest : 'simulation_manifest.json', wasm : 'main.wasm', jscode : 'main.js' }
function loadCompiledSimulator(files) {

    var p_manifest = new Promise(
        function (resolve, reject) {

            fetch(files.manifest, {cache: "no-cache"})
                .then(response => response.json())
                .then(response => {
            
                resolve( response );                    

            }).then(data => { 
                // console.log(data);
            });

        }
    );

    var rawWebAssembly = new Promise(
        function (resolve, reject) {

            fetch(files.wasm, {cache: "no-cache"} ).then(response => {
            
                resolve( response['arrayBuffer']() );

            }).then(data => { 
                // console.log(data);
            });

        }
    );

    var jscode = new Promise(
        function (resolve, reject) {

            fetch(files.jscode, {cache: "no-cache"})
                .then(response => response.text())
                .then(response => {
            
                    resolve( response );                    

                }).then(data => { 
                    // console.log(data);
                });

        }
    );

    promises = {p_manifest : p_manifest, p_rawWebAssembly : rawWebAssembly, p_jscode : jscode}
    return promises;
}




// create instance for the simulator
function createInstance( p_manifest, rawWebAssembly, init_fn ) {
    var Module = {

        instantiateWasm: function (imports, successCallback) {
            console.log('creating wasm');

            return rawWebAssembly.then(function(binary) {

                    console.log('starting WebAssembly.instantiate')

                    var wasmInstantiate = WebAssembly.instantiate(new Uint8Array(binary), imports).then( function(output) {

                        console.log('wasm instantiation succeeded');
                        Module.testWasmInstantiationSucceeded = 1;
                        successCallback(output.instance);

                    }).catch(function(e) {
                        console.log('wasm instantiation failed! ' + e);
                    });

                });
        },

        onRuntimeInitialized: function () {

            p_manifest.then(
                function (manifest) {
                    console.log('loaded the following manifest')
                    console.log(manifest)

                    // init simulator
                    var instance = new Module.simulation();

                    init_fn(instance)
                });

        }
    };

    return Module;
}




function setup_simulation_from_promises(promises, init_fn) {


    p_manifest = promises.p_manifest
    p_jscode   = promises.p_jscode


    p_jscode.then( function (jscode) {

        Module = createInstance( p_manifest, promises.p_rawWebAssembly, init_fn ) 
        
        var gvar = this;
        
        eval( jscode )

        ORTD_simulator( Module )
    })
}



// 
// Simulator
// 

function allocate_arrays_for_output_signals_xy(manifest, Nsamples) {

    // prepare datasets and pre alloc memory for each to fill in data
    var arrays_for_output_signals_xy = {}
    manifest.io.outputs.calculate_output.names.forEach(function (outputName) {

        var data = allocateOutputMemoryXY(Nsamples);

        arrays_for_output_signals_xy[outputName] = data;
    });

    return arrays_for_output_signals_xy
}


// kick this out
function allocateOutputMemoryXY(Nsamples) {
    var dataset_plot = [];
    for (i = 0; i < Nsamples; ++i) {
        dataset_plot.push({ x: 0.0, y: 0.0 });
    }

    return dataset_plot;
}
function allocateOutputMemoryArray(Nsamples) {
    var dataset_plot = [];
    for (i = 0; i < Nsamples; ++i) {
        dataset_plot.push(0.0);
    }

    return dataset_plot;
}


class simulationInstance {

    constructor(manifest, wasm_instance, number_of_samples) {
        this.manifest = manifest
        this.instance = wasm_instance
        this.number_of_samples = number_of_samples

        this.arrays_for_output_signals_array = this.allocate_arrays_for_output_signals_array()
    }

    allocate_arrays_for_output_signals_array() {
        var N = this.number_of_samples

        // prepare datasets and pre alloc memory for each to fill in data
        var arrays_for_output_signals_array = {}
        this.manifest.io.outputs.calculate_output.names.forEach(function (outputName) {
    
            var data = allocateOutputMemoryArray(N);
    
            arrays_for_output_signals_array[outputName] = data;
        });
    
        var data = allocateOutputMemoryArray(N);
        arrays_for_output_signals_array['time'] = data
    
        return arrays_for_output_signals_array
    }

    simulate(inputValues) {

        var Nsamples = this.number_of_samples;
        var sampling_time = this.manifest.sampling_time
        
        // sort inputValues into the inupts for state update and output calculation
        var inputs_updateStates = {}
        var inputs_calcOutputs = {};
        var inputs_resetStates = {};  // normally empty
    
        for (var key in inputValues) {
            if (this.manifest.io.inputs.state_update.names.includes(key)) {
                // input 'key' is an input to the function 'updateStates'
                inputs_updateStates[key] = inputValues[key]
            }
            if (this.manifest.io.inputs.calculate_output.names.includes(key)) {
                // input 'key' is an input to the function 'calcOutputs'
                inputs_calcOutputs[key] = inputValues[key]
            }
        }
    
        this.instance.resetStates(inputs_resetStates);
    
        var t = 0.0
    
        for (i = 0; i < Nsamples; ++i) {
            var outputs = this.instance.calcResults_1(inputs_calcOutputs);
            this.instance.updateStates(inputs_updateStates);
    
            if (!this.manifest.io.outputs.calculate_output.names.includes("time")) {
                // add a signal 'time' in case it is not already present as a system output
                t = t + sampling_time;
                this.arrays_for_output_signals_array["time"][i] = t    
            }
    
            for ( const outputName of this.manifest.io.outputs.calculate_output.names ) {
                this.arrays_for_output_signals_array[outputName][i] = outputs[outputName];
            }
        }
    
    }

}


function setup_simulation_gui_from_promises( simulator_gui_container, promises, settings) {

    // init the gui
    // init_simulator_gui_container(simulator_gui_container)
    // clear_simulator_gui_container(simulator_gui_container)

    show_loading(simulator_gui_container)

    setup_simulation_from_promises(promises, function(instance) {

    promises.p_manifest.then(
        function (manifest) {

            if ( !( 'sampling_time' in manifest )) {
                manifest.sampling_time = 0.01
                console.log('NOTE: as not specified in the manifest, applying default sampling time (100 Hz)')
            }

            // set-up the GUI and simulator
            var simulator = new simulationInstance(manifest, instance, settings.number_of_samples)

            // parameter
            var initvals = genrateParameterInitValues(manifest);
            var plotManager
            var plots_initialized = false

            initParameterEditor(simulator_gui_container, manifest, initvals, function (inputValues) {

                if (plots_initialized) {
                    // on parameter change simulate and plot
                    simulator.simulate(inputValues)
                    plotManager.update()
                }
            });

            simulator.simulate(initvals)

            plotManager = new PlotManager(simulator_gui_container, manifest, simulator.arrays_for_output_signals_array)
            plots_initialized = true

        })

    
    });

}



function setup_simulation_gui( simulator_gui_container, compile_service_url, secret_token, manifest, code, settings ) {

    source_code = {main_cpp : window.btoa( code )  }
    var promises = compileSimulator(source_code, compile_service_url, secret_token);

    var p_manifest = new Promise(
        function (resolve, reject) {

            resolve( JSON.parse( manifest ) )

        })

    promises.p_manifest = p_manifest

    setup_simulation_gui_from_promises( simulator_gui_container, promises, settings)
}




module.exports = {
    loadCompiledSimulator: loadCompiledSimulator,
    setup_simulation_gui_from_promises: setup_simulation_gui_from_promises
}

