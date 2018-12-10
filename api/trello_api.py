from api.api_base import APIBase
from api.http_request import HttpRequest
from trellocard_exception import TrelloCardException
from trellocard_logger import TrelloCardLogger

logger = TrelloCardLogger.get_logger()


class TrelloAPICardMixin(object):
    def read_cards_in_board(self, board_id):
        api_path = "%s/%s/%s/%s" % (self.api_version, self.api_endpoint_board, board_id, self.api_endpoint_card)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if response:
            card_list = []
            for item in response:
                card_list.append(item["id"])
            return card_list
        else:
            logger.log_warning("No response found in get_cards_in_board API call")
            return []

    def read_card_client_name(self, board_id, card_id):
        # Get custom field ids of all client custom fields in the board

        api_path = "%s/%s/%s/%s" % (self.api_version, self.api_endpoint_board, board_id, self.api_endpoint_custom_field)
        api_url = self.build_api_url(api_path)
        response = self.http_request.get(api_url)
        if response:
            client_custom_field_ids = []
            for custom_field in response:
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

            # url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
            api_path = "%s/%s/%s/%s" % (self.api_version, self.api_endpoint_board, board_id, self.api_endpoint_custom_field)
            api_url = self.build_api_url(api_path, **extra_params)
            response = self.http_request.get(api_url)
            client_name = ""
            for custom_field in response:
                custom_field_id = custom_field["id"]
                if custom_field_id == client_custom_field_id:
                    custom_field_values = custom_field["options"]
                    for value in custom_field_values:
                        if value["id"] == client_custom_field_value_id:
                            client_name = value["value"]["text"].strip()
                            break
                    break

            return client_name
        else:
            logger.log_warning("No response found in get_cards_in_board API call")
            return ""


class TrelloAPI(APIBase, TrelloAPICardMixin):
    def __init__(self, api_key, api_token):
        self.api_key = api_key
        self.api_token = api_token

        self.base_url = 'https://api.trello.com'

        self.api_version = '1'

        self.api_endpoint_card = "cards"
        self.api_endpoint_board = "boards"
        self.api_endpoint_custom_field = "customFields"

        self.http_request = HttpRequest()

    def build_api_url(self, relative_path, **url_params):
        # relative_path = 1/cards/" + card_id + "/attachments
        get_params = [
            "key=%s" % self.api_key,
            "token=%s" % self.api_token
        ]
        if url_params:
            for k, v in url_params.items():
                get_params += ["%s=%s" % (k, v)]
        get_params_string = "&".join(get_params)
        api_url = "%s/%s?%s" % (self.base_url, relative_path, get_params_string)
        return api_url

    def call_api(self, api_method, **params):
        logger.log_debug("Calling API method: %s" % api_method)
        logger.log_debug("API request Params: %s" % (str(params)))
        try:
            return getattr(self, api_method)(**params)
        except TrelloCardException as exp:
            logger.log_debug("API call exception for method: %s. Exception message: %s" % (api_method, str(exp)))
            return None


