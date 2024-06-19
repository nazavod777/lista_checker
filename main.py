import asyncio
from os import mkdir
from os.path import exists
from sys import stderr

import aiohttp
from loguru import logger

from core import check_account
from utils import loader

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    loader.semaphore = asyncio.Semaphore(value=threads)

    async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                verify_ssl=None,
                ssl=False,
                use_dns_cache=False,
                ttl_dns_cache=300,
                limit=None
            ),
            headers={
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ru,en;q=0.9,vi;q=0.8,es;q=0.7,cy;q=0.6',
                'origin': 'https://lista.org',
                'referer': 'https://lista.org'
            }
    ) as client:
        tasks: list[asyncio.Task] = [
            asyncio.create_task(
                coro=check_account(
                    client=client,
                    private_key=current_private_key
                )
            )
            for current_private_key in accounts_list
        ]

        tasks_result: float = sum(list(await asyncio.gather(*tasks)))

    logger.info(f'Total Tokens: {tasks_result}')


if __name__ == '__main__':
    if not exists(
            path='result'
    ):
        mkdir(path='result')

    with open(
            file='data/accounts.txt',
            mode='r',
            encoding='utf-8-sig'
    ) as file:
        accounts_list: list[str] = [row.strip().split(':')[-1] for row in file]

    logger.success(f'Successfully Loaded {len(accounts_list)} Accounts')
    threads: int = int(input('\nThreads: '))
    print()

    try:
        import uvloop

        uvloop.run(main())

    except ModuleNotFoundError:
        asyncio.run(main())

    logger.success('The Work Has Been Successfully Finished')
    input('\nPress Enter to Exit..')
