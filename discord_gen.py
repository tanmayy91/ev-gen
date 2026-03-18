"""
Discord Account Generator - Core Logic
Educational purposes only.
"""

import asyncio
import random
import string
from playwright.async_api import async_playwright
from colorama import Fore

# Random username word banks
_ADJECTIVES = [
    "Cool", "Dark", "Epic", "Fast", "Free", "Grand", "High", "Iron",
    "Just", "Kind", "Last", "Main", "Near", "Open", "Pink", "Pure",
    "Real", "Safe", "Teal", "True", "Vast", "Warm", "Wild", "Zero",
]
_NOUNS = [
    "Ace", "Bat", "Cat", "Dog", "Elk", "Fox", "Gnu", "Hen",
    "Ibis", "Jay", "Koi", "Leo", "Mew", "Nix", "Owl", "Pug",
    "Ram", "Sow", "Tau", "Urs", "Vex", "Wax", "Yak", "Zen",
]


def generate_username() -> str:
    """Return a random username that fits Discord's 2-32 character limit."""
    adj = random.choice(_ADJECTIVES)
    noun = random.choice(_NOUNS)
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{adj}{noun}{suffix}"


class DiscordGenerator:
    """Automates Discord account registration with a headed Playwright browser.

    The browser is intentionally left visible so the operator can solve any
    hCaptcha challenge via the Codespace preview tab.
    """

    REGISTER_URL = "https://discord.com/register"

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def context(self):
        """Expose the browser context so other modules (e.g. GmailVerifier)
        can open new pages inside the same browser window."""
        return self._context

    async def init(self) -> None:
        """Launch a headed Chromium browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )

    async def close(self) -> None:
        """Shut down the browser and Playwright instance."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    # ------------------------------------------------------------------
    # Account creation
    # ------------------------------------------------------------------

    async def create_account(
        self, email: str, password: str, verifier=None
    ) -> dict:
        """Register one Discord account and optionally verify it via Gmail.

        Parameters
        ----------
        email:    Registration email (a Gmail + alias).
        password: Password for the new Discord account.
        verifier: Optional ``GmailVerifier`` instance.  When provided, the
                  method automatically (or manually) verifies the account after
                  a successful registration.

        Returns a dict with keys:
            success   – bool
            email     – str
            username  – str
            token     – str | None   (Discord auth token)
            verified  – bool         (True if email was verified)
            note      – str          (optional extra info)
            error     – str          (only when success is False)
        """
        if self._context is None:
            raise RuntimeError("Call init() before create_account().")

        username = generate_username()
        page = await self._context.new_page()

        # Capture the Discord auth token from the /auth/register API response
        captured_token: list[str] = []

        async def _on_response(response) -> None:
            if (
                "/api/v" in response.url
                and "/auth/register" in response.url
                and response.status == 200
            ):
                try:
                    data = await response.json()
                    if isinstance(data, dict) and "token" in data:
                        captured_token.append(data["token"])
                except Exception:  # noqa: BLE001
                    pass

        page.on("response", _on_response)

        try:
            print(Fore.CYAN + "  → Navigating to Discord registration page…")
            await page.goto(
                self.REGISTER_URL, wait_until="domcontentloaded", timeout=30_000
            )

            # ---- fill the form ----
            print(Fore.CYAN + "  → Filling registration form…")

            await page.wait_for_selector('input[name="email"]', timeout=15_000)
            await page.fill('input[name="email"]', email)

            # Discord may use "global_name" (display name) before "username"
            for selector in ['input[name="global_name"]', 'input[name="username"]']:
                locator = page.locator(selector)
                if await locator.count() > 0:
                    await locator.fill(username)
                    break

            await page.fill('input[name="password"]', password)

            # ---- date of birth (must be 18+) ----
            await _fill_date_of_birth(page)

            # ---- submit ----
            await page.locator('button[type="submit"]').click()

            # ---- wait: captcha, email-verification page, or channel view ----
            print(
                Fore.YELLOW
                + "  → If a CAPTCHA appears, solve it in the browser / Codespace"
                + " preview tab, then wait…"
            )

            reg_result = await _wait_for_outcome(page)

            # ---- try localStorage fallback if network hook missed ----
            token = captured_token[0] if captured_token else None
            if not token:
                token = await _token_from_localstorage(page)

            reg_result.update(
                {
                    "email": email,
                    "username": username,
                    "token": token,
                    "verified": False,
                }
            )

            # ---- Gmail verification ----
            if reg_result["success"] and verifier is not None:
                verified = await verifier.verify_discord_account(email)
                reg_result["verified"] = verified

            return reg_result

        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "email": email,
                "username": username,
                "token": None,
                "verified": False,
                "error": str(exc),
            }
        finally:
            await page.close()


# ---------------------------------------------------------------------------
# Helper coroutines
# ---------------------------------------------------------------------------


async def _fill_date_of_birth(page) -> None:
    """Select a fixed date-of-birth (15 Jan 2000 → 25 years old)."""
    month_input = page.locator('input[placeholder="Month"]')
    day_input = page.locator('input[placeholder="Day"]')
    year_input = page.locator('input[placeholder="Year"]')

    if await month_input.count() > 0:
        await month_input.fill("January")
        await month_input.press("Enter")
    else:
        month_sel = page.locator('select[id="month"]')
        if await month_sel.count() > 0:
            await month_sel.select_option(label="January")

    if await day_input.count() > 0:
        await day_input.fill("15")
    else:
        day_sel = page.locator('select[id="day"]')
        if await day_sel.count() > 0:
            await day_sel.select_option(value="15")

    if await year_input.count() > 0:
        await year_input.fill("2000")
    else:
        year_sel = page.locator('select[id="year"]')
        if await year_sel.count() > 0:
            await year_sel.select_option(value="2000")


async def _wait_for_outcome(page, timeout: int = 180_000) -> dict:
    """Block until Discord navigates away from the register page (or times out).

    Returns a partial result dict (email/username/token added by caller).
    """
    try:
        await asyncio.wait_for(
            _poll_for_success(page),
            timeout=timeout / 1000,
        )
        return {"success": True, "note": "Account created."}
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Timed out waiting for registration to complete (180 s).",
        }


async def _poll_for_success(page) -> None:
    """Poll until we detect a successful registration state."""
    while True:
        url = page.url
        if "/channels/" in url or "/app" in url:
            return
        content = await page.content()
        if "Check your email" in content or "verify" in url.lower():
            return
        await asyncio.sleep(1)


async def _token_from_localstorage(page) -> str | None:
    """Try to read the Discord token directly from the page's localStorage."""
    try:
        raw = await page.evaluate(
            "() => window.localStorage.getItem('token')"
        )
        if raw:
            # Discord stores it as a JSON string: '"actual.token.here"'
            return raw.strip('"')
    except Exception:  # noqa: BLE001
        pass
    return None
