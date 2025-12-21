"""
TopoGuard FastAPI Application
REST API for real-time fraud detection.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uvicorn
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topoguard.core.detector import TopoGuard
from topoguard.core.graph_builder import Transaction

app = FastAPI(
    title="TopoGuard API",
    description="Topology-Inspired Anomaly Detection for FinTech Transactions",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = TopoGuard()


class TransactionRequest(BaseModel):
    """Transaction request model."""
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    timestamp: str
    metadata: Optional[dict] = None


class DetectionResponse(BaseModel):
    """Detection response model."""
    transaction_id: str
    anomaly_score: float
    is_fraudulent: bool
    reason: str
    graph_features: dict
    topological_features: dict
    topology_score: float
    structure_score: float


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TopoGuard",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_anomaly(request: TransactionRequest):
    """
    Detect anomaly in a single transaction.
    
    Args:
        request: Transaction data
        
    Returns:
        Detection results
    """
    try:
        # Parse timestamp
        tx_timestamp = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
        
        # Create transaction object
        transaction = Transaction(
            transaction_id=request.transaction_id,
            from_account=request.from_account,
            to_account=request.to_account,
            amount=request.amount,
            timestamp=tx_timestamp,
            metadata=request.metadata
        )
        
        # Detect anomaly
        result = detector.detect(transaction)
        
        return DetectionResponse(
            transaction_id=request.transaction_id,
            **result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/detect/batch")
async def detect_batch(transactions: List[TransactionRequest]):
    """
    Detect anomalies in a batch of transactions.
    
    Args:
        transactions: List of transaction data
        
    Returns:
        List of detection results
    """
    try:
        tx_objects = []
        for req in transactions:
            tx_timestamp = datetime.fromisoformat(req.timestamp.replace('Z', '+00:00'))
            tx_objects.append(Transaction(
                transaction_id=req.transaction_id,
                from_account=req.from_account,
                to_account=req.to_account,
                amount=req.amount,
                timestamp=tx_timestamp,
                metadata=req.metadata
            ))
        
        results = detector.detect_batch(tx_objects)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get current system statistics."""
    graph = detector.graph_builder.build_graph()
    graph_features = detector.graph_builder.get_graph_features(graph)
    
    return {
        "num_transactions": len(detector.graph_builder.transactions),
        "num_accounts": graph_features.get("num_nodes", 0),
        "num_edges": graph_features.get("num_edges", 0),
        "graph_density": graph_features.get("density", 0.0),
        "has_reference": detector.reference_features is not None,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

