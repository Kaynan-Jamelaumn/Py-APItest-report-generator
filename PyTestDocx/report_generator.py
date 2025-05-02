from docx import Document
from docx.shared import RGBColor, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
import matplotlib.pyplot as plt
import logging
import time
import os

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates comprehensive Word document reports for API test results"""
    
    def __init__(self, test_errors, response_times, test_result, 
                 start_time, end_time, base_url, env_info):
        """
        Initialize report generator with test data
        
        Args:
            test_errors (list): List of error messages from failed tests
            response_times (list): List of API response times
            test_result (unittest.TestResult): Test execution results
            start_time (float): Test execution start timestamp
            end_time (float): Test execution end timestamp
            base_url (str): Base API URL tested
            env_info (dict): Environment information
        """
        self.test_errors = test_errors
        self.response_times = response_times
        self.test_result = test_result
        self.start_time = start_time
        self.end_time = end_time
        self.base_url = base_url
        self.env_info = env_info
        self.doc = None  # Will hold the Word document object

        # Calculate test metrics
        self.total_tests = test_result.testsRun if test_result else 0
        self.passed = self.total_tests - len(test_result.failures) - len(test_result.errors) if test_result else 0
        self.failed = len(test_result.failures) + len(test_result.errors) if test_result else len(test_errors)

    def generate(self):
        """Generate the complete report document with all sections"""
        self._create_base_document()  # Initialize document structure
        self._add_summary_table()     # Add test summary table
        self._add_summary_chart()     # Add pie chart visualization
        self._add_response_time_chart()  # Add response time analysis
        self._add_environment_info()  # Add environment details
        self._add_execution_info()    # Add timing information
        self._add_error_section()     # Add detailed error reports

    def save(self, filename):
        """Save the generated document to file"""
        self.doc.save(filename)

    def _create_base_document(self):
        """Create the basic document structure with header and footer"""
        self.doc = Document()
        self._add_header()  # Add report title
        self._add_footer()  # Add page numbering

    def _add_header(self):
        """Add styled document header with title and timestamp"""
        # Main report title
        header = self.doc.add_heading('API Test Automation Report', level=0)
        header_run = header.runs[0]
        header_run.font.color.rgb = RGBColor(0x00, 0x33, 0x66)  # Dark blue
        header_run.font.size = Pt(16)
        header_run.bold = True
        
        # Subtitle
        subheader = self.doc.add_heading('Test Execution Summary', level=1)
        subheader_run = subheader.runs[0]
        subheader_run.font.color.rgb = RGBColor(0x1E, 0x90, 0xFF)  # Dodger blue
        subheader_run.font.size = Pt(12)
        
        # Timestamp
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        timestamp = self.doc.add_paragraph(f"Report generated on: {current_time}")
        timestamp.style = self.doc.styles['Intense Quote']

    def _add_footer(self):
        """Add page number footer to document"""
        section = self.doc.sections[0]
        footer = section.footer
        paragraph = footer.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT  # Right-align footer
        
        # Create page number field using Word XML
        run = paragraph.add_run()
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'begin')
        run._r.append(fldChar)
        
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = 'PAGE'
        run._r.append(instrText)
        
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar)

    def _add_summary_table(self):
        """Add table showing test pass/fail summary"""
        table = self.doc.add_table(rows=1, cols=3)
        table.style = self.doc.styles['Light Shading Accent 1']  # Use style name instead of style_id
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Total Tests'
        hdr_cells[1].text = 'Passed'
        hdr_cells[2].text = 'Failed'
        
        # Data row
        row_cells = table.add_row().cells
        row_cells[0].text = str(self.total_tests)
        row_cells[1].text = str(self.passed)
        row_cells[2].text = str(self.failed)
        
        # Color coding for passed/failed counts
        row_cells[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x00, 0x80, 0x00)  # Green
        row_cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0x00, 0x00)  # Red

    def _add_summary_chart(self):
        """Generate and insert pie chart showing test results"""
        try:
            # Chart data
            labels = ['Passed', 'Failed']
            sizes = [self.passed, self.failed]
            colors = ['#4CAF50', '#FF5252']  # Green and red
            
            # Create pie chart
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures circular pie
            
            # Save chart to temporary file
            chart_path = "test_summary_chart.png"
            plt.savefig(chart_path, bbox_inches='tight')
            plt.close(fig)
            
            # Insert chart into document
            self.doc.add_paragraph("Test Results Overview:")
            self.doc.paragraphs[-1].style = self.doc.styles['Heading 2']
            self.doc.add_picture(chart_path, width=Pt(300))  # 300 points wide
            os.remove(chart_path)  # Clean up temporary file
        except Exception as e:
            logger.error(f"Failed to generate chart: {str(e)}")

    def _add_response_time_chart(self):
        """Generate and insert histogram of API response times grouped by endpoint"""
        try:
            if not self.response_times:
                return  # Skip if no response time data

            # Group response times by endpoint
            from collections import defaultdict
            endpoint_times = defaultdict(list)
            for entry in self.response_times:
                endpoint_times[entry['endpoint']].append(entry['duration'])

            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Plot each endpoint's response times
            colors = ['#4CAF50', '#2196F3', '#FF5722', '#9C27B0']
            for i, (endpoint, times) in enumerate(endpoint_times.items()):
                plt.plot(times, marker='o', linestyle='-', 
                        color=colors[i % len(colors)], 
                        label=f"{endpoint} ({len(times)} calls)")

            plt.xlabel('Request Sequence')
            plt.ylabel('Response Time (seconds)')
            plt.title('Endpoint Response Times Over Test Execution')
            plt.legend()
            plt.grid(True)

            # Save and insert chart
            chart_path = "response_time_chart.png"
            plt.savefig(chart_path, bbox_inches='tight')
            plt.close()
            
            self.doc.add_paragraph("Endpoint Response Time Analysis:")
            self.doc.paragraphs[-1].style = self.doc.styles['Heading 2']
            self.doc.add_picture(chart_path, width=Pt(400))
            os.remove(chart_path)
        except Exception as e:
            logger.error(f"Failed to generate response time chart: {str(e)}")
            raise  # Re-raise to see error in test output
    def _add_environment_info(self):
        """Add table showing test environment details"""
        self.doc.add_heading('Environment Information', level=1)
        env_table = self.doc.add_table(rows=6, cols=2)
        env_table.style = self.doc.styles['Light List Accent 1']
        
        # Environment data to display
        env_info = [
            ("Base API URL", self.base_url),
            ("Python Version", self.env_info['python_version']),
            ("Platform", self.env_info['platform']),
            ("Requests Version", self.env_info['requests_version']),
            ("Hostname", self.env_info['hostname']),
            ("CPU Cores", self.env_info['cpu_cores']),
        ]
        
        # Populate table
        for i, (label, value) in enumerate(env_info):
            env_table.rows[i].cells[0].text = label
            env_table.rows[i].cells[1].text = str(value)
            env_table.rows[i].cells[0].paragraphs[0].runs[0].bold = True  # Bold labels

    def _add_execution_info(self):
        """Add section with test execution timing information"""
        if self.start_time:
            total_duration = self.end_time - self.start_time
            minutes, seconds = divmod(total_duration, 60)
            
            self.doc.add_heading('Execution Information', level=1)
            exec_table = self.doc.add_table(rows=3, cols=2)
            exec_table.style = self.doc.styles['Light List Accent 1']
            
            # Start time row
            exec_table.rows[0].cells[0].text = "Test Execution Started"
            exec_table.rows[0].cells[1].text = time.strftime('%Y-%m-%d %H:%M:%S', 
                                                          time.localtime(self.start_time))
            
            # End time row
            exec_table.rows[1].cells[0].text = "Test Execution Finished"
            exec_table.rows[1].cells[1].text = time.strftime('%Y-%m-%d %H:%M:%S', 
                                                           time.localtime(self.end_time))
            
            # Duration row
            exec_table.rows[2].cells[0].text = "Total Test Duration"
            exec_table.rows[2].cells[1].text = f"{int(minutes)} minutes {seconds:.2f} seconds"
            
            # Bold all labels
            for row in exec_table.rows:
                row.cells[0].paragraphs[0].runs[0].bold = True

    def _add_error_section(self):
        """Add detailed error reports section"""
        self.doc.add_page_break()  # Start new page for errors
        self.doc.add_heading('Test Errors Report', level=1)
        self.doc.add_paragraph(f"The following {len(self.test_errors)} test(s) encountered errors:")
        self.doc.paragraphs[-1].style = self.doc.styles['Intense Quote']
        
        # Set monospace font for error output
        style = self.doc.styles['Normal']
        style.font.name = 'Consolas'
        style.font.size = Pt(10)
        
        # Add each error with formatting
        for error in self.test_errors:
            self._add_single_error_entry(error)
            self.doc.add_paragraph()  # Add spacing between errors

    def _add_single_error_entry(self, error):
        """Format and add a single error entry with syntax highlighting"""
        error_lines = error.strip().split("\n")
        for line in error_lines:
            paragraph = self.doc.add_paragraph()
            
            # Apply different formatting based on line content
            if line.startswith("Test Description:"):
                run = paragraph.add_run(line)
                run.bold = True
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0x00, 0x00, 0x8B)  # Dark blue
                
            elif line.startswith("Test:"):
                run = paragraph.add_run(line)
                run.bold = True
                run.font.color.rgb = RGBColor(0x00, 0x00, 0xFF)  # Blue
                
            elif line.startswith("Error Type:"):
                run = paragraph.add_run(line)
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)  # Red
                
            elif line.startswith("Error Message:"):
                run = paragraph.add_run(line)
                run.italic = True
                run.font.color.rgb = RGBColor(0x8B, 0x00, 0x00)  # Dark red
                self._add_error_message_border(paragraph)  # Add decorative border
                
            elif line.startswith("Request Body:"):
                run = paragraph.add_run(line)
                run.bold = True
                run.font.color.rgb = RGBColor(0x80, 0x00, 0x80)  # Purple
                
            elif line.startswith("Response Status:") or line.startswith("Response URL:"):
                run = paragraph.add_run(line)
                run.font.color.rgb = RGBColor(0x00, 0x80, 0x00)  # Green
                
            elif line.startswith("Response Content:"):
                run = paragraph.add_run(line)
                run.underline = True
                run.font.color.rgb = RGBColor(0x00, 0x80, 0x80)  # Teal
                
            elif line.startswith("----------------------------------------"):
                self.doc.add_paragraph()  # Add extra spacing for separators
                
            else:
                # Color JSON content differently
                if line.strip().startswith(("{", "[")):
                    run = paragraph.add_run(line)
                    run.font.color.rgb = RGBColor(0xA5, 0x2A, 0x2A)  # Brown
                else:
                    paragraph.add_run(line)  # Default formatting

    def _add_error_message_border(self, paragraph):
        """Add decorative border around error messages"""
        p_pr = paragraph._p.get_or_add_pPr()
        borders = OxmlElement('w:pBorders')
        
        # Add borders to all sides
        for border_side in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:{border_side}')
            border.set(qn('w:val'), 'single')  # Single line
            border.set(qn('w:sz'), '12')       # Size
            border.set(qn('w:space'), '0')     # No spacing
            border.set(qn('w:color'), '8B0000')  # Dark red color
            borders.append(border)
        
        p_pr.append(borders)