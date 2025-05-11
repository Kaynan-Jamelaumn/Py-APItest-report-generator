import sys
import unittest
import time
import argparse
import os
import socket
import requests
from PyTestDocx import BaseAPITest, CustomTestResult, CustomTestRunner
from PyTestDocx.report import DocxReportGenerator, HTMLReportGenerator
class TestRunner:
    def __init__(self):
        self.args = None
        self.test_dirs = []
        self.suite = None
        self.all_tests = []
        self.result = None
        self.start_time = None
        self.end_time = None
        self.test_statuses = []
        self.false_positives = []
        self.env_info = {}

    @staticmethod
    def flatten(suite):
        """Recursively yield every TestCase from a TestSuite."""
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                yield from TestRunner.flatten(test)  # Recurse if it's a TestSuite
            else:
                yield test  # Yield individual test

    def parse_arguments(self):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description='Run API tests')
        parser.add_argument('--test-dir', default='tests',
                          help='Directory containing test files (default: tests)')
        self.args = parser.parse_args() # Parse command-line arguments

    def validate_test_directory(self):
        """Ensure the test directory exists."""
        if not os.path.isdir(self.args.test_dir):
            print(f"Error: Test directory '{self.args.test_dir}' not found")
            exit(1) # Exit if directory doesn't exist

    def collect_test_directories(self):
        """Find all directories containing test files."""
        self.test_dirs = []
        for root, dirs, files in os.walk(self.args.test_dir):
            #   # Look for Python test files starting with 'test_'
            if any(f.startswith('test_') and f.endswith('.py') for f in files):
                self.test_dirs.append(root)

    def load_tests(self):
        """Load all test cases from discovered directories."""
        loader = unittest.TestLoader()
        self.suite = unittest.TestSuite()
        for test_dir in self.test_dirs:
              # Discover and add tests to the suite
            self.suite.addTests(loader.discover(test_dir, pattern='test_*.py'))
        self.all_tests = list(self.flatten(self.suite))  # Flatten and list all tests

    def log_test_methods(self):
        """Write all test method names to a log file."""
        with open('all_test_methods.log', 'w') as f:
            for test in self.all_tests:
                method_name = test.id().split('.')[-1]   # Extract method name from test ID
                f.write(f"{method_name}\n")

    def run_tests(self):
        """Execute tests using custom runner and record timings."""
        self.start_time = time.time()
        BaseAPITest.test_start_time = self.start_time
        runner = CustomTestRunner(verbosity=2)
        self.result = runner.run(self.suite)  # Execute the tests
        self.end_time = time.time()

    def process_results(self):
        """Analyze test results and categorize outcomes."""
        self.test_statuses = []
        self.false_positives = []
        
        for test in self.all_tests:
            test_id = test.id()
            status = "Passed" # Default status is 'Passed'
            is_false_positive = False
            
            # Get test duration from different possible sources  (if available)
            duration = getattr(self.result, 'test_times', {}).get(test_id, 0.0)
            if hasattr(test, '_test_run_time'):
                duration = test._test_run_time

            # Check for failures/errors
            for failed_test, error_msg in self.result.failures + self.result.errors:
                if test_id == failed_test.id():
                    status = "Failed"
                      # Identify false positives based on specific error message
                    if "200" in str(error_msg) and "AssertionError" in str(error_msg):
                        is_false_positive = True
                        self.false_positives.append({
                            'test_id': test_id,
                            'error': str(error_msg)
                        })
                    break
            # Append test result details
            self.test_statuses.append({
                'id': test_id.split('.')[-1],  # Test method name
                'name': test_id,
                'status': status,
                'duration': duration,
                'is_false_positive': is_false_positive
            })

    def generate_env_info(self):
        """Collect environment metadata for reporting."""
        self.env_info = {
            'python_version': sys.version.split()[0],
            'platform': sys.platform,
            'requests_version': requests.__version__,
            'hostname': socket.gethostname(),
            'cpu_cores': os.cpu_count()
        }

    def generate_report(self):
        """Create and save the final test report."""
        report = DocxReportGenerator(
            test_errors=BaseAPITest.test_logger.test_errors,
            false_positives=self.false_positives,
            response_times=BaseAPITest.test_logger.response_times,
            test_result=self.result,
            test_statuses=self.test_statuses,
            start_time=self.start_time,
            end_time=self.end_time,
            base_url=BaseAPITest.base_url,
            env_info=self.env_info
        )
        report.generate()
        report.save('test_report.docx')


        report_data = {
        'test_errors': BaseAPITest.test_logger.test_errors,
        'false_positives': self.false_positives,
        'response_times': BaseAPITest.test_logger.response_times,
        'test_result': self.result,
        'test_statuses': self.test_statuses,
        'start_time': self.start_time,
        'end_time': self.end_time,
        'base_url': BaseAPITest.base_url,
        'env_info': self.env_info,
        'total_tests': self.result.testsRun if self.result else 0,
        'passed': (self.result.testsRun - len(self.result.failures) 
                 - len(self.result.errors) if self.result else 0),
        'failed': len(self.result.failures) + len(self.result.errors) 
                 if self.result else len(BaseAPITest.test_logger.test_errors)
    }
    
        html_report = HTMLReportGenerator(report_data)
        html_report.generate()

    def run(self):
        """Main execution flow coordinating all steps."""
        self.parse_arguments()
        self.validate_test_directory()
        self.collect_test_directories()
        
        if not self.test_dirs:
            print(f"No test files found in '{self.args.test_dir}'")
            exit(1)  # Exit if no test files are found

        self.load_tests()
        self.log_test_methods()
        self.run_tests()
        self.process_results()
        self.generate_env_info()
        self.generate_report()

def main():
    runner = TestRunner()
    runner.run()  # Run the test execution flow

if __name__ == '__main__':
    main()   # Execute main if the script is run directlys