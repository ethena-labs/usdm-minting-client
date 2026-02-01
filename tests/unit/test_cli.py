"""Unit tests for usdm.cli module."""

import argparse
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from usdm.cli import build_parser, main


class TestBuildParser:
    """Tests for build_parser function."""

    def test_build_parser_returns_argument_parser(self):
        """build_parser should return ArgumentParser."""
        parser = build_parser()

        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_prog_is_usdm(self):
        """Parser prog should be 'usdm'."""
        parser = build_parser()

        assert parser.prog == "usdm"

    def test_parser_requires_command(self):
        """Parser should require a command."""
        parser = build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestMintCommand:
    """Tests for mint command parsing."""

    def test_mint_command_parses(self):
        """mint command should parse with required args."""
        parser = build_parser()

        args = parser.parse_args(["mint", "--size", "1000"])

        assert args.command == "mint"
        assert args.size == 1000.0

    def test_mint_requires_size(self):
        """mint command should require --size."""
        parser = build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["mint"])

    def test_mint_accepts_beneficiary(self):
        """mint command should accept --beneficiary."""
        parser = build_parser()

        args = parser.parse_args([
            "mint", "--size", "1000",
            "--beneficiary", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        ])

        assert args.beneficiary == "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

    def test_mint_accepts_auto_approve(self):
        """mint command should accept --auto-approve flag."""
        parser = build_parser()

        args = parser.parse_args(["mint", "--size", "1000", "--auto-approve"])

        assert args.auto_approve is True

    def test_mint_auto_approve_defaults_false(self):
        """mint --auto-approve should default to False."""
        parser = build_parser()

        args = parser.parse_args(["mint", "--size", "1000"])

        assert args.auto_approve is False

    def test_mint_accepts_dry_run(self):
        """mint command should accept --dry-run flag."""
        parser = build_parser()

        args = parser.parse_args(["mint", "--size", "1000", "--dry-run"])

        assert args.dry_run is True

    def test_mint_accepts_receipt_timeout(self):
        """mint command should accept --receipt-timeout."""
        parser = build_parser()

        args = parser.parse_args(["mint", "--size", "1000", "--receipt-timeout", "300"])

        assert args.receipt_timeout == 300

    def test_mint_receipt_timeout_defaults_120(self):
        """mint --receipt-timeout should default to 120."""
        parser = build_parser()

        args = parser.parse_args(["mint", "--size", "1000"])

        assert args.receipt_timeout == 120


class TestRedeemCommand:
    """Tests for redeem command parsing."""

    def test_redeem_command_parses(self):
        """redeem command should parse with required args."""
        parser = build_parser()

        args = parser.parse_args(["redeem", "--size", "500"])

        assert args.command == "redeem"
        assert args.size == 500.0

    def test_redeem_requires_size(self):
        """redeem command should require --size."""
        parser = build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["redeem"])

    def test_redeem_accepts_all_flags(self):
        """redeem command should accept all optional flags."""
        parser = build_parser()

        args = parser.parse_args([
            "redeem", "--size", "500",
            "--beneficiary", "0xaddr",
            "--auto-approve",
            "--dry-run",
            "--receipt-timeout", "60"
        ])

        assert args.size == 500.0
        assert args.beneficiary == "0xaddr"
        assert args.auto_approve is True
        assert args.dry_run is True
        assert args.receipt_timeout == 60


class TestAllowanceCommand:
    """Tests for allowance command parsing."""

    def test_allowance_check_parses(self):
        """allowance check command should parse."""
        parser = build_parser()

        args = parser.parse_args([
            "allowance", "check",
            "--token", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        ])

        assert args.command == "allowance"
        assert args.action == "check"
        assert args.token == "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

    def test_allowance_check_requires_token(self):
        """allowance check should require --token."""
        parser = build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["allowance", "check"])

    def test_allowance_check_accepts_spender(self):
        """allowance check should accept --spender."""
        parser = build_parser()

        args = parser.parse_args([
            "allowance", "check",
            "--token", "0xtoken",
            "--spender", "0xspender"
        ])

        assert args.spender == "0xspender"

    def test_allowance_approve_parses(self):
        """allowance approve command should parse."""
        parser = build_parser()

        args = parser.parse_args([
            "allowance", "approve",
            "--token", "0xtoken",
            "--amount", "1000000"
        ])

        assert args.command == "allowance"
        assert args.action == "approve"
        assert args.token == "0xtoken"
        assert args.amount == "1000000"

    def test_allowance_approve_requires_amount(self):
        """allowance approve should require --amount."""
        parser = build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["allowance", "approve", "--token", "0xtoken"])


class TestMain:
    """Tests for main function."""

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.get_web3")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.get_allowance")
    def test_main_allowance_check_returns_zero(
        self, mock_get_allowance, mock_account, mock_get_web3, mock_settings
    ):
        """main should return 0 for successful allowance check."""
        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_settings.return_value.minting_contract = "0x" + "b" * 40
        mock_account.from_key.return_value.address = "0xowner"
        mock_get_allowance.return_value = 1000000

        result = main(["allowance", "check", "--token", "0xtoken"])

        assert result == 0

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.get_web3")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.send_approve_tx")
    @patch("usdm.cli.wait_for_receipt")
    def test_main_allowance_approve_returns_zero(
        self, mock_wait, mock_approve, mock_account, mock_get_web3, mock_settings
    ):
        """main should return 0 for successful allowance approve."""
        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_settings.return_value.minting_contract = "0x" + "b" * 40
        mock_account.from_key.return_value.address = "0xowner"
        mock_approve.return_value = "0xtxhash"
        mock_wait.return_value = {"status": 1}

        result = main(["allowance", "approve", "--token", "0xtoken", "--amount", "1000"])

        assert result == 0

    @patch("usdm.cli.asyncio")
    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    def test_main_mint_calls_async_handler(
        self, mock_account, mock_settings, mock_asyncio
    ):
        """main should call async handler for mint command."""
        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"
        mock_asyncio.run.return_value = 0

        result = main(["mint", "--size", "1000"])

        mock_asyncio.run.assert_called_once()
        assert result == 0

    @patch("usdm.cli.asyncio")
    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    def test_main_redeem_calls_async_handler(
        self, mock_account, mock_settings, mock_asyncio
    ):
        """main should call async handler for redeem command."""
        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"
        mock_asyncio.run.return_value = 0

        result = main(["redeem", "--size", "500"])

        mock_asyncio.run.assert_called_once()
        assert result == 0


class TestHandleRfqCommand:
    """Tests for _handle_rfq_command function."""

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.dry_run")
    async def test_dry_run_prints_json(
        self, mock_dry_run, mock_account, mock_settings, capsys
    ):
        """dry-run should print JSON output."""
        from usdm.cli import _handle_rfq_command
        from usdm.rfq.types import Side

        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"

        mock_result = MagicMock()
        mock_result.rfq = {"rfq_id": "test-123"}
        mock_result.order = {"order_id": "test-123"}
        mock_result.signature = "0xsig"
        mock_result.signer = "0xowner"
        mock_result.domain = {"name": "USDmMinting"}
        mock_dry_run.return_value = mock_result

        args = argparse.Namespace(
            size=1000.0,
            beneficiary=None,
            dry_run=True,
            auto_approve=False,
            receipt_timeout=120,
        )

        result = await _handle_rfq_command(args, Side.MINT)

        assert result == 0
        captured = capsys.readouterr()
        assert "rfq_id" in captured.out

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.submit_and_wait")
    async def test_submit_prints_result(
        self, mock_submit, mock_account, mock_settings, capsys
    ):
        """submit should print tx_hash and status."""
        from usdm.cli import _handle_rfq_command
        from usdm.rfq.types import Side

        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"

        mock_result = MagicMock()
        mock_result.rfq_id = "test-123"
        mock_result.tx_hash = "0x" + "ab" * 32
        mock_result.receipt_status = 1
        mock_result.requoted = False
        mock_submit.return_value = mock_result

        args = argparse.Namespace(
            size=1000.0,
            beneficiary=None,
            dry_run=False,
            auto_approve=False,
            receipt_timeout=120,
        )

        result = await _handle_rfq_command(args, Side.MINT)

        assert result == 0
        captured = capsys.readouterr()
        assert "tx_hash" in captured.out
        assert "success" in captured.out

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.submit_and_wait")
    async def test_submit_shows_reverted_status(
        self, mock_submit, mock_account, mock_settings, capsys
    ):
        """submit should show reverted status when receipt_status is 0."""
        from usdm.cli import _handle_rfq_command
        from usdm.rfq.types import Side

        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"

        mock_result = MagicMock()
        mock_result.rfq_id = "test-123"
        mock_result.tx_hash = "0x" + "ab" * 32
        mock_result.receipt_status = 0
        mock_result.requoted = False
        mock_submit.return_value = mock_result

        args = argparse.Namespace(
            size=1000.0,
            beneficiary=None,
            dry_run=False,
            auto_approve=False,
            receipt_timeout=120,
        )

        await _handle_rfq_command(args, Side.MINT)

        captured = capsys.readouterr()
        assert "reverted" in captured.out

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.submit_and_wait")
    async def test_submit_shows_requoted(
        self, mock_submit, mock_account, mock_settings, capsys
    ):
        """submit should show requoted when order was requoted."""
        from usdm.cli import _handle_rfq_command
        from usdm.rfq.types import Side

        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"

        mock_result = MagicMock()
        mock_result.rfq_id = "test-123"
        mock_result.tx_hash = "0x" + "ab" * 32
        mock_result.receipt_status = 1
        mock_result.requoted = True
        mock_submit.return_value = mock_result

        args = argparse.Namespace(
            size=1000.0,
            beneficiary=None,
            dry_run=False,
            auto_approve=False,
            receipt_timeout=120,
        )

        await _handle_rfq_command(args, Side.MINT)

        captured = capsys.readouterr()
        assert "requoted: true" in captured.out

    @patch("usdm.cli.Settings")
    @patch("usdm.cli.Account")
    @patch("usdm.cli.submit_and_wait")
    async def test_returns_one_on_error(
        self, mock_submit, mock_account, mock_settings, capsys
    ):
        """_handle_rfq_command should return 1 on error."""
        from usdm.cli import _handle_rfq_command
        from usdm.rfq.client import RfqError
        from usdm.rfq.types import Side

        mock_settings.return_value.private_key = "0x" + "a" * 64
        mock_account.from_key.return_value.address = "0xowner"
        mock_submit.side_effect = RfqError("Quote expired")

        args = argparse.Namespace(
            size=1000.0,
            beneficiary=None,
            dry_run=False,
            auto_approve=False,
            receipt_timeout=120,
        )

        result = await _handle_rfq_command(args, Side.MINT)

        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err
