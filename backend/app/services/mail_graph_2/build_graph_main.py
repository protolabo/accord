import os
import time
import argparse
import psutil
from pathlib import Path
import json
from backend.app.services.mail_graph_2.graph_coordinator import GraphCoordinator


def memory_usage_gb():
    """Returns memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024 * 1024)  # Convert to GB


def log_memory_usage(label):
    """Logs current memory usage with a label."""
    print(f"Memory usage ({label}): {memory_usage_gb():.2f} GB")


class OptimizedMockDataService:
    """Service to read and manipulate test JSON data."""

    def __init__(self, mock_data_dir="mockdata", output_dir="output"):
        """
        Initializes the optimized test data service.

        Args:
            mock_data_dir: Path to directory containing test data files
            output_dir: Path to directory for output files
        """
        self.mock_data_dir = Path(mock_data_dir)
        self.output_dir = Path(output_dir)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Validate test data directory
        if not self.mock_data_dir.exists():
            raise ValueError(f"Test data directory '{mock_data_dir}' does not exist")

    def get_all_email_batches(self, max_emails=None):
        """
        Reads all emails at once.

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
                    print(f"Maximum email limit reached ({max_emails})")
                    break

            except Exception as e:
                print(f"Error reading {batch_file.name}: {str(e)}")

        print(f"Total: {len(all_emails)} emails loaded")
        return all_emails


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Build email graphs with optimized performance.')

    parser.add_argument('--input-dir', type=str, default='mockdata',
                        help='Directory containing test JSON data files')

    parser.add_argument('--output-dir', type=str, default='output/graph',
                        help='Directory for saving graph output')

    parser.add_argument('--central-user', type=str, default='alexandre.dupont@acmecorp.com',
                        help='Email of the central user for the graph')

    parser.add_argument('--max-emails', type=int, default=None,
                        help='Maximum number of emails to process (default: all)')

    return parser.parse_args()


def main():
    """Main function to build email graphs."""
    args = parse_args()

    # Record start time
    start_time = time.time()
    log_memory_usage("start")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize services to manipulate JSON test data
    mock_service = OptimizedMockDataService(args.input_dir, args.output_dir)

    # Load test data
    emails = mock_service.get_all_email_batches(max_emails=args.max_emails)

    log_memory_usage("after loading emails")
    print(f"Loaded {len(emails)} emails in {time.time() - start_time:.2f} seconds")

    # Initialize graph coordinator
    graph_coordinator = GraphCoordinator(
        central_user_email=args.central_user,
        output_dir=args.output_dir
    )

    build_start_time = time.time()

    #### ---------  Build graphs using the coordinator --------- ####
    result = graph_coordinator.build_graphs(emails)

    build_time = time.time() - build_start_time
    log_memory_usage("after building graphs")

    # Record overall stats
    stats = {
        "runtime_seconds": time.time() - start_time,
        "build_time_seconds": build_time,
        "emails_processed": len(emails),
        "processing_rate": len(emails) / build_time if build_time > 0 else 0,
        "peak_memory_gb": memory_usage_gb(),
    }

    # Merge with result metadata
    if isinstance(result, dict):
        stats.update(result)

    # Print summary
    print("\nGraph building complete!")
    print(
        f"Total runtime: {stats['runtime_seconds']:.2f} seconds ({stats['runtime_seconds'] / 60:.2f} minutes)")
    print(f"Build time: {build_time:.2f} seconds ({build_time / 60:.2f} minutes)")
    print(f"Processing rate: {stats['processing_rate']:.2f} emails/second")
    print(f"Peak memory usage: {stats['peak_memory_gb']:.2f} GB")
    print(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback

        traceback.print_exc()