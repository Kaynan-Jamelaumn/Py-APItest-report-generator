import os
import logging
from requests.exceptions import RequestException
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

class Authenticator:
    @staticmethod
    def login(test_instance, username: Optional[str] = None, password: Optional[str] = None, endpoint: Optional[str] = None) -> requests.Response:
        """Authenticate and store session credentials
        
        Args:
            test_instance (BaseAPITest): Instance of the test class requiring authentication.
            username (str, optional): Username for authentication. Defaults to .env TEST_USER.
            password (str, optional): Password for authentication. Defaults to .env TEST_PASSWORD.
            endpoint (str, optional): Custom auth endpoint path. If None, tries '/login' first,
                                    then falls back to '/authenticate' if the first attempt fails.
                                    If provided, only tries the specified endpoint.
        
        Returns:
            requests.Response: Authentication response
        
        Raises:
            ValueError: If credentials are missing
            requests.exceptions.RequestException: If all attempts fail (when endpoint=None)
        """
        payload = {
            'login': username or os.getenv('TEST_USER'),
            'password': password or os.getenv('TEST_PASSWORD')
        }

        if not all(payload.values()):
            raise ValueError("Missing credentials in .env file")

        test_instance._request_body = payload
        
        if endpoint is not None:
            url = f"{test_instance.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
            response = test_instance.session.post(url, json=payload, headers=test_instance.headers)
            test_instance.response = response
            
            if response.ok:
                data = response.json()
                test_instance.access_token = data.get('api_jwt', {}).get('access_token')
                test_instance.user_id = data.get('user', {}).get('id')
            return response
        else:
            endpoints_to_try = ['/login', '/authenticate']
            last_response = None
            
            for auth_endpoint in endpoints_to_try:
                url = f"{test_instance.base_url}{auth_endpoint}"
                try:
                    response = test_instance.session.post(url, json=payload, headers=test_instance.headers)
                    test_instance.response = response
                    
                    if response.ok:
                        data = response.json()
                        test_instance.access_token = data.get('api_jwt', {}).get('access_token')
                        test_instance.user_id = data.get('user', {}).get('id')
                        return response
                        
                    last_response = response
                    
                except RequestException as e:
                    logger.warning(f"Authentication attempt failed for {url}: {str(e)}")
                    continue
            
            if last_response is not None:
                return last_response
            raise RequestException("Both /login and /authenticate endpoints failed")

    @staticmethod
    def get_auth_headers(test_instance) -> Dict[str, str]:
        """Get headers with current access token for authenticated requests
        
        Args:
            test_instance (BaseAPITest): Instance of the test class requiring authentication headers
            
        Returns:
            Dict[str, str]: Dictionary containing Authorization and Content-Type headers
        """
        return {
            'Authorization': f'Bearer {test_instance.access_token}',
            'Content-Type': 'application/json'
        }