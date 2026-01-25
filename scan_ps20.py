import sys
import time
import argparse
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from ps20_common import UNIT_IPS, REGISTER_MAP

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
parser.add_argument('-x', '--experiment', action='store_true',
                    help='Experimental mode - read register 4660 (0x1234) for unit identity')
parser.add_argument('-a', '--all', action='store_true',
                    help='Show all registers including decoded ones in raw output')

args = parser.parse_args()
unit = args.unit
ip = UNIT_IPS[unit]
watch_mode = args.watch
table_mode = args.table
experiment_mode = args.experiment
show_all = args.all

if experiment_mode:
    # Experimental mode - read register 4660 (0x1234)
    print(f"--- Experimental Mode: Reading register 4660 (0x1234) ---\n")
    print(f"Connecting to Unit {unit} ({ip})...", end=" ", flush=True)

    client = ModbusTcpClient(ip, port=502, retries=0, timeout=1)
    if not client.connect():
        print("FAILED")
        sys.exit(1)

    print("OK")

    rr = client.read_holding_registers(address=4660, count=1, device_id=1)
    client.close()

    if rr.isError():
        print(f"ERROR reading register 4660: {rr}")
    else:
        value = rr.registers[0]
        print(f"\nRegister 4660 (0x1234): {value} (0x{value:04x})")

    print("\n--- Experiment Complete ---")

elif table_mode:
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
        # Skip decoded registers unless --all is specified
        if not show_all and reg_num in REGISTER_MAP:
            continue

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
    client = ModbusTcpClient(ip, port=502, retries=0, timeout=5)

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
                # Skip decoded registers unless --all is specified
                if not show_all and i in REGISTER_MAP:
                    continue
                # Convert to signed 16-bit if MSB is set
                signed_val = val if val < 32768 else val - 65536
                signed_str = f" (signed: {signed_val:6d})" if val >= 32768 else ""
                name_suffix = f" ({REGISTER_MAP[i]})" if i in REGISTER_MAP else ""
                print(f"  Reg {i:3d}: {val:5d}{signed_str}{name_suffix}")

            # Verify we got exactly 42 registers
            if len(rr.registers) != 42:
                print(f"\nERROR: Expected 42 registers, got {len(rr.registers)}")
                client.close()
                sys.exit(1)

            # Decoded data section
            print("\n--- Decoded Data ---")

            # Timestamp from registers 17+18
            time_t = (rr.registers[17] << 16) | rr.registers[18]
            try:
                dt = datetime.fromtimestamp(time_t)
                print(f"Timestamp (reg 17-18): {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except (ValueError, OSError):
                print(f"Timestamp (reg 17-18): Invalid ({time_t})")

            # Device code from registers 19-27
            device_code = ""
            for i in range(19, 28):
                high_byte = (rr.registers[i] >> 8) & 0xFF
                low_byte = rr.registers[i] & 0xFF
                if 32 <= high_byte <= 126:
                    device_code += chr(high_byte)
                if 32 <= low_byte <= 126:
                    device_code += chr(low_byte)
            print(f"Device Code (reg 19-27): {device_code}")

            # Serial number from registers 28-38
            serial_number = ""
            for i in range(28, 39):
                high_byte = (rr.registers[i] >> 8) & 0xFF
                low_byte = rr.registers[i] & 0xFF
                if 32 <= high_byte <= 126:
                    serial_number += chr(high_byte)
                if 32 <= low_byte <= 126:
                    serial_number += chr(low_byte)
            print(f"Serial Number (reg 28-38): {serial_number}")

            # IP address from registers 40-41
            # Register 40: high byte = octet 4, low byte = octet 3
            # Register 41: high byte = octet 2, low byte = octet 1
            octet4 = (rr.registers[40] >> 8) & 0xFF
            octet3 = rr.registers[40] & 0xFF
            octet2 = (rr.registers[41] >> 8) & 0xFF
            octet1 = rr.registers[41] & 0xFF
            ip_address = f"{octet1}.{octet2}.{octet3}.{octet4}"
            print(f"IP Address (reg 40-41): {ip_address}")
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
                    # Skip decoded registers unless --all is specified
                    if not show_all and i in REGISTER_MAP:
                        continue
                    # Convert to signed 16-bit if MSB is set
                    signed_val = val if val < 32768 else val - 65536
                    signed_str = f" (signed: {signed_val:6d})" if val >= 32768 else ""
                    delta_prev = val - previous_values[i]
                    delta_start = val - initial_values[i]
                    name_suffix = f" ({REGISTER_MAP[i]})" if i in REGISTER_MAP else ""
                    print(f"  Reg {i:3d}: {val:5d}{signed_str}  Δprev: {delta_prev:6d}  Δstart: {delta_start:6d}{name_suffix}")

                previous_values = list(current_values)
                print()

        except KeyboardInterrupt:
            print("\n\nWatch mode stopped by user.")

    print("\n--- Scan Complete ---")
    client.close()
