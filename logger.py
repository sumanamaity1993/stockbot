import logging
import os
from datetime import datetime

def get_logger(name=__name__, log_to_file=True, log_to_console=True, log_level="INFO"):
    os.makedirs("logs", exist_ok=True)
    handlers = []
    if log_to_file:
        file_handler = logging.FileHandler(f'logs/sip_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handlers.append(file_handler)
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handlers.append(console_handler)
    logging.basicConfig(level=getattr(logging, log_level), handlers=handlers)
    return logging.getLogger(name) 