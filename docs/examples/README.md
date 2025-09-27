# Examples

This directory contains practical examples and tutorials for using `almanac`.

## Available Examples

### Basic Usage
- **[daily-monitoring.md](daily-monitoring.md)** - Daily operational monitoring examples
- **[date-queries.md](date-queries.md)** - Various date and time query examples
- **[output-formats.md](output-formats.md)** - Working with different output options

### Advanced Analysis
- **[fiber-analysis.md](fiber-analysis.md)** - Fiber mapping and target analysis
- **[survey-planning.md](survey-planning.md)** - Survey planning and review workflows
- **[data-processing.md](data-processing.md)** - Batch processing and automation

### Integration Examples
- **[python-integration.md](python-integration.md)** - Using `almanac` output in Python analysis
- **[automation-scripts.md](automation-scripts.md)** - Shell scripts and automation examples

## Quick Start Examples

### Today's Observations
```bash
# Basic query - today's observations
almanac

# With progress and details
almanac -vv

# Specific observatory
almanac --apo -v
```

### Recent Data Analysis
```bash
# Last week with fiber mappings
almanac --mjd-start -7 --fibers --output weekly.h5

# Yesterday with detailed output
almanac --mjd -1 -vv --fibers
```

### Historical Surveys
```bash
# Specific survey period
almanac --date-start 2021-01-01 --date-end 2021-12-31 \\
        --fibers --output 2021_survey.h5 -v

# Monthly summary
almanac --date-start 2024-01-01 --date-end 2024-01-31 \\
        --output january_2024.h5
```

## Example Categories

### By Use Case
- **Operations**: Daily monitoring, real-time status checking
- **Research**: Historical analysis, survey statistics, target analysis
- **Development**: Testing, debugging, data validation

### By Data Type
- **Exposures**: Basic exposure metadata and statistics
- **Fibers**: Target assignments and fiber mapping analysis
- **Combined**: Comprehensive datasets for analysis

### By Complexity
- **Beginner**: Simple queries and basic output
- **Intermediate**: Multi-day queries, custom columns, file output
- **Advanced**: Automation, integration, custom processing

## Running Examples

Each example includes:
1. **Command**: The exact command to run
2. **Expected Output**: What you should see
3. **Explanation**: Why it works and when to use it
4. **Variations**: Alternative approaches and options

## Contributing Examples

To add new examples:
1. Create a new markdown file in this directory
2. Follow the existing format and structure
3. Include practical, tested examples
4. Update this README with a link to your example

## Prerequisites

All examples assume:
- `almanac` is installed and configured
- Database access is available (at Utah or properly configured)
- Basic familiarity with command-line interfaces

See the [Installation Guide](../installation.md) and [Configuration Guide](../configuration.md) for setup instructions.