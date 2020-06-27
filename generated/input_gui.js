'use strict';


const e = React.createElement;

class InputBox extends React.Component {
  constructor(props) {
    super(props);
    
    this.state = { values: [] };
  }

  render() {


    // return e(
    //   'button',
    //   { onClick: () => this.setState({ liked: true }) },
    //   'Like'
    // );

    console.log(this.props)

    

    // var element_list = this.props.names.map(name => 
    //   e('button', { key : name }, name )
    // );

    // var element_list = this.props.names.map(name => 
    //   e( 'li', { key : name },
    //     [
    //       name, 
    //       e('button', { key : "button" }, name ),
    //       e('input', { type:'range', key : "slider" } )
    //     ]
    //   )
    // );


    // var element_list = this.props.names.map(name => 
    //   e( 'li', { key : name },
    //     [
    //       name, 
    //       e('button', { key : "button" }, name ),
    //       e('input', { type:'range', key : "slider" } )
    //     ]
    //   )
    // );

    var element_list = []
    for (var i = 0; i < names.length; ++i) {

      var min_val, max_val, default_val;

      if (!(properties[i].default_value === null)) {
        default_val = properties[i].default_value
      } else {
        default_val = 0
      }

      if (!(properties[i].range === null)) {
        min_val = properties[i].range[0]
        max_val = properties[i].range[1]

      } else {
        max_val = 1.0
        min_val = 0.0
      }

      this.state.values.push(default_val)

      console.log(min_val, max_val, default_val)

      // function reset() {
      //   this.setState((state) => {  return { values : v} } )  }
      // }

      var list_element = e( 'li', { key : names[i] },
        [
          name, 
          e('button', { key : "button",
                        onClick: () => { this.setState((state) => { 
                          var v = state.values; v[i] = 0; return { values : v } 
                        } )  }
                      },
           'reset' ),
          e('input', { type:'range', max : max_val , min : min_val, value : default_val, key : "slider" } )
        ]
      )

      element_list.push( list_element )
    }


    return e('ul', {}, element_list)

    // return [
    //   e(
    //   'button',
    //   { onClick: () => this.setState({ liked: true }), key : 1 },
    //   'Like'
    //   ), 
    //   e(
    //     'button',
    //     { onClick: () => this.setState({ liked: true }), key : 2 },
    //     'Like'
    //     )    
    // ];


  }

}

class inputGUI {

  constructor(div, names, properties) {

    ReactDOM.render(e(InputBox, {names : names, properties : properties}, ), div)

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

