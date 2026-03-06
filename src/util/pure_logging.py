import sys
import time
import logging
from pathlib import Path

class PureLogger:
    def __init__(self, name="FlashBlade"):
        self.logger = logging.getLogger(name)
        self.formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%d%b%Y %H:%M:%S")
 
    def setup_logging(self, logpath: str, console=True, level="DEBUG"):
        if isinstance(level, str) and (level not in logging._nameToLevel):
            sys.exit(f"Failed to set up logging, level {level} is invalid")
        elif isinstance(level, int) and (level not in logging._levelToName):
            sys.exit(f"Failed to set up logging, level {level} is invalid")
        elif Path(logpath).is_dir():
            sys.exit(f"Log path should be a file not a directory: {logpath}")
        elif not Path(logpath).parent.exists():
            sys.exit(f"Log path does not exist: {Path(logpath).parent}")
            
        if self.logger.handlers:
            return self.logger
        
        if isinstance(level, str):
            level = logging._nameToLevel[level]

        self.logger.setLevel(level)
        self.logger.propagate = False
        
        fh = logging.FileHandler(logpath)
        fh.setLevel(level)
        fh.setFormatter(self.formatter)
        self.logger.addHandler(fh)

        if console:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(level)
            ch.setFormatter(self.formatter)
            self.logger.addHandler(ch)

    def toggle_console(self, enabled: bool):
        for h in self.logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.setLevel(logging.INFO if enabled else logging.CRITICAL + 1)


class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start_stopwatch(self):
        self.start_time = time.time()
        
    def end_stopwatch(self):
        self.end_time = time.time()

    def get_time_elapsed(self, formatted=True):
        if not self.start_time or not self.end_time:
            return 0
        elif formatted:
            hrs = int(self.end_time - self.start_time // 3600)
            mins = int(self.end_time - self.start_time % 3600 // 60)
            secs = round(self.end_time - self.start_time % 60, 2)
            return f"{hrs} hours, {mins} minutes, {secs} seconds"
        else:
            return int(self.end_time - self.start_time)
        
    def countdown(self, seconds: int):
        for i in range(seconds, -1, -1):
            sys.stdout.write(f"\rCountdown: {i:02d}")
            sys.stdout.flush()
            time.sleep(1)

    def pause(self):
        return input("Press enter to continue...")

    def show_time_elapsed(self):
        hrs = int(self.end_time - self.start_time // 3600)
        mins = int(self.end_time - self.start_time % 3600 // 60)
        secs = round(self.end_time - self.start_time % 60, 2)
        print(f"Time Elapsed: {hrs} hours, {mins} minutes, {secs} seconds")




