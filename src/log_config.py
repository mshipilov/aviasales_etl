import logging
import os
import logging.handlers

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

root_logger = logging.getLogger() 
root_logger.setLevel(logging.DEBUG)  # Set lowest level at root

if not root_logger.handlers:
    formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "app.log"), 
        maxBytes=5*1024*1024, 
        backupCount=3,
        encoding='utf-8'  # for Russian text
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

