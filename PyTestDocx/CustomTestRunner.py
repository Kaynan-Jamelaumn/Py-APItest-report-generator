import unittest
from PyTestDocx import CustomTestResult
# Custom Test Runner to use our result class
class CustomTestRunner(unittest.TextTestRunner): #it controls how the entire collection of tests is executed
    """
    Custom implementation of the unittest TextTestRunner class to use the CustomTestResult.
    Controls how the entire collection of tests is executed and allows tracking results across test cases.
    """
    def _makeResult(self):
        #Override to return an instance of CustomTestResult.
        return CustomTestResult(
            self.stream, self.descriptions, self.verbosity
        )
    
    def run(self, test):
        #Execute the given test suite and propagate results to all test cases.
        
        result = super().run(test)
        # Store the result in all test cases and their class
        for test_case in self._get_all_test_cases(test):
            test_case._result = result
            test_case.__class__._result = result
        return result
    def _get_all_test_cases(self, test):
        """Recursively retrieve all individual test cases from a given test suite"""
        test_cases = []
        if isinstance(test, unittest.TestCase):
            test_cases.append(test)
        elif isinstance(test, unittest.TestSuite):
            for t in test:
                test_cases.extend(self._get_all_test_cases(t))
        return test_cases
