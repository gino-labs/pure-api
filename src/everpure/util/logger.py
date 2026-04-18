import logging
from pathlib import Path

class PureLogger:
    def __init__(self, name, log_path, console=True, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.level = level
        self.logger.setLevel(self.level)
        self.formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%d%b%Y %H:%M:%S")
        
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(self.level)
            ch.setFormatter(self.formatter)
            self.logger.addHandler(ch)

    def set_logfile(self, log_path):
        lp = Path(log_path).resolve()
        exists = False
        for h in self.logger.handlers:
            if isinstance(h, logging.FileHandler) and h.baseFilename == lp:
                exists == True
                break
        if not exists:
            fh = logging.FileHandler(log_path)
            fh.setLevel(self.level)
            fh.setFormatter(self.formatter)
            self.logger.addHandler(fh)




