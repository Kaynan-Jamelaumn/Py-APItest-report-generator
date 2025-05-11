# [file name]: HTMLReportGenerator.py
import os
import json
import time
import logging
import statistics
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
logger = logging.getLogger(__name__)

class HTMLReportGenerator:
    """Generates interactive HTML reports with JavaScript visualizations"""
    
    def __init__(self, report_data):
        """
        Initialize HTML report generator with test data
        
        Args:
            report_data (dict): Contains all test result data needed for the report
        """
        self.report_data = report_data
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Look for templates in a 'templates' subdirectory of this file's location
        template_path = os.path.join(current_dir, 'templates')
        self.template_env = Environment(loader=FileSystemLoader(template_path))
        self.output_file = 'test_report.html'

    def generate(self):
        """Generate the complete HTML report"""
        try:
            # Prepare data for templating
            context = {
                'meta': self._prepare_metadata(),
                'summary': self._prepare_summary_data(),
                'charts': self._prepare_chart_data(),
                'errors': self.report_data['test_errors'],
                'environment': self._prepare_environment_data(),
                'execution': self._prepare_execution_data(),
                'test_cases': self.report_data['test_statuses'],
                'response_stats': self._prepare_response_stats(),
                'false_positives': self.report_data.get('false_positives', [])
            }

            # Render main template
            template = self.template_env.get_template('base.html')
            html_content = template.render(context)
            
            # Write to file
            with open(self.output_file, 'w') as f:
                f.write(html_content)
                
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {str(e)}")
            raise

    def _prepare_metadata(self):
        return {
            'project': os.getenv('PROJECT_NAME', 'N/A'),
            'environment': os.getenv('ENVIRONMENT', 'Staging'),
            'generated': time.strftime('%B %d, %Y %H:%M:%S'),
            'base_url': self.report_data['base_url']
        }

    def _prepare_summary_data(self):
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
        # Prepare data for JavaScript charts
        error_types = defaultdict(int)
        for error in self.report_data['test_errors']:
            # Same error classification logic as DOCX report
            if "400" in str(error):
                error_types["Bad Request (400)"] += 1
            elif "401" in str(error):
                error_types["Unauthorized (401)"] += 1
            elif "404" in str(error):
                error_types["Not Found (404)"] += 1
            elif "500" in str(error):
                error_types["Server Error (500)"] += 1
            elif "Timeout" in str(error):
                error_types["Timeout"] += 1
            else:
                error_types["Other Errors"] += 1

        # Prepare response time data for charts
        response_times = []
        if 'response_times' in self.report_data:
            response_times = sorted(
                [{'duration': rt['duration'], 'timestamp': rt.get('timestamp')} 
                 for rt in self.report_data['response_times']],
                key=lambda x: x['timestamp'] if x.get('timestamp') else 0
            )

        return {
            'summary_labels': ['Passed', 'Failed'],
            'summary_data': [self.report_data['passed'], self.report_data['failed']],
            'error_labels': list(error_types.keys()),
            'error_data': list(error_types.values()),
            'response_times': response_times
        }

    def _prepare_execution_data(self):
        duration = self.report_data['end_time'] - self.report_data['start_time']
        
        # Calculate human-readable duration
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
        if not self.report_data.get('response_times'):
            return None
            
        durations = [rt['duration'] for rt in self.report_data['response_times']]
        avg = statistics.mean(durations) if durations else 0
        median = statistics.median(durations) if durations else 0
        min_val = min(durations) if durations else 0
        max_val = max(durations) if durations else 0
        
        # Calculate percentiles
        try:
            percentiles = {
                'p90': statistics.quantiles(durations, n=10)[-1],
                'p95': statistics.quantiles(durations, n=20)[-1],
                'p99': statistics.quantiles(durations, n=100)[-1]
            }
        except:
            percentiles = {'p90': 0, 'p95': 0, 'p99': 0}
        
        return {
            'average': avg,
            'median': median,
            'min': min_val,
            'max': max_val,
            'count': len(durations),
            'percentiles': percentiles
        }
    
    def _prepare_environment_data(self):
        return {
            'python_version': self.report_data['env_info']['python_version'],
            'platform': self.report_data['env_info']['platform'],
            'requests_version': self.report_data['env_info']['requests_version'],
            'hostname': self.report_data['env_info']['hostname'],
            'cpu_cores': self.report_data['env_info']['cpu_cores'],
            'base_url': self.report_data['base_url']
        }