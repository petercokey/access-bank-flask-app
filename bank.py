# bank.py
from datetime import datetime

class UserDashboard:
    def __init__(self, account_number, balance=0):
        self.account_number = account_number
        self.balance = balance
        self.transactions = []  # list of dicts
        self.inflow = 0
        self.outflow = 0

    def deposit(self, amount, title="Deposit"):
        self.balance += amount
        self.inflow += amount
        self.transactions.append({
            "title": title,
            "amount": amount,
            "type": "inflow",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def transfer(self, amount, title="Transfer"):
        if amount <= self.balance:
            self.balance -= amount
            self.outflow += amount
            self.transactions.append({
                "title": title,
                "amount": amount,
                "type": "outflow",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return True
        return False

    def get_transaction_history(self, limit=5):
        return self.transactions[-limit:]


my_account = UserDashboard("0076482936", 5000 )

class Rewards:
    def __init__(self, points=0, rate=10):
        self.points = points
        self.rate = rate

    def add_transfer_reward(self, amount):
        """Add rewards if transfer >= 100,000"""
        if amount >= 100000:
            earned = int((amount * self.rate) / 100)   # 10% of amount
            self.points += earned
            return earned
        return 0

    
my_reward = Rewards(50000, 20)