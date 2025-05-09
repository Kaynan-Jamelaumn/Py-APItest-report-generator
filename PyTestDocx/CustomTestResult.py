import unittest
import time

# Custom Test Result Class to control error reporting
class CustomTestResult(unittest.TextTestResult):
    """
    Custom implementation of the unittest TextTestResult class to customize error reporting.
    Overrides the default behavior of addError to provide simplified error messages.
    Also tracks test durations for both passed and failed tests.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_times = {}  # Dictionary to store test durations
        self._test_start_times = {}  # Dictionary to track start times by test ID

    def startTest(self, test):
        """Record start time of test"""
        self._test_start_times[test.id()] = time.time()
        super().startTest(test)

    def _record_test_duration(self, test):
        """Internal method to record test duration"""
        test_id = test.id()
        if test_id in self._test_start_times:
            duration = time.time() - self._test_start_times[test_id]
            self.test_times[test_id] = duration
            test._test_run_time = duration

    def stopTest(self, test):
        """Record end time of test and calculate duration for successful tests"""
        self._record_test_duration(test)
        super().stopTest(test)

    def addFailure(self, test, err):
        """
        Handle failure reporting while recording test duration.
        Preserves the original failure reporting behavior.
        """
        self._record_test_duration(test)
        super().addFailure(test, err)

    def addError(self, test, err):
        """
        Handle error reporting by adding simplified error messages without tracebacks.
        Also records test duration before handling the error.
        """
        self._record_test_duration(test)
        ex_type, ex_value, _ = err
        error_message = f"{ex_type.__name__}: {ex_value}"
        self.errors.append((test, error_message))
        if self.showAll:
            self.stream.writeln("ERROR")
        elif self.dots:
            self.stream.write('E')