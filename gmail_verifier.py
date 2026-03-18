"""
Gmail Auto-Verifier
Logs into Gmail via Playwright, finds the Discord verification email, and
clicks the link automatically.  If auto-verification fails for any reason the
user is prompted to verify manually in the browser and press Enter to continue.

Educational purposes only.
"""

import asyncio

from colorama import Fore


class GmailVerifier:
    """Opens Gmail inside the shared browser context to verify Discord accounts.

    Workflow
    --------
    1. Log into Gmail (handles 2FA by waiting for the user to complete it).
    2. Search the inbox for the Discord verification email.
    3. Click "Verify Email".
    4. If any step above fails → print instructions and wait for the user to
       verify manually, then press Enter (or type 'skip') to continue.
    """

    GMAIL_URL = "https://mail.google.com"
    # Narrow search: only unread mails from Discord with "Verify" in subject
    _SEARCH = "from:discord.com subject:Verify is:unread"

    def __init__(self, context, gmail: str, gmail_password: str) -> None:
        self._context = context
        self._gmail = gmail
        self._gmail_password = gmail_password
        self._logged_in = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def verify_discord_account(
        self,
        alias_email: str,
        retries: int = 12,
        interval: int = 5,
    ) -> bool:
        """Try to auto-verify; fall back to a manual prompt if it fails.

        Parameters
        ----------
        alias_email:
            The + alias used during registration (used only for display).
        retries:
            Number of inbox polls before giving up on auto-verification.
        interval:
            Seconds to wait between inbox polls.

        Returns
        -------
        True  – account was verified (auto or manual).
        False – user skipped verification.
        """
        if await self._auto_verify(alias_email, retries, interval):
            return True
        return await self._manual_verify_prompt(alias_email)

    # ------------------------------------------------------------------
    # Gmail login
    # ------------------------------------------------------------------

    async def ensure_logged_in(self) -> bool:
        """Open Gmail and log in if not already. Returns True on success."""
        if self._logged_in:
            return True

        page = await self._context.new_page()
        try:
            print(Fore.CYAN + "  → Opening Gmail…")
            await page.goto(
                self.GMAIL_URL, wait_until="domcontentloaded", timeout=30_000
            )

            # Already at inbox?
            if "mail.google.com/mail" in page.url:
                self._logged_in = True
                print(Fore.GREEN + "  ✓ Already logged into Gmail.")
                await page.close()
                return True

            # ---- Step 1: enter email ----
            await page.wait_for_selector('input[type="email"]', timeout=15_000)
            await page.fill('input[type="email"]', self._gmail)
            await page.click("#identifierNext")

            # ---- Step 2: enter password ----
            await page.wait_for_selector(
                'input[type="password"]', timeout=15_000
            )
            await page.fill('input[type="password"]', self._gmail_password)
            await page.click("#passwordNext")

            # ---- Step 3: wait for inbox (user may need to handle 2FA) ----
            print(
                Fore.YELLOW
                + "  → If Google asks for 2-step verification, complete it"
                + " in the browser window now…"
            )
            deadline = asyncio.get_event_loop().time() + 120
            while asyncio.get_event_loop().time() < deadline:
                if "mail.google.com/mail" in page.url:
                    self._logged_in = True
                    print(Fore.GREEN + "  ✓ Logged into Gmail successfully.")
                    await page.close()
                    return True
                await asyncio.sleep(1)

            print(Fore.RED + "  ✗ Gmail login timed out (120 s).")
            await page.close()
            return False

        except Exception as exc:  # noqa: BLE001
            print(Fore.RED + f"  ✗ Gmail login error: {exc}")
            try:
                await page.close()
            except Exception:  # noqa: BLE001
                pass
            return False

    # ------------------------------------------------------------------
    # Auto-verification (private)
    # ------------------------------------------------------------------

    async def _auto_verify(
        self, alias_email: str, retries: int, interval: int
    ) -> bool:
        """Try to find and click the verification link in Gmail."""
        if not await self.ensure_logged_in():
            return False

        page = await self._context.new_page()
        try:
            await page.goto(
                self.GMAIL_URL, wait_until="domcontentloaded", timeout=30_000
            )

            for attempt in range(1, retries + 1):
                print(
                    Fore.CYAN
                    + f"  → Searching Gmail for verification email"
                    + f" (attempt {attempt}/{retries})…"
                )

                # ---- run inbox search ----
                search_box = page.locator('input[aria-label="Search mail"]')
                await search_box.wait_for(state="visible", timeout=10_000)
                await search_box.triple_click()
                await search_box.fill(self._SEARCH)
                await search_box.press("Enter")
                await asyncio.sleep(2)

                # ---- open first result ----
                first_row = page.locator("tr.zA").first
                if await first_row.count() > 0 and await first_row.is_visible():
                    await first_row.click()
                    await asyncio.sleep(1)

                    href = await self._extract_verify_href(page)
                    if href:
                        print(Fore.CYAN + "  → Clicking verification link…")
                        verify_page = await self._context.new_page()
                        try:
                            await verify_page.goto(
                                href,
                                wait_until="domcontentloaded",
                                timeout=30_000,
                            )
                            await asyncio.sleep(2)
                            print(
                                Fore.GREEN + f"  ✓ Auto-verified: {alias_email}"
                            )
                            return True
                        except Exception as exc:  # noqa: BLE001
                            print(
                                Fore.RED
                                + f"  ✗ Could not open verification URL: {exc}"
                            )
                            return False
                        finally:
                            await verify_page.close()

                    # Email opened but link not found
                    print(
                        Fore.YELLOW
                        + "  ⚠ Email opened but verification link not found."
                    )
                    return False

                # Email not yet arrived
                if attempt < retries:
                    print(
                        Fore.YELLOW
                        + f"  ⚠ Email not found yet; waiting {interval} s…"
                    )
                    await asyncio.sleep(interval)

            return False

        except Exception as exc:  # noqa: BLE001
            print(Fore.RED + f"  ✗ Auto-verification error: {exc}")
            return False
        finally:
            try:
                await page.close()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    async def _extract_verify_href(page) -> str | None:
        """Return the href of the Discord verification link, or None."""
        link = (
            page.locator('a:has-text("Verify Email")')
            .or_(page.locator('a:has-text("verify email")'))
            .or_(page.locator('a[href*="discord.com/verify"]'))
            .or_(page.locator('a[href*="click.discord.com"]'))
            .first
        )
        if await link.count() > 0:
            return await link.get_attribute("href")
        return None

    # ------------------------------------------------------------------
    # Manual-verification fallback (private)
    # ------------------------------------------------------------------

    @staticmethod
    async def _manual_verify_prompt(alias_email: str) -> bool:
        """Print instructions and wait for the user to verify manually.

        Returns True if the user confirmed, False if they typed 'skip'.
        """
        print(
            Fore.YELLOW
            + f"\n  ⚠  Auto-verification failed for: {alias_email}\n"
            + "  Please verify the account manually:\n"
            + "    1. Look at the browser window (or Codespace preview tab)\n"
            + "    2. Open Gmail and find the Discord 'Verify Email' message\n"
            + "    3. Click the 'Verify Email' button inside that email\n"
            + "    4. Return here and press Enter to continue\n"
            + "       — or type  skip  and press Enter to skip this account —"
        )
        answer = await asyncio.to_thread(
            input,
            Fore.WHITE + "  Done? [Enter to confirm / 'skip' to skip]: ",
        )
        if answer.strip().lower() == "skip":
            print(Fore.YELLOW + "  ↷ Skipped verification for this account.")
            return False
        print(Fore.GREEN + "  ✓ Manual verification confirmed.")
        return True
