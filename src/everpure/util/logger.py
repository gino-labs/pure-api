import logging

class PureLogger:
    def __init__(self, name, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.level = level
        self.formatter = logging.Formatter(
            style="{", 
            datefmt="%H:%M:%S", 
            fmt="[{asctime}] {name}: {message}"
        )
        
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(self.formatter)
        self.logger.addHandler(ch)

    def set_logfile(self, logfile):
        fh = logging.FileHandler(logfile)
        fh.setLevel(self.level)
        fh.setFormatter(self.formatter)
        self.logger.addHandler(fh)

    def log(self, msg):
        self.logger.info(msg)
