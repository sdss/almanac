# Daily Monitoring Examples

Examples for daily operational monitoring using `almanac`.

## Basic Daily Checks

### Current Status
```bash
# Today's observations from both observatories
almanac

# Today with progress indicator
almanac -v

# Today with full details
almanac -vv
```

**Expected Output** (minimal):
```
APO: 15 exposures, 3 sequences
LCO: 8 exposures, 2 sequences
```

### Yesterday's Summary
```bash
# Yesterday's observations
almanac --mjd -1

# Yesterday with details
almanac --mjd -1 -vv
```

**Use Case**: Morning review of previous night's operations.

## Observatory-Specific Monitoring

### Apache Point Observatory
```bash
# APO only - today
almanac --apo

# APO yesterday with details
almanac --apo --mjd -1 -vv

# APO last 3 days
almanac --apo --mjd-start -3
```

### Las Campanas Observatory
```bash
# LCO only - today  
almanac --lco

# LCO yesterday with details
almanac --lco --mjd -1 -vv

# LCO last 3 days
almanac --lco --mjd-start -3
```

## Recent Trends

### Last Week
```bash
# Full week summary
almanac --mjd-start -7

# Week with progress display
almanac --mjd-start -7 -v

# Detailed weekly review
almanac --mjd-start -7 -vv
```

**Expected Output** (with -v):
```
Querying APO exposures from MJD 59293 to 59300...
100%|████████████████| 8/8 [00:02<00:00, 3.21it/s]
Querying LCO exposures from MJD 59293 to 59300...
100%|████████████████| 8/8 [00:01<00:00, 4.12it/s]

APO: 127 exposures across 8 nights (avg: 15.9 per night)
LCO: 89 exposures across 8 nights (avg: 11.1 per night)
```

### Last Month
```bash
# Monthly overview
almanac --mjd-start -30

# Save monthly data
almanac --mjd-start -30 --output monthly_$(date +%Y%m).h5 -v
```

## Operational Monitoring Scripts

### Daily Status Script
Create a daily monitoring script:

```bash
#!/bin/bash
# daily_status.sh

echo "=== ALMANAC Daily Status $(date) ==="
echo

echo "Today's Observations:"
almanac -v
echo

echo "Yesterday's Summary:"
almanac --mjd -1
echo

echo "Weekly Totals:"
almanac --mjd-start -7
echo

echo "=== End Status Report ==="
```

**Usage**: `chmod +x daily_status.sh && ./daily_status.sh`

### Observatory Comparison
```bash
#!/bin/bash
# compare_obs.sh

echo "APO vs LCO Comparison (Last 7 Days)"
echo "================================="
echo "APO:"
almanac --apo --mjd-start -7
echo
echo "LCO:"  
almanac --lco --mjd-start -7
```

## Specific Data Monitoring

### Exposure Types
```bash
# Focus on specific exposure info
almanac --mjd -1 --exposure-columns "observatory,mjd,exposure,exptype,nread"

# Look for calibration exposures
almanac --mjd -1 -vv --exposure-columns "observatory,exposure,exptype,lampqrtz,lampthar,lampune"
```

**Expected Output**:
```
Observatory  MJD    Exposure  ExpType  NRead
-----------  -----  --------  -------  -----
apo          59300      1001  OBJECT      47
apo          59300      1002  OBJECT      47  
apo          59300      1003  FLAT         8
```

### Observing Conditions
```bash
# Monitor seeing and focus
almanac --mjd -1 --exposure-columns "observatory,mjd,exposure,seeing,focus"

# Check for comments/issues
almanac --mjd -1 -vv --exposure-columns "observatory,exposure,obscmt"
```

## Data Quality Checks

### Missing Exposures Detection
```bash
# Detailed output helps identify gaps
almanac --mjd -1 -vv

# Look for sequence patterns
almanac --mjd -1 --exposure-columns "observatory,mjd,exposure,exptype"
```

**Note**: `almanac` automatically warns about missing exposures in verbose mode.

### Configuration Changes
```bash
# Monitor configuration/design changes
almanac --mjd-start -3 --exposure-columns "observatory,mjd,configid,designid,fieldid"

# Track plate/cart changes (SDSS-IV)
almanac --mjd-start -3 --exposure-columns "observatory,mjd,plateid,cartid"
```

## Automated Monitoring

### Cron Job Setup
Add to crontab for automated monitoring:

```bash
# Edit crontab
crontab -e

# Add daily 8 AM status email
0 8 * * * /path/to/daily_status.sh | mail -s "Daily APOGEE Status" user@domain.com

# Add hourly checks during observing season
0 20-23,0-6 * * * almanac -v > /var/log/almanac/hourly_$(date +\%H).log
```

### Log Rotation
```bash
# Create logging directory
mkdir -p ~/logs/almanac

# Daily log with rotation
almanac --mjd -1 -vv > ~/logs/almanac/$(date +%Y%m%d).log

# Weekly summary log  
almanac --mjd-start -7 > ~/logs/almanac/weekly_$(date +%Y%W).log
```

## Performance Monitoring

### Response Time Checks
```bash
# Time the database queries
time almanac --mjd -1

# Time with fiber data
time almanac --mjd -1 --fibers
```

### Resource Usage
```bash
# Monitor with system resources
almanac --mjd-start -7 --processes 1 -v &
top -p $!

# Memory usage for large queries
/usr/bin/time -v almanac --mjd-start -30 --fibers --output large.h5
```

## Troubleshooting During Operations

### Quick Diagnostics
```bash
# Test basic connectivity
almanac config show

# Test without database cross-matching
almanac --mjd -1 --fibers --no-x-match

# Minimal processing test
almanac --mjd -1 --exposure-columns "observatory,mjd,exposure"
```

### Error Recovery
```bash
# Retry with different settings
almanac --mjd -1 --processes 1  # Single-threaded
almanac --mjd -1 --no-x-match   # Skip database intensive ops
```

## Integration with Other Tools

### With Observing Logs
```bash
# Combined with other observing tools
echo "ALMANAC Status:" > status.txt
almanac --mjd -1 >> status.txt
echo "Weather Data:" >> status.txt
# ... other monitoring tools
```

### Data Export for Analysis
```bash
# Export for external analysis
almanac --mjd -1 --fibers --output daily_$(date +%Y%m%d).h5 -v

# Quick CSV export (requires additional processing)
almanac --mjd -1 -vv > raw_output.txt
```

These examples provide a foundation for operational monitoring. Adapt the verbosity levels, output formats, and automation based on your specific monitoring needs.