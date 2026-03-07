import os

class EnvironmentReader:
    def __init__(self, *args):
        self.var_names = {}
        self.set_attrs(args)

    def set_attrs(self, args: tuple):
        for arg in args:
            arg = str(arg)
            self.var_names[arg] = arg.lower()
            setattr(self, arg.lower(), os.getenv(arg))

    def get_var(self, var: str):
        var = var.upper()
        return self.var_names[var]

    def get_vars(self, *args):
        vlist = []
        for arg in args:
            vlist.append(getattr(self, arg))
        return vlist