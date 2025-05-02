import unittest

# Custom Test Result Class to control error reporting
class CustomTestResult(unittest.TextTestResult):
    """
    Custom implementation of the unittest TextTestResult class to customize error reporting.
    Overrides the default behavior of addError to provide simplified error messages.
    """
    def addError(self, test, err):
        """
        Handle error reporting by adding simplified error messages without tracebacks.
        """
        ex_type, ex_value, _ = err
        error_message = f"{ex_type.__name__}: {ex_value}"
        self.errors.append((test, error_message))
        if self.showAll:
            self.stream.writeln("ERROR")
        elif self.dots:
            self.stream.write('E')