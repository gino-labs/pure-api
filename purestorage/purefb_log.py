import os
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
        
