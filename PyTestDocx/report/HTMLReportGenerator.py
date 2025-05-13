import os
import json
import time
import logging
import statistics  # For calculating statistical metrics
from jinja2 import Environment, FileSystemLoader # For templating HTML reports
from collections import defaultdict
import re 

# Set up logger for reporting errors or debug information
logger = logging.getLogger(__name__)

class HTMLReportGenerator:
    """
    Generates an HTML test report with charts and test summaries using Jinja2 templates.
    """

    def __init__(self, report_data):
        """
        Initialize the report generator with input test data and load the template environment.
        
        Args:
            report_data (dict): A structured dictionary containing test execution results.
        """
        self.report_data = report_data

        # Resolve absolute path to the directory where this file lives
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the path where HTML templates are stored
        template_path = os.path.join(current_dir, 'templates')

        # Initialize Jinja2 environment with the given template path
        self.template_env = Environment(loader=FileSystemLoader(template_path), autoescape=True)
        self.template_env.filters['extract_test_name'] = self._extract_test_name
        self.template_env.filters['extract_error_type'] = self._extract_error_type
        
        # Define output report file name
        self.output_file = 'test_report.html'

    @staticmethod
    def _extract_test_name(error_text):
        """
        Extract test name from error text using a regex pattern.

        Args:
            error_text (str): The error message text.
        
        Returns:
            str: Extracted test name or "Error" if not found.
        """
        match = re.search(r'Test:\s*(.*)', error_text)
        return match.group(1) if match else "Error"

    @staticmethod
    def _extract_error_type(error_text):
        """
        Extract error type from error text using a regex pattern.

        Args:
            error_text (str): The error message text.
        
        Returns:
            str: Extracted error type or "Unknown Error" if not found.
        """
        match = re.search(r'Type:\s*(.*)', error_text)
        return match.group(1) if match else "Unknown Error"

    def _redact_passwords(self, error_text):
        """
        Replace password values in JSON request bodies with "REDACTED".

        Args:
            error_text (str): The error message text.
        
        Returns:
            str: Error message with passwords redacted.
        """
        password_pattern = re.compile(r'("password"\s*:\s*)(["\'])(.*?)(["\'])', flags=re.IGNORECASE)
        return password_pattern.sub(r'\1\2REDACTED\4', str(error_text))

    def generate(self):
        """
        Render the report template with collected data and write the final HTML report.
        """
        try:
            # Redact passwords in error messages
            processed_errors = [self._redact_passwords(error) for error in self.report_data['test_errors']]
            
            # Prepare contextual data for the HTML template
            context = {
                'meta': self._prepare_metadata(),
                'summary': self._prepare_summary_data(),
                'charts': self._prepare_chart_data(),
                'errors': processed_errors,
                'environment': self._prepare_environment_data(),
                'execution': self._prepare_execution_data(),
                'test_cases': self.report_data['test_statuses'],
                'response_stats': self._prepare_response_stats(),
                'false_positives': self.report_data.get('false_positives', [])
            }

            # Load and render the HTML base template
            template = self.template_env.get_template('base.html')
            html_content = template.render(context)

            # Save rendered HTML content to the output file
            with open(self.output_file, 'w') as f:
                f.write(html_content)

        except Exception as e:
            # Log and re-raise any exceptions encountered during generation
            logger.error(f"Failed to generate HTML report: {str(e)}")
            raise

    def _prepare_metadata(self):
        """
        Gather general metadata for display in the report header.

        Returns:
            dict: Metadata including project name, environment, and generation time.
        """
        return {
            'project': os.getenv('PROJECT_NAME', 'N/A'),
            'environment': os.getenv('ENVIRONMENT', 'Staging'),
            'generated': time.strftime('%B %d, %Y %H:%M:%S'),
            'base_url': self.report_data['base_url']
        }

    def _prepare_summary_data(self):
        """
        Calculate summary metrics including pass rate and false positive count.

        Returns:
            dict: Summary data containing total, passed, failed, and pass rate.
        """
        total = self.report_data['total_tests']
        passed = self.report_data['passed']
        failed = self.report_data['failed']

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total) * 100 if total > 0 else 0,
            'false_positives': len(self.report_data.get('false_positives', []))
        }

    def _prepare_chart_data(self):
        """
        Aggregate data required for chart visualizations.

        Returns:
            dict: Chart data including error types and response times.
        """
        error_types = defaultdict(int)
        
        # Categorize errors by type or status code
        for error in self.report_data['test_errors']:
            match = re.search(r'\b\d{3}\b', str(error))
            if match:
                status_code = match.group()
                error_types[f"{status_code} Error"] += 1
            elif "Timeout" in str(error):
                error_types["Timeout"] += 1
            else:
                error_types["Other Errors"] += 1

        # Process response times for charts
        response_times = []
        for index, rt in enumerate(self.report_data.get('response_times', [])):
            ts = rt.get('timestamp')
            dur = rt.get('duration')  
            name = self.report_data['test_statuses'][index].get('name', 'Unknown Test')
            if ts is None or dur is None:
                continue
            timestamp_ms = float(ts) * 1000 if ts < 1e12 else float(ts)
            duration_ms = float(dur) * 1000
            formatted = time.strftime('%m/%d/%Y %H:%M', time.localtime(timestamp_ms / 1000))
            response_times.append({'timestamp': timestamp_ms, 'formatted_time': formatted, 'duration': duration_ms, 'test_name': name })
        
        response_times.sort(key=lambda x: x['timestamp'])

        return {
            'summary_labels': ['Passed', 'Failed'],
            'summary_data': [self.report_data.get('passed', 0), self.report_data.get('failed', 0)],
            'error_labels': list(error_types.keys()),
            'error_data': list(error_types.values()),
            'response_times': response_times,
        }

    def _prepare_execution_data(self):
        """
        Format start and end timestamps and compute total execution time.

        Returns:
            dict: Execution metadata including start time, end time, and duration.
        """
        duration = self.report_data['end_time'] - self.report_data['start_time']
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        human_duration = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        return {
            'start': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.report_data['start_time'])),
            'end': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.report_data['end_time'])),
            'duration': duration,
            'human_duration': human_duration
        }

    def _prepare_response_stats(self):
        """
        Calculate statistical metrics for response durations.

        Returns:
            dict: Response time statistics including averages, percentiles, and counts.
        """
        durations = [float(rt['duration']) for rt in self.report_data.get('response_times', []) if rt.get('duration') is not None]
        if not durations:
            return None

        stats = {
            'average': statistics.mean(durations),
            'median': statistics.median(durations),
            'min': min(durations),
            'max': max(durations),
            'count': len(durations),
            'percentiles': {
                'p90': statistics.quantiles(durations, n=100)[89] if len(durations) >= 10 else None,
                'p95': statistics.quantiles(durations, n=100)[94] if len(durations) >= 10 else None,
                'p99': statistics.quantiles(durations, n=100)[98] if len(durations) >= 10 else None
            }
        }

        return stats

    def _prepare_environment_data(self):
        """
        Gather system environment information for display in the report.

        Returns:
            dict: Environment metadata including Python version, platform, and hostname.
        """
        return {
            'python_version': self.report_data['env_info']['python_version'],
            'platform': self.report_data['env_info']['platform'],
            'requests_version': self.report_data['env_info']['requests_version'],
            'hostname': self.report_data['env_info']['hostname'],
            'cpu_cores': self.report_data['env_info']['cpu_cores'],
            'base_url': self.report_data['base_url']
        }