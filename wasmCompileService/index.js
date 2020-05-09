



var express        =         require("express");
var bodyParser     =         require("body-parser");
var app            =         express();

var cors = require('cors')
app.use(cors())
// app.use(bodyParser.urlencoded({ extended: false }));


app.use(bodyParser.json(  limit='5000kb' ) );

// let parserJSON = bodyParser.json(type='*/*', limit='5000kb')

app.post('/upload', function(req,res){

    res.header("Access-Control-Allow-Origin", "*");

    console.log( req.body )

    var source_code = req.body.main_cpp;
    var password = req.body.password;

    console.log(source_code)


  return_vals = { manifest : "blub", rawWebAssembly : "xxxxx", jscode : "x=1" }

  raw_return_data = JSON.stringify(return_vals)


  res.setHeader('Content-Type', 'application/json')
  res.end( raw_return_data )

  // res.end(    '{ "manifest" : "ok" }'  );
});






// app.post('/upload', parserJSON, function(req,res){

//   res.header("Access-Control-Allow-Origin", "*");

//   console.log( req.body )

// // var source_code = req.body.main_cpp;
// // var password = req.body.password;

// // console.log("password is " + password);

// // console.log(source_code)

// res.end("yes");
// });




app.listen(3000,function(){
  console.log("Started on PORT 3000");
})






// const express = require('express');
// const fileUpload = require('express-fileupload');
// const cors = require('cors');
// const bodyParser = require('body-parser');
// const morgan = require('morgan');
// const _ = require('lodash');

// const app = express();

// // enable files upload
// app.use(fileUpload({
//     createParentPath: true,
//     limits: { 
//         fileSize: 2 * 1024 * 1024 * 1024 //2MB max file(s) size
//     },
// }));

// //add other middleware
// app.use(cors());
// app.use(bodyParser.json());
// app.use(bodyParser.urlencoded({extended: true}));
// app.use(morgan('dev'));


// app.post('/upload',function(req,res){

//     var user_name=req.body.user;
//     var password=req.body.password;

//     console.log(req.body)


//     console.log("User name = "+user_name+", password is "+password);

//     res.end("yes");
// });



// // upoad single file
// app.post('/upload-avatar', async (req, res) => {
//     try {
//         if(!req.files) {
//             res.header("Access-Control-Allow-Origin", "*");
//             //res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");

//             res.send({
//                 status: false,
//                 message: 'No file uploaded'
                
//             });
//         } else {
//             //Use the name of the input field (i.e. "avatar") to retrieve the uploaded file
//             let avatar = req.files.avatar;
            
//             //Use the mv() method to place the file in upload directory (i.e. "uploads")
//             avatar.mv('./uploads/' + avatar.name);

//             //send response
//             res.header("Access-Control-Allow-Origin", "*");
//             res.send({
//                 status: true,
//                 message: 'File is uploaded',
//                 data: {
//                     name: avatar.name,
//                     mimetype: avatar.mimetype,
//                     size: avatar.size
//                 }
//             });
//         }
//     } catch (err) {
//         res.status(500).send(err);
//     }
// });

// // upload multiple files
// app.post('/upload_sourcecode', async (req, res) => {
//     try {
//         console.log(req)

//         if(!req.files) {
//             res.send({
//                 status: false,
//                 message: 'No file uploaded'
//             });

//             console.log('no file')
//         } else {

//             console.log('got file')


//             let data = []; 
    
//             //loop all files
//             _.forEach(_.keysIn(req.files.photos), (key) => {
//                 let photo = req.files.photos[key];
                
//                 //move photo to upload directory
//                 photo.mv('./uploads/' + photo.name);

//                 //push file details
//                 data.push({
//                     name: photo.name,
//                     mimetype: photo.mimetype,
//                     size: photo.size
//                 });
//             });
    
//             //return response
//             res.send({
//                 status: true,
//                 message: 'Files are uploaded',
//                 data: data
//             });
//         }
//     } catch (err) {
//         res.status(500).send(err);
//     }
// });

// //make uploads directory static
// app.use(express.static('uploads'));

// //start app 
// const port = process.env.PORT || 3000;

// app.listen(port, () => 
//   console.log(`App is listening on port ${port}.`)
// );