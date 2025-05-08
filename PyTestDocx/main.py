import sys
import unittest

import time
import argparse
import os
from PyTestDocx import BaseAPITest, CustomTestResult, CustomTestRunner, ReportGenerator
from PyTestDocx.report import ReportGenerator
import socket
import requests

def flatten(suite):
    """
        Recursively yield every TestCase instance from a TestSuite.
        Used to collect all test cases from nested test suites.
    """
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from flatten(t)
        else:
            yield t

def collect_test_directories(base_dir):
    """
    Collect all directories containing test files in the given base directory.
    """
    test_dirs = []
    for root, dirs, files in os.walk(base_dir):
        if any(file.startswith('test_') and file.endswith('.py') for file in files):
            test_dirs.append(root)
    return test_dirs

def main():
    # Set up paths for project and parent directory
    # project_dir = os.path.dirname(os.path.abspath(__file__))  # Path to the current file
    # parent_dir  = os.path.dirname(project_dir)                # Parent directory
    # sys.path.insert(0, parent_dir)  # Add parent directory to sys.path for imports

    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run API tests')
    parser.add_argument('--test-dir', default='tests', 
                       help='Directory containing test files (default: tests)')
    args = parser.parse_args()

    # Validate the test directory exists
    if not os.path.isdir(args.test_dir):
        print(f"Error: Test directory '{args.test_dir}' not found")
        exit(1)

    # Record the start time before any tests begin
    BaseAPITest.test_start_time = time.time()

    # Collect all test directories recursively
    test_dirs = collect_test_directories(args.test_dir)
    if not test_dirs:
        print(f"No test files found in directory '{args.test_dir}' or its subdirectories.")
        exit(1)

    # Load test cases from all discovered directories
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_dir in test_dirs:
        suite.addTests(loader.discover(test_dir, pattern='test_*.py'))

    # Flatten the test suite and log each test method name
    all_tests = list(flatten(suite))
    with open('all_test_methods.log', 'w') as f:
        for test in all_tests:
            # test.id() returns 'tests.module.ClassName.test_method'
            full_id = test.id()
            method_name = full_id.split('.')[-1]
            f.write(f"{method_name}\n")

    # Run tests using the custom test runner
    runner = CustomTestRunner(verbosity=2)
    result = runner.run(suite)
    # Capture end time after all tests complete
    end_time = time.time()
    
    # Generate the report
    env_info = {
        'python_version': sys.version.split()[0],
        'platform': sys.platform,
        'requests_version': requests.__version__,
        'hostname': socket.gethostname(),
        'cpu_cores': os.cpu_count()
    }
    
    report = ReportGenerator(
        test_errors=BaseAPITest.test_logger.test_errors,  # Access through the logger instance
        response_times=BaseAPITest.test_logger.response_times,  # Also moved to logger
        test_result=result,
        start_time=BaseAPITest.test_start_time,
        end_time=end_time,
        base_url=BaseAPITest.base_url,
        env_info=env_info
    )
    report.generate()
    report.save('test_report.docx')
    
if __name__ == '__main__':
    main()