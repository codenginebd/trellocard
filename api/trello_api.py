from api.api_base import APIBase
from api.http_request import HttpRequest
from api.mixins.trellocard_crud_mixin import TrelloAPICardCRUDMixin
from api.mixins.trellocard_query_mixin import TrelloAPICardQueryMixin
from entities.trellocard import TrelloCard
from trellocard_exception import TrelloCardException
from trellocard_logger import TrelloCardLogger

logger = TrelloCardLogger.get_logger()


class TrelloAPI(APIBase, TrelloAPICardQueryMixin, TrelloAPICardCRUDMixin):
    def __init__(self, api_key, api_token):
        self.api_key = api_key
        self.api_token = api_token

        self.base_url = 'https://api.trello.com'

        self.api_version = '1'

        self.api_endpoint_card = "cards"
        self.api_endpoint_board = "boards"
        self.api_endpoint_list = "lists"
        self.api_endpoint_custom_field = "customFields"

        self.http_request = HttpRequest()

    def build_api_url(self, relative_path, **url_params):
        # relative_path = 1/cards/" + card_id + "/attachments
        get_params = []
        if url_params:
            for k, v in url_params.items():
                get_params += ["%s=%s" % (k, v)]
        get_params += [
            "key=%s" % self.api_key,
            "token=%s" % self.api_token
        ]
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


