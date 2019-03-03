


struct dynlib_block_t {
  struct dynlib_simulation_t *sim; // The simulation which this block belongs to
  
  int block_type; // 0 normal dynamic; 1 static function
  int d_feedthrough; // Direct Feedthrough?

  //char identification[10];
  char *identification;
  int numID;
  int own_outcache; // output cache memory should not be allocated
  int own_outcache_toconfigure;

  int *ipar;
  double *rpar;
  void *opar;

  int Nout;
  struct dynlib_outlist_t *outlist; // Pointer auf ausgangswerte cache Liste (1. Eintrag)
  void *outdata; // Datendie für die Ausgänge angelegt werden - unused if own_outcache = 1

  int Nin;
  struct dynlib_inlist_t *inlist; // Pointer auf Eingangliste, die verknuepfungen zu anderen Blöcken herstelt.  (1. Eintrag)

  int (*comp_func)(int flag, struct dynlib_block_t *block);  // Computational function
  
  char block_initialised; // Was the INIT-FLAG of the comp_func successfully called?
  
  void *work;

  // execution lists

//   struct dynlib_block_t *exec_list_prev;
//   struct dynlib_block_t *exec_list_next;
//   struct dynlib_block_t *exec_sup_list_prev;
//   struct dynlib_block_t *exec_sup_list_next;
// 
//   // allblocks list
//   struct dynlib_block_t *allblocks_list_prev;
//   struct dynlib_block_t *allblocks_list_next;

  // simulator helper vars

 // int needs_output_update; // After updated states is called this is set to 1 in order to indicate the need for the need of output an update 

  // Events
  //int event_mask;
  //int Nevents; // number of subscribed events
  //char event_map[LIBDYN_MAX_BLOCK_EVENTS]; // maps block side event (index) to simulation event (array values)
  //int block_events; // active events that the block receives

  // Used by execution list generation algorithm

//  int remaining_input_availability;
//  char block_executed;

  // comput. func. extra parameters
//  void *extraparam;
  
  // 
  int irpar_config_id;
  int btype;
};

