
"""
[DEPRECATED]
This manual graph memory is deprecated in favor of `skills.knowledge.graph_rag`.
Please use `skills.knowledge.graph_rag.implementation` for new code.
"""
import warnings
warnings.warn("skills.knowledge.memory.graph_store is deprecated. Use skills.knowledge.graph_rag instead.", DeprecationWarning, stacklevel=2)

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class GraphMemory:
    """
    Mental Model / Knowledge Graph for the Agent.
    Stores 'Nodes' (Papers, Concepts) and 'Edges' (Relations like 'refutes', 'supports').
    
    IMPROVEMENTS (2024-01-30):
    - Added persistence to JSON file
    - Added timestamps for temporal reasoning
    - Added multi-hop traversal for complex relationship queries
    - Added edge metadata for richer relationships
    """
    def __init__(self, persist_path: Optional[str] = None):
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self.persist_path = persist_path
        
        # Load existing graph if persistence path exists
        if persist_path and os.path.exists(persist_path):
            self._load()
        
    def _save(self):
        """Persist graph to JSON file."""
        if self.persist_path:
            data = {
                "nodes": self.nodes,
                "edges": self.edges,
                "last_modified": datetime.now().isoformat()
            }
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
    def _load(self):
        """Load graph from JSON file."""
        if self.persist_path and os.path.exists(self.persist_path):
            with open(self.persist_path, 'r') as f:
                data = json.load(f)
                self.nodes = data.get("nodes", {})
                self.edges = data.get("edges", [])
        
    def add_node(self, id: str, type: str, content: Any, metadata: Optional[Dict] = None):
        """Adds a fact/paper to memory with optional metadata."""
        self.nodes[id] = {
            "type": type, 
            "content": content,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._save()
        
    def add_edge(self, source_id: str, target_id: str, relation_type: str, 
                 confidence: float = 1.0, evidence: Optional[str] = None):
        """Adds a relationship between two nodes with optional metadata."""
        self.edges.append({
            "source": source_id,
            "target": target_id, 
            "relation": relation_type,
            "confidence": confidence,
            "evidence": evidence,
            "created_at": datetime.now().isoformat()
        })
        self._save()
        
    def get_related_nodes(self, node_id: str, relation_type: str = None) -> List[Dict]:
        """Finds all nodes related to the given node."""
        related = []
        for edge in self.edges:
            if edge["source"] == node_id:
                if relation_type and edge["relation"] != relation_type:
                    continue
                target = self.nodes.get(edge["target"])
                if target:
                    related.append({
                        "node": target,
                        "relation": edge["relation"],
                        "direction": "outgoing",
                        "confidence": edge.get("confidence", 1.0),
                        "evidence": edge.get("evidence")
                    })
            elif edge["target"] == node_id:
                if relation_type and edge["relation"] != relation_type:
                    continue
                source = self.nodes.get(edge["source"])
                if source:
                    related.append({
                        "node": source,
                        "relation": edge["relation"],
                        "direction": "incoming",
                        "confidence": edge.get("confidence", 1.0),
                        "evidence": edge.get("evidence")
                    })
        return related

    def multi_hop_query(self, start_id: str, max_depth: int = 2) -> Dict[int, List[Dict]]:
        """
        Multi-hop traversal from a starting node.
        Returns nodes at each depth level.
        
        Example: Find all papers that refute papers that support Paper A
        """
        result = {0: [self.nodes.get(start_id)]}
        visited = {start_id}
        current_frontier = [start_id]
        
        for depth in range(1, max_depth + 1):
            next_frontier = []
            depth_results = []
            
            for node_id in current_frontier:
                related = self.get_related_nodes(node_id)
                for r in related:
                    # Find the ID of the related node
                    for nid, ndata in self.nodes.items():
                        if ndata == r["node"] and nid not in visited:
                            visited.add(nid)
                            next_frontier.append(nid)
                            depth_results.append({
                                "node_id": nid,
                                "node": r["node"],
                                "path_relation": r["relation"],
                                "path_direction": r["direction"]
                            })
            
            result[depth] = depth_results
            current_frontier = next_frontier
            
        return result

    def reasoning_query(self, query_concept: str) -> str:
        """
        Simple graph traversal to answer relationship questions.
        Example: "What refutes Fact X?" -> Looks for incoming 'refutes' edges to Fact X node.
        """
        # 1. Find the target node
        target_id = None
        for nid, data in self.nodes.items():
            if query_concept in str(data["content"]):
                target_id = nid
                break
        
        if not target_id:
            return "I don't have that concept in my memory."
            
        # 2. Check connections
        related = self.get_related_nodes(target_id)
        if not related:
            return "I know about this concept, but I don't see any stored relationships."
            
        summary = f"Regarding {query_concept}:\n"
        for r in related:
            rel = r["relation"]
            content = r["node"]["content"]
            direction = r["direction"]
            confidence = r.get("confidence", 1.0)
            
            confidence_str = f" (confidence: {confidence:.0%})" if confidence < 1.0 else ""
            
            if direction == "incoming" and rel == "refutes":
                summary += f"- It is REFUTED by: {content}{confidence_str}\n"
            elif direction == "incoming" and rel == "supports":
                summary += f"- It is SUPPORTED by: {content}{confidence_str}\n"
            else:
                summary += f"- Linked via {rel}: {content}{confidence_str}\n"
                
        return summary
    
    def get_stats(self) -> Dict:
        """Returns statistics about the knowledge graph."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": list(set(n["type"] for n in self.nodes.values())),
            "relation_types": list(set(e["relation"] for e in self.edges))
        }

