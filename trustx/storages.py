class LocalStorage:
    data = dict(profiles={i: 'contents' for i in range(256)},
                competitions={i: (f'competition {i + 1}', int(i % 2 == 0))
                              for i in range(256)},
                contracts={i: (i, i + 1) for i in range(255)},
                payments={i: 'contents' for i in range(4)})

    def __getattr__(self, name):
        return self.data[name]
