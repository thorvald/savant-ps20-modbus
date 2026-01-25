# Savant PS20 Modbus Findings

## Device Capabilities
- **Only supports**: Holding Registers (function code 3)
- **Does NOT support**: Input Registers, Coils, Discrete Inputs (all timeout)
- **Limited implementation**: Always returns exactly 42 registers regardless of address or count requested
- Requesting any address/count combination returns registers 0-41

## Development Environment
- Virtual environment: `savant_debug/` (in repo root)
- Activate: `source savant_debug/bin/activate`

### Scanner Script (`scan_ps20.py`)
- Interactive tool for exploring and debugging PS20 registers
- Run: `python3 scan_ps20.py` (defaults to unit 1)
- Specify unit: `python3 scan_ps20.py -u 8` or `--unit 8` (unit numbers 1-8)
- Watch mode: `python3 scan_ps20.py -w` or `--watch` (track changes over time with deltas)
- Table mode: `python3 scan_ps20.py -t` or `--table` (shows all 8 units in 2D table)
- Combined: `python3 scan_ps20.py -u 5 -w`
- Show all: `python3 scan_ps20.py -a` (include decoded registers in raw output)

### Data Collector (`ps20_collector.py`)
- Continuous data collection to InfluxDB for all 8 units
- Run: `python3 ps20_collector.py` (default 5 second polling)
- Custom interval: `python3 ps20_collector.py -i 10` (10 second polling)
- **Batch writes**: Collects all 8 units first, then writes in single batch with same timestamp
- InfluxDB: `172.30.0.199:8086`
- Database: `home`
- Measurement: `ps20`
- Tags: `unit_number`, `serial_number`, `ip_address`
- Fields: `reg_0` through `reg_16` (signed + unsigned), `reg_39` (signed + unsigned), `device_code`, `timestamp`

## Register Map
Total registers available: **42 (registers 0-41)**

### Decoded Registers
- **Register 17-18**: Unix timestamp (32-bit)
  - Register 17: High 16 bits
  - Register 18: Low 16 bits
  - Decode: `(reg_17 << 16) | reg_18`

- **Register 19-27**: Device code (ASCII, 18 bytes)
  - Each register contains 2 ASCII characters (big-endian)
  - High byte = first character, low byte = second character
  - Decode: Extract high/low bytes, filter printable ASCII (32-126)

- **Register 28-38**: Serial number (ASCII, 22 bytes)
  - Each register contains 2 ASCII characters (big-endian)
  - Same encoding as device code

- **Register 40-41**: IP address (4 bytes)
  - Register 40: high byte = octet 4, low byte = octet 3
  - Register 41: high byte = octet 2, low byte = octet 1
  - Decode: `octet1.octet2.octet3.octet4`

### Unknown Registers
- **Registers 0-16**: Unknown (likely power, voltage, current, SOC, etc.)
- **Register 39**: Unknown (always value 1 observed)

### Value Encoding
- All register values are 16-bit unsigned (0-65535)
- Some registers use 2's complement signed interpretation:
  - If value >= 32768: `signed_value = value - 65536`
  - Useful for bidirectional measurements (e.g., battery current: charge vs discharge)

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

## Grafana Queries

### Per-Unit Query (shows individual units)
```sql
SELECT mean("reg_$register") FROM "ps20"
WHERE $timeFilter
GROUP BY time($__interval), "unit_number"::tag fill(previous)
```
- Alias by: `$tag_unit_number`
- Use panel repeat with `register` variable set to "All"

### Sum Query (aggregated across all units)
```sql
SELECT sum("value") FROM (
  SELECT mean("reg_$register") as "value" FROM "ps20"
  WHERE $timeFilter
  GROUP BY time($__interval), "unit_number"
) GROUP BY time($__interval)
```
- Alias by: `Sum`
- Batch collection ensures all units in same time bucket for proper summing

## InfluxDB Commands

### Query recent data
```bash
curl -G 'http://172.30.0.199:8086/query?db=home' \
  --data-urlencode "q=SELECT time, unit_number, reg_0 FROM ps20 ORDER BY time DESC LIMIT 20"
```

### Drop measurement (clean slate)
```bash
curl -X POST 'http://172.30.0.199:8086/query?db=home' \
  --data-urlencode "q=DROP MEASUREMENT ps20"
```
