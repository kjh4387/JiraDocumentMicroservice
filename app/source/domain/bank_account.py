
class bank_account:
    def __init__(self, account_number: str, bank_name: str):
        self.account_number = account_number
        self.bank_name = bank_name

    def __str__(self):
        return self.bank_name + self.account_number