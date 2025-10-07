import psutil
import time
import os
from collections import deque

# --- Configuration ---
# Length of the rolling CPU history (30 seconds)
CPU_HISTORY_LENGTH = 30 
# Height of the vertical CPU history graph
GRAPH_HEIGHT = 5 
# Initialize CPU history as a deque for efficient popping/appending
cpu_history = deque([0.0] * CPU_HISTORY_LENGTH, maxlen=CPU_HISTORY_LENGTH)

# --- ANSI Color Codes (Make sure your terminal supports them) ---
class ANSI:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Text Colors
    WHITE = '\033[37m'
    
    # Background Colors
    BG_CPU = '\033[41m'  # Red for CPU
    BG_MEM = '\033[44m'  # Blue for Memory
    BG_DISK = '\033[42m' # Green for Disk
    BG_NET = '\033[43m'  # Yellow for Network

def clear_console():
    """Clears the terminal screen."""
    # Check OS type: 'nt' for Windows, 'posix' for Linux/Mac
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def get_resources():
    """Fetches the current system resource usage data."""
    try:
        data = {}
        
        # CPU Usage
        data['cpu_percent'] = psutil.cpu_percent(interval=0.1)

        # Memory Usage
        v_mem = psutil.virtual_memory()
        data['mem_total_gb'] = v_mem.total / (1024 ** 3)
        data['mem_used_gb'] = v_mem.used / (1024 ** 3)
        data['mem_percent'] = v_mem.percent

        # Disk Usage (Root Partition)
        disk_usage = psutil.disk_usage(os.path.abspath(os.sep))
        data['disk_total_gb'] = disk_usage.total / (1024 ** 3)
        data['disk_used_gb'] = disk_usage.used / (1024 ** 3)
        data['disk_percent'] = disk_usage.percent

        # Network I/O (Total since system boot)
        net_io = psutil.net_io_counters()
        data['bytes_sent_mb'] = net_io.bytes_sent / (1024 * 1024)
        data['bytes_recv_mb'] = net_io.bytes_recv / (1024 * 1024)
        
        return data
    except Exception as e:
        print(f"An error occurred while fetching resources: {e}")
        return {
            "cpu_percent": 0.0, "mem_total_gb": 0.0, "mem_used_gb": 0.0, "mem_percent": 0.0,
            "disk_total_gb": 0.0, "disk_used_gb": 0.0, "disk_percent": 0.0,
            "bytes_sent_mb": 0.0, "bytes_recv_mb": 0.0,
        }

def get_colored_bar(percent, bg_color, length=30):
    """
    Creates a colored, horizontal progress bar.
    
    Args:
        percent (float): Percentage (0-100).
        bg_color (str): ANSI background color code.
        length (int): Total length of the bar characters.
    
    Returns:
        str: The colored bar string.
    """
    # Calculate fill characters
    fill_count = int(percent / 100 * length)
    empty_count = length - fill_count
    
    # Use a solid block character ' ' with background color for the fill
    # And a light grey background for the empty space
    fill = f"{bg_color}{' ' * fill_count}{ANSI.RESET}"
    empty = f"\033[47m{' ' * empty_count}{ANSI.RESET}" # Light grey background for empty
    
    return f"|{fill}{empty}|"

def render_cpu_history_graph(history):
    """
    Generates a vertical Unicode console graph of the CPU history.

    Args:
        history (deque): Deque of past CPU percentage readings.
    Returns:
        str: The multi-line string representing the graph.
    """
    graph_lines = []
    
    # Render rows from top (100%) to bottom (0%)
    for h in range(GRAPH_HEIGHT, 0, -1):
        # Calculate the threshold for this height level (e.g., h=5 -> 80-100%, h=1 -> 0-20%)
        # Threshold: 100 * (h / GRAPH_HEIGHT)
        threshold = 100 * (h / GRAPH_HEIGHT) 
        
        # Percentage marker on the left
        marker = f"{int(threshold):>3}%"
        line = f"{marker} | "
        
        for val in history:
            # Check if the value meets or exceeds the threshold for this height
            if val >= threshold:
                # Use solid block for higher load, light block for medium load
                line += f"{ANSI.BG_CPU} {ANSI.RESET}" # Red block for CPU load
            elif val > 0 and h == 1:
                # Always show at least a small dot if there's *some* load, even if it's below the lowest threshold
                line += "·" 
            else:
                line += " "
        
        graph_lines.append(line)
    
    # Add a baseline for time/count
    graph_lines.append("----+" + "-" * CPU_HISTORY_LENGTH)
    
    return "\n".join(graph_lines)


def display_monitor(data, iteration):
    """
    Prints the resource usage data to the console with Task Manager style.
    """
    # Clear and print the header
    clear_console()
    print(f"{ANSI.BOLD}===================================================={ANSI.RESET}")
    print(f"{ANSI.BOLD}        Task Manager Style Resource Monitor         {ANSI.RESET}")
    print(f"        (Refresh: 1s | History: {CPU_HISTORY_LENGTH}s)       ")
    print(f"{ANSI.BOLD}===================================================={ANSI.RESET}")
    print(f"Last Update: {time.strftime('%Y-%m-%d %H:%M:%S')} (Iteration {iteration})")
    print("-" * 52)
    
    # ------------------- CPU DISPLAY -------------------
    cpu_bar = get_colored_bar(data['cpu_percent'], ANSI.BG_CPU)
    print(f"{ANSI.BOLD}CPU Usage:{ANSI.RESET}")
    print(f"  Load: {data['cpu_percent']:>5.1f}%  {cpu_bar}")
    print("\n" + render_cpu_history_graph(cpu_history))
    print("-" * 52)

    # ------------------- MEMORY DISPLAY -------------------
    mem_bar = get_colored_bar(data['mem_percent'], ANSI.BG_MEM)
    print(f"{ANSI.BOLD}Memory (RAM) Usage:{ANSI.RESET}")
    print(f"  Load: {data['mem_percent']:>5.1f}%  {mem_bar}")
    print(f"  Used: {data['mem_used_gb']:>5.2f} GB / Total: {data['mem_total_gb']:>5.2f} GB")
    print("-" * 52)

    # ------------------- DISK DISPLAY -------------------
    disk_bar = get_colored_bar(data['disk_percent'], ANSI.BG_DISK)
    print(f"{ANSI.BOLD}Disk Usage (Root):{ANSI.RESET}")
    print(f"  Load: {data['disk_percent']:>5.1f}%  {disk_bar}")
    print(f"  Used: {data['disk_used_gb']:>5.2f} GB / Total: {data['disk_total_gb']:>5.2f} GB")
    print("-" * 52)

    # ------------------- NETWORK DISPLAY -------------------
    print(f"{ANSI.BOLD}Network I/O (Total):{ANSI.RESET}")
    print(f"  Data Sent:     {data['bytes_sent_mb']:>7.2f} MB")
    print(f"  Data Received: {data['bytes_recv_mb']:>7.2f} MB")
    print("-" * 52)

    print(f"{ANSI.BOLD}Note:{ANSI.RESET} Colors require ANSI support. Press Ctrl+C to stop.")


def main():
    """Initializes and runs the resource monitoring loop."""
    global cpu_history # Use the global deque initialized above
    iteration = 0
    
    try:
        while True:
            iteration += 1
            resource_data = get_resources()
            
            # Update the CPU history buffer (deque automatically handles maxlen)
            cpu_history.append(resource_data['cpu_percent'])
            
            display_monitor(resource_data, iteration)
            
            # Wait for 1 second before the next update
            time.sleep(1)
            
    except KeyboardInterrupt:
        clear_console()
        print("\nTask Manager Monitor stopped by user.")
        print("Exiting.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    # On Windows, try to enable ANSI support (may not work in all environments)
    if os.name == 'nt':
        os.system('') 
    
    main()
