#!/usr/bin/env python3
from pymodbus.client import ModbusTcpClient
from ps20_common import UNIT_IPS

def decode_serial_number(registers):
    serial_number = ""
    for i in range(28, 39):
        high_byte = (registers[i] >> 8) & 0xFF
        low_byte = registers[i] & 0xFF
        if 32 <= high_byte <= 126:
            serial_number += chr(high_byte)
        if 32 <= low_byte <= 126:
            serial_number += chr(low_byte)
    return serial_number

print("Verifying unit order:")
for unit_num in sorted(UNIT_IPS.keys()):
    ip = UNIT_IPS[unit_num]
    try:
        client = ModbusTcpClient(ip, port=502, retries=0, timeout=2)
        if client.connect():
            rr = client.read_holding_registers(address=0, count=125, device_id=1)
            client.close()
            if not rr.isError():
                serial = decode_serial_number(rr.registers)
                last_3 = serial[-3:]
                print(f"Unit {unit_num}: {last_3}")
    except Exception as e:
        print(f"Unit {unit_num}: ERROR - {e}")
