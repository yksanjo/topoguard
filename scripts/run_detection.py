"""
Run detection on transaction data.
"""

import json
import argparse
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topoguard.core.detector import TopoGuard
from topoguard.core.graph_builder import Transaction


def main():
    parser = argparse.ArgumentParser(description="Run TopoGuard detection")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    parser.add_argument("--output", type=str, help="Output JSON file (optional)")
    
    args = parser.parse_args()
    
    # Load transactions
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    # Initialize detector
    detector = TopoGuard()
    
    # Process transactions
    results = []
    fraud_count = 0
    
    for tx_data in data:
        tx = Transaction(
            transaction_id=tx_data["transaction_id"],
            from_account=tx_data["from_account"],
            to_account=tx_data["to_account"],
            amount=tx_data["amount"],
            timestamp=datetime.fromisoformat(tx_data["timestamp"]),
            metadata=tx_data.get("metadata")
        )
        
        result = detector.detect(tx)
        result["transaction_id"] = tx.transaction_id
        results.append(result)
        
        if result["is_fraudulent"]:
            fraud_count += 1
            print(f"🚨 FRAUD DETECTED: {tx.transaction_id} (score: {result['anomaly_score']:.3f})")
            print(f"   Reason: {result['reason']}")
    
    print(f"\n📊 Summary:")
    print(f"   Total transactions: {len(results)}")
    print(f"   Fraudulent: {fraud_count} ({fraud_count/len(results)*100:.1f}%)")
    print(f"   Average anomaly score: {sum(r['anomaly_score'] for r in results)/len(results):.3f}")
    
    # Save results if output specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to {args.output}")


if __name__ == "__main__":
    main()

