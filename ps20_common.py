"""
Shared configuration and utilities for Savant PS20 Modbus tools
"""

# PS20 unit IP address mappings
# Unit 1 is the leader (serial ends in 840)
UNIT_IPS = {
    1: "172.20.232.225",  # Leader - serial NC-70-2505-01-0096-840
    2: "172.20.233.255",  # Serial NC-70-2505-01-0123-214
    3: "172.20.57.246",   # Serial NC-70-2505-01-0120-355
    4: "172.20.223.225",  # Serial NC-70-2505-01-0094-476
    5: "172.20.224.91",   # Serial NC-70-2505-01-0069-262
    6: "172.20.232.77",   # Serial NC-70-2505-01-0087-524
    7: "172.20.232.89",   # Serial NC-70-2505-01-0144-487
    8: "172.20.223.207"   # Serial NC-70-2505-01-0040-670
}

# Known register mappings
REGISTER_MAP = {
    17: "timestamp_high",  # Registers 17+18 form 32-bit Unix timestamp
    18: "timestamp_low",
    19: "device_code[0]",  # Registers 19-27 contain device code (ASCII)
    20: "device_code[1]",
    21: "device_code[2]",
    22: "device_code[3]",
    23: "device_code[4]",
    24: "device_code[5]",
    25: "device_code[6]",
    26: "device_code[7]",
    27: "device_code[8]",
    28: "serial[0]",       # Registers 28-38 contain serial number (ASCII)
    29: "serial[1]",
    30: "serial[2]",
    31: "serial[3]",
    32: "serial[4]",
    33: "serial[5]",
    34: "serial[6]",
    35: "serial[7]",
    36: "serial[8]",
    37: "serial[9]",
    38: "serial[10]",
    40: "ip_high",         # Registers 40-41 contain IP address
    41: "ip_low"
}
