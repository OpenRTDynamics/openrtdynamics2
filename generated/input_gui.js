'use strict';


const e = React.createElement;

class Slider extends React.Component {
  constructor(props) {
    super(props);
    this.state = { val: props.default_value };
  }

  update = (val) => {
    console.log(val)
    this.props.onChange(val)
    this.setState( {val: val } )
  }

  render() {
    return [

      e('button', { key : "button",
                    onClick: () => this.update( this.props.default_value ) 
                  },
                  'reset' ),

      e('input', {  type:'range', 
                    max : this.props.max_val, 
                    min : this.props.min_val, 
                    value : this.state.val,
                    className : "slider",
                    key : "slider",
                    onChange: (e) => this.update( e.target.value ) 

                }),

      'val = ' + this.state.val

    ];
  }


  // render() {
  //   return [

  //     e('button', { key : "button",
  //                   onClick: () => { this.setState((state) => { 
  //                     return { val : this.props.default_value } 
  //                   } )  }
  //                 },
  //                 'reset' ),

  //     e('input', {  type:'range', 
  //                   max : this.props.max_val, 
  //                   min : this.props.min_val, 
  //                   value : this.state.val,
  //                   className : "slider",
  //                   key : "slider",
  //                   onChange: (e) => this.setState( {val: e.target.value } ) 

  //               }),

  //     'val = ' + this.state.val

  //   ];
  // }



}

class InputBox extends React.Component {
  constructor(props) {
    super(props);
    
    this.state = { values: [] };
  }

  onChange = (e) => {
    console.log(e)
    this.props.onChange(e)
  }

  render() {


    console.log(this.props)

    


    var element_list = []
    for (var i = 0; i < names.length; ++i) {

      var min_val, max_val, default_value;

      if (!(properties[i].default_value === null)) {
        default_value = properties[i].default_value
      } else {
        default_value = 0
      }

      if (!(properties[i].range === null)) {
        min_val = properties[i].range[0]
        max_val = properties[i].range[1]

      } else {
        max_val = 1.0
        min_val = 0.0
      }

      // this.state.values.push(default_value)

      console.log(min_val, max_val, default_value)

      // function reset() {
      //   this.setState((state) => {  return { values : v} } )  }
      // }

      var list_element = e( 'li', { key : names[i] },
        [
          name,

          e( Slider, { key:name, max_val : max_val, min_val : min_val, default_value : default_value, onChange:this.onChange } )



        ]
      )

      element_list.push( list_element )
    }


    return e('ul', {}, element_list)

  }

}

class inputGUI {

  constructor(div, names, properties) {

    ReactDOM.render(e(InputBox, {names : names, properties : properties, onChange : this.onChange }, ), div)

  }

  onChange = (e) => {
    console.log(e)
  }

}


var names = ['a', 'b', 'c']
var properties = [ 
  {  range : [0,2.2], default_value : 1.11 },
  {  range : [-2, 2], default_value : -0.1 },
  {  range : [0,200], default_value : 111 }
]  

const div = document.querySelector('#input_container');
var input_gui = new inputGUI(div, names, properties)

