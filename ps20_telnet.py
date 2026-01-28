#!/usr/bin/env python3
"""
Extract configuration from PS20 units via telnet (port 22222)
"""
import sys
import json
import socket
from collections import Counter
from ps20_common import UNIT_IPS, UNIT_SERIALS

TELNET_PORT = 22222
PROMPT = b"root@OpenWrt:/#"
TIMEOUT = 5

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


def get_ems_config(unit_ip):
    """Connect to unit via telnet and extract /mnt/ems_config"""
    try:
        # Connect to telnet port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((unit_ip, TELNET_PORT))

        # Wait for initial prompt
        data = b""
        while PROMPT not in data:
            chunk = sock.recv(4096)
            if not chunk:
                raise Exception("Connection closed before prompt")
            data += chunk

        # Send command
        sock.sendall(b"cat /mnt/ems_config\n")

        # Read response until we see the prompt again
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if PROMPT in response:
                break

        sock.close()

        # Parse response: command echo + JSON + prompt
        response_str = response.decode('utf-8', errors='replace')

        # Remove command echo (first line)
        lines = response_str.split('\n', 1)
        if len(lines) > 1:
            json_part = lines[1]
        else:
            json_part = response_str

        # Remove trailing prompt
        if "root@OpenWrt:/#" in json_part:
            json_part = json_part.split("root@OpenWrt:/#")[0]

        # Parse JSON
        config = json.loads(json_part.strip())
        return config

    except socket.timeout:
        raise Exception("Connection timed out")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON: {e}")


def find_mode(values):
    """Find the most common value in a list"""
    if not values:
        return None
    counter = Counter(values)
    return counter.most_common(1)[0][0]


def format_value(value, mode):
    """Format a value with color based on comparison to mode"""
    if value is None:
        return "-"

    # For string values, no color comparison
    if isinstance(value, str) or isinstance(mode, str):
        if value == mode:
            return str(value)
        else:
            # Different string - highlight in yellow/different
            return f"{RED}{value}{RESET}"

    # For numeric values
    try:
        if value > mode:
            return f"{GREEN}{value}{RESET}"
        elif value < mode:
            return f"{RED}{value}{RESET}"
        else:
            return str(value)
    except TypeError:
        return str(value)


def main():
    print("PS20 Telnet Config Extractor")
    print("=" * 40)
    print()

    # Collect configs from all units
    unit_configs = {}  # unit_ip -> config dict
    unit_order = []    # maintain order

    for unit_number in sorted(UNIT_IPS.keys()):
        unit_ip = UNIT_IPS[unit_number]
        print(f"Reading Unit {unit_number} ({unit_ip})...", end=" ", flush=True)

        try:
            config = get_ems_config(unit_ip)
            unit_configs[unit_ip] = config
            unit_order.append((unit_number, unit_ip))
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
            unit_order.append((unit_number, unit_ip))
            unit_configs[unit_ip] = None

    print()

    # Build 2D dictionary: key -> { ip -> value }
    all_keys = set()
    for config in unit_configs.values():
        if config:
            all_keys.update(config.keys())

    all_keys = sorted(all_keys)

    # Build the key -> { ip -> value } structure
    key_values = {}
    for key in all_keys:
        key_values[key] = {}
        for unit_num, unit_ip in unit_order:
            config = unit_configs.get(unit_ip)
            if config and key in config:
                key_values[key][unit_ip] = config[key]
            else:
                key_values[key][unit_ip] = None

    # Calculate column widths
    key_width = max(len(key) for key in all_keys) if all_keys else 20
    val_width = 12  # width for each value column

    # Print header
    print("=" * (key_width + 3 + len(unit_order) * (val_width + 1)))
    header = f"{'Key':<{key_width}}"
    for unit_num, unit_ip in unit_order:
        # Use last 3 digits of serial as identifier
        short_id = UNIT_SERIALS[unit_num][-3:]
        header += f" {f'U{unit_num}({short_id})':>{val_width}}"
    print(header)
    print("-" * (key_width + 3 + len(unit_order) * (val_width + 1)))

    # Print each key row
    for key in all_keys:
        # Get all non-None values for this key
        values = [v for v in key_values[key].values() if v is not None]
        mode = find_mode(values) if values else None

        row = f"{key:<{key_width}}"
        for unit_num, unit_ip in unit_order:
            value = key_values[key].get(unit_ip)
            formatted = format_value(value, mode)

            # Calculate display width (without ANSI codes)
            if value is None:
                display_val = "-"
            else:
                display_val = str(value)

            # Pad based on display width, but include color codes
            padding = val_width - len(display_val)
            row += " " + " " * padding + formatted

        print(row)

    print("=" * (key_width + 3 + len(unit_order) * (val_width + 1)))
    print()
    print(f"Legend: {GREEN}Higher than mode{RESET} | {RED}Lower than mode{RESET} | Normal = mode")


if __name__ == "__main__":
    main()
