'use strict';


const e = React.createElement;

class Slider extends React.Component {
  constructor(props) {
    super(props);
    this.state = { val: props.default_value };
  }

  update = (val) => {
    this.props.onChange({ index:this.props.index, name: this.props.name, val:val })
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
                    step : (this.props.max_val - this.props.min_val) / this.props.steps,
                    value : this.state.val,
                    className : "slider",
                    key : "slider",
                    onChange: (e) => this.update( parseFloat(e.target.value) ) 

                }),

      'val = ' + this.state.val

    ];
  }


}

class InputBox extends React.Component {
  constructor(props) {
    super(props);
    
    this.state = { values: [] };
  }

  onChange = (e) => {
    this.props.onChange(e)
  }

  render() {

    var element_list = []
    for (var i = 0; i < this.props.names.length; ++i) {

      var index = i
      console.log(this.props.properties)

      
      var name = this.props.names[i]
      var properties = this.props.properties[i]
      if (properties === null) {
        properties = {}
      }


      var min_val, max_val, default_value, steps;

      if ('default_value' in properties && !(properties.default_value === null)) {
        default_value = properties.default_value
      } else {
        default_value = 0
      }

      if ('range' in properties && !(properties.range === null)) {
        min_val = properties.range[0]
        max_val = properties.range[1]

      } else {
        max_val = 1.0
        min_val = 0.0
      }

      if ('steps' in properties && !(properties.steps === null)) {
        steps = properties.steps
      } else {
        steps = 1000
      }

      

      console.log(min_val, max_val, default_value)

      var list_element = e( 'div', { key : name },
        [
          name,

          e( Slider, {  
                        key:'slider', 
                        index:index, 
                        name : name,
                        max_val : max_val, 
                        min_val : min_val, 
                        steps : steps,
                        default_value : default_value, 
                        onChange: (e) => this.onChange(e) 
                      })

        ]
      )

      element_list.push( list_element )
    }


    return e('div', {}, element_list)

  }

}

class inputGUI {

  constructor(div1, names, properties, change_callback) {
    this.change_callback = change_callback
    ReactDOM.render(e(InputBox, {names : names, properties : properties, onChange : this.onChange }, ), div1)
  }

  onChange = (e) => {
    this.change_callback(e)
  }

}


var names = ['a', 'b', 'c']
var properties = [ 
  {  range : [0,2.2], steps : 1000, default_value : 1.11 },
  {  range : [-2, 2], steps : 1000, default_value : -0.1 },
  {  range : [0,200], steps : 100,  default_value : 111 }
]  

const div = document.querySelector('#input_container');
var input_gui = new inputGUI(div, names, properties, (e) => console.log(e) )

