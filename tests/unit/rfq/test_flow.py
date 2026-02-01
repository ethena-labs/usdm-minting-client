"""Unit tests for usdm.rfq.flow module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from usdm.rfq.flow import (
    AllowanceInsufficientError,
    DryRunResult,
    SubmitReceiptResult,
    SubmitResult,
    dry_run,
    is_stale_quote_error,
    submit_and_wait,
    submit_with_allowance,
)
from usdm.rfq.types import RfqRequest, RfqResponse, Side


TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_BENEFACTOR = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TEST_COLLATERAL = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
TEST_CONTRACT = "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"


class TestIsStaleQuoteError:
    """Tests for is_stale_quote_error function."""

    @pytest.mark.parametrize(
        "message",
        [
            "stale quote",
            "quote expired",
            "RFQ expired",
            "order expired",
            "STALE quote error",
            "Quote has EXPIRED",
        ],
    )
    def test_detects_stale_errors(self, message):
        """is_stale_quote_error should detect stale/expired messages."""
        assert is_stale_quote_error(message) is True
        assert is_stale_quote_error(Exception(message)) is True

    @pytest.mark.parametrize(
        "message",
        [
            "Invalid signature",
            "Insufficient balance",
            "Network error",
            "Unknown error",
        ],
    )
    def test_rejects_non_stale_errors(self, message):
        """is_stale_quote_error should reject non-stale errors."""
        assert is_stale_quote_error(message) is False
        assert is_stale_quote_error(Exception(message)) is False

    def test_case_insensitive(self):
        """is_stale_quote_error should be case insensitive."""
        assert is_stale_quote_error("STALE QUOTE") is True
        assert is_stale_quote_error("stale quote") is True


class TestSubmitResult:
    """Tests for SubmitResult dataclass."""

    def test_submit_result_stores_fields(self):
        """SubmitResult should store all fields."""
        result = SubmitResult(
            tx_hash="0x" + "ab" * 32,
            rfq_id="test-123",
            requoted=False,
        )

        assert result.tx_hash == "0x" + "ab" * 32
        assert result.rfq_id == "test-123"
        assert result.requoted is False

    def test_submit_result_is_frozen(self):
        """SubmitResult should be immutable."""
        result = SubmitResult(
            tx_hash="0x" + "ab" * 32,
            rfq_id="test-123",
            requoted=False,
        )

        with pytest.raises(AttributeError):
            result.tx_hash = "modified"


class TestSubmitReceiptResult:
    """Tests for SubmitReceiptResult dataclass."""

    def test_receipt_result_stores_fields(self):
        """SubmitReceiptResult should store all fields."""
        result = SubmitReceiptResult(
            tx_hash="0x" + "ab" * 32,
            rfq_id="test-123",
            requoted=False,
            receipt_status=1,
            receipt={"status": 1},
        )

        assert result.tx_hash == "0x" + "ab" * 32
        assert result.rfq_id == "test-123"
        assert result.requoted is False
        assert result.receipt_status == 1
        assert result.receipt == {"status": 1}


class TestDryRunResult:
    """Tests for DryRunResult dataclass."""

    def test_dry_run_result_stores_fields(self):
        """DryRunResult should store all fields."""
        result = DryRunResult(
            rfq={"rfq_id": "test-123"},
            order={"order_id": "test-123"},
            signature="0xsig",
            signer="0xaddr",
            domain={"name": "USDmMinting"},
        )

        assert result.rfq == {"rfq_id": "test-123"}
        assert result.order == {"order_id": "test-123"}
        assert result.signature == "0xsig"
        assert result.signer == "0xaddr"
        assert result.domain == {"name": "USDmMinting"}


class TestAllowanceInsufficientError:
    """Tests for AllowanceInsufficientError exception."""

    def test_error_is_exception(self):
        """AllowanceInsufficientError should be an Exception."""
        assert issubclass(AllowanceInsufficientError, Exception)

    def test_error_with_message(self):
        """AllowanceInsufficientError should accept custom message."""
        error = AllowanceInsufficientError("Allowance 0 below required 1000")

        assert "Allowance 0 below required 1000" in str(error)


class TestSubmitWithAllowance:
    """Tests for submit_with_allowance function."""

    @pytest.fixture
    def mock_dependencies(self, settings, sample_rfq_response):
        """Set up mocked dependencies for submit_with_allowance."""
        with (
            patch("usdm.rfq.flow.RfqClient") as mock_client_cls,
            patch("usdm.rfq.flow.get_web3") as mock_get_web3,
            patch("usdm.rfq.flow.get_allowance") as mock_get_allowance,
            patch("usdm.rfq.flow.resolve_domain") as mock_resolve_domain,
            patch("usdm.rfq.flow.sign_order") as mock_sign_order,
        ):
            mock_client = MagicMock()
            mock_client.get_quote = AsyncMock(return_value=sample_rfq_response)
            mock_client.submit_order = AsyncMock(return_value="0x" + "ab" * 32)
            mock_client_cls.return_value = mock_client

            mock_w3 = MagicMock()
            mock_w3.eth.chain_id = 1
            mock_get_web3.return_value = mock_w3

            mock_get_allowance.return_value = 2000000000  # Sufficient allowance

            mock_domain = MagicMock()
            mock_domain.verifying_contract = TEST_CONTRACT
            mock_resolve_domain.return_value = mock_domain

            mock_signed = MagicMock()
            mock_signed.signature = "0xsig"
            mock_sign_order.return_value = mock_signed

            yield {
                "client": mock_client,
                "w3": mock_w3,
                "get_allowance": mock_get_allowance,
                "resolve_domain": mock_resolve_domain,
                "sign_order": mock_sign_order,
            }

    async def test_submit_with_allowance_returns_result(
        self, settings, sample_rfq_response, mock_dependencies
    ):
        """submit_with_allowance should return SubmitResult on success."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        result = await submit_with_allowance(
            settings, request, benefactor=TEST_BENEFACTOR
        )

        assert isinstance(result, SubmitResult)
        assert result.tx_hash == "0x" + "ab" * 32
        assert result.rfq_id == sample_rfq_response.rfq_id
        assert result.requoted is False

    async def test_submit_raises_on_insufficient_allowance(
        self, settings, sample_rfq_response, mock_dependencies
    ):
        """submit_with_allowance should raise on insufficient allowance."""
        mock_dependencies["get_allowance"].return_value = 0  # No allowance

        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        with pytest.raises(AllowanceInsufficientError):
            await submit_with_allowance(
                settings, request, benefactor=TEST_BENEFACTOR, auto_approve=False
            )

    async def test_submit_auto_approves_when_enabled(
        self, settings, sample_rfq_response, mock_dependencies
    ):
        """submit_with_allowance should auto-approve when enabled."""
        mock_dependencies["get_allowance"].side_effect = [0, 2000000000]

        with (
            patch("usdm.rfq.flow.send_approve_tx") as mock_approve,
            patch("usdm.rfq.flow.wait_for_receipt") as mock_wait,
        ):
            mock_approve.return_value = "0xapprove_tx"
            mock_wait.return_value = {"status": 1}

            request = RfqRequest(
                side=Side.MINT,
                size=1000.0,
                benefactor=TEST_BENEFACTOR,
            )

            result = await submit_with_allowance(
                settings, request, benefactor=TEST_BENEFACTOR, auto_approve=True
            )

            mock_approve.assert_called_once()
            assert result.tx_hash == "0x" + "ab" * 32


class TestDryRun:
    """Tests for dry_run function."""

    @pytest.fixture
    def mock_dry_run_deps(self, settings, sample_rfq_response):
        """Set up mocked dependencies for dry_run."""
        with (
            patch("usdm.rfq.flow.RfqClient") as mock_client_cls,
            patch("usdm.rfq.flow.get_web3") as mock_get_web3,
            patch("usdm.rfq.flow.resolve_domain") as mock_resolve_domain,
            patch("usdm.rfq.flow.sign_order") as mock_sign_order,
        ):
            mock_client = MagicMock()
            mock_client.get_quote = AsyncMock(return_value=sample_rfq_response)
            mock_client_cls.return_value = mock_client

            mock_w3 = MagicMock()
            mock_w3.eth.chain_id = 1
            mock_get_web3.return_value = mock_w3

            mock_domain = MagicMock()
            mock_domain.to_dict.return_value = {
                "name": "USDmMinting",
                "version": "1",
                "chainId": 1,
                "verifyingContract": TEST_CONTRACT,
            }
            mock_resolve_domain.return_value = mock_domain

            mock_signed = MagicMock()
            mock_signed.signature = "0xsignature"
            mock_signed.signer_address = TEST_BENEFACTOR
            mock_sign_order.return_value = mock_signed

            yield {
                "client": mock_client,
                "w3": mock_w3,
                "resolve_domain": mock_resolve_domain,
                "sign_order": mock_sign_order,
            }

    async def test_dry_run_returns_result(
        self, settings, sample_rfq_response, mock_dry_run_deps
    ):
        """dry_run should return DryRunResult."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        result = await dry_run(settings, request, benefactor=TEST_BENEFACTOR)

        assert isinstance(result, DryRunResult)
        assert result.signature == "0xsignature"
        assert result.signer == TEST_BENEFACTOR

    async def test_dry_run_does_not_submit(
        self, settings, sample_rfq_response, mock_dry_run_deps
    ):
        """dry_run should not submit the order."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        await dry_run(settings, request, benefactor=TEST_BENEFACTOR)

        mock_dry_run_deps["client"].submit_order.assert_not_called()

    async def test_dry_run_does_not_check_allowance(
        self, settings, sample_rfq_response, mock_dry_run_deps
    ):
        """dry_run should not check or modify allowances."""
        with patch("usdm.rfq.flow.get_allowance") as mock_allowance:
            request = RfqRequest(
                side=Side.MINT,
                size=1000.0,
                benefactor=TEST_BENEFACTOR,
            )

            await dry_run(settings, request, benefactor=TEST_BENEFACTOR)

            mock_allowance.assert_not_called()

    async def test_dry_run_includes_rfq_data(
        self, settings, sample_rfq_response, mock_dry_run_deps
    ):
        """dry_run should include RFQ response data."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        result = await dry_run(settings, request, benefactor=TEST_BENEFACTOR)

        assert "rfq_id" in result.rfq

    async def test_dry_run_includes_domain(
        self, settings, sample_rfq_response, mock_dry_run_deps
    ):
        """dry_run should include EIP-712 domain."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        result = await dry_run(settings, request, benefactor=TEST_BENEFACTOR)

        assert result.domain["name"] == "USDmMinting"
        assert result.domain["chainId"] == 1
