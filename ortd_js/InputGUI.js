'use strict';


class Slider {
  constructor(div, props) {
    this.div = div
    this.props = props;
    this.state = { val: props.default_value };

    this.build()
  }

  update = (val) => {
    this.props.onChange({ index:this.props.index, name: this.props.name, val:val })

    this.state.val = val

    this.v.innerText = '' + this.state.val
//    this.s.setAttribute('value', this.state.val)

    this.s.value = this.state.val

    // update elements
  }

  build() {
    // button
    var b = document.createElement('button')
    b.addEventListener("click", () => this.update( this.props.default_value ) );
//    b.innerHTML =  '<b style=\'font-size: 40px;\'>&#8634;</b>' // '&#8634;' // '↺'
    b.innerHTML =  'reset' 
    b.setAttribute('class', 'parameter_button_reset')

    // slider
    var s = document.createElement('input')
    s.setAttribute('type', 'range')
    s.setAttribute('max', this.props.max_val)
    s.setAttribute('min', this.props.min_val)
    s.setAttribute('step', (this.props.max_val - this.props.min_val) / this.props.steps)
    s.setAttribute('className', 'slider')
    s.addEventListener('input', (e) => this.update( parseFloat(e.target.value) )  )
    s.setAttribute('class', 'parameter_slider')


    this.s = s

    // value
    this.v = document.createElement('div')
    this.v.setAttribute('class', 'parameter_value_display')

    // combine into div
    this.div.appendChild(b)
    this.div.appendChild(s)
    this.div.appendChild(this.v)
    this.div.setAttribute('class', 'parameter_arange')

    //
    this.update(this.props.default_value)

  }

}





class InputBox {
  constructor(div, props) {
    this.div = div
    this.props = props;
    this.state = {  };

    this.build()
  }

  update = () => {
    // update elements
  }

  build() {

    for (var i = 0; i < this.props.names.length; ++i) {

      var index = i
      
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


      // container for one row
      var r = document.createElement('div')


      // name
      var n = document.createElement('span')
      if ('title' in properties) {
        n.innerText = properties.title
      } else {
        n.innerText = name
      }

      // container for sliders
      var c = document.createElement('div')
      new Slider(c, {  
        index:index, 
        name : name,
        max_val : max_val, 
        min_val : min_val, 
        steps : steps,
        default_value : default_value, 
        onChange: (e) => this.props.onChange(e)
      })

      //
      r.appendChild(n)
      r.appendChild(c)

      // combine into div
      this.div.appendChild(r)
    }

    //
    this.update()

  }

}



class inputGUI {

  constructor(div1, names, properties, change_callback) {
    this.change_callback = change_callback

    this.div = div1

    new InputBox( this.div, {names : names, properties : properties, onChange : this.onChange } )
  }


  onChange = (e) => {
    this.change_callback(e)
  }

}


module.exports = {
  inputGUI: inputGUI
}




// // example code

// var names = ['a', 'b', 'c']
// var properties = [ 
//   {  range : [0,2.2], steps : 1000, default_value : 1.11, title : 'some title' },
//   {  range : [-2, 2], steps : 1000, default_value : -0.1 },
//   {  range : [0,200], steps : 100,  default_value : 111 }
// ]  

// const div = document.querySelector('#input_container');
// var input_gui = new inputGUI(div, names, properties, (e) => console.log(e) )

