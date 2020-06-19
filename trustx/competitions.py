class Competition:
    def __str__(self):
        return self.name


class Competitions:
    def __init__(self, storage):
        self.storage = storage

    def __len__(self):
        return len(self.storage.competitions)

    def __iter__(self):
        for k, v in self.storage.competitions.items():
            competition = Competition()
            competition.id = k
            competition.name = v[0]
            competition.active = v[1]
            yield competition
