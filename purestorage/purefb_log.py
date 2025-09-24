import os
import time
import json
from datetime import datetime

class PureLog:
    def __init__(self):
        self.logfile = f"{datetime.now().strftime('%d%b%Y')}-pure-python.log"
        self.logdir = "logs"

    def timestamp(self):
        now = datetime.now()
        formatted_timestamp = f"{now.strftime('%d%b%Y-%H:%M:%S')}"
        return formatted_timestamp

    def write_log(self, message, jsondata=None, show_output=False):
        os.makedirs(self.logdir, exist_ok=True)
        todays_log = os.path.join(self.logdir, self.logfile)
        stamp = self.timestamp()

        with open(todays_log, 'a') as log:
            log.write(f"[{stamp}] {message}\n")

        if show_output:
            print(message)
            print()

        if jsondata:
            with open(todays_log, 'a') as log:
                json.dump(jsondata, log, indent=4)
                log.write("\n")
            if show_output:
                print(json.dumps(jsondata, indent=4))
                print()

class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.todays_log = PureLog()

    def start_stopwatch(self, show_start_time=True):
        self.start_time = time.time()
        if show_start_time:
            formatted = time.strftime("%H:%M:%S", time.localtime(self.start_time))
            self.todays_log.write_log(f"Stopwatch started: {formatted}", show_output=True)
        
    def end_stopwatch(self, showtime=True):
        self.end_time = time.time()
        if showtime:
            self.show_time_elapsed()

    def get_time_elapsed(self, dictionary=False):
        if not self.start_time or not self.end_time:
            return 0
        
        if dictionary:
            elapsed_time_dict = {
                "hours": int((self.end_time - self.start_time) // 3600),
                "minutes": int(((self.end_time - self.start_time) % 3600) // 60),
                "seconds": round((self.end_time - self.start_time) % 60, 2)
            }
            return elapsed_time_dict
        else:
            return self.end_time - self.start_time
        
    def show_time_elapsed(self):
        time_elapsed = self.get_time_elapsed(dictionary=True)
        time_string = "Time elapsed: "
        
        if time_elapsed.get("hours") > 0:
            time_string += f"{time_elapsed.get('hours')} hours, "
        
        if time_elapsed.get("minutes"):
            time_string += f"{time_elapsed.get('minutes')} minutes, "
        
        time_string += f"{time_elapsed.get('seconds')} seconds"
        self.todays_log.write_log(time_string, show_output=True)

class ApiError(Exception):
    def __init__(self, message, code=None, context=None,):
        self.code = code
        self.context = context
        self.message = message
        super()._init__(message)

