from functions import *

api_key = get_api_key()
api_token = get_api_token()
board_id_to_sync = get_board_id_to_sync()

# Client <-> Board mapping
client_board_mapping = get_client_board_mapping()

# List all cards located in the source board
card_list = get_cards_in_board(board_id_to_sync, api_key, api_token)

# For each card in the source board
for card_id in card_list:
    # Get the client name
    client_name = get_card_client_name(board_id_to_sync, card_id, api_key, api_token)

    # Check if client name exists and if the client has a dedicated board
    if client_name != "" and client_name in client_board_mapping:
        # Get the destination board id
        destination_board_id = client_board_mapping[client_name]

        # Get card information
        card_name = get_card_name(card_id, api_key, api_token)
        card_due_date = get_card_due_date(card_id, api_key, api_token)
        card_description = get_card_description(card_id, api_key, api_token)
        card_attachments = get_card_attachments(card_id, api_key, api_token)
        card_quote = get_card_quote(board_id_to_sync, card_id, api_key, api_token)
        card_owner = get_card_owner(board_id_to_sync, card_id, api_key, api_token)

        # Get the corresponding destination card id in file
        destination_card_id = get_corresponding_destination_card_id(card_id)

        # No corresponding destination card id, the card has never been synced, we need to create it
        if destination_card_id == "":
            # Get destination list id
            card_list_name = get_card_list_name_formatted(card_id, api_key, api_token)
            destination_list_id = get_list_id(destination_board_id, card_list_name, api_key, api_token)

            # Create card with name, due date, description and get id of the newly created card
            destination_card_id = create_card(destination_board_id
                                            , destination_list_id
                                            , card_name
                                            , card_due_date
                                            , card_description
                                            , api_key
                                            , api_token)

            # Store mapping source card id <-> destination card id in file
            store_card_mapping(card_id, destination_card_id, client_name)

            # Add attachments
            add_card_attachments(destination_card_id, card_attachments, api_key, api_token)

            # Add quote value
            update_card_quote(destination_board_id, destination_card_id, card_quote, api_key, api_token)

            # Add owner
            update_card_owner(destination_board_id, destination_card_id, card_owner, api_key, api_token)

            print("Card Created - " + client_name + " - Id " + destination_card_id)

        # One corresponding destination card id, the card has already been synced before
        else:
            # Check if the client name is the same as the last time it was synced
            destination_client_name = get_corresponding_destination_client_name(card_id)
            # If names are identical then update the card
            if client_name == destination_client_name:
                # Update name, due date and description
                update_card(destination_card_id, card_name, card_due_date, card_description, api_key, api_token)

                # Delete attachments
                delete_card_attachments(destination_card_id, api_key, api_token)

                # Add attachments
                add_card_attachments(destination_card_id, card_attachments, api_key, api_token)

                # Update quote value
                update_card_quote(destination_board_id, destination_card_id, card_quote, api_key, api_token)

                # Update owner
                update_card_owner(destination_board_id, destination_card_id, card_owner, api_key, api_token)

                # Check if the list of the card was changed
                origin_list_name = get_card_list_name_formatted(card_id, api_key, api_token)
                destination_list_name = get_card_list_name_formatted(destination_card_id, api_key, api_token)

                # If the card was moved to another list then move it
                if destination_list_name != origin_list_name:
                    destination_list_id = get_list_id(destination_board_id, origin_list_name, api_key, api_token)
                    move_card(destination_card_id, destination_list_id, api_key, api_token)

                print("Card Updated - " + client_name + " - Id " + destination_card_id)

            # If names don't match then delete the previously synced card that is incorrect and create a new one in the correct board
            else:
                # Delete previously synced card that is incorrect
                delete_card(destination_card_id, api_key, api_token)

                # Remove mapping source card id <-> destination card id in file
                remove_card_mapping(destination_card_id)

                # Create card in the correct board
                # Get destination list id
                card_list_name = get_card_list_name_formatted(card_id, api_key, api_token)
                destination_list_id = get_list_id(destination_board_id, card_list_name, api_key, api_token)

                # Create card with name, due date, description and get id of the newly created card
                destination_card_id = create_card(destination_board_id
                                                , destination_list_id
                                                , card_name
                                                , card_due_date
                                                , card_description
                                                , api_key
                                                , api_token)

                # Store mapping source card id <-> destination card id in file
                store_card_mapping(card_id, destination_card_id, client_name)

                # Add attachments
                add_card_attachments(destination_card_id, card_attachments, api_key, api_token)

                # Add quote value
                update_card_quote(destination_board_id, destination_card_id, card_quote, api_key, api_token)

                # Add owner
                update_card_owner(destination_board_id, destination_card_id, card_owner, api_key, api_token)

                print("Card Deleted and Recreated - " + client_name + " - Id " + destination_card_id)

# List all source cards in mapping file
source_card_list_from_mapping_file = get_mapping_source_card_list()

# List cards in source board
source_card_list = get_cards_in_board(board_id_to_sync, api_key, api_token)

# For each source card in mapping file
for source_card in source_card_list_from_mapping_file:
    # If it's not in the source board
    if source_card not in source_card_list:
        # Delete the corresponding card
        corresponding_destination_card_id = get_corresponding_destination_card_id(source_card)
        delete_card(corresponding_destination_card_id, api_key, api_token)

        # Remove mapping source card id <-> destination card id in file
        remove_card_mapping(source_card)

        print("Card Deleted - Id " + destination_card_id)
