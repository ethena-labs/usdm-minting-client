from typing import Any

from web3 import Web3

ERC20_MIN_ABI: list[dict[str, Any]] = [
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


class AllowanceError(Exception):
    """Raised when allowance checks fail."""


class ApproveError(Exception):
    """Raised when approve transaction fails."""


def get_allowance(w3: Web3, token_address: str, owner: str, spender: str) -> int:
    token = w3.eth.contract(
        address=w3.to_checksum_address(token_address),
        abi=ERC20_MIN_ABI,
    )
    return int(
        token.functions.allowance(
            w3.to_checksum_address(owner),
            w3.to_checksum_address(spender),
        ).call()
    )


def send_approve_tx(
    w3: Web3,
    private_key: str,
    token_address: str,
    spender: str,
    amount: int,
) -> str:
    token = w3.eth.contract(
        address=w3.to_checksum_address(token_address),
        abi=ERC20_MIN_ABI,
    )
    owner = w3.eth.account.from_key(private_key).address
    unsigned = token.functions.approve(
        w3.to_checksum_address(spender),
        amount,
    ).build_transaction(
        {
            "from": owner,
            "nonce": w3.eth.get_transaction_count(owner),
            "gas": w3.eth.estimate_gas({"from": owner}) + 5000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }
    )
    signed = w3.eth.account.sign_transaction(unsigned, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def wait_for_receipt(w3: Web3, tx_hash: str, timeout: int = 120) -> object:
    return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout, poll_latency=5)
