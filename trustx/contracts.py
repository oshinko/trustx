class Contract:
    pass


class Contracts:
    def __init__(self, storage):
        self.storage = storage

    def __len__(self):
        return len(self.storage.contracts)

    def __iter__(self):
        for k, v in self.storage.contracts.items():
            contract = Contract()
            contract.id = k
            contract.contractor = v[0]
            contract.contractee = v[1]
            yield contract
