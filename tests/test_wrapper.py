import uuid
import asyncio
from aiolotus.utils import logger
from client import Lotus


async def get_customer_id(*args, **kwargs):
    return 'my_customer_id'

async def get_event_name(*args, **kwargs):
    return 'my_event_id'

@Lotus.on_event(
    customer_id = get_customer_id,
    event_name = get_event_name,
)
async def log_event(*args, **kwargs):
    return str(uuid.uuid4())


async def run_test(n_times: int = 100):
    for _ in range(n_times):
        await log_event(
            model = 'test_model',
        )
    await asyncio.sleep(15)

    await Lotus.async_shutdown()

asyncio.run(run_test())

