import hashlib
import requests
import ssl
from urllib3.util.ssl_ import create_urllib3_context
from flask import current_app
from functools import wraps
from requests.adapters import HTTPAdapter


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

    def _create_session(self):
        session = requests.Session()
        adapter = CustomHTTPAdapter(max_retries=3)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _calculate_signature(self, params):
        param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.md5(f"{param_str}{self.secret_key}".encode()).hexdigest()

    def _make_request(self, method, endpoint, params=None, data=None, json_data=None):
        url = f"{self.base_url}/common_api/1.0/{endpoint}"
        headers = {}

        # Добавляем подпись для всех методов, кроме ping
        if endpoint != 'ping':
            headers['Signature'] = self._calculate_signature(params)

        try:
            if method.upper() == 'GET':
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    verify=self.verify_ssl
                )
            elif method.upper() == 'POST':
                if json_data:
                    headers['Content-Type'] = 'application/json'
                    response = self.session.post(
                        url,
                        json=json_data,
                        headers=headers,
                        verify=self.verify_ssl
                    )
                else:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    response = self.session.post(
                        url,
                        data=data,
                        headers=headers,
                        verify=self.verify_ssl
                    )
            else:
                return {
                    "code": -1,
                    "descr": "Unsupported HTTP method",
                    "data": {}
                }

            return self._process_response(response)

        except requests.exceptions.SSLError as e:
            return {
                "code": -1,
                "descr": f"SSL Error: {str(e)}",
                "data": {}
            }
        except requests.exceptions.RequestException as e:
            return {
                "code": -1,
                "descr": f"Request failed: {str(e)}",
                "data": {}
            }

    def ping(self):
        """Пинг для проверки доступности"""
        return self._make_request('GET', 'ping')

    def get_crew_groups_list(self):
        """Получить список групп экипажа"""
        params = {}  # Пустые параметры, но подпись будет сгенерирована
        return self._make_request('GET', 'get_crew_groups_list', params=params)

    def get_crew_info(self, crew_id, fields=None):
        """
        Получить информацию об экипаже
        :param crew_id: ID экипажа (обязательный)
        :param fields: список полей через запятую (опциональный)
        """
        params = {'crew_id': crew_id}
        if fields:
            params['fields'] = fields
        return self._make_request('GET', 'get_crew_info', params=params)

    def get_order_states_list(self):
        """Получить список состояний заказа"""
        params = {}  # Пустые параметры, но подпись будет сгенерирована
        return self._make_request('GET', 'get_order_states_list', params=params)

    def _process_response(self, response):
        try:
            return response.json()
        except ValueError:
            return {
                "code": -1,
                "descr": "Invalid JSON response",
                "data": {
                    "status_code": response.status_code,
                    "content": response.text[:500]
                }
            }
