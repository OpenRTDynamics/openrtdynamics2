#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>
#include <list>
#include <functional>


using namespace std;

#include "libdynV2.h"








ExecutionLineNode::ExecutionLineNode()
{
}

ExecutionLineNode::~ExecutionLineNode()
{
}







ExecutionLine::ExecutionLine()
{
    ListBegin = nullptr;
    ListEnd = nullptr;
}

ExecutionLine::~ExecutionLine()
{

    
}


void ExecutionLine::PushNode(ExecutionLineNode* node)
{
    if (ListBegin == nullptr) {
        ListBegin = node;
        ListEnd = node;
        
        cout << "Push Node (FIRST): ListBegin: " << ListBegin << " ListEnd " << ListEnd << "\n";
    } else {
        ListEnd->NextNode = node;
        ListEnd = node;
        cout << "Push Node: ListBegin: " << ListBegin << " ListEnd " << ListEnd << "\n";
    }
    
}

// 

void ExecutionLine::TraverseTree(std::function<void (int type, ExecutionLineNode *node  )> f)
{

    auto current = ListBegin;
    
    if (current == nullptr)
        return;

    // cout << "current " << current << " ListEnd " << ListEnd << "\n";

    // call lambda function
    f(1, current);

    
    
    while  (current != ListEnd) {

        
        
        current = current->NextNode;
        // cout << "current " << current << " ListEnd " << ListEnd << "\n";
        
        // call lambda function
        f(1, current);
        
        
    }
    
}




Simulation::Simulation()
{
 
    for (i = 0; i < 100; ++i ) {
        auto node = new ExecutionLineNode();
        Line.PushNode(node);
    }
    
    
    auto DisplayNode = [] ( int type, ExecutionLineNode *node ) {
        cout << "node " << node << 1 << "\n";
    };
    
    Line.TraverseTree( DisplayNode );
}













