import sys
from pymodbus.client import ModbusTcpClient

# Usage: python3 scan_ps20.py <IP_ADDRESS>
if len(sys.argv) < 2:
    print("Error: Please provide IP address.")
    sys.exit(1)

ip = sys.argv[1]
client = ModbusTcpClient(ip, port=502, retries=0, timeout=1)

print(f"--- Connecting to {ip} ---")
if not client.connect():
    print("Failed to connect! Check IP and ensure Port 502 is open.")
    sys.exit(1)

print("\n--- Reading Holding Registers (address 0-124) ---")
rr = client.read_holding_registers(address=0, count=125, device_id=1)
if rr.isError():
    print(f"ERROR: {rr}")
else:
    print("OK - Found data:")
    for i, val in enumerate(rr.registers):
        if val > 0:  # Only show non-zero values
            print(f"  Reg {i}: {val}")

print("\n--- Scan Complete ---")
client.close()
