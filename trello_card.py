"""This section ensure the program id creation in the program.lock
file which will be used by all modules thorughout the program"""
import random

from config_manager import ConfigManager

config = ConfigManager()

directory, file_name, file_path = config.read_lock_file()

with open(file_path, "w") as fp:
    value = random.getrandbits(40)
    fp.write(str(value))


import os
from datetime import datetime
from api.trello_api import TrelloAPI
from trellocardio.file_manager import FileManager
from trellocard_logger import TrelloCardLogger


logger = TrelloCardLogger.get_logger()


class TrelloCardSyncProgram(object):

    def perform_prerequisites(self):
        logger.log_info("Reading API credentials")

        self.api_key = self.config.read_api_key()
        self.api_token = self.config.read_api_token()

        if any([not self.api_key, not self.api_token]):
            logger.log_warning("API Key and Token must be present. Aborting...")
            exit()

        logger.log_info("API Credentials read done")

        logger.log_info("Reading board ID to sync")

        self.board_id_to_sync = self.config.read_board_id_to_sync()

        if not self.board_id_to_sync:
            logger.log_warning("Board ID to Sync must be present. Aborting ...")
            exit()

        logger.log_info("Read done for board ID to sync")

        if not self.board_id_to_sync:
            logger.log_info("Board ID to Sync must be present in config.json. Aborting now...")
            exit()

        logger.log_info("Reading card mapping file path")
        self.card_mapping_file_path = self.config.read_card_mapping_file_path()
        if not self.card_mapping_file_path or not os.path.exists(self.card_mapping_file_path):
            logger.log_warning("card mapping file either not found or invalid. %s" % self.card_mapping_file_path)

        logger.log_info("card mapping file path found: %s" % self.card_mapping_file_path)

        logger.log_info("Checking if card mapping file is writable or not")
        if not os.access(self.card_mapping_file_path, os.W_OK):
            logger.log_info("%s is not writable" % self.card_mapping_file_path)
        else:
            logger.log_info("Found %s writable" % self.card_mapping_file_path)

        logger.log_info("Reading client board id mapping file path")

        self.client_board_mapping_file_path = self.config.read_client_board_mapping_file_path()

        if not self.client_board_mapping_file_path or not os.path.exists(self.client_board_mapping_file_path):
            logger.log_warning(
                "client mapping file either not found or invalid. %s" % self.client_board_mapping_file_path)

        logger.log_info("client board id mapping file found: %s" % self.client_board_mapping_file_path)

        logger.log_info("Reading client board mapping")
        self.client_board_mapping = FileManager.read_client_board_mapping(self.client_board_mapping_file_path)
        logger.log_info("Read done client board mapping")

        logger.log_info(
            "*********************************** start content: client board mapping ************************************")
        logger.log_info(str(self.client_board_mapping))
        logger.log_info(
            "*********************************** end content: client board mapping ************************************")

    def read_cards_for_board_sync(self):
        logger.log_info("Creating API instance")
        self.api = TrelloAPI(api_key=self.api_key, api_token=self.api_token)
        logger.log_info("API instance created")

        logger.log_info("Reading all cards in the board id to sync: %s" % self.board_id_to_sync)
        self.cards = self.api.call_api("read_cards_in_board", board_id=self.board_id_to_sync)

        if not self.cards:
            logger.log_warning("No associated cards found with the board id: %s. Aborting..." % self.board_id_to_sync)
            exit()
        else:
            logger.log_info("%s cards found in board: %s" % (len(self.cards), self.board_id_to_sync))
            logger.log_info(
                "*********************** Content start: CARDS in Board: %s *********************** " % self.board_id_to_sync)
            logger.log_info(str(self.cards))
            logger.log_info(
                "*********************** Content End: CARDS in Board: %s *********************** " % self.board_id_to_sync)

    def perform_sync(self):
        for card_id in self.cards:
            client_name = self.api.call_api("get_card_client_name", board_id=self.board_id_to_sync, card_id=card_id)

    def start_sync(self):
        self.perform_prerequisites()
        self.read_cards_for_board_sync()
        self.perform_sync()

    def __enter__(self):
        self.config = ConfigManager()

        lock_dir, lock_fname, lock_fpath = self.config.read_lock_file()
        program_id = FileManager.read_program_id(lock_fpath)

        now_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.0")

        logger.log_info("Starting TrelloCard Sync program at %s" % now_dt)

        logger.log_info("======================= Start Program - %s =======================" % program_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        lock_dir, lock_fname, lock_fpath = self.config.read_lock_file()
        program_id = FileManager.read_program_id(lock_fpath)

        logger.log_info("======================= End Program - %s =======================" % program_id)

        now_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.0")

        logger.log_info("Ending TrelloCard Sync program at %s" % now_dt)

        FileManager.delete_file(lock_fpath)

if __name__ == "__main__":
    trellocard_sync_instance = TrelloCardSyncProgram()
    with trellocard_sync_instance:
        trellocard_sync_instance.start_sync()
