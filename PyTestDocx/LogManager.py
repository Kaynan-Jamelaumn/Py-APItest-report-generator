import os
import logging

class LogManager:
    """Handles test logging, error tracking, and file management."""
    
    ERROR_LOG_FILE = "test_errors.log"      # File for error logs
    ERROR_DOCX_FILE = "test_errors.docx"    # File for generated report
    EXECUTED_LOG_FILE = "executed_tests.log" # File for test execution log
    
    def __init__(self):
        self.test_errors = []
        self.response_times = []
        self._configure_logging()

    def _configure_logging(self):
        """Configure logging handlers and clear old files."""
        self._clear_log_files()
        file_handler = logging.FileHandler(self.ERROR_LOG_FILE)
        file_handler.setLevel(logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.addHandler(file_handler)

    def _clear_log_files(self):
        """Initialize log files with empty content."""
        with open(self.ERROR_LOG_FILE, 'w') as f:
            f.write("")
        if os.path.exists(self.ERROR_DOCX_FILE):
            os.remove(self.ERROR_DOCX_FILE)
        with open(self.EXECUTED_LOG_FILE, 'w') as f:
            f.write("")

    def log_executed_test(self, test_id, status):
        """Log test execution attempts and results."""
        with open(self.EXECUTED_LOG_FILE, 'a') as f:
            f.write(f"{status}: {test_id}\n")

    def log_test_error(self, log_entry):
        """Record errors and write to error log."""
        logger = logging.getLogger(__name__)
        logger.error(log_entry)
        self.test_errors.append(log_entry)