from api.api_base import APIBase
from api.http_request import HttpRequest
from entities.trellocard import TrelloCard
from trellocard_exception import TrelloCardException
from trellocard_logger import TrelloCardLogger

logger = TrelloCardLogger.get_logger()


class TrelloAPICardCRUDMixin(object):

    def create_card(self, list_id, name, due_date, description):
        # url = "https://api.trello.com/1/cards?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s" % (self.api_version, self.api_endpoint_card)
        api_url = self.build_api_url(api_path)
        payload = {"name":name,"desc":description,"due":due_date,"idList":list_id}
        response = self.http_request.post(url=api_url, data=payload)
        if response and "id" in response:
            card_id = response.get("id")
            logger.log_info("Card created with id: % and payload: %s" % (card_id, str(payload)))
            return card_id
        logger.log_warning("No card created with info: %s" % (str(payload)))

    def update_card(self, card_id, name, due_date, description):
        # url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_card, card_id)
        api_url = self.build_api_url(api_path)
        payload = {"name":name,"desc":description,"due":due_date}
        response = self.http_request.put(url=api_url, json_data=payload)
        if response:
            logger.log_info("Card updated successfully. Card id: %s and card details: %s" % (card_id, str(payload)))
            return True
        else:
            logger.log_info("Card info update failed. Card id: %s and card details: %s" % (card_id, str(payload)))
            return False

    def add_card_attachments(self, card_id, card_attachments):
        for attachment in card_attachments:
            if len(attachment) < 2:
                continue
            attachment_name = attachment[0]
            attachment_url = attachment[1]
            # url = "https://api.trello.com/1/cards/" + card_id + "/attachments?key=" + api_key + "&token=" + api_token
            api_path = "%s/%s/%s/attachments" % (self.api_version, self.api_endpoint_card, card_id)
            api_url = self.build_api_url(api_path)
            payload = {"name": attachment_name, "url": attachment_url}
            response = self.http_request.post(url=api_url, data=payload)
            if response:
                logger.log_info("Card attachments added successfully")
            else:
                logger.log_info("Card attachment add failed")

    def delete_card_attachments(self, card_id):
        # url = "https://api.trello.com/1/cards/" + card_id + "/attachments?key=" + api_key + "&token=" + api_token
        attachment_list = self.read_card_attachments(card_id)

        # Delete attachments
        for attachment in attachment_list:
            attachment_id = attachment[2]
            # url = "https://api.trello.com/1/cards/" + card_id + "/attachments/" + attachment_id + "?key=" + api_key + "&token=" + api_token
            api_path = "%s/%s/%s/attachments/%s" % (self.api_version, self.api_endpoint_card, card_id, attachment_id)
            api_url = self.build_api_url(api_path)
            response = self.http_request.delete(url=api_url)
            if response:
                logger.log_info("Attachment deleted")
            else:
                logger.log_info("Attachment delete failed")

    def update_card_quote(self, board_id, card_id, quote_value):
        # Get quote custom field id
        # url = "https://api.trello.com/1/boards/" + board_id + "/customFields?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s/customFields" % (self.api_version, self.api_endpoint_board, board_id)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        quote_custom_field_id = None
        if not response:
            logger.log_info("card quote update failed. No response found for quote custom field id")
            return False
        for custom_field in response:
            if "id" in custom_field and "name" in custom_field:
                custom_field_id = custom_field["id"].strip()
                custom_field_name = custom_field["name"].strip()
                if custom_field_name == "Quote":
                    quote_custom_field_id = custom_field_id

        if not quote_custom_field_id:
            logger.log_info("card quote update failed. No quote custom field id found from quote custom field API response")
            return False

        # Update quote value
        # url = "https://api.trello.com/1/card/" + card_id + "/customField/" + quote_custom_field_id + "/item?key=" + api_key + "&token=" + api_token
        api_path = "%s/card/%s/customField/%s/item" % (self.api_version, card_id, quote_custom_field_id)
        api_url = self.build_api_url(api_path)
        payload = {"value": {"number": quote_value}}
        response = self.http_request.put(api_url, json_data=payload)
        if response:
            logger.log_info("Card quote updated succesfully")
            return True
        else:
            logger.log_info("Card quote update failed")
            return False

    def update_card_owner(self,board_id, card_id, owner):
        # Get owner custom field id and value id
        # url = "https://api.trello.com/1/boards/" + board_id + "/customFields?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s/customFields" % (self.api_version, self.api_endpoint_board, board_id)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if not response:
            logger.log_warning("Owner custom field value could not be updated. No response found: %s" % api_url)
            return False

        owner_custom_field_id = None
        owner_custom_field_value_id = None
        for custom_field in response:
            if "id" in custom_field and "name" in custom_field:
                custom_field_id = custom_field["id"].strip()
                custom_field_name = custom_field["name"].strip()
                if custom_field_name == "Owner":
                    owner_custom_field_id = custom_field_id
                    owner_custom_field_values = custom_field["options"]
                    for value in owner_custom_field_values:
                        if value["value"]["text"].strip() == owner:
                            owner_custom_field_value_id = value["id"]
                            break

        if any([not owner_custom_field_id, not owner_custom_field_value_id]):
            logger.log_warning("Owner custom field value could not be updated. Both custom field id and custom field value id missing")
            return False

        api_path = "%s/card/%s/customField/%s/item" % (self.api_version, card_id, owner_custom_field_id)
        api_url = self.build_api_url(api_path)
        payload = {"idValue": owner_custom_field_value_id}
        response = self.http_request.put(api_url, json_data=payload)
        if response:
            logger.log_info("Card owner updated succesfully")
            return True
        else:
            logger.log_info("Card owner update failed")
            return False

    def move_card(self, card_id, list_id):
        # url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_card, card_id)
        api_url = self.build_api_url(api_path)
        payload = {"idList": list_id}
        response = self.http_request.put(api_url, json_data=payload)
        if response:
            logger.log_info("Card moved to new list successfully")
            return True
        else:
            logger.log_info("Card did not move to new list successfully")
            return False

    def delete_card(self, card_id):
        # url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
        api_path = "%s/%s/%s" % (self.api_version, self.api_endpoint_card, card_id)
        api_url = self.build_api_url(api_path)
        response = self.http_request.delete(api_url)
        if response:
            logger.log_info("Card deleted successfully. Card id: %s" % card_id)
            return True
        else:
            logger.log_warning("Card delete failed for card id: %s" % card_id)
            return False