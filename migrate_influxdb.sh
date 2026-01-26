#!/bin/bash
# Migrate ps20 InfluxDB data from 0-indexed to 1-indexed register names
# This script:
# 1. Copies ps20 -> ps20_new with renamed fields
# 2. Drops ps20
# 3. Copies ps20_new -> ps20
# 4. Drops ps20_new

INFLUX_HOST="172.30.0.199"
INFLUX_PORT="8086"
INFLUX_DB="home"

echo "=== InfluxDB Migration: ps20 register renaming (0-indexed -> 1-indexed) ==="
echo ""

# Step 1: Transform ps20 -> ps20_new with renamed fields
echo "Step 1: Copying ps20 -> ps20_new with renamed fields..."
curl -s -X POST "http://${INFLUX_HOST}:${INFLUX_PORT}/query?db=${INFLUX_DB}" \
  --data-urlencode "q=SELECT
    reg_0 AS reg_1, reg_0_unsigned AS reg_1_unsigned,
    reg_1 AS reg_2, reg_1_unsigned AS reg_2_unsigned,
    reg_2 AS reg_3, reg_2_unsigned AS reg_3_unsigned,
    reg_3 AS reg_4, reg_3_unsigned AS reg_4_unsigned,
    reg_4 AS reg_5, reg_4_unsigned AS reg_5_unsigned,
    reg_5 AS reg_6, reg_5_unsigned AS reg_6_unsigned,
    reg_6 AS reg_7, reg_6_unsigned AS reg_7_unsigned,
    reg_7 AS reg_8, reg_7_unsigned AS reg_8_unsigned,
    reg_8 AS reg_9, reg_8_unsigned AS reg_9_unsigned,
    reg_9 AS reg_10, reg_9_unsigned AS reg_10_unsigned,
    reg_10 AS reg_11, reg_10_unsigned AS reg_11_unsigned,
    reg_11 AS reg_12, reg_11_unsigned AS reg_12_unsigned,
    reg_12 AS reg_13, reg_12_unsigned AS reg_13_unsigned,
    reg_13 AS reg_14, reg_13_unsigned AS reg_14_unsigned,
    reg_14 AS reg_15, reg_14_unsigned AS reg_15_unsigned,
    reg_15 AS reg_16, reg_15_unsigned AS reg_16_unsigned,
    reg_16 AS reg_17, reg_16_unsigned AS reg_17_unsigned,
    reg_39 AS reg_40, reg_39_unsigned AS reg_40_unsigned,
    device_code, timestamp
  INTO ps20_new FROM ps20 GROUP BY *"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy data to ps20_new"
    exit 1
fi
echo "Done."
echo ""

# Step 2: Drop original ps20
echo "Step 2: Dropping original ps20 measurement..."
curl -s -X POST "http://${INFLUX_HOST}:${INFLUX_PORT}/query?db=${INFLUX_DB}" \
  --data-urlencode "q=DROP MEASUREMENT ps20"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to drop ps20"
    exit 1
fi
echo "Done."
echo ""

# Step 3: Copy ps20_new -> ps20
echo "Step 3: Copying ps20_new -> ps20..."
curl -s -X POST "http://${INFLUX_HOST}:${INFLUX_PORT}/query?db=${INFLUX_DB}" \
  --data-urlencode "q=SELECT * INTO ps20 FROM ps20_new GROUP BY *"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy data back to ps20"
    exit 1
fi
echo "Done."
echo ""

# Step 4: Drop ps20_new
echo "Step 4: Dropping temporary ps20_new measurement..."
curl -s -X POST "http://${INFLUX_HOST}:${INFLUX_PORT}/query?db=${INFLUX_DB}" \
  --data-urlencode "q=DROP MEASUREMENT ps20_new"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to drop ps20_new"
    exit 1
fi
echo "Done."
echo ""

echo "=== Migration complete! ==="
echo ""
echo "Verifying new field names:"
curl -s -G "http://${INFLUX_HOST}:${INFLUX_PORT}/query?db=${INFLUX_DB}" \
  --data-urlencode "q=SHOW FIELD KEYS FROM ps20"
