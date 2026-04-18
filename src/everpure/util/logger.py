import sys
import logging
from pathlib import Path

class Logger:
    def __init__(self, name="FlashBlade"):
        self.logger = logging.getLogger(name)
        self.formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%d%b%Y %H:%M:%S")




