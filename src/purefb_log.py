import os
import sys
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
    
    def set_logfile(self, logfile, no_date=False):
        if no_date:
            self.logfile = f"{logfile}.log"
        else:
            self.logfile = f"{logfile}-{datetime.now().strftime('%d%b%Y')}.log"

    def set_logdir(self, logdir):
        self.logdir = f"logs/{logdir}"

    def get_logfile_path(self):
        return f"{self.logdir}/{self.logfile}"
    
    def get_logdir_path(self):
        return self.logdir

    def write_log(self, message, jsondata=None, show_output=False, end_print="\n\n"):
        os.makedirs(self.logdir, exist_ok=True)
        todays_log = os.path.join(self.logdir, self.logfile)
        stamp = self.timestamp()

        with open(todays_log, 'a') as log:
            log.write(f"[{stamp}] {message}\n")

        if show_output:
            print(message, end=end_print)

        if jsondata:
            with open(todays_log, 'a') as log:
                json.dump(jsondata, log, indent=4)
                log.write("\n")
            if show_output:
                print(json.dumps(jsondata, indent=4))
                print()

    # Dump a json config into logs/configs/<name>.json
    def dump_config(self, json_input, filename):
        os.makedirs("logs/pure_configs", exist_ok=True)
        with open(f"logs/pure_configs/{filename}.json", "w") as cfg:
            json.dump(json_input, cfg, indent=4)

class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.todays_log = PureLog()

    def set_log(self, logger_instance):
        self.todays_log = logger_instance

    def start_stopwatch(self, show_start_time=True):
        self.start_time = time.time()
        if show_start_time:
            formatted = time.strftime("%H:%M:%S", time.localtime(self.start_time))
            self.todays_log.write_log(f"Stopwatch started: {formatted}", show_output=True)
        
    def end_stopwatch(self, showtime=True):
        self.end_time = time.time()
        if showtime:
            self.show_time_elapsed()

    def get_time_elapsed(self, time_string=False, dictionary=False):
        if not self.start_time or not self.end_time:
            return 0
        
        elapsed_time_dict = {
            "hours": int((self.end_time - self.start_time) // 3600),
            "minutes": int(((self.end_time - self.start_time) % 3600) // 60),
            "seconds": round((self.end_time - self.start_time) % 60, 2)
        }

        time_elapsed_string = "Time elapsed: "
        
        if time_string:
            if elapsed_time_dict.get("hours") > 0:
                time_elapsed_string += f"{elapsed_time_dict.get('hours')} hours, "
            
            if elapsed_time_dict.get("minutes"):
                time_elapsed_string += f"{elapsed_time_dict.get('minutes')} minutes, "
            
            time_elapsed_string += f"{elapsed_time_dict.get('seconds')} seconds"
            return time_elapsed_string
        elif dictionary:
            return elapsed_time_dict
        else:
            return self.end_time - self.start_time
        
    def countdown(self, seconds):
        for i in range(seconds, -1, -1):
            sys.stdout.write(f"\rCountdown: {i:02d}")
            sys.stdout.flush()
            time.sleep(1)
        print("\nTime Elapsed. Continuing...")
        print()
        
    def show_time_elapsed(self, show_output=True):
        time_elapsed = self.get_time_elapsed(dictionary=True)
        time_string = "Time elapsed: "
        
        if time_elapsed.get("hours") > 0:
            time_string += f"{time_elapsed.get('hours')} hours, "
        
        if time_elapsed.get("minutes"):
            time_string += f"{time_elapsed.get('minutes')} minutes, "
        
        time_string += f"{time_elapsed.get('seconds')} seconds"
        self.todays_log.write_log(time_string, show_output=show_output)




