"""Unit tests for usdm.rpc module."""

from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

from usdm.rpc import get_web3


class TestGetWeb3:
    """Tests for get_web3 function."""

    @patch("usdm.rpc.HTTPProvider")
    @patch("usdm.rpc.Web3")
    def test_get_web3_returns_web3_instance(self, mock_web3_cls, mock_provider, settings):
        """get_web3 should return a Web3 instance."""
        mock_web3_instance = MagicMock(spec=Web3)
        mock_web3_cls.return_value = mock_web3_instance

        result = get_web3(settings)

        assert result == mock_web3_instance

    @patch("usdm.rpc.HTTPProvider")
    @patch("usdm.rpc.Web3")
    def test_get_web3_uses_settings_rpc_url(self, mock_web3_cls, mock_provider, settings):
        """get_web3 should use RPC URL from settings."""
        get_web3(settings)

        mock_provider.assert_called_once_with(settings.rpc_url)

    @patch("usdm.rpc.HTTPProvider")
    @patch("usdm.rpc.Web3")
    def test_get_web3_creates_http_provider(self, mock_web3_cls, mock_provider, settings):
        """get_web3 should create HTTPProvider with settings URL."""
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance

        get_web3(settings)

        mock_web3_cls.assert_called_once_with(mock_provider_instance)
