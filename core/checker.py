import asyncio

import aiohttp
from eth_account.account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger

from utils import get_proxy, loader, append_file


class Checker:
    def __init__(self,
                 client: aiohttp.ClientSession,
                 private_key: str,
                 account: LocalAccount) -> None:
        self.client: aiohttp.ClientSession = client
        self.private_key: str = private_key
        self.account: LocalAccount = account

    def get_sign_hash(self) -> str:
        return self.account.sign_message(
            signable_message=encode_defunct(
                text='Thank you for your support of Lista DAO. Sign in to view airdrop details.')
        ).signature.hex()

    async def check_account(self) -> float:
        sign_hash: str = self.get_sign_hash()

        while True:
            response_text: None = None

            try:
                r: aiohttp.ClientResponse = await self.client.get(
                    url='https://api.lista.org/api/airdrop/proof',
                    params={
                        'address': self.account.address,
                        'message': 'Thank you for your support of Lista DAO. Sign in to view airdrop details.',
                        'signature': sign_hash
                    },
                    proxy=get_proxy()
                )

                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                amount_in_wei: int = int(response_json['data']['amountWei'])

                if amount_in_wei <= 0:
                    logger.error(f'{self.private_key} | Invalid Allocation')
                    return 0

                amount_humanize: float = amount_in_wei / (10 ** 18)

                logger.success(f'{self.private_key} | Found Allocation: {amount_humanize}')

                async with asyncio.Lock():
                    await append_file(
                        file_path='result/eligible.txt',
                        file_content=f'{self.private_key} | {amount_humanize}\n'
                    )

            except Exception as error:
                if response_text:
                    logger.error(
                        f'{self.private_key} | Unexpected Error When Parsing Allocation: {error}, '
                        f'response: {response_text}'
                    )

                else:
                    logger.error(
                        f'{self.private_key} | Unexpected Error When Parsing Allocation: {error}'
                    )


async def check_account(client: aiohttp.ClientSession,
                        private_key: str) -> float:
    async with loader.semaphore:
        try:
            account: LocalAccount = Account.from_key(private_key=private_key)

        except ValueError:
            logger.error(f'{private_key} | Invalid Private Key')
            return 0

        checker: Checker = Checker(
            client=client,
            private_key=private_key,
            account=account
        )
        return await checker.check_account()
