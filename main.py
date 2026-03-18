"""
Discord Account Generator – Entry Point
Educational purposes only.

Usage:
    python main.py

The script asks for:
  1. Your Gmail address
  2. A password for the new Discord accounts
  3. How many accounts to create

It then uses Gmail's + alias trick to derive unique registration addresses:
    e.g.  tanmayyyy38@gmail.com  →  tanmayyyy38+1@gmail.com,
                                    tanmayyyy38+2@gmail.com, …

A headed Chromium browser is opened for each account so you can solve any
hCaptcha challenge that Discord presents via the Codespace preview tab.
"""

import asyncio
import getpass
import sys

from colorama import Fore, Style, init

from discord_gen import DiscordGenerator

init(autoreset=True)

# ---------------------------------------------------------------------------
# Email helpers
# ---------------------------------------------------------------------------


def parse_gmail(address: str) -> tuple[str, str]:
    """Return (local, domain) after stripping any existing + alias part."""
    address = address.strip().lower()
    if "@" not in address:
        raise ValueError("Not a valid email address.")
    local, domain = address.split("@", 1)
    local = local.split("+")[0]  # drop existing alias if any
    return local, domain


def build_aliases(base_email: str, count: int, start: int = 1) -> list[str]:
    """Generate *count* Gmail + aliases starting from *start*.

    >>> build_aliases("tanmayyyy38@gmail.com", 3)
    ['tanmayyyy38+1@gmail.com', 'tanmayyyy38+2@gmail.com', 'tanmayyyy38+3@gmail.com']
    """
    local, domain = parse_gmail(base_email)
    return [f"{local}+{i}@{domain}" for i in range(start, start + count)]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def prompt(message: str) -> str:
    return input(Fore.WHITE + message).strip()


def print_banner() -> None:
    print(Fore.CYAN + "=" * 55)
    print(Fore.CYAN + "   Discord Account Generator  •  Educational Use Only")
    print(Fore.CYAN + "=" * 55)
    print(
        Fore.YELLOW
        + "\n⚠️  DISCLAIMER\n"
        + "   This tool is provided for EDUCATIONAL PURPOSES ONLY.\n"
        + "   Creating multiple Discord accounts may violate Discord's\n"
        + "   Terms of Service (https://discord.com/terms).\n"
        + "   You are solely responsible for how you use this tool.\n"
    )


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def collect_inputs() -> tuple[str, str, int]:
    """Interactively collect gmail, password, and count from the operator."""

    # Gmail
    while True:
        gmail = prompt("Enter your Gmail address: ")
        if gmail.endswith("@gmail.com"):
            break
        print(Fore.RED + "  ✗ Please enter a valid @gmail.com address.")

    # Password
    while True:
        password = getpass.getpass(Fore.WHITE + "Enter password for new Discord accounts: ")
        if len(password) >= 8:
            break
        print(Fore.RED + "  ✗ Password must be at least 8 characters.")

    # Count
    while True:
        raw = prompt("How many accounts to create? (1–50): ")
        try:
            count = int(raw)
            if 1 <= count <= 50:
                break
            raise ValueError
        except ValueError:
            print(Fore.RED + "  ✗ Please enter a whole number between 1 and 50.")

    return gmail, password, count


async def run(aliases: list[str], password: str) -> None:
    """Create all accounts sequentially and print a summary."""
    generator = DiscordGenerator()
    await generator.init()

    results: list[dict] = []
    total = len(aliases)

    try:
        for idx, email in enumerate(aliases, start=1):
            print(Fore.CYAN + f"\n[{idx}/{total}] Creating account → {email}")
            result = await generator.create_account(email, password)
            results.append(result)

            if result["success"]:
                note = result.get("note", "")
                print(
                    Fore.GREEN
                    + f"  ✓ Success! Username: {result['username']}"
                    + (f"  ({note})" if note else "")
                )
            else:
                print(Fore.RED + f"  ✗ Failed: {result.get('error', 'unknown error')}")

    finally:
        await generator.close()

    # Summary
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(Fore.CYAN + "\n" + "=" * 55)
    print(Fore.CYAN + "  Results")
    print(Fore.CYAN + "=" * 55)
    print(Fore.GREEN + f"  ✓ Successful : {len(successful)}")
    print(Fore.RED + f"  ✗ Failed     : {len(failed)}")

    if successful:
        print(Fore.WHITE + "\n  Created accounts:")
        for r in successful:
            print(Fore.GREEN + f"    • {r['email']}  (username: {r['username']})")

    if failed:
        print(Fore.WHITE + "\n  Failed accounts:")
        for r in failed:
            print(Fore.RED + f"    • {r['email']}  – {r.get('error', '?')}")

    print()


def main() -> None:
    print_banner()
    gmail, password, count = collect_inputs()

    aliases = build_aliases(gmail, count)

    print(Fore.GREEN + f"\n  Will create {count} account(s) using these emails:")
    for alias in aliases:
        print(Fore.GREEN + f"    • {alias}")

    confirm = prompt("\nProceed? (y/n): ").lower()
    if confirm != "y":
        print(Fore.YELLOW + "Aborted.")
        sys.exit(0)

    print(
        Fore.CYAN
        + "\n  Starting browser… open the Codespace 'Ports' / preview tab"
        + " if you need to interact with a CAPTCHA.\n"
    )

    asyncio.run(run(aliases, password))


if __name__ == "__main__":
    main()
