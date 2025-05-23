import logging
import time
import os

# File management
file_path: str = os.path.join("logs", f"{int(time.time())}.log")
os.makedirs("logs", exist_ok=True)

# Config logging
logger = logging.getLogger(__name__)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)

# Log File
file_handler = logging.FileHandler(file_path, mode='w', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)