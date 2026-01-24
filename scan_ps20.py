import sys
import time
from pymodbus.client import ModbusTcpClient

# Known register mappings
REGISTER_MAP = {
    18: "uptime_seconds"
}

# Parse command-line arguments
if len(sys.argv) < 2:
    print("Error: Please provide IP address.")
    print("Usage: python3 scan_ps20.py <IP_ADDRESS> [--watch|-w]")
    sys.exit(1)

ip = sys.argv[1]
watch_mode = "--watch" in sys.argv or "-w" in sys.argv
client = ModbusTcpClient(ip, port=502, retries=0, timeout=1)

print(f"--- Connecting to {ip} ---")
if not client.connect():
    print("Failed to connect! Check IP and ensure Port 502 is open.")
    sys.exit(1)

print("\n--- Reading Holding Registers (address 0-124) ---")

if not watch_mode:
    # Single read mode
    rr = client.read_holding_registers(address=0, count=125, device_id=1)
    if rr.isError():
        print(f"ERROR: {rr}")
    else:
        print("OK - Found data:")
        for i, val in enumerate(rr.registers):
            name_suffix = f" ({REGISTER_MAP[i]})" if i in REGISTER_MAP else ""
            print(f"  Reg {i:3d}: {val:5d}{name_suffix}")
else:
    # Watch mode - track changes over time
    print("Watch mode enabled - tracking changes every second (Ctrl+C to stop)")

    # Get initial values
    rr = client.read_holding_registers(address=0, count=125, device_id=1)
    if rr.isError():
        print(f"ERROR: {rr}")
        sys.exit(1)

    initial_values = rr.registers
    previous_values = list(initial_values)

    print("Initial values captured. Starting monitoring...\n")

    try:
        iteration = 0
        while True:
            time.sleep(1)
            iteration += 1

            rr = client.read_holding_registers(address=0, count=125, device_id=1)
            if rr.isError():
                print(f"ERROR: {rr}")
                continue

            current_values = rr.registers

            print(f"--- Update {iteration} ---")
            for i, val in enumerate(current_values):
                delta_prev = val - previous_values[i]
                delta_start = val - initial_values[i]
                name_suffix = f" ({REGISTER_MAP[i]})" if i in REGISTER_MAP else ""
                print(f"  Reg {i:3d}: {val:5d}  Δprev: {delta_prev:6d}  Δstart: {delta_start:6d}{name_suffix}")

            previous_values = list(current_values)
            print()

    except KeyboardInterrupt:
        print("\n\nWatch mode stopped by user.")

print("\n--- Scan Complete ---")
client.close()
