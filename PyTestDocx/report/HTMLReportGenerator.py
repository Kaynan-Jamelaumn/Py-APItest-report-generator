# [file name]: HTMLReportGenerator.py

import os
import json
import time
import logging
import statistics
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
import re 
# Set up logger for reporting errors or debug information
logger = logging.getLogger(__name__)

class HTMLReportGenerator:
    """Generates an HTML test report with charts and test summaries using Jinja2 templates."""

    def __init__(self, report_data):
        """
        Constructor: Initialize the report generator with input test data and load the template environment.
        
        Args:
            report_data (dict): A structured dictionary containing test execution results.
        """
        self.report_data = report_data

        # Resolve absolute path to the directory where this file lives
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the path where HTML templates are stored
        template_path = os.path.join(current_dir, 'templates')

        # Initialize Jinja2 environment with the given template path
        self.template_env = Environment(loader=FileSystemLoader(template_path), autoescape=True  )
        self.template_env.filters['extract_test_name'] = self._extract_test_name
        self.template_env.filters['extract_error_type'] = self._extract_error_type
        # Define output report file name
        self.output_file = 'test_report.html'

    @staticmethod
    def _extract_test_name(error_text):
        """Extract test name from error text."""
        match = re.search(r'Test:\s*(.*)', error_text)
        return match.group(1) if match else f"Error"

    @staticmethod
    def _extract_error_type(error_text):
        """Extract error type from error text."""
        match = re.search(r'Type:\s*(.*)', error_text)
        return match.group(1) if match else "Unknown Error"

    def _redact_passwords(self, error_text):
        """Replace password values in JSON request bodies with REDACTED."""
        # Match JSON format password fields
        password_pattern = re.compile(
            r'("password"\s*:\s*)(["\'])(.*?)(["\'])', 
            flags=re.IGNORECASE
        )
        return password_pattern.sub(r'\1\2REDACTED\4', str(error_text))


    def generate(self):
        """Render the report template with collected data and write the final HTML report."""
        try:
            # Add password redaction to errors before passing to context
            processed_errors = [self._redact_passwords(error) 
                              for error in self.report_data['test_errors']]
            # Prepare all contextual data needed by the template
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

            # Output rendered HTML to a file
            with open(self.output_file, 'w') as f:
                f.write(html_content)

        except Exception as e:
            # Log and re-raise exceptions for traceability
            logger.error(f"Failed to generate HTML report: {str(e)}")
            raise

    def _prepare_metadata(self):
        """Gather general metadata for display in the report header."""
        return {
            'project': os.getenv('PROJECT_NAME', 'N/A'),  # Pull from env variable if available
            'environment': os.getenv('ENVIRONMENT', 'Staging'),
            'generated': time.strftime('%B %d, %Y %H:%M:%S'),  # Human-readable timestamp
            'base_url': self.report_data['base_url']
        }

    def _prepare_summary_data(self):
        """Calculate summary metrics including pass rate and false positive count."""
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
        Aggregate data required for chart visualizations:
        - Error type frequency
        - Time-series of response times
        """
        error_types = defaultdict(int)
    
        for error in self.report_data['test_errors']:
            # Extract HTTP status code from error message using regex
            match = re.search(r'\b\d{3}\b', str(error))
            if match:
                status_code = match.group()
                error_types[f"{status_code} Error"] += 1
            elif "Timeout" in str(error):
                error_types["Timeout"] += 1
            else:
                error_types["Other Errors"] += 1

        # Process response times (moved outside of the error loop)
        response_times = []
        if 'response_times' in self.report_data:
            response_times = sorted(
                [rt for rt in self.report_data['response_times'] if rt.get('timestamp')],
                key=lambda x: x['timestamp']
            )
        
        return {
            'summary_labels': ['Passed', 'Failed'],
            'summary_data': [self.report_data['passed'], self.report_data['failed']],
            'error_labels': list(error_types.keys()),
            'error_data': list(error_types.values()),
            'response_times': response_times
        }

    def _prepare_execution_data(self):
        """Format start/end timestamps and compute total execution time."""
        duration = self.report_data['end_time'] - self.report_data['start_time']

        # Convert seconds to hours, minutes, seconds format
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        human_duration = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        return {
            'start': time.strftime('%Y-%m-%d %H:%M:%S', 
                                   time.localtime(self.report_data['start_time'])),
            'end': time.strftime('%Y-%m-%d %H:%M:%S', 
                                 time.localtime(self.report_data['end_time'])),
            'duration': duration,
            'human_duration': human_duration
        }


    def _prepare_response_stats(self):
        """
        Calculate statistical metrics for response durations with robust error handling.
        Returns a dictionary with average, median, min, max, count, and percentiles.
        Returns None if no valid response time data is available.
        """
        if not self.report_data.get('response_times'):
            return None

        try:
            # Extract valid durations (ignore None or invalid values)
            durations = []
            for rt in self.report_data['response_times']:
                try:
                    duration = float(rt['duration'])
                    if duration >= 0:  # Only accept non-negative durations
                        durations.append(duration)
                except (ValueError, KeyError, TypeError):
                    continue

            if not durations:
                return None

            # Basic statistics
            stats = {
                'average': statistics.mean(durations),
                'median': statistics.median(durations),
                'min': min(durations),
                'max': max(durations),
                'count': len(durations),
                'percentiles': {
                    'p90': 0,
                    'p95': 0,
                    'p99': 0
                }
            }

            # Calculate percentiles only if we have enough data points
            if len(durations) >= 10:
                try:
                    quantiles = statistics.quantiles(durations, n=100)
                    stats['percentiles']['p90'] = quantiles[89]  # 90th percentile
                    stats['percentiles']['p95'] = quantiles[94]  # 95th percentile
                    stats['percentiles']['p99'] = quantiles[98]  # 99th percentile
                except Exception:
                    # Fallback to simpler calculation if quantiles fails
                    sorted_durations = sorted(durations)
                    n = len(sorted_durations)
                    stats['percentiles']['p90'] = sorted_durations[int(0.9 * n) - 1]
                    stats['percentiles']['p95'] = sorted_durations[int(0.95 * n) - 1]
                    stats['percentiles']['p99'] = sorted_durations[int(0.99 * n) - 1]

            return stats

        except Exception as e:
            logger.error(f"Error calculating response statistics: {str(e)}")
            return None

        return stats
    def _prepare_environment_data(self):
        """Return system environment data such as Python version, platform, and hostname."""
        return {
            'python_version': self.report_data['env_info']['python_version'],
            'platform': self.report_data['env_info']['platform'],
            'requests_version': self.report_data['env_info']['requests_version'],
            'hostname': self.report_data['env_info']['hostname'],
            'cpu_cores': self.report_data['env_info']['cpu_cores'],
            'base_url': self.report_data['base_url']
        }
