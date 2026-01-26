import argparse
from eth_account import Account

from usdm.allowances import get_allowance, send_approve_tx, wait_for_receipt
from usdm.config import Settings
from usdm.rpc import get_web3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="usdm-allowance")
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
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
