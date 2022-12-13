# aiolotus
 Unofficial Asyncronous Python Client for [Lotus](https://github.com/uselotus/lotus)

 **Latest Version**: [![PyPI version](https://badge.fury.io/py/aiolotus.svg)](https://badge.fury.io/py/aiolotus)

 **[Official Client](https://github.com/uselotus/lotus-python)**

 
---

## Installation

```bash
# Install from PyPI
pip install aiolotus

# Install from source
pip install git+https://github.com/GrowthEngineAI/aiolotus.git
```

## Usage

WIP - Simple Usage Example

```python
import asyncio
from aiolotus import Lotus
from aiolotus.utils import logger

Lotus.configure(
    apikey = '...',
    url = '',
)

async def run_test():
    res = await Lotus.get_all_customers()
    logger.info(res)

    res = await Lotus.get_all_metrics()
    logger.info(res)

    res = await Lotus.get_all_plans()
    logger.info(res)

    res = await Lotus.get_all_subscriptions()
    logger.info(res)

    await Lotus.async_shutdown()


asyncio.run(run_test())

```