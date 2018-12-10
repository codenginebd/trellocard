import os
import logging
from datetime import datetime
from config_manager import ConfigManager


class TrelloCardLogger(object):

    def __init__(self, log_file):
        self.logger = logging.getLogger()

        self.logger.setLevel(logging.DEBUG)

        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

        file_handler = logging.FileHandler("{0}.log".format(log_file))
        file_handler.setFormatter(log_formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

    @classmethod
    def get_logger(cls):
        config = ConfigManager()
        lock_dir, lock_file_name, lock_file_path = config.read_lock_file()

        program_id = ""
        with open(lock_file_path, "r") as f:
            program_id = f.read()

        log_file_directory = config.read_log_file_directory()

        if not os.path.exists(log_file_directory):
            os.makedirs(log_file_directory)

        now_date = datetime.utcnow().strftime('%d_%m_%Y')

        log_file_name = now_date + "_" + program_id

        log_file_path = os.path.join(log_file_directory, log_file_name)

        return cls(log_file=log_file_path)

    def log_info(self, message):
        self.logger.info(message)

    def log_debug(self, message):
        self.logger.debug(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_db(self, db_instance, log_table, data):
        pass
