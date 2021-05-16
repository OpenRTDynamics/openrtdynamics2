from . import lang as dy


cpp_class_code = """

class CircularBuffer {
public:

    double *state_memory;
    int n, write_cnt, abs_cnt;

    CircularBuffer(int n) {
    
        this->state_memory = new double[n];
        this->n         = n;
        this->write_cnt = 0;
        this->abs_cnt   = 0;   
    }
    
    ~CircularBuffer() {
    
        delete[] this->state_memory;
    }

    void reset() {
    
        this->write_cnt = 0;
        this->abs_cnt   = 0;

        for (int i = 0; i < n; ++i) {
            state_memory[i] = 0;
        }
    }
    
    void get_current_absolute_write_index(int & index) {
        index = this->abs_cnt;

        // printf( "get_current_absolute_write_index (%p): %d\\n", this, this->abs_cnt );
    }

    void get_absolute_minimal_index(int & index) {
        index = this->abs_cnt - this->n;

        if (index < 0) {
            index = 0;
        }
    }

    void read_from_absolute_index(double & output, int abs_index) {
    
        int diff = this->abs_cnt - abs_index; // >= 0
    
        int arr_index = this->write_cnt - diff;
        
        if (arr_index < 0) {
          arr_index = this->n - (-arr_index);
        }
        
        if (arr_index >= this->n) { // check this
        
            // error
            // printf("read_from_absolute_index: bad index %d (maximal valid index: %d)\\n", abs_index, this->abs_cnt-1);
            output = NAN;
            
        } else if ( arr_index < 0 ) {
        
            // error
            // printf("read_from_absolute_index: bad index %d (maximal valid index: %d)\\n", abs_index, this->abs_cnt-1);
            output = NAN;
            
        } else {
        
            output = state_memory[ arr_index ];
            
        }        
    }
    
    void append_to_buffer(double value) {
    
        state_memory[ this->write_cnt ] = value;
        
        this->abs_cnt++;
        this->write_cnt++;
        
        if (this->write_cnt >= this->n) {
        
            // wrap
            this->write_cnt = 0;
        }

        // printf( "append_to_buffer (%p): %d %f\\n", this, this->abs_cnt, value );

    }

};

typedef CircularBuffer *CircularBufferPtr;
"""

def new_circular_buffer_float64(n : int):
    
    dy.include_cpp_code(identifier = 'CircularBuffer', code = cpp_class_code)
    dafatype_circular_buffer = dy.DataTypePointer( cpp_type_name_class = 'CircularBuffer' )  
    shared_ptr   = dy.cpp_allocate_class( datatype=dafatype_circular_buffer, code_constructor_call='CircularBuffer(' + str(n) + ')' )
    
    return shared_ptr


def read_from_absolute_index(shared_states_ptr, index):
    
    value = dy.cpp_call_class_member_function(
        ptr_signal    = shared_states_ptr,

        input_signals = [ index ],
        input_types   = [ dy.DataTypeInt32(1)   ],
        output_types  = [ dy.DataTypeFloat64(1) ],

        # call the function read_from_index        
        member_function_name_to_calc_outputs = 'read_from_absolute_index'
    )
    
    return value[0]


def get_current_absolute_write_index(shared_states_ptr):
    
    value = dy.cpp_call_class_member_function(
        ptr_signal    = shared_states_ptr,

        input_signals = [  ],
        input_types   = [  ],
        output_types  = [ dy.DataTypeInt32(1) ],

        # call the function read_from_index        
        member_function_name_to_calc_outputs = 'get_current_absolute_write_index'
    )
    
    return value[0]

def get_absolute_minimal_index(shared_states_ptr):
    
    value = dy.cpp_call_class_member_function(
        ptr_signal    = shared_states_ptr,

        input_signals = [  ],
        input_types   = [  ],
        output_types  = [ dy.DataTypeInt32(1) ],

        # call the function read_from_index        
        member_function_name_to_calc_outputs = 'get_absolute_minimal_index'
    )
    
    return value[0]




def append_to_buffer(shared_states_ptr, value_to_write):
    
    dy.cpp_call_class_member_function(
        ptr_signal    = shared_states_ptr,

        input_signals = [ value_to_write        ],
        input_types   = [ dy.DataTypeFloat64(1) ],
        output_types  = [  ],

        # call the function write_to_index on *state update*
        member_function_name_to_update_states = 'append_to_buffer'
    )
    