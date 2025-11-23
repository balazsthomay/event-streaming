import os

class PaymentProcessor:
    def __init__(self):
        # Hardcoded secret - severity 10
        self.api_key = "sk_live_4242424242424242"
    
    def process_payment(self, amount, card_number):
        # Command injection - severity 9
        os.system(f"charge_card {card_number} {amount}")
        return True
