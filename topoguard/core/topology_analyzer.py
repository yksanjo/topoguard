"""
Topology Analyzer
Performs topological data analysis on transaction graphs using persistent homology.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import networkx as nx
from ripser import ripser
from persim import PersistenceImager
import warnings
warnings.filterwarnings('ignore')


class TopologyAnalyzer:
    """
    Analyzes topological structure of transaction graphs using persistent homology.
    """
    
    def __init__(self, max_dimension: int = 2, metric: str = "euclidean"):
        """
        Initialize the topology analyzer.
        
        Args:
            max_dimension: Maximum homology dimension to compute
            metric: Distance metric for persistence computation
        """
        self.max_dimension = max_dimension
        self.metric = metric
        self.persim = PersistenceImager(pixel_size=0.1, birth_range=(0, 2), pers_range=(0, 2))
    
    def graph_to_point_cloud(self, graph: nx.DiGraph) -> np.ndarray:
        """
        Convert graph to point cloud using node embeddings.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            Point cloud as numpy array
        """
        if graph.number_of_nodes() == 0:
            return np.array([]).reshape(0, 2)
        
        # Use graph layout for embedding
        try:
            pos = nx.spring_layout(graph, dim=2, seed=42)
        except:
            # Fallback: use degree-based coordinates
            degrees = dict(graph.degree())
            pos = {node: [degrees.get(node, 0), graph.in_degree(node)] for node in graph.nodes()}
        
        # Extract coordinates
        nodes = list(graph.nodes())
        point_cloud = np.array([pos[node] for node in nodes])
        
        return point_cloud
    
    def compute_persistence(self, point_cloud: np.ndarray) -> Dict:
        """
        Compute persistent homology of point cloud.
        
        Args:
            point_cloud: Point cloud as numpy array
            
        Returns:
            Dictionary with persistence diagrams and features
        """
        if point_cloud.shape[0] < 3:
            # Not enough points for meaningful topology
            return {
                "diagrams": [],
                "total_persistence": 0.0,
                "num_features": 0,
                "max_persistence": 0.0,
            }
        
        try:
            # Compute persistence
            diagrams = ripser(point_cloud, maxdim=self.max_dimension, metric=self.metric)
            dgms = diagrams['dgms']
            
            # Extract features
            total_persistence = 0.0
            num_features = 0
            max_persistence = 0.0
            
            for dim, dgm in enumerate(dgms):
                if len(dgm) > 0:
                    # Persistence = death - birth
                    persistences = dgm[:, 1] - dgm[:, 0]
                    total_persistence += np.sum(persistences)
                    num_features += len(dgm)
                    max_persistence = max(max_persistence, np.max(persistences) if len(persistences) > 0 else 0.0)
            
            return {
                "diagrams": dgms,
                "total_persistence": float(total_persistence),
                "num_features": int(num_features),
                "max_persistence": float(max_persistence),
            }
        except Exception as e:
            # Fallback for computation errors
            return {
                "diagrams": [],
                "total_persistence": 0.0,
                "num_features": 0,
                "max_persistence": 0.0,
                "error": str(e),
            }
    
    def compute_topological_features(self, graph: nx.DiGraph) -> Dict[str, float]:
        """
        Compute comprehensive topological features from graph.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            Dictionary of topological features
        """
        if graph.number_of_nodes() == 0:
            return {
                "total_persistence": 0.0,
                "num_topological_features": 0,
                "max_persistence": 0.0,
                "topological_complexity": 0.0,
            }
        
        # Convert to point cloud
        point_cloud = self.graph_to_point_cloud(graph)
        
        # Compute persistence
        persistence_data = self.compute_persistence(point_cloud)
        
        # Compute complexity metric
        complexity = persistence_data["total_persistence"] / max(persistence_data["num_features"], 1)
        
        features = {
            "total_persistence": persistence_data["total_persistence"],
            "num_topological_features": persistence_data["num_features"],
            "max_persistence": persistence_data["max_persistence"],
            "topological_complexity": complexity,
        }
        
        return features
    
    def compute_anomaly_score(self, 
                             graph: nx.DiGraph, 
                             reference_features: Optional[Dict] = None) -> float:
        """
        Compute anomaly score based on topological deviation.
        
        Args:
            graph: Current transaction graph
            reference_features: Reference topological features (for comparison)
            
        Returns:
            Anomaly score between 0 and 1
        """
        current_features = self.compute_topological_features(graph)
        
        if reference_features is None:
            # No reference: use absolute complexity
            score = min(current_features["topological_complexity"] / 10.0, 1.0)
        else:
            # Compare to reference
            complexity_diff = abs(
                current_features["topological_complexity"] - 
                reference_features.get("topological_complexity", 0.0)
            )
            persistence_diff = abs(
                current_features["total_persistence"] - 
                reference_features.get("total_persistence", 0.0)
            )
            
            # Normalize differences
            max_complexity = max(
                current_features["topological_complexity"],
                reference_features.get("topological_complexity", 1.0)
            )
            max_persistence = max(
                current_features["total_persistence"],
                reference_features.get("total_persistence", 1.0)
            )
            
            complexity_score = complexity_diff / max(max_complexity, 1.0)
            persistence_score = persistence_diff / max(max_persistence, 1.0)
            
            score = 0.6 * complexity_score + 0.4 * persistence_score
            score = min(score, 1.0)
        
        return float(score)

