from langgraph.graph import StateGraph, END
from app.application.agent.state import AgentState
from app.application.agent.nodes import AgentNodes

def create_agent_graph(nodes: AgentNodes):
    """
    Builds and compiles the LangGraph StateGraph workflow.
    Extensible for future tools via the detect_intent state property.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Register Graph Nodes
    workflow.add_node("load_memory", nodes.load_memory)
    workflow.add_node("detect_intent", nodes.detect_intent)
    workflow.add_node("retrieve_context", nodes.retrieve_context)
    workflow.add_node("generate_response", nodes.generate_response)
    workflow.add_node("save_messages", nodes.save_messages)
    
    # 2. Register Graph Flow (Edges)
    workflow.set_entry_point("load_memory")
    workflow.add_edge("load_memory", "detect_intent")
    workflow.add_edge("detect_intent", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_response")
    workflow.add_edge("generate_response", "save_messages")
    workflow.add_edge("save_messages", END)
    
    return workflow.compile()
