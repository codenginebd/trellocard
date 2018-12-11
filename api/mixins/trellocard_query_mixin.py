from api.api_base import APIBase
from api.http_request import HttpRequest
from entities.trellocard import TrelloCard
from trellocard_exception import TrelloCardException
from trellocard_logger import TrelloCardLogger

logger = TrelloCardLogger.get_logger()


class TrelloAPICardQueryMixin(object):
    def read_cards_in_board(self, board_id):
        api_path = "%s/%s/%s/%s" % (self.api_version, self.api_endpoint_board, board_id, self.api_endpoint_card)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if response:
            card_list = []
            for item in response:
                if item.get("id"):
                    card_list.append(item["id"])
            return card_list
        else:
            logger.log_warning("No response found in get_cards_in_board API call")
            return []

    def read_card_client_name(self, board_id, card_id):
        # Get custom field ids of all client custom fields in the board
        try:
            api_path = "%s/%s/%s/%s" % (self.api_version, self.api_endpoint_board, board_id, self.api_endpoint_custom_field)
            api_url = self.build_api_url(api_path)
            board_response = self.http_request.get(api_url)
            if board_response:
                client_custom_field_ids = []
                for custom_field in board_response:
                    custom_field_id = custom_field["id"]
                    custom_field_name = custom_field["name"]
                    if "Client A-K" in custom_field_name or "Client L-Z" in custom_field_name:
                        client_custom_field_ids.append(custom_field_id)

                # Get client custom field id and value id for the card
                api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_card, card_id)
                extra_params = {
                    "fields": "name",
                    "customFieldItems": "true"
                }
                api_url = self.build_api_url(api_path, **extra_params)
                response = self.http_request.get(api_url)
                client_custom_field_id = ""
                if response:
                    if "customFieldItems" in response:
                        card_custom_fields = response["customFieldItems"]
                        for i in range(len(card_custom_fields)):
                            custom_field_id = card_custom_fields[i]["idCustomField"]
                            if custom_field_id in client_custom_field_ids:
                                client_custom_field_id = custom_field_id
                                client_custom_field_value_id = card_custom_fields[i]["idValue"]
                    else:
                        logger.log_warning("customFieldItems not found in API response: %s" % api_url)
                else:
                    logger.log_warning("Empty response founf in API Call: %s" % api_url)

                # Get client name from client custom field id and value id for the card

                client_name = ""
                for custom_field in board_response:
                    custom_field_id = custom_field.get("id")
                    if custom_field_id == client_custom_field_id:
                        custom_field_values = custom_field.get("options")
                        for value in custom_field_values:
                            if value.get("id") == client_custom_field_value_id:
                                client_name = value["value"]["text"].strip()
                                break
                        break

                return client_name
            else:
                logger.log_warning("No response found in get_cards_in_board API call")
                return ""
        except TrelloCardException as exp:
            logger.log_warning("Exception in method read_card_client_name. Exception: %s" % str(exp))

    def read_card_attachments(self, card_id):
        attachments = []
        # url = "https://api.trello.com/1/cards/" + card_id + "/attachments?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s/attachments" % (self.api_version, self.api_endpoint_card, card_id)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if response:
            for attachment in response:
                if attachment.get("name"):
                    attachment_details = []
                    attachment_details += [attachment.get("name", "")]
                    attachment_details += [attachment.get("url", "")]
                    attachment_details += [attachment.get("id", "")]
                    attachments += [attachment_details]
        return attachments

    def read_card_custom_fields(self, board_id, card_id):
        # First get the custom field ids
        # url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
        try:
            api_path = "%s/%s/%s/customFields" % (self.api_version, self.api_endpoint_board, board_id)
            api_url = self.build_api_url(api_path)
            response = self.http_request.get(api_url)
            quote_custom_field_id, owner_custom_field_id = "", ""
            if not response:
                logger.log_warning("No response found in API call: %s" % api_url)
                return None, None
            for custom_field in response:
                if "id" in custom_field and "name" in custom_field:
                    custom_field_id = custom_field["id"].strip()
                    custom_field_name = custom_field["name"].strip()
                    if custom_field_name == "Quote":
                        quote_custom_field_id = custom_field_id
                    elif custom_field_name == "Owner":
                        owner_custom_field_id = custom_field_id

            if not quote_custom_field_id and not owner_custom_field_id:
                logger.log_warning("No custom field id found associated with the board id: %s" % board_id)
                return None, None

            # Now get the custom field values
            quote_custom_field_value, owner_custom_field_value = None, None
            #  url = "https://api.trello.com/1/cards/" + card_id + "?fields=name&customFieldItems=true&key=" + api_key + "&token=" + api_token
            api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_card, card_id)
            extra_params = {
                "fields": "name",
                "customFieldItems": "true"
            }
            api_url = self.build_api_url(api_path, **extra_params)
            response = self.http_request.get(api_url)
            if not response or "customFieldItems" not in response:
                logger.log_warning("No custom field value found for board id: %s and card id: %s" % (board_id, card_id))
                return None, None

            card_custom_fields = response["customFieldItems"]
            for i in range(len(card_custom_fields)):
                try:
                    custom_field_id = card_custom_fields[i]["idCustomField"]
                    if custom_field_id == quote_custom_field_id:
                        quote_custom_field_value = card_custom_fields[i]["value"]["number"]
                    elif custom_field_id == owner_custom_field_id:
                        owner_custom_field_value = card_custom_fields[i]["value"]["number"]

                    if quote_custom_field_value and owner_custom_field_value:
                        break
                except TrelloCardException as exp:
                    logger.log_warning("Keyerror in method read_card_custom_fields. Exception: %s" % str(exp))

            return quote_custom_field_value, owner_custom_field_value
        except TrelloCardException as exp:
            logger.log_warning("Exception in method read_card_custom_fields. Exception: %s" % str(exp))
            return None, None

    def read_list_id(self, board_id, name):
        # url = "https://api.trello.com/1/boards/" + board_id + "/lists?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s/%s" % (self.api_version, self.api_endpoint_board, board_id, self.api_endpoint_list)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if not response:
            logger.log_warning("Empty response found for list id. URL: %s" % api_url)
        for list in response:
            if "id" in list and "name" in list:
                list_id = list["id"].strip()
                list_name = list["name"].strip()
                if list_name == name:
                    return list_id
                    break

    def read_card_list_name_formatted(self, card_list_id):
        # url = "https://api.trello.com/1/lists/" + card_list_id + "?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_list, card_list_id)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)

        if response and "name" in response:
            card_list_name = response["name"].strip()

            # Rename list names so they match with the client boards
            if card_list_name == "Suspendo": card_list_name = "Suspended"
            if card_list_name == "Finito": card_list_name = "Returned"

            return card_list_name
        else:
            logger.log_warning("No Card List Name found for card list id: %s" % card_list_id)

    def read_trello_card(self, card_id, basic_info_only=False):
        api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_card, card_id)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if response:
            name = response.get('name', '')
            due_date = response.get('due', '')
            description = response.get('desc', '')
            card_list_id = response.get("idList", "")

            trellocard = TrelloCard()
            trellocard.card_list_id = card_list_id
            trellocard.card_name = name
            trellocard.card_due_date = due_date
            trellocard.card_description = description

            if not basic_info_only:
                attachments = self.read_card_attachments(card_id)
                trellocard.card_attachments = attachments

            return trellocard

        else:
            logger.log_debug("No response found for card id: %s. URL: %s" % (card_id, api_url))
