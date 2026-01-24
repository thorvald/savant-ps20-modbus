import sys
import time
import argparse
from pymodbus.client import ModbusTcpClient

# Known register mappings
REGISTER_MAP = {
    18: "uptime_seconds"
}

# PS20 unit IP address mappings
UNIT_IPS = {
    1: "172.20.233.255",
    2: "172.20.57.246",
    3: "172.20.223.225",
    4: "172.20.224.91",
    5: "172.20.232.77",
    6: "172.20.232.89",
    7: "172.20.232.225",
    8: "172.20.223.207"
}

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description='Scan Savant PS20 Modbus registers',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=f"Available units:\n" + '\n'.join(f"  {u}: {ip}" for u, ip in UNIT_IPS.items())
)
parser.add_argument('-u', '--unit', type=int, default=1, choices=list(UNIT_IPS.keys()),
                    help='PS20 unit number (default: 1)')
parser.add_argument('-w', '--watch', action='store_true',
                    help='Enable watch mode - track changes every second')
parser.add_argument('-t', '--table', action='store_true',
                    help='Table mode - show all units in a 2D table for comparison')

args = parser.parse_args()
unit = args.unit
ip = UNIT_IPS[unit]
watch_mode = args.watch
table_mode = args.table

if table_mode:
    # Table mode - read from all units and display in a 2D table
    print("--- Table Mode: Reading from all units ---\n")

    all_unit_data = {}
    for u in sorted(UNIT_IPS.keys()):
        unit_ip = UNIT_IPS[u]
        print(f"Reading Unit {u} ({unit_ip})...", end=" ", flush=True)

        client = ModbusTcpClient(unit_ip, port=502, retries=0, timeout=1)
        if not client.connect():
            print("FAILED")
            all_unit_data[u] = None
            continue

        rr = client.read_holding_registers(address=0, count=125, device_id=1)
        client.close()

        if rr.isError():
            print("ERROR")
            all_unit_data[u] = None
        else:
            print("OK")
            all_unit_data[u] = rr.registers

    print("\n--- Register Comparison Table ---")

    # Determine the maximum number of registers returned by any unit
    max_registers = max(len(data) for data in all_unit_data.values() if data is not None)

    # Print header
    header = "Reg"
    for u in sorted(UNIT_IPS.keys()):
        header += f"    U{u}"
    print(header)
    print("-" * len(header))

    # Print each register row
    for reg_num in range(max_registers):
        row = f"{reg_num:3d}"
        for u in sorted(UNIT_IPS.keys()):
            if all_unit_data[u] is None or reg_num >= len(all_unit_data[u]):
                row += "     -"
            else:
                row += f" {all_unit_data[u][reg_num]:5d}"

        # Add register name if known
        if reg_num in REGISTER_MAP:
            row += f"  ({REGISTER_MAP[reg_num]})"

        print(row)

    print("\n--- Table Complete ---")

else:
    # Single unit mode (either single read or watch)
    client = ModbusTcpClient(ip, port=502, retries=0, timeout=1)

    print(f"--- Connecting to Unit {unit} ({ip}) ---")
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
