import os
import time
import argparse
import json
import psutil
from optimized_graph_builder import OptimizedEmailGraphBuilder
from optimized_mock_data_service import OptimizedMockDataService

def memory_usage_gb():
    """Return the memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024 * 1024)  # Convert to GB

def log_memory_usage(label):
    """Log current memory usage with a label."""
    print(f"Memory usage ({label}): {memory_usage_gb():.2f} GB")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Build an email graph with optimized performance.')
    
    parser.add_argument('--input-dir', type=str, default='mockdata',
                        help='Directory containing mock data JSON files')
    
    parser.add_argument('--output-dir', type=str, default='output/graph',
                        help='Directory for saving graph output')

    # default user = alexandre.dupont@acmecorp.com
    parser.add_argument('--central-user', type=str, default='alexandre.dupont@acmecorp.com',
                        help='Email of the central user for the graph')
    
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Number of emails to process in each batch')
    
    parser.add_argument('--max-emails', type=int, default=None,
                        help='Maximum number of emails to process (default: all)')
    
    parser.add_argument('--processes', type=int, default=None,
                        help='Number of parallel processes (default: auto)')

    
    return parser.parse_args()

def run_profiler(func, *args, **kwargs):
    """Run with profiling if enabled."""
    try:
        import cProfile
        import pstats
        import io
        
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(30)
        
        print("Performance Profile:")
        print(s.getvalue())
        
        return result
    except ImportError:
        print("cProfile not available. Running without profiling.")
        return func(*args, **kwargs)

def main():
    """Main function to build email graph."""
    args = parse_args()
    
    # Record start time
    start_time = time.time()
    log_memory_usage("start")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize services to manipulate mock JSON data.
    mock_service = OptimizedMockDataService(args.input_dir, args.output_dir)
    
    # Load mock data
    print(f"Loading emails from {args.input_dir}...")
    emails = mock_service.get_all_email_batches(max_emails=args.max_emails)
    
    log_memory_usage("after loading emails")
    print(f"Loaded {len(emails)} emails in {time.time() - start_time:.2f} seconds")
    
    # Initialize graph builder
    graph_builder = OptimizedEmailGraphBuilder(
        central_user_email=args.central_user,
        output_dir=args.output_dir
    )
    
    # Save run configuration
    config = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_dir": args.input_dir,
        "output_dir": args.output_dir,
        "central_user": args.central_user,
        "batch_size": args.batch_size,
        "max_emails": args.max_emails,
        "processes": args.processes,
        "total_emails": len(emails)
    }

    # save configuration in json file
    config_file = os.path.join(args.output_dir, "run_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    

    build_start_time = time.time()
    
    # some mode of running

    # two-phase mode
    result = run_profiler(graph_builder.build_graph_two_phase, emails)
    
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
    
    # Save stats
    stats_file = os.path.join(args.output_dir, "performance_stats.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\nGraph build complete!")
    print(f"Total runtime: {stats['runtime_seconds']:.2f} seconds ({stats['runtime_seconds']/60:.2f} minutes)")
    print(f"Build time: {build_time:.2f} seconds ({build_time/60:.2f} minutes)")
    print(f"Processing rate: {stats['processing_rate']:.2f} emails/second")
    print(f"Peak memory usage: {stats['peak_memory_gb']:.2f} GB")
    print(f"Results saved to: {args.output_dir}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
