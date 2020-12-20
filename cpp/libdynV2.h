#ifndef H_libdynV2
#define H_libdynV2


#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>
#include <list>
#include <functional>


//class ExecutionTree;





class Block {
  
private:
    void *compfnptr;
    
public:
    Block();
    ~Block();
    
    void Exec();
    void Reset();
    
    // inlucde libdyn block struct
    
};



class ExecutionLine;



class ExecutionLineNode {
public:
    ExecutionLineNode *NextNode;
    //ExecutionTree *Subsystem;
    
    Block block;
    
    std::list< ExecutionLine> SubLine;
    
public:
    ExecutionLineNode();
    ~ExecutionLineNode();
    
    
};






class ExecutionLine {
private:
    ExecutionLineNode *ListBegin, *ListEnd;
 
public:
    ExecutionLine();
    ~ExecutionLine();
    
    void PushNode( ExecutionLineNode *node );
    void TraverseTree( std::function < void ( int type,  ExecutionLineNode *node )> f );
    void ShowTree( );
    
    
    
};




class Simulation {
private:
    int i; 
    ExecutionLine Line;
    
    
public:
    Simulation();
    ~Simulation();
    
    
};






#endif

