"""
Generate sample transaction data for testing.
"""

import json
import argparse
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()


def generate_transactions(num_transactions: int, 
                         num_accounts: int = 50,
                         fraud_rate: float = 0.05) -> list:
    """
    Generate synthetic transaction data.
    
    Args:
        num_transactions: Number of transactions to generate
        num_accounts: Number of unique accounts
        fraud_rate: Percentage of fraudulent transactions
        
    Returns:
        List of transaction dictionaries
    """
    accounts = [f"acc_{i:03d}" for i in range(num_accounts)]
    transactions = []
    
    base_time = datetime.now()
    
    for i in range(num_transactions):
        # Normal transactions: small amounts, distributed accounts
        if random.random() > fraud_rate:
            amount = random.uniform(10, 1000)
            from_acc = random.choice(accounts)
            to_acc = random.choice([a for a in accounts if a != from_acc])
        else:
            # Fraudulent: large amounts, concentrated accounts
            amount = random.uniform(5000, 50000)
            # Create hub account for fraud
            hub_account = random.choice(accounts)
            if random.random() > 0.5:
                from_acc = hub_account
                to_acc = random.choice([a for a in accounts if a != hub_account])
            else:
                from_acc = random.choice([a for a in accounts if a != hub_account])
                to_acc = hub_account
        
        timestamp = base_time - timedelta(
            hours=random.uniform(0, 24),
            minutes=random.uniform(0, 60)
        )
        
        transactions.append({
            "transaction_id": f"tx_{i:06d}",
            "from_account": from_acc,
            "to_account": to_acc,
            "amount": round(amount, 2),
            "timestamp": timestamp.isoformat(),
            "metadata": {
                "type": "transfer",
                "currency": "USD"
            }
        })
    
    return transactions


def main():
    parser = argparse.ArgumentParser(description="Generate sample transaction data")
    parser.add_argument("--transactions", type=int, default=10000, help="Number of transactions")
    parser.add_argument("--accounts", type=int, default=50, help="Number of accounts")
    parser.add_argument("--fraud-rate", type=float, default=0.05, help="Fraud rate (0-1)")
    parser.add_argument("--output", type=str, default="data/sample_transactions.json", help="Output file")
    
    args = parser.parse_args()
    
    transactions = generate_transactions(
        args.transactions,
        args.accounts,
        args.fraud_rate
    )
    
    # Create output directory if needed
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, 'w') as f:
        json.dump(transactions, f, indent=2)
    
    print(f"Generated {len(transactions)} transactions to {args.output}")


if __name__ == "__main__":
    main()

