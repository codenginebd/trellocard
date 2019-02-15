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
            logger.log_warning("API Key and Token are missing. They must be present. Program Aborting...")
            exit()

        logger.log_info("API Credentials has been read")

        logger.log_info("Reading the board ID which need to sync")

        self.board_id_to_sync = self.config.read_board_id_to_sync()

        if not self.board_id_to_sync:
            logger.log_warning("No board ID found to sync. Please make sure board id is present in the config file. You need to set the board_id_to_sync parameter in config.json. Once you have set the board ID please run the program again. Program is Aborting now ...")
            exit()

        logger.log_info("The following board will be sync")
        logger.log_info("Board ID to sync: %s" % self.board_id_to_sync)

        logger.log_info("Reading the card mapping file path from config.json")
        self.card_mapping_file_path = self.config.read_card_mapping_file_path()
        if not self.card_mapping_file_path or not os.path.exists(self.card_mapping_file_path):
            if not self.card_mapping_file_path:
                logger.log_warning("card mapping file path not found in the config.json. You need to set files->card_mapping_file value for card mapping file path. Once you have set please continue running the program again. Program is Aborting now ...")
            if not os.path.exists(self.card_mapping_file_path):
                logger.log_warning("card mapping file path is not correct. You need to set a correct value in files->card_mapping_file value for card mapping file path. Once you have set please continue running the program again. Program is Aborting now ...")

            exit()

        logger.log_info("card mapping file path found: %s" % self.card_mapping_file_path)

        logger.log_info("Checking if card mapping file is writable or not")
        if not os.access(self.card_mapping_file_path, os.W_OK):
            logger.log_info("%s is not writable. Aborting..." % self.card_mapping_file_path)
            exit()
        else:
            #logger.log_info("Card mapp %s writable" % self.card_mapping_file_path)
            pass

        logger.log_info("Reading client board id mapping file path from config.json")

        self.client_board_mapping_file_path = self.config.read_client_board_mapping_file_path()

        if not self.client_board_mapping_file_path or not os.path.exists(self.client_board_mapping_file_path):
            logger.log_warning(
                "client mapping file either not found or invalid. %s" % self.client_board_mapping_file_path)
            logger.log_info("You need to set the client board mapping file path in config.json files->client_board_mapping section")
            logger.log_info("Once you have set the value in config.json please continue running the program again")
            logger.log_warning("Program is Aborting now...")
            exit()

        logger.log_info("client board id mapping file found: %s" % self.client_board_mapping_file_path)

        logger.log_info("Reading client board mapping data from client board id mapping file: %s" % self.client_board_mapping_file_path)
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
        logger.log_info("Reading all cards from the board %s to sync" % self.board_id_to_sync, pretty=True)
        try:
            self.cards = self.api.call_api("read_cards_in_board", board_id=self.board_id_to_sync)
        except Exception as exp:
            logger.log_warning("cards reading failed from the source board. Exception: %s" % (str(exp)))
            logger.log_warning("Cards reading failed from the source board: %s. Exception: %s" % (self.board_id_to_sync, str(exp)), pretty=True)
            self.cards = None

        if not self.cards:
            logger.log_warning("No associated cards found with the board id: %s. Aborting..." % self.board_id_to_sync)
            logger.log_info("Program is aborting now. Please make sure the internet connection is ok and you have correct rights or permissions to read the source board before trying next time", pretty=True)
            exit()
        else:
            logger.log_info("%s cards found in board: %s" % (len(self.cards), self.board_id_to_sync))
            logger.log_info(
                "*********************** Content start: CARDS in Board: %s *********************** " % self.board_id_to_sync)
            logger.log_info(str(self.cards))
            logger.log_info(
                "*********************** Content End: CARDS in Board: %s *********************** " % self.board_id_to_sync)

            logger.log_info("Card read done from the source board. Total %s cards found in the board: %s" % (len(self.cards), self.board_id_to_sync), pretty=True)
            logger.log_info("The following cards found in the source board: ", pretty=True)
            logger.log_info(str(self.cards), pretty=True)

    def sync_new_card(self, card_id, card_list_id, destination_board_id, card_name,
                      card_due_date, card_description, card_attachments, client_name,
                      card_quote, card_owner):
        
        logger.log_info("New Card sync has started for card: %s" % card_id, pretty=True)
        logger.log_info("Getting the card list name using card list id", pretty=True)
        card_list_name = self.api.call_api("read_card_list_name_formatted", card_list_id=card_list_id)

        logger.log_info("Card list name found: %s" % card_list_name, pretty=True)
        logger.log_info("Getting the destination list id using the card list name found where card will be synced to", pretty=True)

        destination_list_id = self.api.call_api("read_list_id", board_id=destination_board_id, name=card_list_name)

        if destination_list_id:
            logger.log_info("Destination list id found: %s" % destination_list_id, pretty=True)
        else:
            logger.log_info("Destination list id not found. Card sync not possible. Skipping...", pretty=True)
            logger.log_info("Please create the destination list: %s where card will be synced to before running the program again." % (card_list_name, ), pretty=True)
            return

        # Create card with name, due date, description and get id of the newly created card
        logger.log_info("Creating a new card in destination list")
        logger.log_info("Creating a new card in destination list: %s" % card_list_name, pretty=True)
        destination_card_id = self.api.call_api("create_card", list_id=destination_list_id,
                                                name=card_name,
                                                due_date=card_due_date,
                                                description=card_description)
        if not destination_card_id:
            logger.log_warning("destination card could not be created. Skipping")
            logger.log_info("Card sync failed in destination list: %s. Skipping..." % destination_list_id, pretty=True)
            return
        
        logger.log_info("destination card created with id: %s" % destination_card_id)
        logger.log_info("Card created successfully with destination board list: %s. New synced card ID: %s" % (destination_list_id, destination_card_id), pretty=True)

        logger.log_info("Saving card mapping in local file")
        logger.log_info("Updating card mapping file with this new created card id", pretty=True)

        saved = FileManager.save_card_mapping(self.card_mapping_file_path, card_id, destination_card_id, client_name)
        if not saved:
            logger.log_warning("Saving card mapping failed")
            logger.log_warning("Update in card mapping file with this new created card id failed", pretty=True)

        logger.log_info("Adding card attachments")
        logger.log_info("Now will update card attachments", pretty=True)

        self.api.call_api("add_card_attachments", card_id=destination_card_id, card_attachments=card_attachments)
        logger.log_info("Card attachments added in destination card")
        logger.log_info("Card attachments updated in the destination card", pretty=True)

        logger.log_info("Updating Card quote")
        logger.log_info("Updating Card quote in the destination card", pretty=True)
        if card_quote:
            updated = self.api.call_api("update_card_quote", board_id=destination_board_id,
                                        card_id=destination_card_id, quote_value=card_quote)
            if updated:
                logger.log_info("Card quote updated successfully")
                logger.log_info("Card quote updated successfully", pretty=True)
            else:
                logger.log_info("Card quote update failed")
                logger.log_info("Card quote update failed", pretty=True)
        else:
            if card_list_name != 'Received':
                logger.log_warning("Card quote not found")
                logger.log_warning("Card quote not found to update in the destination card", pretty=True)

        logger.log_info("Updating card owner")
        logger.log_info("Updating card owner in the destination card", pretty=True)
        if card_owner:
            updated = self.api.call_api("update_card_owner", board_id=destination_board_id,
                                        card_id=destination_card_id, owner=card_owner)
            if updated:
                logger.log_info("Card owner updated successfully")
                logger.log_info("Card owner updated successfully", pretty=True)
            else:
                logger.log_info("Card owner update failed")
                logger.log_info("Card owner update failed", pretty=True)
        else:
            if card_list_name not in ['Received', 'Loaded', 'Queued']:
                logger.log_warning("Card owner not found")
                logger.log_warning("Card owner not found to update in the destination card", pretty=True)

        logger.log_info("Card Created - " + client_name + " - Id " + destination_card_id)

        logger.log_info("Card sync done for client: %s from source list to destination list." % client_name, pretty=True)


    def perform_sync(self):

        logger.log_info("Card sync will start now", pretty=True)

        for card_id in self.cards:
            try:

                logger.log_info("Reading client name for card: %s" % card_id, pretty=True)

                client_name = self.api.call_api("read_card_client_name", board_id=self.board_id_to_sync, card_id=card_id)
                logger.log_info("Card ID: %s and Client Name: %s" % (card_id, client_name))

                if client_name and client_name in self.client_board_mapping:
                    destination_board_id = self.client_board_mapping[client_name]
                    # Get card information

                    logger.log_info("Client name reading done and client name found: %s" % client_name, pretty=True)
                    logger.log_info("Destination board found: %s for client name: %s" % (destination_board_id, client_name), pretty=True)

                    # TrelloCard
                    logger.log_info("Reading trello card: %s" % card_id)

                    logger.log_info("Reading card details for card: %s from trello using API." % card_id, pretty=True)

                    trellocard_entity = self.api.call_api("read_trello_card", card_id=card_id)

                    card_list_id = trellocard_entity.card_list_id
                    card_name = trellocard_entity.card_name
                    card_due_date = trellocard_entity.card_due_date
                    card_description = trellocard_entity.card_description
                    card_attachments = trellocard_entity.card_attachments

                    card_quote, card_owner = self.api.call_api("read_card_custom_fields",
                                                               board_id=self.board_id_to_sync,
                                                               card_id=card_id)

                    logger.log_info("The following details have been found for card: %s" % card_id, pretty=True)
                    logger.log_info("========================Card Details started===========================", pretty=True)
                    logger.log_info("Card List ID: %s" % card_list_id, pretty=True)
                    logger.log_info("Card Name: %s" % card_name, pretty=True)
                    logger.log_info("Card Due Date: %s" % card_due_date, pretty=True)
                    logger.log_info("Card Description: %s" % card_description, pretty=True)
                    logger.log_info("Card Attachments: %s" % str(card_attachments), pretty=True)
                    logger.log_info("Card Quote: %s" % card_quote, pretty=True)
                    logger.log_info("Card Owner: %s" % card_owner, pretty=True)
                    logger.log_info("========================Card Details ended===========================", pretty=True)

                    # Get the corresponding destination card id in file

                    logger.log_info("Reading corresponding destination card ID in card mapping file for the source card: %s" % card_id, pretty=True)

                    destination_card_id = FileManager.read_corresponding_destination_card_id(file_path=self.card_mapping_file_path,
                                                                                             card_id_to_find=card_id)

                    logger.log_info("Destination card id for card %s: %s" % (card_id, destination_card_id))

                    logger.log_info("card_list_id=%s, card_name=%s, card_due_date=%s, card_description=%s, "
                                    "card_attachments=%s, card_quote=%s, card_owner=%s, destination_card_id=%s" %
                                    (card_list_id, card_name, card_due_date, card_description, str(card_attachments),
                                     card_quote, card_owner, destination_card_id))

                    if not destination_card_id:
                        logger.log_info("No corresponding destination card id for card id: '%s', "
                                        "the card has never been synced, we need to create it." % card_id)

                        logger.log_info("No corresponding destination card found for card: '%s', "
                                        "the card has never been synced, we need to create it." % card_id, pretty=True)

                        self.sync_new_card(card_id, card_list_id, destination_board_id, card_name,
                          card_due_date, card_description, card_attachments, client_name,
                          card_quote, card_owner)

                        logger.log_info("New card added to the destination board")
                        logger.log_info("New card added to the destination board", pretty=True)
                        
                    else:
                        # Check if the client name is the same as the last time it was synced
                        logger.log_info("Check if the client name is the same as the last time it was synced")
                        logger.log_info("Card found in the destination board. Now checking if the client name is same", pretty=True)
                        destination_client_name = FileManager.read_corresponding_destination_client_name(file_path=self.card_mapping_file_path,
                                                                                                         card_id_to_find=card_id)
                        # If names are identical then update the card
                        logger.log_info("Client name found in source card: %s and destination card: %s" % (client_name, destination_client_name),
                                        pretty=True)
                        logger.log_info("Client name: %s and destination client name: %s" % (client_name, destination_client_name))
                        if client_name == destination_client_name:
                            logger.log_info("Card synced before with the same name. Updating now...")
                            logger.log_info("Card synced before with the same name. Updating now with:", pretty=True)
                            # Update name, due date and description
                            logger.log_info("Card Name: %s" % card_name, pretty=True)
                            logger.log_info("Due Date: %s" % card_due_date, pretty=True)
                            logger.log_info("Description: %s" % card_description, pretty=True)

                            updated = self.api.call_api("update_card", card_id=destination_card_id,
                                                        name=card_name,
                                                        due_date=card_due_date,
                                                        description=card_description)
                            if updated:
                                logger.log_info("Card updated with name, due date and description")
                                logger.log_info("Card updated with name, due date and description", pretty=True)
                            else:
                                logger.log_info("Card update failed with name, due date and description")
                                logger.log_info("Card update failed with name, due date and description", pretty=True)

                            logger.log_info("Deleting card attachments")
                            logger.log_info("Updating card attachments", pretty=True)
                            self.api.call_api("delete_card_attachments", card_id=destination_card_id)
                            logger.log_info("Existing attachments deleted. Now adding new attachments")

                            self.api.call_api("add_card_attachments", card_id=destination_card_id, card_attachments=card_attachments)
                            logger.log_info("New attachments updated")
                            logger.log_info("Card attachments updated", pretty=True)
                            logger.log_info("Updating quote")
                            logger.log_info("Updating quote", pretty=True)
                            updated = self.api.call_api("update_card_quote", board_id=destination_board_id,
                                                        card_id=destination_card_id, quote_value=card_quote)
                            if updated:
                                logger.log_info("Card quote updated")
                                logger.log_info("Card quote updated", pretty=True)
                            else:
                                logger.log_info("Card quote update failed")
                                logger.log_info("Card quote update failed", pretty=True)

                            logger.log_info("Updating card owner")
                            logger.log_info("Updating card owner", pretty=True)
                            updated = self.api.call_api("update_card_owner", board_id=destination_board_id,
                                                        card_id=destination_card_id, owner=card_owner)
                            if updated:
                                logger.log_info("Card owner updated")
                                logger.log_info("Card owner updated", pretty=True)
                            else:
                                logger.log_info("Card owner update failed")
                                logger.log_info("Card owner update failed", pretty=True)

                            logger.log_info("Checking whether the card list has been changed or not")
                            logger.log_info("Checking whether the card list has been changed or not", pretty=True)
                            origin_list_name = self.api.call_api("read_card_list_name_formatted", card_list_id=card_list_id)
                            trellocard_ = self.api.call_api("read_trello_card", card_id=destination_card_id, basic_info_only=True)

                            destination_list_name = self.api.call_api("read_card_list_name_formatted",
                                                                      card_list_id=trellocard_.card_list_id)

                            logger.log_info("Checking if the card was moved to another list then move it")
                            logger.log_info("Original Card Id: %s, Destination Card Id: %s,"
                                            " Origin list name: %s and destination list name: %s" %
                                            (card_id, destination_card_id, origin_list_name, destination_list_name))
                            if destination_list_name != origin_list_name:
                                logger.log_info("Card list was changed. Updating it")
                                logger.log_info("Card list was changed. Updating it", pretty=True)
                                destination_list_id = self.api.call_api("read_list_id",
                                                                        board_id=destination_board_id,
                                                                        name=origin_list_name)
                                if destination_list_id:
                                    updated = self.api.call_api("move_card", card_id=destination_card_id,
                                                                list_id=destination_list_id)
                                    if updated:
                                        logger.log_info("Destination list updated")
                                        logger.log_info("Destination list updated", pretty=True)
                                    else:
                                        logger.log_warning("Destination list not updated")
                                        logger.log_warning("Destination list not updated", pretty=True)
                                else:
                                    logger.log_warning("Destination list not updated")
                                    logger.log_warning("Destination list not updated", pretty=True)

                            logger.log_info("Card Updated - " + client_name + " - Id " + destination_card_id)

                            logger.log_info("Card Updated - Client: " + client_name + " - Card Id " + destination_card_id, pretty=True)
                        else:
                            logger.log_info("Names don't match. Now delete the previously synced card that "
                                            "is incorrect and create a new one in the correct board")
                            logger.log_info("Names don't match. Now delete the previously synced card that "
                                            "is incorrect and create a new one in the correct board", pretty=True)
                            logger.log_info("Deleting previously synced card")
                            logger.log_info("Deleting previously synced card", pretty=True)
                            deleted = self.api.call_api("delete_card", card_id=destination_card_id)
                            if deleted:
                                logger.log_info("Card deleted")
                                logger.log_info("Card deleted", pretty=True)
                            else:
                                logger.log_warning("Card was not deleted. Aborting")
                                logger.log_warning("Card was not deleted. Skipping...", pretty=True)
                                continue

                            logger.log_info("Remove mapping source card id <-> destination card id in file")
                            logger.log_info("Remove mapping source card id <-> destination card id in file", pretty=True)
                            FileManager.remove_card_id_mapping(file_path=self.card_mapping_file_path, card_id=destination_card_id)

                            logger.log_info("Card deleted. Now recreating it")
                            logger.log_info("Card deleted. Now recreating it", pretty=True)

                            self.sync_new_card(card_id, card_list_id, destination_board_id, card_name,
                                               card_due_date, card_description, card_attachments, client_name,
                                               card_quote, card_owner)

                            logger.log_info(
                                "Card Deleted and Recreated - " + client_name + " - Id " + destination_card_id)
                            logger.log_info(
                                "Card Deleted and Recreated - " + client_name + " - Id " + destination_card_id, pretty=True)
                else:
                    if not client_name:
                        logger.log_warning("Client name not found for card id: %s" % card_id)
                        logger.log_warning("No client name found for card: %s" % card_id, pretty=True)
                    else:
                        logger.log_warning("Client name not in client board mapping")

                        logger.log_info("Client name: %s found for card: %s" % (client_name, card_id), pretty=True)
                        logger.log_warning("But client name %s not found in client board mapping file for card: %s" % (client_name, card_id), pretty=True)

            except Exception as exp:
                logger.log_warning("Exception for card: %s: %s" % (card_id, str(exp)))

    def perform_post_cleanup(self):
        logger.log_info("Performing post cleanup")
        logger.log_info("Performing post cleanup", pretty=True)
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

                    logger.log_info("Card Deleted from destination " + corresponding_destination_card_id)
                except Exception as exp:
                    logger.log_warning("Exception in post cleanup. %s" % str(exp))
                    logger.log_warning("Exception in post cleanup. %s" % str(exp), pretty=True)
        logger.log_info("post cleanup completed", pretty=True)

    def start_sync(self):
        self.perform_prerequisites()
        self.read_cards_for_board_sync()
        self.perform_sync()
        self.perform_post_cleanup()

    def test(self):
        self.perform_prerequisites()
        self.api = TrelloAPI(api_key=self.api_key, api_token=self.api_token)
        # trello_card = self.api.call_api('read_trello_card', card_id='5c062dc5e8e6166b3129fd09', basic_info_only=True)
        # print("Source Card: %s" % trello_card)
        # tc2 = self.api.call_api('read_trello_card', card_id='5c114d043fccb34632c6cadd', basic_info_only=True)
        # print("Destination Card: %s" % tc2)
        # cln = self.api.call_api('read_card_list_name_formatted', card_list_id='5a6084e9868303a7c358962f')
        # print("Name" + cln)
        # c_id = self.api.call_api('read_list_id', board_id='NL22QylC', name=cln)
        # print(c_id)
        quote_custom_field_value, owner_custom_field_value = self.api.call_api('read_card_custom_fields',
                                                                               board_id='rEICc3JH',
                                                                               card_id='aSrkEGPp')
        print("Quote: %s" % quote_custom_field_value)
        print("Owner: %s" % owner_custom_field_value)

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
        # trellocard_sync_instance.test()