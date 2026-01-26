#!/usr/bin/env python3
import sys
import time
import argparse
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from influxdb import InfluxDBClient
from ps20_common import UNIT_IPS

# InfluxDB configuration
INFLUX_HOST = "172.30.0.199"
INFLUX_PORT = 8086
INFLUX_DB = "home"
INFLUX_MEASUREMENT = "ps20"

# Polling interval in seconds
POLL_INTERVAL = 5


def decode_device_code(registers):
    """Decode device code from registers 20-28 (1-indexed)"""
    device_code = ""
    for i in range(20, 29):
        high_byte = (registers[i] >> 8) & 0xFF
        low_byte = registers[i] & 0xFF
        if 32 <= high_byte <= 126:
            device_code += chr(high_byte)
        if 32 <= low_byte <= 126:
            device_code += chr(low_byte)
    return device_code


def decode_serial_number(registers):
    """Decode serial number from registers 29-39 (1-indexed)"""
    serial_number = ""
    for i in range(29, 40):
        high_byte = (registers[i] >> 8) & 0xFF
        low_byte = registers[i] & 0xFF
        if 32 <= high_byte <= 126:
            serial_number += chr(high_byte)
        if 32 <= low_byte <= 126:
            serial_number += chr(low_byte)
    return serial_number


def decode_ip_address(registers):
    """Decode IP address from registers 41-42 (1-indexed)"""
    # Register 41: high byte = octet 4, low byte = octet 3
    # Register 42: high byte = octet 2, low byte = octet 1
    octet4 = (registers[41] >> 8) & 0xFF
    octet3 = registers[41] & 0xFF
    octet2 = (registers[42] >> 8) & 0xFF
    octet1 = registers[42] & 0xFF
    return f"{octet1}.{octet2}.{octet3}.{octet4}"


def decode_timestamp(registers):
    """Decode Unix timestamp from registers 18-19 (1-indexed)"""
    return (registers[18] << 16) | registers[19]


def to_signed(value):
    """Convert 16-bit unsigned to signed (2's complement)"""
    return value if value < 32768 else value - 65536


def collect_unit_data(unit_number, unit_ip):
    """Collect data from a single PS20 unit and return data point (does not write)"""
    try:
        # Connect to PS20 unit
        client = ModbusTcpClient(unit_ip, port=502, retries=1, timeout=5)
        if not client.connect():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Unit {unit_number} ({unit_ip}): Connection FAILED")
            return None

        # Read registers (1-indexed)
        rr = client.read_holding_registers(address=1, count=125, device_id=1)
        client.close()

        if rr.isError():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Unit {unit_number} ({unit_ip}): Read ERROR - {rr}")
            return None

        # Convert to dictionary with 1-indexed keys
        registers = {i: val for i, val in enumerate(rr.registers, start=1)}

        # Decode stable identifiers
        serial_number = decode_serial_number(registers)
        ip_address = decode_ip_address(registers)
        device_code = decode_device_code(registers)
        timestamp = decode_timestamp(registers)

        # Build tags
        tags = {
            "unit_number": str(unit_number),
            "serial_number": serial_number,
            "serial_suffix": serial_number[-3:],  # Last 3 digits for Grafana labels
            "ip_address": ip_address
        }

        # Build fields
        fields = {
            "device_code": device_code,
            "timestamp": timestamp
        }

        # Add registers 1-17 (signed and unsigned)
        for i in range(1, 18):
            unsigned_val = registers[i]
            signed_val = to_signed(unsigned_val)
            fields[f"reg_{i}"] = signed_val
            fields[f"reg_{i}_unsigned"] = unsigned_val

        # Add register 40 (signed and unsigned)
        unsigned_val = registers[40]
        signed_val = to_signed(unsigned_val)
        fields["reg_40"] = signed_val
        fields["reg_40_unsigned"] = unsigned_val

        # Return data point for batch writing
        data_point = {
            "measurement": INFLUX_MEASUREMENT,
            "tags": tags,
            "fields": fields
        }

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Unit {unit_number} ({unit_ip}): OK - {serial_number}")
        return data_point

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Unit {unit_number} ({unit_ip}): Exception - {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Collect Savant PS20 Modbus data to InfluxDB',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-i', '--interval', type=int, default=POLL_INTERVAL,
                        help=f'Polling interval in seconds (default: {POLL_INTERVAL})')

    args = parser.parse_args()
    poll_interval = args.interval

    print(f"PS20 Data Collector")
    print(f"===================")
    print(f"InfluxDB: {INFLUX_HOST}:{INFLUX_PORT}")
    print(f"Database: {INFLUX_DB}")
    print(f"Measurement: {INFLUX_MEASUREMENT}")
    print(f"Polling interval: {poll_interval} seconds")
    print(f"Units: {len(UNIT_IPS)}")
    print()

    # Connect to InfluxDB
    try:
        influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)
        # Test connection
        influx_client.ping()
        print("Connected to InfluxDB successfully")
    except Exception as e:
        print(f"Failed to connect to InfluxDB: {e}")
        sys.exit(1)

    print("\nStarting data collection (Ctrl+C to stop)...\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            cycle_start = time.time()
            print(f"--- Cycle {iteration} ---")

            # Collect from all units
            all_data_points = []
            for unit_number in sorted(UNIT_IPS.keys()):
                unit_ip = UNIT_IPS[unit_number]
                data_point = collect_unit_data(unit_number, unit_ip)
                if data_point:
                    all_data_points.append(data_point)

            # Write all data points with same timestamp in batch
            if all_data_points:
                try:
                    influx_client.write_points(all_data_points)
                    print(f"Batch wrote {len(all_data_points)} units to InfluxDB")
                except Exception as e:
                    print(f"ERROR writing batch to InfluxDB: {e}")

            print()

            # Wait for next cycle
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, poll_interval - cycle_duration)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\nData collection stopped by user.")

    print("Exiting...")


if __name__ == "__main__":
    main()
