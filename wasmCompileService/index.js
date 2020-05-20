var express        = require("express");
var bodyParser     = require("body-parser");
var app            = express();
const tmp          = require('tmp');
const { exec }     = require("child_process");
const fs           = require('fs')

var cors = require('cors')
app.use(cors())


const config = require('./config.json');
var emcc_binary = config.emcc_binary




function compile(tmp_dir, source_code) {

  command = '' + emcc_binary + '  --bind -s MODULARIZE=1 -s EXPORT_NAME="ORTD_simulator" main.cpp -g4 -s -o main.js'

  var p_compile = new Promise(
    function (resolve, reject) {

      exec(command, { cwd : tmp_dir }, (error, stdout, stderr) => {
        if (error) {
            console.log(`error: ${error.message}`);

            reject( error.message )
            return;
        }
        if (stderr) {
            console.log(`stderr: ${stderr}`);
            return;
        }
        console.log(`stdout: ${stdout}`);

        resolve( stdout.message )
      });

    })


    var p_wasm = new Promise(
      function (resolve, reject) {
  
        p_compile.then( function(result) {

          fs.readFile(tmp_dir + '/main.wasm', (err, data) => {
            if (err) {

              console.error(err)
              reject(err)

              return
            }

            resolve(data)
        
          })
        })

    })


    var p_jsfile = new Promise(
      function (resolve, reject) {
  
        p_compile.then( function(result) {

          fs.readFile(tmp_dir + '/main.js', (err, data) => {
            if (err) {
              
              console.error(err)
              reject(err)

              return
            }

            resolve(data)
        
          })
        })

    })


    return {p_wasm : p_wasm, p_jsfile : p_jsfile}

}


app.use(bodyParser.json(  limit='5000kb' ) );


app.post('/upload', function(req,res) {

    res.header("Access-Control-Allow-Origin", "*");

    console.log( req.body )

    var source_code = req.body.source_code;
    var password = req.body.password;

    console.log(source_code)

    tmp_dir = './uploads'


    fs.writeFile(tmp_dir + "/main.cpp",  new Buffer(source_code.main_cpp, 'base64'), function(err) {
      if (err) {

        return
      }

      ret = compile(tmp_dir, source_code)


      // wait for the compiler
      ret.p_wasm.then( function(result) {

        rawWebAssembly = result
    
        ret.p_jsfile.then( function(result) {
    
          jscode = result
    
          return_vals = { manifest : "blub", rawWebAssembly : rawWebAssembly.toString('base64'), jscode : jscode.toString('base64') }
          raw_return_data = JSON.stringify(return_vals)
        
          res.setHeader('Content-Type', 'application/json')
          res.end( raw_return_data )
        })
      })


    })

  
});


app.use('/js', express.static('js'))


var port = parseInt(config.node_port)

app.listen(port,function(){
  console.log("Listening on port " + port );
})




