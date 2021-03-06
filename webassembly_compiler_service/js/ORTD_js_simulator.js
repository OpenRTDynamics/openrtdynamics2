
function init_simulator_gui_container(divElement) {

    if ( divElement.getElementsByClassName("parameter_editor").length == 0
         && divElement.getElementsByClassName("plot_plotly").length == 0 ) {

            divElement.innerHTML = `
            <div class='parameter_editor'></div>
            <div class="plot_plotly" width="400" height="200"></div>
         `;
    
         }

}

function clear_simulator_gui_container(simulator_gui_container) {

    var parameterEditorDivs = simulator_gui_container.getElementsByClassName("parameter_editor" ) 
    var plotDivs            = simulator_gui_container.getElementsByClassName('plot_plotly')

    for (var i = 0; i < parameterEditorDivs.length; i++) {
        parameterEditorDivs[i].innerHTML = ''
    }

    for (var i = 0; i < plotDivs.length; i++) {
        plotDivs[i].innerHTML = 'Loading..'
    }

}









function simulate(instance, manifest, arrays_for_output_signals_array, arrays_for_output_signals_xy, settings, inputValues) {

    var Nsamples = settings.number_of_samples;
    var sampling_time = settings.sampling_time
    
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

        t = t + sampling_time;
        arrays_for_output_signals_array["time"][i] = t

        manifest.io.outputs.calculate_output.names.forEach(function (outputName) {
            arrays_for_output_signals_array[outputName][i] = outputs[outputName];

            arrays_for_output_signals_xy[outputName][i].x = t;
            arrays_for_output_signals_xy[outputName][i].y = outputs[outputName];
        });
    }

    console.log( arrays_for_output_signals_array )
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

    var value_storage = {} // will be filled in by the input gui on creation

    // for (var i=0; i<i1.length; ++i) {
    //     if ( !(p1[i] === null) && 'default_value' in p1[i] ) {
    //         value_storage[ i1[i] ] = p1[i].default_value
    //     } else {
    //         value_storage[ i1[i] ] = 0.0
    //     }
    // }

    var editorDiv = simulator_gui_container.getElementsByClassName("parameter_editor" )[0]
    editorDiv.innerHTML = ''
    var input_gui = new inputGUI2(editorDiv, i1, p1, (e) => { console.log(e); value_storage[e.name] = e.val ; fn(value_storage) } )

    return input_gui
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

    var plotDivs = simulator_gui_container.getElementsByClassName('plot_plotly');

    
    function prepare_trace(arrays_for_output_signals_array, x_name, y_name, tracke_name) {

        //
        // TODO: no checking of x_name, y_name is performed
        //

        var trace = {
            x: arrays_for_output_signals_array[x_name],
            y: arrays_for_output_signals_array[y_name],
            type: 'scatter',
            name: tracke_name
        };

        return trace
    }


   var N = plotDivs.length

   console.log('building ', N)

   for (var i = 0; i < N; i++) {

        graphDiv = plotDivs[i]
        graphDiv.innerHTML = ''
        var data = []

        console.log('new plot', i, graphDiv)

        if (graphDiv.hasAttribute('x') && graphDiv.hasAttribute('y')) {

            x_names = graphDiv.getAttribute('x').split(" ")
            y_names = graphDiv.getAttribute('y').split(" ")

            // TODO: handle unknown names
            if (x_names.length == 1) {
                x_name = x_names[0]

                y_names.forEach(function (y_name) {
                    trace = prepare_trace(arrays_for_output_signals_array, x_name, y_name, y_name)
                    data.push(trace)    
                })
    
            } else if ( x_names.length == y_names.length ) {

                for (var j=0; j < x_names.length; ++j) {
                    trace = prepare_trace(arrays_for_output_signals_array, x_names[j], y_names[j], x_names[j] + '/' + y_names[j] )
                    data.push(trace)    
                }

            } else {
                console.log('error in setting-up plot: number of x vs. y signals is not matching')
            }

    
        } else {
    
    
            console.log('no special atrributes found')
    
            // put all output signal into one plot
            manifest.io.outputs.calculate_output.names.forEach(function (outputName) {
    
                trace = prepare_trace(arrays_for_output_signals_array, "time", outputName)
                data.push(trace)
    
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

        var layout = {
          title: title,
          xaxis: {
            title: xlabel,
            showgrid: true,
            zeroline: true
          },
          yaxis: {
            title: ylabel,
            showline: true
          }
        };
        Plotly.newPlot(graphDiv, data, layout);

    }


}


function updatePlotsPlotly(simulator_gui_container) {

    var plotDivs = simulator_gui_container.getElementsByClassName('plot_plotly');
    var N = plotDivs.length
 
    for (var i = 0; i < N; i++) {
        graphDiv = plotDivs[i]
        Plotly.redraw(graphDiv)
    }
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

        i = i + 1;
    });


    // plot
    var ctx = simulator_gui_container.getElementsByClassName('plot')[0];
    ctx.innerHTML = ''


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

            console.log('loading wasm data...')

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

function setup_simulation_gui_from_promises( simulator_gui_container, promises, settings) {

    // init the gui
    init_simulator_gui_container(simulator_gui_container)
    clear_simulator_gui_container(simulator_gui_container)

    setup_simulation_from_promises(promises, function(instance) {

    promises.p_manifest.then(
        function (manifest) {

            // set-up the GUI                        
            console.log('simulation ready')

            var arrays_for_output_signals_xy = allocate_arrays_for_output_signals_xy(manifest, settings.number_of_samples)
            var arrays_for_output_signals_array = allocate_arrays_for_output_signals_array(manifest, settings.number_of_samples)

            // parameter
            var initvals = genrateParameterInitValues(manifest);

            // var myLineChart

            var plots_initialized = false

            initParameterEditor(simulator_gui_container, manifest, initvals, function (inputValues) {

                if (plots_initialized) {
                    // on parameter change simulate and plot
                    simulate(instance, manifest, arrays_for_output_signals_array, 
                                arrays_for_output_signals_xy, settings, inputValues);

                    // myLineChart.update();

                    updatePlotsPlotly(simulator_gui_container) 
                }
            });


            simulate(instance, manifest, arrays_for_output_signals_array, 
                        arrays_for_output_signals_xy, settings, initvals);



            // myLineChart = preparePlotsChartJS(simulator_gui_container, manifest, 
            // arrays_for_output_signals_array, arrays_for_output_signals_xy);

            preparePlotsPlotly(simulator_gui_container, manifest, arrays_for_output_signals_array)

            plots_initialized = true




            // myLineChart.update();

        })

    
    });

}



function setup_simulation_gui( simulator_gui_container, compile_service_url, secret_token, manifest, code, settings ) {

    source_code = {main_cpp : window.btoa( code )  }
    var promises = compileSimulator(source_code, compile_service_url, secret_token);

    var p_manifest = new Promise(
        function (resolve, reject) {

            console.log(manifest)

            resolve( JSON.parse( manifest ) )

        })

    promises.p_manifest = p_manifest

    setup_simulation_gui_from_promises( simulator_gui_container, promises, settings)
}

