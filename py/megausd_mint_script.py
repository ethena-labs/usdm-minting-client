"""
This module provides functionality to handle JSON data.
It includes functions to read, write, and manipulate JSON objects.
"""

import json
import os
import time
import logging
from dataclasses import dataclass
from enum import IntEnum

import requests
from dotenv import load_dotenv, find_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_utils import to_hex, to_bytes
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s"
)

# Load environment variables
env_path = find_dotenv()
load_dotenv(env_path)

# Constants
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
RPC_URL = os.getenv("RPC_URL")
MEGAUSD_MINTING_ADDRESS = (
    "0x7293D7afaAD2F461c2E87561c222Ece165B0f995" 
)
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
COLLATERAL_ASSET = "USDC"
COLLATERAL_ASSET_ADDRESS = USDC_ADDRESS

AMOUNT = 25
ALLOW_INFINITE_APPROVALS = False

# URLs
MEGAUSD_PUBLIC_URL = "https://public.api.megausd.money/"
MEGAUSD_PRIVATE_URL = "https://private.api.megausd.money/"
MEGAUSD_PUBLIC_URL_STAGING = "https://public.api.staging.megausd.money/"
MEGAUSD_PRIVATE_URL_STAGING = "https://private.api.staging.megausd.money/"


def load_abi(file_path):
    """
    Load and return the ABI (Application Binary Interface) from a JSON file.

    Args:
        file_path (str): The path to the JSON file containing the ABI.

    Returns:
        dict: The ABI loaded from the file.
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


ERC20_ABI = load_abi("py/erc20_abi.json")


class SignatureType(IntEnum):
    """Enumeration of supported signature types for minting."""

    EIP712 = 0
    EIP1271 = 1


@dataclass(init=True, order=True)
class Signature:
    """
    Represents a digital signature with its type and corresponding bytes.

    Attributes:
        signature_type (SignatureType): The type of the signature (e.g., EIP712, EIP1271).
        signature_bytes (bytes): The raw bytes of the signature.
    """

    signature_type: SignatureType
    signature_bytes: bytes


def get_rfq_data(url):
    """
    Fetches RFQ (Request for Quote) data from the given URL.

    Args:
        url (str): The endpoint URL to fetch data from.

    Returns:
        dict or None: Parsed JSON data if the request is successful,
        or None if an error occurs.
    """
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching RFQ data: {e}")
        return None


def big_int_amount(amount: int):
    """
    Converts an integer amount to a larger value by multiplying it by 10^6.

    Args:
        amount (int): The base integer value to be converted.

    Returns:
        int: The scaled-up value.
    """
    return amount * (10**6)


def get_allowance(w3, collateral_address: str):
    """
    Retrieves the token allowance for the minting address.

    Args:
        w3 (Web3): The Web3 instance connected to the blockchain.
        collateral_address (str): The address of the ERC-20 token contract.

    Returns:
        int: The allowance value for the minting address.
    """
    # pylint: disable=no-value-for-parameter
    account = Account.from_key(PRIVATE_KEY)

    allowance_contract = w3.eth.contract(
        address=Web3.to_checksum_address(collateral_address), abi=ERC20_ABI
    )

    allowance = allowance_contract.functions.allowance(
        account.address, MEGAUSD_MINTING_ADDRESS
    ).call()
    return allowance


def approve(w3, collateral_address: str, private_key: str, amount: int):
    """
    Approves a specified amount of tokens for a spender to transfer on behalf of the caller.

    This function interacts with an ERC-20 token contract to approve the `MEGAUSD_MINTING_ADDRESS`
    to spend a specific `amount` of tokens from the caller's address.

    Args:
        w3 (Web3): An instance of the Web3 class to interact with the Ethereum blockchain.
        collateral_address (str): The address of the ERC-20 token contract.
        private_key (str): The private key of the caller's wallet used to sign the transaction.
        amount (int): The amount of tokens to approve for spending.

    Returns:
        str: The transaction hash of the sent approval transaction.

    Raises:
        Exception: If the transaction fails due to network or contract issues.
    """
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(collateral_address), abi=ERC20_ABI
    )
    print("SUBMITTING APPROVAL", amount)
    transaction = contract.functions.approve(MEGAUSD_MINTING_ADDRESS, amount)
    account = Account.from_key(PRIVATE_KEY)  # pylint: disable=no-value-for-parameter

    tx = transaction.build_transaction(
        {
            "from": account.address,
            "value": 0,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # wait for the transaction to be mined
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()


def create_mint_order(rfq_data, acc, collateral_asset_address):
    """
    Creates a mint order with the provided RFQ data and account details.

    This function generates a mint order dictionary that includes the RFQ ID, order type, expiry time,
    nonce, and details about the benefactor and beneficiary. It also includes collateral information
    such as the asset address and amount, as well as the amount of MEGAUSD to mint.

    Args:
        rfq_data (dict): A dictionary containing the RFQ data.
        acc (object): An account object that contains the address of the user making the mint request.
        collateral_asset_address (str): The address of the collateral asset to be used in the mint order.

    Returns:
        dict: A dictionary containing the mint order with the following keys:
            - order_id (str): The RFQ ID as a string.
            - order_type (str): The type of the order, which is "MINT".
            - expiry (int): The timestamp representing when the order expires.
            - nonce (int): A nonce used for order identification and security.
            - benefactor (str): The address of the benefactor (the person creating the order).
            - beneficiary (str): The address of the beneficiary (the recipient of the minted tokens).
            - collateral_asset (str): The address of the collateral asset.
            - collateral_amount (int): The amount of collateral to be provided.
            - megausd_amount (int): The amount of MEGAUSD to be minted.
    """
    logging.info("Creating mint order...")
    return {
        "order_id": str(rfq_data["rfq_id"]),
        "order_type": rfq_data["side"],
        "expiry": int(time.time() + 60),
        "nonce": int(time.time() + 60),
        "benefactor": acc.address,
        "beneficiary": acc.address,
        "collateral_asset": collateral_asset_address,
        "collateral_amount": int(rfq_data["collateral_amount"]),
        "megausd_amount": int(rfq_data["megausd_amount"]),
    }


def sign_order(w3, mint_order, acc, megausd_minting_contract):
    """
    Signs an order using the provided account and returns the signature. EIP712 signature is used.
        struct Order(
            string  order_id,
            uint8   order_type,
            uint120 expiry,
            uint128 nonce,
            address benefactor,
            address beneficiary,
            address collateral_asset,
            uint128 collateral_amount,
            uint128 megausd_amount
        )
    """
    logging.info("Signing order...")
    order_tuple = (
        str(mint_order["order_id"]),
        0 if mint_order["order_type"] == "MINT" else 1,
        mint_order["expiry"],
        mint_order["nonce"],
        w3.to_checksum_address(mint_order["benefactor"]),
        w3.to_checksum_address(mint_order["beneficiary"]),
        w3.to_checksum_address(mint_order["collateral_asset"]),
        mint_order["collateral_amount"],
        mint_order["megausd_amount"],
    )
    order_hash = megausd_minting_contract.functions.hashOrder(order_tuple).call()
    order_signed = acc.signHash(order_hash)
    order_rsv = (
        to_bytes(order_signed.r) + to_bytes(order_signed.s) + to_bytes(order_signed.v)
    )
    return Signature(SignatureType.EIP712, order_rsv)


def generate_order_signature():
    mint_abi = load_abi("py/megausd_mint_abi.json")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    megausd_minting_contract = w3.eth.contract(
        address=Web3.to_checksum_address(MEGAUSD_MINTING_ADDRESS), abi=mint_abi
    )
    acc: LocalAccount = Account.from_key(PRIVATE_KEY)
    amount = 0.015

    mint_order = {
        "order_id": "a",
        "order_type": "MINT",
        "expiry": int(time.time() + 86400 * 365),
        "nonce": int(time.time()),
        "benefactor": acc.address,
        "beneficiary": acc.address,
        "collateral_asset": USDC_ADDRESS,
        "collateral_amount": int(amount * 10**6),
        "megausd_amount": int(amount * 10**18)
    }

    order_tuple = (
        str(mint_order["order_id"]),
        0 if mint_order["order_type"] == "MINT" else 1,
        mint_order["expiry"],
        mint_order["nonce"],
        w3.to_checksum_address(mint_order["benefactor"]),
        w3.to_checksum_address(mint_order["beneficiary"]),
        w3.to_checksum_address(mint_order["collateral_asset"]),
        mint_order["collateral_amount"],
        mint_order["megausd_amount"],
    )

    # string order_id;
    # OrderType order_type;
    # uint120 expiry;
    # uint128 nonce;
    # address benefactor;
    # address beneficiary;
    # address collateral_asset;
    # uint128 collateral_amount;
    # uint128 megausd_amount;

    signature = sign_order(w3, mint_order, acc, megausd_minting_contract)
    signature_hex = to_hex(signature.signature_bytes)
    print(mint_order)
    print(signature_hex)
    print(signature)

    sig = (0, signature_hex)

    route = (
        [w3.to_checksum_address("0x0d20d44Fbd48752241a2b18979dF2424e8a5F022")],
        [10000]
    )

    tx = megausd_minting_contract.functions.mint(order_tuple, route, sig).build_transaction({
        "from": acc.address,
        "nonce": w3.eth.get_transaction_count(acc.address),
        "gas": 500000,
        "gasPrice": w3.eth.gas_price
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print("Transaction sent:", tx_hash.hex())


def main():
    """
    Minting flow
    """
    logging.info("Starting MEGAUSD minting script...")
    if not all([PRIVATE_KEY, RPC_URL]):
        logging.error("Missing environment variables. Please check your .env file.")
        return
    if COLLATERAL_ASSET not in ["USDC"]:
        logging.error("Invalid COLLATERAL_ASSET.")
        return

    mint_abi = load_abi("py/megausd_mint_abi.json")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    # pylint: disable=no-value-for-parameter
    acc: LocalAccount = Account.from_key(PRIVATE_KEY)

    allowance = get_allowance(w3, COLLATERAL_ASSET_ADDRESS)
    print("ALLOWANCE", allowance)

    if allowance < big_int_amount(AMOUNT):
        print("ALLOWANCE IS LESS THAN AMOUNT")
        approval_amount = (
            (2**256) - 1 if ALLOW_INFINITE_APPROVALS else big_int_amount(AMOUNT)
        )

        print("APPROVAL AMOUNT", approval_amount)

        tx_hash = approve(w3, COLLATERAL_ASSET_ADDRESS, PRIVATE_KEY, approval_amount)
        print(f"Approval submitted: https://etherscan.io/tx/{tx_hash}")

    megausd_minting_contract = w3.eth.contract(
        address=Web3.to_checksum_address(MEGAUSD_MINTING_ADDRESS), abi=mint_abi
    )

    rfq_url = f"{MEGAUSD_PUBLIC_URL_STAGING}rfq?pair={COLLATERAL_ASSET}/MEGAUSD&type_=ALGO&side=MINT&size={AMOUNT}&benefactor={acc.address}"
    rfq_data = get_rfq_data(rfq_url)

    if rfq_data is None:
        return

    mint_order = create_mint_order(rfq_data, acc, COLLATERAL_ASSET_ADDRESS)
    signature = sign_order(w3, mint_order, acc, megausd_minting_contract)

    signature_hex = to_hex(signature.signature_bytes)
    order_url = f"{MEGAUSD_PUBLIC_URL_STAGING}order?signature={signature_hex}"

    try:
        logging.info(f"Submitting order: {mint_order}")
        response = requests.post(order_url, json=mint_order, timeout=60)
        response_data = response.json()
        if response.status_code != 200:
            logging.error(
                f"Issue submitting order: HTTP {response.status_code}: {response_data['error']}"
            )
        else:
            tx_id = response_data["tx"]
            logging.info(f"Transaction submitted: https://etherscan.io/tx/{tx_id}")
    except requests.RequestException as e:
        logging.error(f"Error submitting order: {e}")


if __name__ == "__main__":
    #main()
    generate_order_signature()