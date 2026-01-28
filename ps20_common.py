"""
Shared configuration and utilities for Savant PS20 Modbus tools
"""

# PS20 unit IP address mappings
# Unit 1 is the leader (serial ends in 840)
UNIT_IPS = {
    1: "172.20.232.225",  # Leader - serial NC-70-2505-01-0096-840
    2: "172.20.224.91",   # Serial NC-70-2505-01-0069-262
    3: "172.20.232.89",   # Serial NC-70-2505-01-0144-487
    4: "172.20.57.246",   # Serial NC-70-2505-01-0120-355
    5: "172.20.232.77",   # Serial NC-70-2505-01-0087-524
    6: "172.20.223.207",  # Serial NC-70-2505-01-0040-670
    7: "172.20.223.225",  # Serial NC-70-2505-01-0094-476
    8: "172.20.233.255"   # Serial NC-70-2505-01-0123-214
}

# Unit number to serial number mapping
UNIT_SERIALS = {
    1: "NC-70-2505-01-0096-840",  # Leader
    2: "NC-70-2505-01-0069-262",
    3: "NC-70-2505-01-0144-487",
    4: "NC-70-2505-01-0120-355",
    5: "NC-70-2505-01-0087-524",
    6: "NC-70-2505-01-0040-670",
    7: "NC-70-2505-01-0094-476",
    8: "NC-70-2505-01-0123-214"
}

# Known register mappings (1-indexed)
REGISTER_MAP = {
    18: "timestamp_high",  # Registers 18+19 form 32-bit Unix timestamp
    19: "timestamp_low",
    20: "device_code[0]",  # Registers 20-28 contain device code (ASCII)
    21: "device_code[1]",
    22: "device_code[2]",
    23: "device_code[3]",
    24: "device_code[4]",
    25: "device_code[5]",
    26: "device_code[6]",
    27: "device_code[7]",
    28: "device_code[8]",
    29: "serial[0]",       # Registers 29-39 contain serial number (ASCII)
    30: "serial[1]",
    31: "serial[2]",
    32: "serial[3]",
    33: "serial[4]",
    34: "serial[5]",
    35: "serial[6]",
    36: "serial[7]",
    37: "serial[8]",
    38: "serial[9]",
    39: "serial[10]",
    41: "ip_high",         # Registers 41-42 contain IP address
    42: "ip_low"
}
