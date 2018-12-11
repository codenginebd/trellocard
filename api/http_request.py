import requests
from enum import Enum
from trellocard_exception import TrelloCardException
from trellocard_logger import TrelloCardLogger

logger = TrelloCardLogger.get_logger()


class HttpMethod(Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"


class HttpRequest(object):

    def __init__(self):
        self.allowed_methods = [HttpMethod.GET.value, HttpMethod.POST.value, HttpMethod.PUT.value,
                                HttpMethod.DELETE.value, HttpMethod.PATCH.value]

    def get_success_status_code(self, request_method):
        success_status_code_mapping = {
            HttpMethod.GET.value: 200,
            HttpMethod.POST.value: 200,
            HttpMethod.PUT.value: 200,
            HttpMethod.DELETE.value: 200
        }
        return success_status_code_mapping[request_method]

    def perform_request(self, request_method, url, params=None, json=False, timeout=300):
        try:

            if request_method not in self.allowed_methods:
                logger.log_warning("The requested method: %s not allowed. "
                                   "Allowed methods are: %s" % (request_method, str(self.allowed_methods)))
                return None

            logger.log_info("Performing HTTP %s with the following information" % (request_method))
            logger.log_info("URL: %s\nParams: %s\nJSON: %s" % (url, str(params), json))

            method_invoke = getattr(requests, request_method)
            method_invoke_params = {
                'url': url,
                'timeout': timeout
            }
            if params:
                if json:
                    method_invoke_params['json'] = params
                else:
                    method_invoke_params['params'] = params

            response = method_invoke(**method_invoke_params)

            target_status_code = self.get_success_status_code(request_method)
            if response.status_code == target_status_code:
                logger.log_info("Response returned with status code: %s" % response.status_code)
                response.encoding = None
                return response.json()
            else:
                logger.log_info("Response returned with status code: %s" % response.status_code)
                return None

        except TrelloCardException as exp:
            logger.log_info("Exception in HttpReqeust.get. URL: %s and exception message: %s" % (url, str(exp)))
            return None

    def get(self, url):
        return self.perform_request(HttpMethod.GET.value, url)

    def post(self, url, data=None, json_data=None):
        is_json = json_data is not None
        params = data or json_data
        return self.perform_request(HttpMethod.POST.value, url, params=params, json=is_json)

    def put(self, url, json_data):
        return self.perform_request(HttpMethod.PUT.value, url, params=json_data, json=True)

    def delete(self, url):
        return self.perform_request(HttpMethod.DELETE.value, url)