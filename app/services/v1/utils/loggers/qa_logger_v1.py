import csv
from datetime import datetime
import os


class QALogger:
    def __init__(self, filename="qa_logs.csv"):
        self.filename = filename
        self.setup_csv()

    def setup_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'question', 'response'])

    def log_qa(self, question: str, response: str):
        """Log a question-answer pair to CSV"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, question, response])
