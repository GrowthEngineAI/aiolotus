import asyncio
from client import Lotus
from aiolotus.utils import logger


async def run_test():
    res = await Lotus.get_all_customers()
    logger.info(res)


    res = await Lotus.get_all_metrics()
    logger.info(res)

    res = await Lotus.get_all_plans()
    logger.info(res)

    res = await Lotus.get_all_subscriptions()
    logger.info(res)

    # Auth Error
    # res = await Lotus.get_all_users()
    # logger.info(res)
    await Lotus.async_shutdown()


asyncio.run(run_test())
