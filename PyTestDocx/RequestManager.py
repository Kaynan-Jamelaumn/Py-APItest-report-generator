import json
import time
import logging
from typing import Any, Dict, List, Optional, Literal
from requests import Response
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class RequestManager:
    """Handles HTTP request execution, retries, and logging for API tests."""
    
    def __init__(self, base_url: str, session, test_logger):
        """
        Initialize the RequestHandler.
        
        Args:
            base_url (str): The base API URL
            session: The requests Session object
            test_logger: The test logger instance for tracking metrics
        """
        self.base_url = base_url
        self.session = session
        self.test_logger = test_logger
        
    def make_request(self, 
        method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'], 
        url: str, 
        expected_status: Optional[int]=None, 
        json_check: Optional[Dict[str, Any]]=None,
        redact_sensitive_keys: bool=True,
        redact_sensitive_data: bool=True,
        sensitive_keys: Optional[List[str]]=None, 
        sensitive_headers: Optional[List[str]]=None, 
        max_response_time: Optional[float]=None, 
        retriable_status_codes: Optional[List[int]]=None,
        **kwargs: Any) -> Response:
        """Utility method to make API requests with timing, error handling, automatic assertions, and retries.

        Args:
            method (str): HTTP method (e.g., 'GET', 'POST').
            url (str): Full URL to send the request to.
            expected_status (int, optional): Expected HTTP status code.
            json_check (dict, optional): Key-value pairs to validate in JSON response.
            redact_sensitive_keys (bool): Redact sensitive headers (default: True).
            redact_sensitive_data (bool): Redact sensitive data values (default: True).
            sensitive_keys (list): Custom keys to redact in data (default: None).
            sensitive_headers (list): Custom headers to redact (default: None).
            max_response_time (float): Maximum allowed response time in seconds (default: None).
            retriable_status_codes (list, optional): List of HTTP status codes that trigger retries. 
                                               Defaults to None (no status-based retries).

            **kwargs: Additional request parameters (timeout, max_retries, retry_delay).
            

        Returns:
            requests.Response: The response object.
        """
        request_details = self._prepare_request_details(method, url, kwargs, redact_sensitive_data, sensitive_keys)
        processed_headers = self._process_request_headers(kwargs, redact_sensitive_keys, sensitive_headers)
        request_body = self._process_request_body(kwargs, redact_sensitive_data, sensitive_keys)
        
        self._log_request_details(method, url, processed_headers, request_details['params'], request_body)
        
        max_retries, retry_delay, timeout = self._setup_retry_config(kwargs)
        retriable_status_codes = retriable_status_codes or []

        response, duration = self._execute_request_with_retries(
            method, url, timeout, max_retries, retry_delay, retriable_status_codes, kwargs
        )

        self._validate_response(
            response, expected_status, json_check, max_response_time, duration, method, url
        )
        return response

    def _prepare_request_details(
        self,
        method: str,
        url: str,
        kwargs: dict,
        redact_sensitive_data: bool,
        sensitive_keys: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Capture and redact request parameters."""
        request_params = kwargs.get('params', {})

        if redact_sensitive_data:
            request_params = self._redact_sensitive_data(request_params, sensitive_keys)

        return {
            'method': method,
            'url': url,
            'params': request_params
        }

    def _process_request_headers(
        self,
        kwargs: dict,
        redact_sensitive_keys: bool,
        sensitive_headers: Optional[List[str]]
    ) -> Dict[str, str]:
        """Process and redact headers."""
        request_headers = self.session.headers.copy()
        if 'headers' in kwargs:
            request_headers.update(kwargs['headers'])

        return (
            self._redact_headers(request_headers, sensitive_headers)
            if redact_sensitive_keys
            else request_headers
        )

    def _process_request_body(
        self,
        kwargs: dict,
        redact_sensitive_data: bool,
        sensitive_keys: Optional[List[str]]
    ) -> Optional[Any]:
        """Process and redact request body."""
        request_body = None
        if 'files' in kwargs:
            request_body = {'files': kwargs['files']}
        elif 'json' in kwargs:
            request_body = (
                self._redact_sensitive_data(kwargs['json'], sensitive_keys)
                if redact_sensitive_data
                else kwargs['json']
            )
        elif 'data' in kwargs:
            request_body = (
                self._redact_sensitive_data(kwargs['data'], sensitive_keys)
                if redact_sensitive_data
                else kwargs['data']
            )
        return request_body

    def _log_request_details(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        body: Optional[Any]
    ) -> None:
        """Log request details with redacted sensitive information."""
        logger.debug(f"Request Method: {method}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request Headers: {headers}")
        if params:
            logger.debug(f"Request Params: {json.dumps(params, indent=2)}")
        if body is not None:
            logger.debug(f"Request Body: {json.dumps(body, indent=2)}")

    def _setup_retry_config(self, kwargs: dict) -> tuple:
        """Extract retry configuration from kwargs."""
        max_retries = kwargs.pop('max_retries', 3)
        retry_delay = kwargs.pop('retry_delay', 1)
        timeout = kwargs.pop('timeout', 10)
        return max_retries, retry_delay, timeout

    def _execute_request_with_retries(
        self,
        method: str,
        url: str,
        timeout: float,
        max_retries: int,
        retry_delay: float,
        retriable_status_codes: List[int],
        kwargs: dict
    ) -> tuple:
        """Execute request with retry logic."""
        attempts = 0
        response = None
        duration = 0

        while attempts <= max_retries:
            start_time = time.time()
            try:
                response = self.session.request(method, url, timeout=timeout, **kwargs)
                duration = time.time() - start_time
                self._track_response_metrics(url, method, duration, response.status_code, attempts + 1)

                if self._should_retry_response(response, attempts, max_retries, retriable_status_codes):
                    logger.info(
                        f"Retrying {method} {url} ({response.status_code} error) "
                        f"[Attempt {attempts+1}/{max_retries}]"
                    )
                    time.sleep(retry_delay)
                    attempts += 1
                    continue
                break
            except RequestException as e:
                duration = time.time() - start_time
                self._track_error_metrics(url, method, duration, e, attempts + 1)
                if self._should_retry_exception(attempts, max_retries):
                    logger.info(f"Retrying {method} {url} ({e}) [Attempt {attempts+1}/{max_retries}]")
                    time.sleep(retry_delay)
                    attempts += 1
                else:
                    raise AssertionError(f"Request failed after {max_retries} retries") from e
        return response, duration

    def _track_response_metrics(
        self,
        url: str,
        method: str,
        duration: float,
        status_code: int,
        attempt: int
    ) -> None:
        """Track metrics for successful responses."""
        self.test_logger.response_times.append({
            'endpoint': url.replace(self.base_url, '').strip('/'),
            'method': method,
            'duration': duration,
            'status_code': status_code,
            'attempt': attempt
        })

    def _track_error_metrics(
        self,
        url: str,
        method: str,
        duration: float,
        error: Exception,
        attempt: int
    ) -> None:
        """Track metrics for failed requests."""
        self.test_logger.response_times.append({
            'endpoint': url.replace(self.base_url, '').strip('/'),
            'method': method,
            'duration': duration,
            'error': str(error),
            'attempt': attempt
        })

    def _should_retry_response(
        self,
        response: Response,
        attempts: int,
        max_retries: int,
        retriable_status_codes: List[int]
    ) -> bool:
        """Determine if a response should be retried."""
        return response.status_code in retriable_status_codes and attempts < max_retries

    def _should_retry_exception(self, attempts: int, max_retries: int) -> bool:
        """Determine if an exception should be retried."""
        return attempts < max_retries

    def _validate_response(
        self,
        response: Response,
        expected_status: Optional[int],
        json_check: Optional[dict],
        max_response_time: Optional[float],
        duration: float,
        method: str,
        url: str
    ) -> None:
        """Validate response status and performance."""
        if expected_status is not None:
            self._assert_response_status(response, expected_status, json_check)
        elif not (200 <= response.status_code < 300):
            raise AssertionError(f"Unexpected status {response.status_code}. Response: {response.text}")

        if max_response_time is not None and duration > max_response_time:
            raise AssertionError(
                f"Response time {duration:.2f}s exceeds maximum allowed {max_response_time}s "
                f"for {method} {url}"
            )

    def _assert_response_status(
        self,
        response: Response,
        expected_status: int,
        json_check: Optional[dict]
    ) -> None:
        """Validate response status code and optionally JSON content."""
        if response.status_code != expected_status:
            raise AssertionError(
                f"Expected status {expected_status}, got {response.status_code}. "
                f"Response: {response.text}"
            )

        if json_check and response.status_code < 400:
            try:
                response_data = response.json()
                for key, value in json_check.items():
                    if response_data.get(key) != value:
                        raise AssertionError(f"Expected {key}={value}")
            except ValueError:
                raise AssertionError("Expected JSON response but got non-JSON content")

    def _redact_headers(self, headers: Dict[str, str], sensitive_headers: Optional[List[str]]=None) -> Dict[str, str]:
        """Redact sensitive headers using provided list or defaults."""
        default_sensitive_headers = {'Authorization', 'Cookie', 'Set-Cookie', 'X-Auth-Token', 'X-API-Key'}
        sensitive_headers = set(sensitive_headers) if sensitive_headers else default_sensitive_headers
        return {k: '***' if k in sensitive_headers else v for k, v in headers.items()}

    def _redact_sensitive_data(self, data: Any, sensitive_keys: Optional[List[str]]=None)-> Any:
        """Recursively redact sensitive values using provided keys or defaults."""
        default_sensitive_keys = {'password', 'token', 'secret', 'api_key', 'authorization'}
        sensitive_keys = set(sensitive_keys) if sensitive_keys else default_sensitive_keys
        
        if isinstance(data, dict):
            return {k: '***' if k.lower() in sensitive_keys else self._redact_sensitive_data(v, sensitive_keys) 
                    for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact_sensitive_data(item, sensitive_keys) for item in data]
        return data