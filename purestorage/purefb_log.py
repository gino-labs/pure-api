import os
import json
from datetime import datetime

now = datetime.now()

day = now.strftime("%d").lstrip("0")
formatted = f"{now.strftime('%b')}{day}_{now.strftime('%H_%M')}"

print(formatted)
