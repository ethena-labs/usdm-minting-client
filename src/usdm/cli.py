import argparse
import asyncio
import sys

from eth_account import Account

from usdm.allowances import get_allowance, send_approve_tx, wait_for_receipt
from usdm.config import Settings
from usdm.rfq.client import RfqError
from usdm.rfq.flow import AllowanceInsufficientError, submit_and_wait
from usdm.rfq.types import RfqRequest, Side
from usdm.rpc import get_web3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="usdm")
    subparsers = parser.add_subparsers(dest="command", required=True)

    allowance = subparsers.add_parser("allowance")
    allowance_sub = allowance.add_subparsers(dest="action", required=True)

    check = allowance_sub.add_parser("check")
    check.add_argument("--token", required=True)
    check.add_argument("--spender")

    approve = allowance_sub.add_parser("approve")
    approve.add_argument("--token", required=True)
    approve.add_argument("--spender")
    approve.add_argument("--amount", required=True)

    mint = subparsers.add_parser("mint")
    mint.add_argument("--size", required=True, type=float)
    mint.add_argument("--beneficiary")
    mint.add_argument("--auto-approve", action="store_true")
    mint.add_argument("--receipt-timeout", type=int, default=120)

    redeem = subparsers.add_parser("redeem")
    redeem.add_argument("--size", required=True, type=float)
    redeem.add_argument("--beneficiary")
    redeem.add_argument("--auto-approve", action="store_true")
    redeem.add_argument("--receipt-timeout", type=int, default=120)

    return parser


async def _handle_rfq_command(args: argparse.Namespace, side: Side) -> int:
    try:
        settings = Settings()
        benefactor = Account.from_key(settings.private_key).address
        request = RfqRequest(side=side, size=args.size)
        result = await submit_and_wait(
            settings,
            request,
            benefactor,
            beneficiary=args.beneficiary,
            auto_approve=args.auto_approve,
            receipt_timeout=args.receipt_timeout,
        )
        status = "success" if result.receipt_status == 1 else "reverted"
        print(f"rfq_id: {result.rfq_id}")
        print(f"tx_hash: {result.tx_hash}")
        print(f"status: {status}")
        if result.requoted:
            print("requoted: true")
        return 0
    except (AllowanceInsufficientError, RfqError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: unexpected failure: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "mint":
        return asyncio.run(_handle_rfq_command(args, Side.MINT))

    if args.command == "redeem":
        return asyncio.run(_handle_rfq_command(args, Side.REDEEM))

    settings = Settings()
    w3 = get_web3(settings)
    owner = Account.from_key(settings.private_key).address
    spender = (
        args.spender
        or settings.allowance_spender
        or settings.eip712_verifying_contract
    )
    if not spender:
        raise SystemExit("spender not provided and no default configured")

    if args.command == "allowance" and args.action == "check":
        current = get_allowance(w3, args.token, owner, spender)
        print(current)
        return 0

    if args.command == "allowance" and args.action == "approve":
        amount = int(args.amount)
        tx_hash = send_approve_tx(w3, settings.private_key, args.token, spender, amount)
        wait_for_receipt(w3, tx_hash)
        print(tx_hash)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
