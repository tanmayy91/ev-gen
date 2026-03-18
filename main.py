"""
Discord Account Generator – Entry Point
Educational purposes only.

Usage:
    python main.py

The script asks for:
  1. Your Gmail address  (used for account registration + auto-verification)
  2. Your Gmail password (used to log into Gmail to click the verify link)
  3. A password for the new Discord accounts
  4. How many accounts to create

Gmail's + alias trick is used to generate unique registration addresses:
    tanmayyyy38@gmail.com  →  tanmayyyy38+1@gmail.com,
                               tanmayyyy38+2@gmail.com, …

A headed Chromium browser opens so you can solve any CAPTCHA manually.
After each registration the script auto-verifies via Gmail; if that fails
it pauses and asks you to verify manually in the browser, then press Enter.

Output files (appended on each run):
    tokens.txt  – one Discord token per line
    acc.txt     – email:password:token per line
"""

import asyncio
import getpass
import sys
from pathlib import Path

from colorama import Fore, init

from discord_gen import DiscordGenerator
from gmail_verifier import GmailVerifier

init(autoreset=True)

TOKENS_FILE = Path("tokens.txt")
ACCOUNTS_FILE = Path("acc.txt")


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
# Input collection
# ---------------------------------------------------------------------------


def collect_inputs() -> tuple[str, str, str, int]:
    """Return (gmail, gmail_password, discord_password, count)."""

    # Gmail address
    while True:
        gmail = prompt("Enter your Gmail address: ")
        if gmail.endswith("@gmail.com"):
            break
        print(Fore.RED + "  ✗ Please enter a valid @gmail.com address.")

    # Gmail password (for inbox verification)
    print(
        Fore.CYAN
        + "  (Gmail password is used only to open your inbox and click the\n"
        + "   Discord verification link — it is never stored or sent anywhere.)"
    )
    gmail_password = getpass.getpass(Fore.WHITE + "Enter your Gmail password: ")

    # Discord account password
    while True:
        discord_password = getpass.getpass(
            Fore.WHITE + "Enter password for new Discord accounts: "
        )
        if len(discord_password) >= 8:
            break
        print(Fore.RED + "  ✗ Password must be at least 8 characters.")

    # Number of accounts
    while True:
        raw = prompt("How many accounts to create? (1–50): ")
        try:
            count = int(raw)
            if 1 <= count <= 50:
                break
            raise ValueError
        except ValueError:
            print(Fore.RED + "  ✗ Please enter a whole number between 1 and 50.")

    return gmail, gmail_password, discord_password, count


# ---------------------------------------------------------------------------
# File saving
# ---------------------------------------------------------------------------


def save_results(results: list[dict], discord_password: str) -> None:
    """Append successful results to tokens.txt and acc.txt."""
    successful = [r for r in results if r.get("success") and r.get("token")]
    if not successful:
        return

    with TOKENS_FILE.open("a", encoding="utf-8") as tf:
        for r in successful:
            tf.write(r["token"] + "\n")

    with ACCOUNTS_FILE.open("a", encoding="utf-8") as af:
        for r in successful:
            af.write(f"{r['email']}:{discord_password}:{r['token']}\n")

    print(
        Fore.GREEN
        + f"\n  💾 Saved {len(successful)} token(s) to "
        + f"{TOKENS_FILE}  and  {ACCOUNTS_FILE}"
    )


# ---------------------------------------------------------------------------
# Main async runner
# ---------------------------------------------------------------------------


async def run(
    aliases: list[str],
    gmail: str,
    gmail_password: str,
    discord_password: str,
) -> list[dict]:
    """Create all accounts sequentially, verify each, and return results."""
    generator = DiscordGenerator()
    await generator.init()

    # Build the verifier once and reuse it (stays logged into Gmail)
    verifier = GmailVerifier(generator.context, gmail, gmail_password)

    results: list[dict] = []
    total = len(aliases)

    try:
        for idx, email in enumerate(aliases, start=1):
            print(Fore.CYAN + f"\n[{idx}/{total}] Creating account → {email}")
            result = await generator.create_account(
                email, discord_password, verifier=verifier
            )
            results.append(result)

            if result["success"]:
                token_display = (
                    result["token"][:20] + "…"
                    if result.get("token")
                    else "not captured"
                )
                verified_tag = (
                    Fore.GREEN + "verified ✓"
                    if result.get("verified")
                    else Fore.YELLOW + "unverified"
                )
                print(
                    Fore.GREEN
                    + f"  ✓ Created  username={result['username']}"
                    + f"  token={token_display}"
                    + f"  [{verified_tag}{Fore.GREEN}]"
                )
            else:
                print(
                    Fore.RED
                    + f"  ✗ Failed: {result.get('error', 'unknown error')}"
                )

    finally:
        await generator.close()

    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    print_banner()
    gmail, gmail_password, discord_password, count = collect_inputs()

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
        + " if you need to interact with a CAPTCHA or Gmail 2FA.\n"
    )

    results = asyncio.run(run(aliases, gmail, gmail_password, discord_password))

    # ---- persist results ----
    save_results(results, discord_password)

    # ---- print summary ----
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(Fore.CYAN + "\n" + "=" * 55)
    print(Fore.CYAN + "  Summary")
    print(Fore.CYAN + "=" * 55)
    print(Fore.GREEN + f"  ✓ Successful : {len(successful)}")
    print(Fore.RED + f"  ✗ Failed     : {len(failed)}")

    if successful:
        print(Fore.WHITE + "\n  Created accounts:")
        for r in successful:
            verified = "✓ verified" if r.get("verified") else "⚠ unverified"
            print(
                Fore.GREEN
                + f"    • {r['email']}  username={r['username']}  [{verified}]"
            )

    if failed:
        print(Fore.WHITE + "\n  Failed accounts:")
        for r in failed:
            print(Fore.RED + f"    • {r['email']}  – {r.get('error', '?')}")

    print(
        Fore.CYAN
        + f"\n  Output files:  {TOKENS_FILE}  |  {ACCOUNTS_FILE}\n"
    )


if __name__ == "__main__":
    main()
