import os
import logging
from datetime import datetime
from config_manager import ConfigManager


class TrelloCardLogger(object):

    def __init__(self, log_file, log_file2=None):
        self.logger = logging.getLogger('program')

        self.logger.setLevel(logging.DEBUG)

        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

        file_handler = logging.FileHandler("{0}.log".format(log_file))
        file_handler.setFormatter(log_formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

        if log_file2:
            self.logger_pretty = logging.getLogger('pretty')

            self.logger_pretty.setLevel(logging.DEBUG)

            log_formatter2 = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

            file_handler2 = logging.FileHandler("{0}.log".format(log_file2))
            file_handler2.setFormatter(log_formatter2)
            stream_handler2 = logging.StreamHandler()
            stream_handler2.setFormatter(log_formatter2)
            if not self.logger_pretty.handlers:
                self.logger_pretty.addHandler(file_handler2)
                self.logger_pretty.addHandler(stream_handler2)

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

        log_file2_name = log_file_name + '_pretty'

        log_file_path = os.path.join(log_file_directory, log_file_name)

        log_file2_path = os.path.join(log_file_directory, log_file2_name)

        return cls(log_file=log_file_path, log_file2=log_file2_path)

    def log_info(self, message, pretty=False):
        if not pretty:
            self.logger.info(message)
        else:
            self.logger_pretty.info(message)

    def log_debug(self, message, pretty=False):
        if not pretty:
            self.logger.debug(message)
        else:
            self.logger_pretty.debug(message)

    def log_warning(self, message, pretty=False):
        if not pretty:
            self.logger.warning(message)
        else:
            self.logger_pretty.warning(message)

    def log_db(self, db_instance, log_table, data):
        pass


if __name__ == "__main__":
    logger = TrelloCardLogger.get_logger()
    logger.log_info("Hello!")
    logger.log_info("Hello Pretty!", pretty=True)
