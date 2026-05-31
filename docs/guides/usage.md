---
title: "Usage"
schema_type: common
status: published
owner: core-maintainer
purpose: "Usage guide for AMC."
tags:
  - guide
  - usage
---

This guide covers common usage patterns for AMC.

## Installation

### From PyPI

```bash
pip install amc
```

### From Source

```bash
git clone https://github.com/williaby/AMC
cd amc
uv sync --all-extras
```

## Library Usage

### Basic Import

```python
from amc import __version__

print(f"Version: {__version__}")
```

### Logging

```python
from amc.utils.logging import get_logger, setup_logging

# Setup logging
setup_logging(level="DEBUG", json_logs=False)

# Get a logger
logger = get_logger(__name__)
logger.info("Hello from AMC")
```
