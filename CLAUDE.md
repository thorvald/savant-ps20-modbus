# Savant PS20 Modbus Findings

## Device Capabilities
- **Only supports**: Holding Registers (function code 3)
- **Does NOT support**: Input Registers, Coils, Discrete Inputs (all timeout)

## Development Environment
- Virtual environment: `savant_debug/` (in repo root)
- Activate: `source savant_debug/bin/activate`
- Script location: `scan_ps20.py` (in repo root)
- Run: `python3 scan_ps20.py` (defaults to unit 1)
- Specify unit: `python3 scan_ps20.py -u 8` or `--unit 8` (unit numbers 1-8)
- Watch mode: `python3 scan_ps20.py -w` or `--watch`
- Combined: `python3 scan_ps20.py -u 5 -w`

## Data Characteristics
- Registers 0-99 contain actual data
- Registers 100+ are mirrors/aliases of 0-99 (exact duplicates)
- Only first 100 registers are unique

## Pymodbus API (v3.11.4)
```python
ModbusTcpClient(host, port=502, retries=0, timeout=1)
read_holding_registers(address: int, *, count: int = 1, device_id: int = 1)
```
- `address` is positional
- All other params are keyword-only (enforced by `*`)

## Connection Settings
- 8 PS20 units (unit numbers 1-8)
- Port: 502
- retries: 0 (for fast development)
- timeout: 1 second
- device_id: 1

## Unit IP Addresses
- Unit 1: 172.20.233.255
- Unit 2: 172.20.57.246
- Unit 3: 172.20.223.225
- Unit 4: 172.20.224.91
- Unit 5: 172.20.232.77
- Unit 6: 172.20.232.89
- Unit 7: 172.20.232.225
- Unit 8: 172.20.223.207

## Sample Register Values
```
Reg 0: 300, Reg 4: 359, Reg 6: 566, Reg 7: 817
Reg 9: 7229, Reg 12: 4220-4221, Reg 15: 4223
Reg 16: 10467, Reg 17: 26996, Reg 18: 63980-64024
Reg 19-38: Various 11k-17k range values
Reg 39: 1, Reg 40: 53215, Reg 41: 5292
```
