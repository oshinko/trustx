class Profiles:
    def __init__(self, storage):
        self.storage = storage

    def __len__(self):
        return len(self.storage.profiles)
