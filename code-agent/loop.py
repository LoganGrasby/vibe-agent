import subprocess
import time
import sys

restart_count = 0
max_consecutive_failures = 5
consecutive_failures = 0

while True:
    try:
        print(f"\n{'='*50}")
        print(f"Starting agent... (Restart count: {restart_count})")
        print(f"{'='*50}\n")
        
        # Run the agent
        result = subprocess.run(["adk", "web"], check=True)
        
        # If we get here, the agent exited normally
        if result.returncode == 0:
            print("\nAgent exited gracefully - restarting...")
            restart_count += 1
            consecutive_failures = 0
            time.sleep(1)  # Brief pause before restart
        else:
            print(f"\nAgent exited with code {result.returncode}")
            consecutive_failures += 1
            
    except subprocess.CalledProcessError as e:
        print(f"\nAgent crashed with error: {e}")
        consecutive_failures += 1
        
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        consecutive_failures += 1
    
    # Check if we should give up
    if consecutive_failures >= max_consecutive_failures:
        print(f"\nToo many consecutive failures ({consecutive_failures}). Stopping.")
        break
    
    if consecutive_failures > 0:
        wait_time = min(consecutive_failures * 2, 30)  # Exponential backoff, max 30s
        print(f"\nWaiting {wait_time} seconds before retry...")
        time.sleep(wait_time)