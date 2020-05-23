
function init_simulator_gui_container(divElement) {

    divElement.innerHTML = `
        <div class='editor_holder'></div>
        <div class="plotly" width="400" height="200"></div>
        <canvas class="plot" width="400" height="200"></canvas>
    `;
}
function clear_simulator_gui_container(divElement) {

    divElement.innerHTML = '<b>Loading ...</b>';
}







function simulate(instance, manifest, arrays_for_output_signals_array, arrays_for_output_signals_xy, Nsamples, inputValues) {

    // sort inputValues into the inupts for state update and output calculation
    var inputs_updateStates = {}
    var inputs_calcOutputs = {};
    var inputs_resetStates = {};  // normally empty

    for (var key in inputValues) {
        if (manifest.io.inputs.state_update.names.includes(key)) {
            // input 'key' is an input to the function 'updateStates'
            inputs_updateStates[key] = inputValues[key]
        }
        if (manifest.io.inputs.calculate_output.names.includes(key)) {
            // input 'key' is an input to the function 'calcOutputs'
            inputs_calcOutputs[key] = inputValues[key]
        }
    }

    instance.resetStates(inputs_resetStates);

    var t = 0.0

    for (i = 0; i < Nsamples; ++i) {
        outputs = instance.calcResults_1(inputs_calcOutputs);
        instance.updateStates(inputs_updateStates);

        t = t + 0.01;
        arrays_for_output_signals_array["time"][i] = t

        manifest.io.outputs.calculate_output.names.forEach(function (outputName) {
            arrays_for_output_signals_array[outputName][i] = outputs[outputName];

            arrays_for_output_signals_xy[outputName][i].x = t;
            arrays_for_output_signals_xy[outputName][i].y = outputs[outputName];
        });
    }

    console.log( arrays_for_output_signals_xy )
}

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



function genrateParameterInitValues(manifest) {
    // generate list of properties
    i1 = manifest.io.inputs.state_update.names.concat(manifest.io.inputs.calculate_output.names);

    var initvals = {}
    for (i = 0; i < i1.length; ++i) {
        initvals[i1[i]] = 0.1
    }

    return initvals;
}









function initParameterEditor(simulator_gui_container, manifest, initvals, fn) {

    // Set default options
    // JSONEditor.defaults.options.theme = 'bootstrap2';

    // generate list of properties
    i1 = manifest.io.inputs.state_update.names.concat(manifest.io.inputs.calculate_output.names);
    t1 = manifest.io.inputs.state_update.cpptypes.concat(manifest.io.inputs.calculate_output.cpptypes);

    var properties = {}
    for (i = 0; i < i1.length; ++i) {
        properties[i1[i]] = { "type": "number", "format": "range", "propertyOrder": i,
            "options": {
                    "infoText": "..."
            }
        }
    }

    // Initialize the editor
    var editor = new JSONEditor(  simulator_gui_container.getElementsByClassName("editor_holder" )[0], {
        schema: {
            type: "object",
            properties: properties
        }
    });

    // Set the initial inputValues
    editor.setValue(initvals);

    // Listen for changes
    editor.on("change", function () {
        fn(editor.getValue());
    });

    return editor;
}



function allocate_arrays_for_output_signals_xy(manifest, Nsamples) {

    // prepare datasets and pre alloc memory for each to fill in data
    var arrays_for_output_signals_xy = {}
    manifest.io.outputs.calculate_output.names.forEach(function (outputName) {

        var data = allocateOutputMemoryXY(Nsamples);

        arrays_for_output_signals_xy[outputName] = data;
    });

    return arrays_for_output_signals_xy
}


function allocate_arrays_for_output_signals_array(manifest, Nsamples) {

    // prepare datasets and pre alloc memory for each to fill in data
    var arrays_for_output_signals_array = {}
    manifest.io.outputs.calculate_output.names.forEach(function (outputName) {

        var data = allocateOutputMemoryArray(Nsamples);

        arrays_for_output_signals_array[outputName] = data;
    });

    var data = allocateOutputMemoryArray(Nsamples);
    arrays_for_output_signals_array['time'] = data

    return arrays_for_output_signals_array
}




function preparePlotsPlotly(simulator_gui_container, manifest, arrays_for_output_signals_array) {

    var graphDiv = simulator_gui_container.getElementsByClassName('plotly')[0];

    var data = []


    manifest.io.outputs.calculate_output.names.forEach(function (outputName) {

        var trace = {
            x: arrays_for_output_signals_array['time'],
            y: arrays_for_output_signals_array[outputName],
            type: 'scatter',
            name: outputName
        };
        
        data.push(trace)

    });

    console.log("plotly")
    console.log(data)

    var layout = {
      title: 'signals',
      xaxis: {
        title: 'time',
        showgrid: true,
        zeroline: true
      },
      yaxis: {
        title: 'value',
        showline: true
      }
    };
    Plotly.newPlot(graphDiv, data, layout);

    return data
}


function updatePlotsPlotly(simulator_gui_container) {

    var graphDiv = simulator_gui_container.getElementsByClassName('plotly')[0];
    Plotly.redraw(graphDiv)
}






function preparePlotsChartJS(simulator_gui_container, manifest, arrays_for_output_signals_xy) {


    // default colors
    var colorList = ['black', 'red', 'green', 'blue', 'yellow', 'grey'];

    // prepare datasets and pre alloc memory for each to fill in data
    var datasets = []
    var i = 0
    manifest.io.outputs.calculate_output.names.forEach(function (outputName) {

        console.log('added output ')
        console.log(outputName)

        // var data = allocateOutputMemory(Nsamples);
        data = arrays_for_output_signals_xy[outputName]

        var color;
        if (i < colorList.length) {
            color = colorList[i];
        } else {
            color = 'black'
        }

        var dataset = {
            label: outputName,
            borderColor: color,
            data: data
        };

        datasets.push(dataset);
        // dataList[outputName] = data;
        i = i + 1;
    });


    // plot
    var ctx = simulator_gui_container.getElementsByClassName('plot')[0];


    var myLineChart = new Chart(ctx, {
        type: "scatter",
        data: { datasets },
        options: {
            animation: {
                duration: 01 // general animation time
            },
            hover: {
                animationDuration: 0 // duration of animations when hovering an item
            },
            responsiveAnimationDuration: 0 // animation duration after a resize
        }
    });

    return myLineChart;
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

                    console.log(result)

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



// load wasm file
function loadCompiledSimulator() {

    var p_manifest = new Promise(
        function (resolve, reject) {

            console.log('loading manifest')

            fetch('simulation_manifest.json', {cache: "no-cache"})
                .then(response => response.json())
                .then(response => {
            
                resolve( response );                    

            }).then(data => { 
                console.log(data);
            });

        }
    );

    var rawWebAssembly = new Promise(
        function (resolve, reject) {

            console.log('loading wasm data')

            fetch('main.wasm', {cache: "no-cache"} ).then(response => {
            
                resolve( response['arrayBuffer']() );

            }).then(data => { 
                console.log(data);
            });

        }
    );

    var jscode = new Promise(
        function (resolve, reject) {

            console.log('loading js part of wasm data')

            fetch('main.js', {cache: "no-cache"})
                .then(response => response.text())
                .then(response => {
            
                    resolve( response );                    

                }).then(data => { 
                    console.log(data);
                });

        }
    );

    promises = {p_manifest : p_manifest, p_rawWebAssembly : rawWebAssembly, p_jscode : jscode}

    console.log(promises)


    return promises;
}




// create instance fo the simulator
function createInstance( p_manifest, rawWebAssembly, init_fn ) {
    var Module = {

        instantiateWasm: function (imports, successCallback) {
            console.log('creating wasm');

            return rawWebAssembly.then(function(binary) {

                    console.log('starting WebAssembly.instantiate')
                    console.log(binary);

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


    console.log(promises)

    p_manifest = promises.p_manifest
    p_jscode   = promises.p_jscode


    p_jscode.then( function (jscode) {

        console.log( jscode )

        Module = createInstance( p_manifest, promises.p_rawWebAssembly, init_fn ) 
        
        var gvar = this;
        
        eval( jscode )

        ORTD_simulator( Module )
    })
}

function setup_simulation_gui_from_promises( simulator_gui_container, promises) {

    console.log(promises)

    clear_simulator_gui_container( simulator_gui_container )

    setup_simulation_from_promises(promises, function(instance) {



        promises.p_manifest.then(
            function (manifest) {

                // set-up the GUI                        
                console.log('simulation ready')


                var Nsamples = 200;

                arrays_for_output_signals_xy = allocate_arrays_for_output_signals_xy(manifest, Nsamples)
                arrays_for_output_signals_array = allocate_arrays_for_output_signals_array(manifest, Nsamples)

                // init the gui
                init_simulator_gui_container(simulator_gui_container)

                // parameter
                var initvals = genrateParameterInitValues(manifest);

                // var myLineChart

                initParameterEditor(simulator_gui_container, manifest, initvals, function (inputValues) {

                    // on parameter change simulate and plot
                    simulate(instance, manifest, arrays_for_output_signals_array, 
                             arrays_for_output_signals_xy, Nsamples, inputValues);

                    // myLineChart.update();

                    updatePlotsPlotly(simulator_gui_container) 
                });


                simulate(instance, manifest, arrays_for_output_signals_array, 
                          arrays_for_output_signals_xy, Nsamples, initvals);



                // myLineChart = preparePlotsChartJS(simulator_gui_container, manifest, 
                // arrays_for_output_signals_array, arrays_for_output_signals_xy);

                plotly_data = preparePlotsPlotly(simulator_gui_container, manifest, arrays_for_output_signals_array)




                // myLineChart.update();

            })

    
    });

}



function setup_simulation_gui( simulator_gui_container, compile_service_url, secret_token, manifest, code ) {

    source_code = {main_cpp : window.btoa( code )  }
    var promises = compileSimulator(source_code, compile_service_url, secret_token);

    var p_manifest = new Promise(
        function (resolve, reject) {

            console.log(manifest)

            resolve( JSON.parse( manifest ) )

        })

    promises.p_manifest = p_manifest

    setup_simulation_gui_from_promises( simulator_gui_container, promises)
}

