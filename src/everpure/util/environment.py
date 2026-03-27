import os

class EnvironmentReader:
    def __init__(self, name: str, mgt: str, token: str, *args):
        self.name = os.environ[name]
        self.mgt = os.environ[mgt]
        self.token = os.environ[token]
        self.vars = [self.name, self.mgt, self.token]
        if args:
            for arg in args:
                setattr(self, arg.lower(), arg)

    def __iter__(self):
        return iter(self.vars)

