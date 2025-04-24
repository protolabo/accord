import os
import time
import argparse
import psutil
from backend.app.services.mail_graph.graph_coordinator import GraphCoordinator
from optimized_mock_data_service import OptimizedMockDataService


def memory_usage_gb():
    """Return the memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024 * 1024)  # Convert to GB


def log_memory_usage(label):
    """Log current memory usage with a label."""
    print(f"Memory usage ({label}): {memory_usage_gb():.2f} GB")

def main(input_dir = "'../../data/mockdata",output_dir = "'../../data/mockdata/output/graph",central_user = "alexandre.dupont@acmecorp.com",max_emails = None):
    """Main function to build email graph."""

    # Record start time
    start_time = time.time()
    log_memory_usage("start")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize services to manipulate mock JSON data.
    mock_service = OptimizedMockDataService(input_dir, output_dir)

    # Load mock data
    emails = mock_service.get_all_email_batches(max_emails= max_emails)

    log_memory_usage("after loading emails")
    print(f"Loaded {len(emails)} emails in {time.time() - start_time:.2f} seconds")

    # Initialize graph coordinator
    graph_coordinator = GraphCoordinator(
        central_user_email= central_user,
        output_dir= output_dir
    )


    build_start_time = time.time()

    #### ---------  Build graph using the coordinator --------- ####
    result = graph_coordinator.build_graph_exec(emails)

    build_time = time.time() - build_start_time
    log_memory_usage("after building graph")

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
    print("\nGraph build complete!")
    print(f"Total runtime: {stats['runtime_seconds']:.2f} seconds ({stats['runtime_seconds'] / 60:.2f} minutes)")
    print(f"Build time: {build_time:.2f} seconds ({build_time / 60:.2f} minutes)")
    print(f"Processing rate: {stats['processing_rate']:.2f} emails/second")
    print(f"Peak memory usage: {stats['peak_memory_gb']:.2f} GB")
    print(f"Results saved to: {output_dir}")


#if __name__ == "__main__":
#    main()
