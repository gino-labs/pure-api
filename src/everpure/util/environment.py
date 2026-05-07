import os

class EnvironmentReader:
    def __init__(self, name: str, mgt: str, token: str, **kwargs):
        self.name = os.environ[name]
        self.mgt = os.environ[mgt]
        self.token = os.environ[token]
        self.vars = [self.name, self.mgt, self.token]
        if kwargs:
            for k, w in kwargs.items():
                setattr(self, k, w)

    def __iter__(self):
        return iter(self.vars)

