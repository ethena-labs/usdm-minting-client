"""Unit tests for usdm.allowances module."""

from unittest.mock import MagicMock, patch

import pytest
from eth_account import Account

from usdm.allowances import (
    ERC20_MIN_ABI,
    AllowanceError,
    ApproveError,
    get_allowance,
    send_approve_tx,
    wait_for_receipt,
)


# Test addresses
TEST_TOKEN = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
TEST_OWNER = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TEST_SPENDER = "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


class TestERC20MinABI:
    """Tests for ERC20_MIN_ABI constant."""

    def test_abi_contains_allowance_function(self):
        """ABI should contain the allowance function."""
        allowance_fn = next(
            (fn for fn in ERC20_MIN_ABI if fn.get("name") == "allowance"),
            None,
        )

        assert allowance_fn is not None
        assert allowance_fn["type"] == "function"
        assert len(allowance_fn["inputs"]) == 2
        assert allowance_fn["outputs"][0]["type"] == "uint256"

    def test_abi_contains_approve_function(self):
        """ABI should contain the approve function."""
        approve_fn = next(
            (fn for fn in ERC20_MIN_ABI if fn.get("name") == "approve"),
            None,
        )

        assert approve_fn is not None
        assert approve_fn["type"] == "function"
        assert len(approve_fn["inputs"]) == 2
        assert approve_fn["outputs"][0]["type"] == "bool"


class TestGetAllowance:
    """Tests for get_allowance function."""

    def test_get_allowance_returns_int(self, mock_web3):
        """get_allowance should return allowance as integer."""
        mock_contract = MagicMock()
        mock_contract.functions.allowance.return_value.call.return_value = 1000000
        mock_web3.eth.contract.return_value = mock_contract

        result = get_allowance(mock_web3, TEST_TOKEN, TEST_OWNER, TEST_SPENDER)

        assert result == 1000000
        assert isinstance(result, int)

    def test_get_allowance_calls_contract_with_checksum_addresses(self, mock_web3):
        """get_allowance should convert addresses to checksum format."""
        mock_contract = MagicMock()
        mock_contract.functions.allowance.return_value.call.return_value = 0
        mock_web3.eth.contract.return_value = mock_contract

        get_allowance(mock_web3, TEST_TOKEN, TEST_OWNER, TEST_SPENDER)

        mock_web3.to_checksum_address.assert_any_call(TEST_TOKEN)
        mock_web3.to_checksum_address.assert_any_call(TEST_OWNER)
        mock_web3.to_checksum_address.assert_any_call(TEST_SPENDER)

    def test_get_allowance_with_zero_allowance(self, mock_web3):
        """get_allowance should handle zero allowance."""
        mock_contract = MagicMock()
        mock_contract.functions.allowance.return_value.call.return_value = 0
        mock_web3.eth.contract.return_value = mock_contract

        result = get_allowance(mock_web3, TEST_TOKEN, TEST_OWNER, TEST_SPENDER)

        assert result == 0

    def test_get_allowance_with_large_value(self, mock_web3):
        """get_allowance should handle large uint256 values."""
        large_value = 2**256 - 1
        mock_contract = MagicMock()
        mock_contract.functions.allowance.return_value.call.return_value = large_value
        mock_web3.eth.contract.return_value = mock_contract

        result = get_allowance(mock_web3, TEST_TOKEN, TEST_OWNER, TEST_SPENDER)

        assert result == large_value


class TestSendApproveTx:
    """Tests for send_approve_tx function."""

    def test_send_approve_tx_returns_tx_hash(self, mock_web3):
        """send_approve_tx should return transaction hash."""
        mock_contract = MagicMock()
        mock_contract.functions.approve.return_value.build_transaction.return_value = {
            "from": TEST_OWNER,
            "nonce": 0,
            "gas": 26000,
            "gasPrice": 20_000_000_000,
            "chainId": 1,
        }
        mock_web3.eth.contract.return_value = mock_contract
        mock_web3.eth.send_raw_transaction.return_value = bytes.fromhex("ab" * 32)

        result = send_approve_tx(
            mock_web3,
            TEST_PRIVATE_KEY,
            TEST_TOKEN,
            TEST_SPENDER,
            1000000,
        )

        assert result == "ab" * 32
        assert isinstance(result, str)

    def test_send_approve_tx_builds_correct_transaction(self, mock_web3):
        """send_approve_tx should build transaction with correct parameters."""
        mock_contract = MagicMock()
        # Return a complete transaction dict that eth_account can sign
        build_tx_mock = MagicMock(return_value={
            "from": TEST_OWNER,
            "nonce": 0,
            "gas": 26000,
            "gasPrice": 20_000_000_000,
            "chainId": 1,
            "to": TEST_TOKEN,
            "data": "0x",
            "value": 0,
        })
        mock_contract.functions.approve.return_value.build_transaction = build_tx_mock
        mock_web3.eth.contract.return_value = mock_contract
        mock_web3.eth.send_raw_transaction.return_value = bytes.fromhex("ab" * 32)

        send_approve_tx(
            mock_web3,
            TEST_PRIVATE_KEY,
            TEST_TOKEN,
            TEST_SPENDER,
            5000000,
        )

        mock_contract.functions.approve.assert_called_once()
        call_args = mock_contract.functions.approve.call_args
        assert call_args[0][1] == 5000000

    def test_send_approve_tx_signs_transaction(self, mock_web3):
        """send_approve_tx should sign the transaction with private key."""
        mock_contract = MagicMock()
        mock_contract.functions.approve.return_value.build_transaction.return_value = {
            "from": TEST_OWNER,
            "nonce": 0,
            "gas": 26000,
            "gasPrice": 20_000_000_000,
            "chainId": 1,
        }
        mock_web3.eth.contract.return_value = mock_contract
        mock_web3.eth.send_raw_transaction.return_value = bytes.fromhex("ab" * 32)

        send_approve_tx(
            mock_web3,
            TEST_PRIVATE_KEY,
            TEST_TOKEN,
            TEST_SPENDER,
            1000000,
        )

        mock_web3.eth.send_raw_transaction.assert_called_once()


class TestWaitForReceipt:
    """Tests for wait_for_receipt function."""

    def test_wait_for_receipt_returns_receipt(self, mock_web3):
        """wait_for_receipt should return transaction receipt."""
        expected_receipt = {"status": 1, "transactionHash": "0x" + "ab" * 32}
        mock_web3.eth.wait_for_transaction_receipt.return_value = expected_receipt

        result = wait_for_receipt(mock_web3, "0x" + "ab" * 32)

        assert result == expected_receipt

    def test_wait_for_receipt_uses_default_timeout(self, mock_web3):
        """wait_for_receipt should use 120 second default timeout."""
        mock_web3.eth.wait_for_transaction_receipt.return_value = {"status": 1}

        wait_for_receipt(mock_web3, "0x" + "ab" * 32)

        mock_web3.eth.wait_for_transaction_receipt.assert_called_with(
            "0x" + "ab" * 32,
            timeout=120,
            poll_latency=5,
        )

    def test_wait_for_receipt_accepts_custom_timeout(self, mock_web3):
        """wait_for_receipt should accept custom timeout."""
        mock_web3.eth.wait_for_transaction_receipt.return_value = {"status": 1}

        wait_for_receipt(mock_web3, "0x" + "ab" * 32, timeout=300)

        mock_web3.eth.wait_for_transaction_receipt.assert_called_with(
            "0x" + "ab" * 32,
            timeout=300,
            poll_latency=5,
        )


class TestExceptionClasses:
    """Tests for exception classes."""

    def test_allowance_error_is_exception(self):
        """AllowanceError should be an Exception."""
        assert issubclass(AllowanceError, Exception)

    def test_approve_error_is_exception(self):
        """ApproveError should be an Exception."""
        assert issubclass(ApproveError, Exception)

    def test_allowance_error_with_message(self):
        """AllowanceError should accept custom message."""
        error = AllowanceError("Allowance check failed")

        assert str(error) == "Allowance check failed"

    def test_approve_error_with_message(self):
        """ApproveError should accept custom message."""
        error = ApproveError("Approve transaction failed")

        assert str(error) == "Approve transaction failed"
