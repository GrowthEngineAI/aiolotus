import time
import uuid
import asyncio
from aiolotus.utils import logger
from client import Lotus

async def benchmark_events(
    n_events: int = 1000, 
    customer_id: str = "test",
):
    """
    See how far we can push events
    """

    # Test non-blocking events
    start = time.time()
    for i in range(n_events):
        await Lotus.track_event(
            customer_id = customer_id,
            event_name = f"benchmark_event_non_blocking_{i}",
            properties = {"benchmark_size": n_events, "benchmark_index": i, "benchmark_id": str(uuid.uuid4())},
            blocking = False,
        )
    end = time.time()
    logger.info(f"Non-blocking events: {n_events} in {end-start:.2f} seconds. Average {n_events/(end-start):.2f} events per second")

    # Test blocking events
    # start = time.time()
    # for i in range(n_events):
    #     await Lotus.track_event(
    #         customer_id = customer_id,
    #         event_name = "benchmark_event_blocking",
    #         properties = {"benchmark_size": n_events, "benchmark_index": i, "benchmark_id": str(uuid.uuid4())},
    #         blocking = True,
    #     )
    # end = time.time()
    # logger.info(f"Blocking events: {n_events} in {end-start:.2f} seconds. Average {n_events/(end-start):.2f} events per second")


async def run_bm():
    await benchmark_events(n_events=10000, customer_id="test")
    await asyncio.sleep(15.0)
    await Lotus.async_shutdown()

asyncio.run(run_bm())