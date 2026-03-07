import os

class EnvironmentVariables:
    def __init__(self, *args):
        self.set_attrs(args)

    def set_attrs(self, args: tuple):
        for arg in args:    
            setattr(self, arg, os.getenv(arg))

    def get_vars(self, *args):
        vlist = []
        for arg in args:
            vlist.append(getattr(self, arg))
        return vlist