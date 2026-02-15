"""
TopoGuard Main Detector
Orchestrates graph building and topological analysis for fraud detection.
"""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from loguru import logger

from .graph_builder import TransactionGraphBuilder, Transaction
from .topology_analyzer import TopologyAnalyzer


class TopoGuard:
    """
    Main TopoGuard detector that combines graph building and topological analysis.
    """
    
    def __init__(self, 
                 time_window_hours: int = 24,
                 anomaly_threshold: float = 0.7,
                 persistence_weight: float = 0.6,
                 graph_structure_weight: float = 0.4):
        """
        Initialize TopoGuard detector.
        
        Args:
            time_window_hours: Time window for graph construction
            anomaly_threshold: Score threshold for flagging anomalies
            persistence_weight: Weight for topological persistence features
            graph_structure_weight: Weight for graph structure features
        """
        self.graph_builder = TransactionGraphBuilder(time_window_hours)
        self.topology_analyzer = TopologyAnalyzer()
        self.anomaly_threshold = anomaly_threshold
        self.persistence_weight = persistence_weight
        self.graph_structure_weight = graph_structure_weight
        
        # Reference features for adaptive learning
        self.reference_features: Optional[Dict] = None
        self.adaptive_learning = True
        self.learning_rate = 0.01
        
        logger.info("TopoGuard initialized")
    
    def add_transaction(self, transaction: Transaction):
        """Add a transaction to the system."""
        self.graph_builder.add_transaction(transaction)
    
    def detect(self, transaction: Optional[Transaction] = None) -> Dict:
        """
        Detect anomalies in the current transaction graph.
        
        Args:
            transaction: Optional new transaction to add before detection
            
        Returns:
            Dictionary with detection results
        """
        if transaction:
            self.add_transaction(transaction)
        
        # Build current graph
        graph = self.graph_builder.build_graph()
        
        if graph.number_of_nodes() < 3:
            # Not enough data for meaningful analysis
            return {
                "anomaly_score": 0.0,
                "is_fraudulent": False,
                "reason": "Insufficient transaction data",
                "graph_features": {},
                "topological_features": {},
            }
        
        # Get graph structure features
        graph_features = self.graph_builder.get_graph_features(graph)
        
        # Get topological features
        topological_features = self.topology_analyzer.compute_topological_features(graph)
        
        # Compute anomaly score
        if self.reference_features and self.adaptive_learning:
            # Compare to reference
            topology_score = self.topology_analyzer.compute_anomaly_score(
                graph, self.reference_features
            )
        else:
            # Use absolute complexity
            topology_score = min(topological_features["topological_complexity"] / 10.0, 1.0)
        
        # Graph structure anomaly indicators
        structure_score = 0.0
        if graph_features["density"] > 0.5:  # Unusually dense
            structure_score += 0.3
        if graph_features["strongly_connected_components"] == 1 and graph_features["num_nodes"] > 20:
            # All nodes connected (suspicious for large graphs)
            structure_score += 0.2
        if graph_features["max_in_degree_centrality"] > 0.8:
            # Single account receiving most transactions
            structure_score += 0.3
        if graph_features["max_out_degree_centrality"] > 0.8:
            # Single account sending most transactions
            structure_score += 0.2
        
        # Combine scores
        anomaly_score = (
            self.persistence_weight * topology_score +
            self.graph_structure_weight * structure_score
        )
        anomaly_score = min(anomaly_score, 1.0)
        
        is_fraudulent = anomaly_score >= self.anomaly_threshold
        
        # Update reference features (adaptive learning)
        if self.adaptive_learning and not is_fraudulent:
            self._update_reference_features(topological_features, graph_features)
        
        result = {
            "anomaly_score": float(anomaly_score),
            "is_fraudulent": is_fraudulent,
            "reason": self._generate_reason(anomaly_score, graph_features, topological_features),
            "graph_features": graph_features,
            "topological_features": topological_features,
            "topology_score": float(topology_score),
            "structure_score": float(structure_score),
        }
        
        if is_fraudulent:
            logger.warning(f"Fraud detected: score={anomaly_score:.3f}")
        
        return result
    
    def detect_batch(self, transactions: List[Transaction]) -> List[Dict]:
        """
        Detect anomalies for a batch of transactions.
        
        Args:
            transactions: List of transactions
            
        Returns:
            List of detection results
        """
        results = []
        for tx in transactions:
            result = self.detect(tx)
            results.append({
                "transaction_id": tx.transaction_id,
                **result
            })
        return results
    
    def _update_reference_features(self, 
                                   topological_features: Dict,
                                   graph_features: Dict):
        """Update reference features using exponential moving average."""
        if self.reference_features is None:
            self.reference_features = {
                **topological_features,
                **graph_features
            }
        else:
            # Exponential moving average
            for key in topological_features:
                if key in self.reference_features:
                    self.reference_features[key] = (
                        (1 - self.learning_rate) * self.reference_features[key] +
                        self.learning_rate * topological_features[key]
                    )
                else:
                    self.reference_features[key] = topological_features[key]
            
            for key in graph_features:
                if key in self.reference_features:
                    self.reference_features[key] = (
                        (1 - self.learning_rate) * self.reference_features[key] +
                        self.learning_rate * graph_features[key]
                    )
                else:
                    self.reference_features[key] = graph_features[key]
    
    def _generate_reason(self, 
                        anomaly_score: float,
                        graph_features: Dict,
                        topological_features: Dict) -> str:
        """Generate human-readable reason for the anomaly score."""
        reasons = []
        
        if anomaly_score >= 0.8:
            reasons.append("High topological complexity deviation")
        elif anomaly_score >= 0.6:
            reasons.append("Moderate structural anomaly detected")
        
        if graph_features.get("density", 0) > 0.5:
            reasons.append("Unusually dense transaction network")
        
        if graph_features.get("max_in_degree_centrality", 0) > 0.8:
            reasons.append("Single account receiving majority of transactions")
        
        if topological_features.get("topological_complexity", 0) > 5.0:
            reasons.append("Abnormal topological structure")
        
        if not reasons:
            return "Normal transaction pattern"
        
        return "; ".join(reasons)




