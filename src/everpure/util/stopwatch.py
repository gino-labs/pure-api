import time

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
