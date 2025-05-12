import unittest
import requests
from dotenv import load_dotenv
import os
import json
import logging
import sys
import socket
import time
from typing import (
    Optional, Dict, List, Any, Union, 
    Type, Literal, TypeVar, Counter, cast
)
# Type aliases
Response = requests.Response
JSONType = Union[Dict[str, Any], List[Any]]

from PyTestDocx.auth import Authenticator
from PyTestDocx.report import LogManager
from PyTestDocx.RequestManager import RequestManager

# Configure logging to display INFO level messages -- root logger (only basic config here)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class BaseAPITest(unittest.TestCase):
    """Base class for API tests with common setup and utilities"""
    
    # Class variables shared across all test cases
    test_start_time: Optional[float]  = None  # Timestamp when tests started
    test_end_time: Optional[float]  = None    # Timestamp when tests ended
    test_logger = LogManager()  # Initialize the logger instance here
    base_url: str = os.getenv("BASE_API_URL", "https://test.com")  # Base API URL

    @classmethod
    def setUpClass(cls):
        """Shared setup for all test classes - runs once before any tests"""
        cls.test_start_time = time.time()
        cls.session = requests.Session()  # Reuse session for all requests
        cls.headers = {'Content-Type': 'application/json'}  # Default headers
        cls.access_token = None  # Will store authentication token
        cls.user_id = None       # Will store authenticated user ID
        cls.request_handler = RequestManager(cls.base_url, cls.session, cls.test_logger)
    @classmethod
    def tearDownClass(cls):
        """Generate report if there are errors - runs after all tests complete"""
        cls.test_end_time = time.time()
        
    def run(self, result: Optional[unittest.TestResult] = None) -> None:
        """Override the default test run method to add custom logging"""
        # Log test attempt
        self.test_logger.log_executed_test(self.id(), "ATTEMPTING")
        
        if result is None:
            result = self.defaultTestResult()
            
        result.startTest(self)
        test_method = getattr(self, self._testMethodName)

        try:
            self._outcome = result
            self.setUp()
            test_method()
            self.tearDown()
            result.addSuccess(self)
            self.test_logger.log_executed_test(self.id(), "SUCCESS")
        except Exception as e:
            self._log_test_failure(e, result)
            result.addError(self, sys.exc_info())
            self.test_logger.log_executed_test(self.id(), f"ERROR ({type(e).__name__})")
        finally:
            result.stopTest(self)


    def login(self, username: Optional[str]=None, password: Optional[str]=None, endpoint: Optional[str]=None) -> Response:
        """Authenticate and store session credentials. See Authenticator.login for full documentation."""
        return Authenticator.login(self, username, password, endpoint)

    def auth_headers(self)-> Dict[str, str]:
        """Get headers with current access token for authenticated requests"""
        return Authenticator.get_auth_headers(self)



    @staticmethod
    def _truncate_long_string(value: Any, max_length: int = 20) -> Any:
        """Truncate strings with long repeating characters to make logs cleaner"""
        if not isinstance(value, str) or len(value) <= max_length:
            return value
        
        from collections import Counter
        char_counts = Counter(value)
        most_common = char_counts.most_common(1)[0]
        
        # If 80% of characters are the same, truncate
        if most_common[1] / len(value) > 0.8:
            return value[:max_length] + "..."
        return value

    def _log_test_failure(self, exception: Exception, result: unittest.TestResult)-> None:
        """Log detailed information about test failures"""
        test_method = getattr(self, self._testMethodName)
        # Get test description from docstring if available
        test_description = test_method.__doc__.strip() if test_method.__doc__ else "No description available"
        response = getattr(self, 'response', None)  # Get response if it exists
        payload = self._request_body
        request_body = getattr(self, '_request_body', None)  # Get request body if it exists
        # Format payload information
        payload_info = ""
        if payload is not None:
            try:
                if isinstance(payload, (dict, list)):
                    formatted_payload = json.dumps(payload, indent=2, ensure_ascii=False)
                else:
                    formatted_payload = str(payload)
                payload_info = f"\nPayload Sent:\n{formatted_payload}\n"  # Updated label
            except Exception as e:
                payload_info = f"\nPayload: (Could not format: {str(e)})\n"

        # Format response information (no truncation)
        response_info = ""
        if response is not None:
            try:
                response_content = response.json()
                response_info = json.dumps(response_content, indent=2)
            except ValueError:
                response_info = response.text
            response_info = (
                f"\nResponse Status: {response.status_code}\n"
                f"Response URL: {response.url}\n"
                f"Response Content:\n{response_info}\n"  # Full content
            )

        # Create log entry
        log_entry = (
            f"\nTest Description: {test_description}\n"
            f"Test: {self._testMethodName}\n"
            f"Error Type: {type(exception).__name__}\n"
            f"Error Message: {str(exception)}\n"
            f"{payload_info}"
            f"{response_info}"
            "----------------------------------------\n"
        )
        self.test_logger.log_test_error(log_entry)

    def assert_response(self, response: Response, expected_status: int, json_check: Optional[Dict[str, Any]]=None) -> None:
        """Universal response assertion with status code and optional JSON validation"""
        self.response = response

        try:
            # Verify status code matches expected
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Expected status {expected_status}, got {response.status_code}. Response: {response.text}"
            )
        except AssertionError as e:
            raise

        # For error responses, ensure there's content
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except ValueError:
                self.assertTrue(response.text.strip(), "Error response should contain content")

        # If JSON validation is requested and response is successful
        if json_check and response.status_code < 400:
            try:
                response_data: JSONType  = response.json()
                # Check each key-value pair in json_check
                for key, value in json_check.items():
                    self.assertEqual(response_data.get(key), value, f"Expected {key}={value}")
            except ValueError:
                self.fail("Expected JSON response but got non-JSON content")
                
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
        Delegates to RequestHandler for actual implementation.
        """

        self._request_body = kwargs.get('json', kwargs.get('data', None))
        return self.request_handler.make_request(
            method=method,
            url=url,
            expected_status=expected_status,
            json_check=json_check,
            redact_sensitive_keys=redact_sensitive_keys,
            redact_sensitive_data=redact_sensitive_data,
            sensitive_keys=sensitive_keys,
            sensitive_headers=sensitive_headers,
            max_response_time=max_response_time,
            retriable_status_codes=retriable_status_codes,
            **kwargs
        )

