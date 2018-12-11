"""This section ensure the program id creation in the program.lock
file which will be used by all modules thorughout the program"""
import random

from config_manager import ConfigManager
from entities.trellocard import TrelloCard

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
            logger.log_info("%s is not writable. Aborting..." % self.card_mapping_file_path)
            exit()
        else:
            logger.log_info("Found %s writable" % self.card_mapping_file_path)

        logger.log_info("Reading client board id mapping file path")

        self.client_board_mapping_file_path = self.config.read_client_board_mapping_file_path()

        if not self.client_board_mapping_file_path or not os.path.exists(self.client_board_mapping_file_path):
            logger.log_warning(
                "client mapping file either not found or invalid. %s" % self.client_board_mapping_file_path)
            logger.log_warning("Aborting...")
            exit()

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
        try:
            self.cards = self.api.call_api("read_cards_in_board", board_id=self.board_id_to_sync)
        except Exception as exp:
            logger.log_warning("cards read failed. Exception: %s" % (str(exp)))
            self.cards = None

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

    def sync_new_card(self, card_id, card_list_id, destination_board_id, card_name,
                      card_due_date, card_description, card_attachments, client_name,
                      card_quote, card_owner):
        card_list_name = self.api.call_api("read_card_list_name_formatted", card_list_id=card_list_id)
        destination_list_id = self.api.call_api("read_list_id", board_id=destination_board_id, name=card_list_name)

        # Create card with name, due date, description and get id of the newly created card
        logger.log_info("Creating a new card in destination board")
        destination_card_id = self.api.call_api("create_card", list_id=destination_list_id,
                                                name=card_name,
                                                due_date=card_due_date,
                                                description=card_description)
        if not destination_card_id:
            logger.log_warning("destination card could not be created")
            return
        logger.log_info("destination card created with id: %s" % destination_card_id)

        logger.log_info("Saving card mapping in local file")
        saved = FileManager.save_card_mapping(self.card_mapping_file_path, card_id, destination_card_id, client_name)
        if not saved:
            logger.log_warning("Saving card mapping failed")

        logger.log_info("Adding card attachments")

        self.api.call_api("add_card_attachments", card_id=destination_card_id, card_attachments=card_attachments)
        logger.log_info("Card attachments added in destination card")

        logger.log_info("Updating Card quote")
        if card_quote:
            updated = self.api.call_api("update_card_quote", board_id=destination_board_id,
                                        card_id=destination_card_id, quote_value=card_quote)
            if updated:
                logger.log_info("Card quote updated successfully")
            else:
                logger.log_info("Card quote update failed")
        else:
            logger.log_warning("Card quote not found")

        logger.log_info("Updating card owner")
        if card_owner:
            updated = self.api.call_api("update_card_owner", board_id=destination_board_id,
                                        card_id=destination_card_id, owner=card_owner)
            if updated:
                logger.log_info("Card owner updated successfully")
            else:
                logger.log_info("Card owner update failed")
        else:
            logger.log_warning("Card owner not found")

        logger.log_info("Card Created - " + client_name + " - Id " + destination_card_id)

    def perform_sync(self):
        for card_id in self.cards:
            try:
                client_name = self.api.call_api("read_card_client_name", board_id=self.board_id_to_sync, card_id=card_id)
                logger.log_info("Card ID: %s and Client Name: %s" % (card_id, client_name))

                if client_name and client_name in self.client_board_mapping:
                    destination_board_id = self.client_board_mapping[client_name]
                    # Get card information

                    # TrelloCard
                    logger.log_info("Reading trello card: %s" % card_id)
                    trellocard_entity = self.api.call_api("read_trello_card", card_id=card_id)

                    card_list_id = trellocard_entity.card_list_id
                    card_name = trellocard_entity.card_name
                    card_due_date = trellocard_entity.card_due_date
                    card_description = trellocard_entity.card_description
                    card_attachments = trellocard_entity.card_attachments

                    card_quote, card_owner = self.api.call_api("read_card_custom_fields",
                                                               board_id=self.board_id_to_sync,
                                                               card_id=card_id)
                    # Get the corresponding destination card id in file
                    destination_card_id = FileManager.read_corresponding_destination_card_id(self.card_mapping_file_path, card_id)

                    logger.log_info("card_list_id=%s, card_name=%s, card_due_date=%s, card_description=%s, "
                                    "card_attachments=%s, card_quote=%s, card_owner=%s, destination_card_id=%s" %
                                    (card_list_id, card_name, card_due_date, card_description, str(card_attachments),
                                     card_quote, card_owner, destination_card_id))

                    if not destination_card_id:
                        logger.log_info("No corresponding destination card id for card id: '%s', "
                                        "the card has never been synced, we need to create it." % card_id)

                        self.sync_new_card(card_id, card_list_id, destination_board_id, card_name,
                          card_due_date, card_description, card_attachments, client_name,
                          card_quote, card_owner)

                        logger.log_info("New card added to the destination board")
                    else:
                        # Check if the client name is the same as the last time it was synced
                        destination_client_name = FileManager.read_corresponding_destination_client_name(card_id)
                        # If names are identical then update the card
                        if client_name == destination_client_name:
                            logger.log_info("Card synced before with the same name. Updating now...")
                            # Update name, due date and description
                            updated = self.api.call_api("update_card", card_id=destination_card_id,
                                                        name=card_name,
                                                        due_date=card_due_date,
                                                        description=card_description)
                            if updated:
                                logger.log_info("Card updated with name, due date and description")
                            else:
                                logger.log_info("Card update failed with name, due date and description")

                            logger.log_info("Deleting card attachments")
                            self.api.call_api("delete_card_attachments", card_id=destination_card_id)
                            logger.log_info("Existing attachments deleted. Now adding new attachments")

                            self.api.call_api("add_card_attachments", card_id=destination_card_id, card_attachments=card_attachments)
                            logger.log_info("New attachments updated")

                            logger.log_info("Updating quote")
                            updated = self.api.call_api("update_card_quote", board_id=destination_board_id,
                                                        card_id=destination_card_id, quote_value=card_quote)
                            if updated:
                                logger.log_info("Card quote updated")
                            else:
                                logger.log_info("Card quote update failed")

                            logger.log_info("Updating card owner")
                            updated = self.api.call_api("update_card_owner", board_id=destination_board_id,
                                                        card_id=destination_card_id, owner=card_owner)
                            if updated:
                                logger.log_info("Card owner updated")
                            else:
                                logger.log_info("Card owner update failed")

                            logger.log_info("Checking whether the card list has been changed or not")
                            origin_list_name = self.api.call_api("read_card_list_name_formatted", card_list_id=card_list_id)
                            trellocard_ = self.api.call_api("read_trello_card", card_id=destination_card_id, basic_info_only=True)

                            destination_list_name = self.api.call_api("read_card_list_name_formatted",
                                                                      card_list_id=trellocard_.card_list_id)

                            logger.log_info("Checking if the card was moved to another list then move it")
                            if destination_list_name != origin_list_name:
                                logger.log_info("Card list was changed. Updating it")
                                destination_list_id = self.api.call_api("read_list_id",
                                                                        board_id=destination_board_id,
                                                                        name=origin_list_name)
                                if destination_list_id:
                                    updated = self.api.call_api("move_card", card_id=destination_card_id,
                                                                list_id=destination_list_id)
                                    if updated:
                                        logger.log_info("Destination list updated")
                                    else:
                                        logger.log_warning("Destination list not updated")
                                else:
                                    logger.log_warning("Destination list not updated")

                            logger.log_info("Card Updated - " + client_name + " - Id " + destination_card_id)
                        else:
                            logger.log_info("Names don't match. Now delete the previously synced card that "
                                            "is incorrect and create a new one in the correct board")
                            logger.log_info("Deleting previously synced card")
                            deleted = self.api.call_api("delete_card", card_id=destination_card_id)
                            if deleted:
                                logger.log_info("Card deleted")
                            else:
                                logger.log_warning("Card was not deleted. Aborting")
                                continue

                            logger.log_info("Remove mapping source card id <-> destination card id in file")
                            FileManager.remove_card_id_mapping(self.card_mapping_file_path, destination_card_id)

                            logger.log_info("Card deleted. Now recreating it")

                            self.sync_new_card(card_id, card_list_id, destination_board_id, card_name,
                                               card_due_date, card_description, card_attachments, client_name,
                                               card_quote, card_owner)

                            logger.log_info("Card Deleted and Recreated - " + client_name + " - Id " + destination_card_id)
                else:
                    if not client_name:
                        logger.log_warning("Client name not found for card id: %s" % card_id)
                    else:
                        logger.log_warning("Client name not in client board mapping")
            except Exception as exp:
                logger.log_warning("Exception for card: %s: %s" % (card_id, str(exp)))

    def perform_post_cleanup(self):
        logger.log_info("Performing post cleanup")
        logger.log_info("List all source cards in mapping file")
        source_card_list_from_mapping_file = FileManager.read_mapping_source_card_list(self.card_mapping_file_path)

        logger.log_info("List cards in source board")
        source_card_list = self.api.call_api("read_cards_in_board", board_id=self.board_id_to_sync)

        # For each source card in mapping file
        for source_card in source_card_list_from_mapping_file:
            # If it's not in the source board
            if source_card not in source_card_list:
                try:
                    # Delete the corresponding card
                    corresponding_destination_card_id = FileManager.read_corresponding_destination_card_id(self.card_mapping_file_path,
                                                                                                           source_card)
                    self.api.call_api("delete_card", card_id=corresponding_destination_card_id)

                    # Remove mapping source card id <-> destination card id in file
                    FileManager.remove_card_id_mapping(self.card_mapping_file_path, source_card)

                    logger.log_info("Card Deleted from destination " + destination_card_id)
                except Exception as exp:
                    logger.log_warning("Exception in post cleanup. %s" % str(exp))

    def start_sync(self):
        self.perform_prerequisites()
        self.read_cards_for_board_sync()
        self.perform_sync()
        self.perform_post_cleanup()

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
