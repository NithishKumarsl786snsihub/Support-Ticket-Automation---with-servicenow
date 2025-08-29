"""
LangGraph Workflow Graph
Constructs the complete workflow for ticket automation
"""

from langgraph.graph import StateGraph, END

from utils.models import WorkflowState
from workflow.nodes_optimized import (
    scheduler_node,
    message_fetcher_node,
    optimized_classifier_node as classifier_node,
    optimized_summary_node as summary_node,
    optimized_category_extractor_node as category_extractor_node,
    servicenow_node,
    notification_node,
    tracker_node
)

def create_workflow() -> StateGraph:
    """Create the complete LangGraph workflow"""
    
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("scheduler", scheduler_node)
    workflow.add_node("message_fetcher", message_fetcher_node)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("category_extractor", category_extractor_node)
    workflow.add_node("servicenow", servicenow_node)
    workflow.add_node("notification", notification_node)
    workflow.add_node("tracker", tracker_node)
    
    # Define workflow edges
    workflow.add_edge("scheduler", "message_fetcher")
    workflow.add_edge("message_fetcher", "classifier")
    workflow.add_edge("classifier", "summary")
    workflow.add_edge("summary", "category_extractor")
    workflow.add_edge("category_extractor", "servicenow")
    workflow.add_edge("servicenow", "notification")
    workflow.add_edge("notification", "tracker")
    workflow.add_edge("tracker", END)
    
    # Set entry point
    workflow.set_entry_point("scheduler")
    
    return workflow.compile()
