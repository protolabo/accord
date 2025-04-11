import json
from pathlib import Path
import time


class OptimizedMockDataService:
    """Service to efficiently read and manipulate mock JSON data."""

    def __init__(self, mock_data_dir="mockdata", output_dir="output"):
        """
        Initialize the optimized mock data service.

        Args:
            mock_data_dir: Path to directory containing mock data files
            output_dir: Path to directory for output files
        """
        self.mock_data_dir = Path(mock_data_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Validate mock data directory
        if not self.mock_data_dir.exists():
            raise ValueError(f"Mock data directory '{mock_data_dir}' does not exist")

    def get_all_email_batches(self, max_emails=None):
        """
        Read all emails at once (less memory efficient but compatible with existing code).
        Use with caution for large datasets.
        
        Args:
            max_emails: Maximum number of emails to read (None for all)
            
        Returns:
            list: All emails
        """
        all_emails = []
        batch_files = sorted(list(self.mock_data_dir.glob("*.json")))
        
        if not batch_files:
            print(f"No JSON files found in {self.mock_data_dir}")
            return all_emails
            
        print(f"Reading {len(batch_files)} files...")
        
        for batch_file in batch_files:
            try:
                print(f"Reading {batch_file.name}...")
                start_time = time.time()
                
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                
                read_time = time.time() - start_time
                print(f"Read {len(batch_data)} emails from {batch_file.name} in {read_time:.2f} seconds")
                
                all_emails.extend(batch_data)
                
                # Check if we've reached the maximum
                if max_emails and len(all_emails) >= max_emails:
                    all_emails = all_emails[:max_emails]
                    print(f"Reached maximum emails limit ({max_emails})")
                    break
                
            except Exception as e:
                print(f"Error reading {batch_file.name}: {str(e)}")
        
        print(f"Total: {len(all_emails)} emails loaded")
        return all_emails

