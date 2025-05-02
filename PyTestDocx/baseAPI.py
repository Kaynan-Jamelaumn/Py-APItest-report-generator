import unittest
import requests
from dotenv import load_dotenv
import os
import json
import logging
import sys
import socket
import time
from .report_generator import ReportGenerator

# Configure logging to display INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class BaseAPITest(unittest.TestCase):
    """Base class for API tests with common setup and utilities"""
    
    # Class variables shared across all test cases
    test_start_time = None  # Timestamp when tests started
    test_end_time = None    # Timestamp when tests ended
    _test_errors = []       # List to accumulate test errors
    ERROR_LOG_FILE = "test_errors.log"      # File for error logs
    ERROR_DOCX_FILE = "test_errors.docx"    # File for generated report
    EXECUTED_LOG_FILE = "executed_tests.log" # File for test execution log
    base_url = "https://qas-api.simtro.com.br/api"  # Base API URL
    _response_times = []    # List to track API response times

    @classmethod
    def setUpClass(cls):
        """Shared setup for all test classes - runs once before any tests"""
        cls.test_start_time = time.time()
        cls.session = requests.Session()  # Reuse session for all requests
        cls.headers = {'Content-Type': 'application/json'}  # Default headers
        cls.access_token = None  # Will store authentication token
        cls.user_id = None       # Will store authenticated user ID
        
        # Clear previous log files
        with open(cls.ERROR_LOG_FILE, 'w') as f:
            f.write("")
        if os.path.exists(cls.ERROR_DOCX_FILE):
            os.remove(cls.ERROR_DOCX_FILE)
        with open(cls.EXECUTED_LOG_FILE, 'w') as f:
            f.write("")

    @classmethod
    def tearDownClass(cls):
        """Generate report if there are errors - runs after all tests complete"""
        cls.test_end_time = time.time()

        # # If there were errors, generate a report
        # if cls._test_errors:
        #     report = ReportGenerator(
        #         test_errors=cls._test_errors,
        #         response_times=cls._response_times,
        #         test_result=cls._result,
        #         start_time=cls.test_start_time,
        #         end_time=cls.test_end_time,
        #         base_url=cls.base_url,
        #         env_info={
        #             'python_version': sys.version.split()[0],
        #             'platform': sys.platform,
        #             'requests_version': requests.__version__,
        #             'hostname': socket.gethostname(),
        #             'cpu_cores': os.cpu_count()
        #         }
        #     )
        #     report.generate()
        #     report.save(cls.ERROR_DOCX_FILE)

    def run(self, result=None):
        """Override the default test run method to add custom logging"""
        # Log test attempt
        with open(self.EXECUTED_LOG_FILE, 'a') as f:
            f.write(f"ATTEMPTING: {self.id()}\n")

        if result is None:
            result = self.defaultTestResult()

        # Store the result object for later use in tearDownClass
        self._result = result
        type(self)._result = result
        result.startTest(self)
        test_method = getattr(self, self._testMethodName)

        try:
            self._outcome = result
            self.setUp()
            test_method()
            self.tearDown()
            result.addSuccess(self)
            # Log successful test
            with open(self.EXECUTED_LOG_FILE, 'a') as f:
                f.write(f"  SUCCESS: {self.id()}\n")
        except Exception as e:
            # Handle test failure
            self._log_test_failure(e, result)
            result.addError(self, sys.exc_info())
            # Log failed test
            with open(self.EXECUTED_LOG_FILE, 'a') as f:
                f.write(f"  ERROR: {self.id()} ({type(e).__name__})\n")
        finally:
            result.stopTest(self)

    @staticmethod
    def _truncate_long_string(value, max_length=20):
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

    def _log_test_failure(self, exception, result):
        """Log detailed information about test failures"""
        test_method = getattr(self, self._testMethodName)
        # Get test description from docstring if available
        test_description = test_method.__doc__.strip() if test_method.__doc__ else "No description available"
        response = getattr(self, 'response', None)  # Get response if it exists
        request_body = getattr(self, '_request_body', None)  # Get request body if it exists

        # Format response information
        response_info = ""
        if response is not None:
            try:
                response_content = response.json()
                response_info = json.dumps(response_content, indent=2)
            except ValueError:
                response_info = response.text

            # Truncate very long responses
            if len(response_info) > 500:
                response_info = response_info[:497] + "..."
            response_info = (f"\nResponse Status: {response.status_code}\n"
                            f"Response URL: {response.url}\n"
                            f"Response Content:\n{response_info}\n")

        # Format request body information
        request_body_info = ""
        if request_body is not None:
            try:
                if isinstance(request_body, (dict, list)):
                    formatted_body = json.dumps(request_body, indent=2, ensure_ascii=False)
                else:
                    formatted_body = str(request_body)
                request_body_info = f"\nRequest Body:\n{formatted_body}\n"
            except Exception as e:
                request_body_info = f"\nRequest Body: (Could not format: {str(e)})\n"

        # Create comprehensive log entry
        log_entry = (f"\nTest Description: {test_description}\n"
                    f"Test: {self._testMethodName}\n"
                    f"Error Type: {type(exception).__name__}\n"
                    f"Error Message: {str(exception)}\n"
                    f"{request_body_info}"
                    f"{response_info}"
                    "----------------------------------------\n")

        logger.error(log_entry)
        BaseAPITest._test_errors.append(log_entry)  # Add to errors list for reporting

    def login(self, username=None, password=None):
        """Authenticate and store session credentials"""
        url = f"{self.base_url}/login"
        # Use provided credentials or fall back to .env file
        payload = {
            'login': username or os.getenv('TEST_USER'),
            'password': password or os.getenv('TEST_PASSWORD')
        }

        # Validate we have credentials
        if not all(payload.values()):
            raise ValueError("Missing credentials in .env file")

        self._request_body = payload
        response = self.session.post(url, json=payload, headers=self.headers)
        self.response = response
        if response.ok:
            data = response.json()
            # Store auth token and user ID for future requests
            self.access_token = data.get('api_jwt', {}).get('access_token')
            self.user_id = data.get('user', {}).get('id')
        return response

    def assert_response(self, response, expected_status, json_check=None):
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
                response_data = response.json()
                # Check each key-value pair in json_check
                for key, value in json_check.items():
                    self.assertEqual(response_data.get(key), value, f"Expected {key}={value}")
            except ValueError:
                self.fail("Expected JSON response but got non-JSON content")

    def auth_headers(self):
        """Get headers with current access token for authenticated requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def make_request(self, method, url, expected_status=None, **kwargs):
        """Utility method to make API requests with timing and error handling"""
        self._request_body = None
        start_time = time.time()

        # Capture request body for logging
        if 'files' in kwargs:
            self._request_body = {'files': kwargs['files']}
        elif 'json' in kwargs:
            self._request_body = kwargs['json']
        elif 'data' in kwargs:
            self._request_body = kwargs['data']

        # Make the actual request
        response = self.session.request(method, url, **kwargs)
        self.response = response
        duration = time.time() - start_time
        # Track response time - add endpoint identification
        BaseAPITest._response_times.append({
            'endpoint': url.replace(self.base_url, '').strip('/'),  # Store endpoint
            'duration': duration,
            'test_class': self.__class__.__name__  # Store test class name
        })
        # If no expected status provided and response is an error, log it
        if expected_status is None and response.status_code >= 400:
            self.log_error_response(response)

        return response