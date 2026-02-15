"""
Transaction Graph Builder
Constructs temporal graphs from financial transactions for topological analysis.
"""

import networkx as nx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class Transaction:
    """Represents a financial transaction."""
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    timestamp: datetime
    metadata: Optional[Dict] = None


class TransactionGraphBuilder:
    """
    Builds temporal graphs from transaction data for topological analysis.
    """
    
    def __init__(self, time_window_hours: int = 24):
        """
        Initialize the graph builder.
        
        Args:
            time_window_hours: Time window for graph construction
        """
        self.time_window_hours = time_window_hours
        self.transactions: List[Transaction] = []
    
    def add_transaction(self, transaction: Transaction):
        """Add a transaction to the buffer."""
        self.transactions.append(transaction)
        # Keep only transactions within the time window
        cutoff = transaction.timestamp - timedelta(hours=self.time_window_hours)
        self.transactions = [
            tx for tx in self.transactions 
            if tx.timestamp >= cutoff
        ]
    
    def build_graph(self, current_time: Optional[datetime] = None) -> nx.DiGraph:
        """
        Build a directed graph from transactions.
        
        Args:
            current_time: Reference time for filtering (defaults to latest transaction)
            
        Returns:
            NetworkX directed graph
        """
        if not self.transactions:
            return nx.DiGraph()
        
        if current_time is None:
            current_time = max(tx.timestamp for tx in self.transactions)
        
        cutoff = current_time - timedelta(hours=self.time_window_hours)
        recent_transactions = [
            tx for tx in self.transactions 
            if tx.timestamp >= cutoff
        ]
        
        G = nx.DiGraph()
        
        # Add nodes (accounts)
        accounts = set()
        for tx in recent_transactions:
            accounts.add(tx.from_account)
            accounts.add(tx.to_account)
        
        G.add_nodes_from(accounts)
        
        # Add edges (transactions) with weights
        edge_weights = {}
        for tx in recent_transactions:
            edge = (tx.from_account, tx.to_account)
            if edge not in edge_weights:
                edge_weights[edge] = []
            edge_weights[edge].append(tx.amount)
        
        # Normalize edge weights
        all_amounts = [amount for amounts in edge_weights.values() for amount in amounts]
        if all_amounts:
            max_amount = max(all_amounts)
            min_amount = min(all_amounts)
            amount_range = max_amount - min_amount if max_amount != min_amount else 1.0
        else:
            amount_range = 1.0
        
        for edge, amounts in edge_weights.items():
            # Weight = normalized total flow + frequency
            total_flow = sum(amounts)
            frequency = len(amounts)
            normalized_flow = (total_flow - min_amount) / amount_range if amount_range > 0 else 0.5
            weight = 0.7 * normalized_flow + 0.3 * (frequency / len(recent_transactions))
            
            G.add_edge(edge[0], edge[1], weight=weight, flow=total_flow, count=frequency)
        
        return G
    
    def get_graph_features(self, graph: nx.DiGraph) -> Dict[str, float]:
        """
        Extract topological features from the graph.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            Dictionary of graph features
        """
        if graph.number_of_nodes() == 0:
            return {
                "num_nodes": 0,
                "num_edges": 0,
                "density": 0.0,
                "avg_clustering": 0.0,
                "avg_degree": 0.0,
                "strongly_connected_components": 0,
                "weakly_connected_components": 0,
            }
        
        # Convert to undirected for some metrics
        G_undirected = graph.to_undirected()
        
        features = {
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "density": nx.density(graph),
            "avg_clustering": nx.average_clustering(G_undirected),
            "avg_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes(),
            "strongly_connected_components": nx.number_strongly_connected_components(graph),
            "weakly_connected_components": nx.number_weakly_connected_components(graph),
        }
        
        # Add centrality measures
        if graph.number_of_nodes() > 0:
            try:
                in_degree_centrality = nx.in_degree_centrality(graph)
                out_degree_centrality = nx.out_degree_centrality(graph)
                features["max_in_degree_centrality"] = max(in_degree_centrality.values()) if in_degree_centrality else 0.0
                features["max_out_degree_centrality"] = max(out_degree_centrality.values()) if out_degree_centrality else 0.0
            except:
                features["max_in_degree_centrality"] = 0.0
                features["max_out_degree_centrality"] = 0.0
        
        return features




