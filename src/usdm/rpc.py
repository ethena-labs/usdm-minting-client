from web3 import HTTPProvider, Web3

from usdm.config import Settings


def get_web3(settings: Settings) -> Web3:
    return Web3(HTTPProvider(settings.rpc_url))
