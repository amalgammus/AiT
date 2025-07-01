import hashlib
import requests
import logging
from urllib3.util.ssl_ import create_urllib3_context
from requests.adapters import HTTPAdapter

# Настройка логирования
logger = logging.getLogger(__name__)


class CustomHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers="DEFAULT@SECLEVEL=1")
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers="DEFAULT@SECLEVEL=1")
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super().proxy_manager_for(*args, **kwargs)


class APIClient:
    def __init__(self, base_url, secret_key, verify_ssl=False):
        self.base_url = base_url.rstrip('/')
        self.secret_key = secret_key
        self.verify_ssl = verify_ssl
        self.session = self._create_session()

    @staticmethod
    def _create_session():
        """Создает и настраивает сессию requests"""
        session = requests.Session()
        adapter = CustomHTTPAdapter(max_retries=3)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @staticmethod
    def _process_response(response):
        """Обрабатывает ответ API"""
        try:
            json_response = response.json()
            logger.debug("Parsed JSON response: %s", json_response)
            return json_response
        except ValueError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error(error_msg)
            return {
                "code": -1,
                "descr": error_msg,
                "data": {
                    "status_code": response.status_code,
                    "content": response.text[:500]
                }
            }

    def _calculate_signature(self, params):
        """Calculate MD5 signature for request parameters"""
        param_str = '&'.join(f"{k}={v}" for k, v in params.items())
        signature = hashlib.md5(f"{param_str}{self.secret_key}".encode()).hexdigest()
        return signature

    def _make_request(self, method, endpoint, params=None, data=None, json_data=None):
        url = f"{self.base_url}/common_api/1.0/{endpoint}"
        headers = {}
        request_params = params or {}
        request_data = data or {}

        # Для всех методов кроме ping добавляем подпись
        if endpoint != 'ping':
            all_params = {**request_params, **request_data}
            if json_data:
                all_params.update(json_data)
            signature = self._calculate_signature(all_params)
            headers['Signature'] = signature

        try:
            if method.upper() == 'GET':
                response = self.session.get(
                    url,
                    params=request_params,
                    headers=headers,
                    verify=self.verify_ssl
                )
            elif method.upper() == 'POST':
                if json_data:
                    headers['Content-Type'] = 'application/json'
                    response = self.session.post(
                        url,
                        params=request_params,
                        json=json_data,
                        headers=headers,
                        verify=self.verify_ssl
                    )
                else:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    form_data = {**request_params, **request_data}
                    response = self.session.post(
                        url,
                        data=form_data,
                        headers=headers,
                        verify=self.verify_ssl
                    )
            else:
                error_msg = f"Unsupported HTTP method: {method}"
                return {
                    "code": -1,
                    "descr": error_msg,
                    "data": {}
                }

            return self._process_response(response)

        except requests.exceptions.SSLError as e:
            error_msg = f"SSL Error: {str(e)}"
            return {
                "code": -1,
                "descr": error_msg,
                "data": {}
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            return {
                "code": -1,
                "descr": error_msg,
                "data": {}
            }

    # API Methods
    def ping(self):
        """Проверка доступности сервера"""
        return self._make_request('GET', 'ping')

    def get_crew_groups_list(self):
        """Получить список групп экипажа"""
        params = {}
        return self._make_request('GET', 'get_crew_groups_list', params=params)

    def get_crew_info(self, crew_id, fields=None):
        """Получить информацию об экипаже"""
        params = {'crew_id': crew_id}
        if fields:
            params['fields'] = fields
        return self._make_request('GET', 'get_crew_info', params=params)

    def get_order_states_list(self):
        """Получить список состояний заказа"""
        params = {}
        return self._make_request('GET', 'get_order_states_list', params=params)

    def get_crew_states_list(self):
        """Получить список состояний экипажа"""
        params = {}
        return self._make_request('GET', 'get_crew_states_list', params=params)

    def change_order_state(self, order_id, new_state, cancel_order_penalty_sum=None):
        """Изменить состояние заказа"""
        params = {
            'order_id': order_id,
            'new_state': new_state
        }
        if cancel_order_penalty_sum is not None:
            params['cancel_order_penalty_sum'] = cancel_order_penalty_sum

        return self._make_request('POST', 'change_order_state', data=params)
