"""
Discord Account Generator - Core Logic
Educational purposes only.
"""

import asyncio
import random
import string
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
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
    """Automates Discord account registration with headed Playwright browser.

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

    async def create_account(self, email: str, password: str) -> dict:
        """Attempt to register one Discord account.

        Returns a dict with keys:
            success  – bool
            email    – str
            username – str
            note     – str (optional extra info)
            error    – str (only when success is False)
        """
        if self._context is None:
            raise RuntimeError("Call init() before create_account().")

        username = generate_username()
        page = await self._context.new_page()

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
            submit = page.locator('button[type="submit"]')
            await submit.click()

            # ---- wait: captcha, email-verification page, or channel view ----
            print(
                Fore.YELLOW
                + "  → If a CAPTCHA appears in the browser, please solve it in the "
                + "Codespace preview tab, then wait…"
            )

            result = await _wait_for_outcome(page)
            result["email"] = email
            result["username"] = username
            return result

        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "email": email,
                "username": username,
                "error": str(exc),
            }
        finally:
            await page.close()


# ---------------------------------------------------------------------------
# Helper coroutines
# ---------------------------------------------------------------------------


async def _fill_date_of_birth(page) -> None:
    """Select a fixed date-of-birth (15 Jan 2000 → 25 years old)."""
    # Month selector (Discord uses a react-select or plain selects – handle both)
    month_input = page.locator('input[placeholder="Month"]')
    day_input = page.locator('input[placeholder="Day"]')
    year_input = page.locator('input[placeholder="Year"]')

    if await month_input.count() > 0:
        await month_input.fill("January")
        await month_input.press("Enter")
    else:
        # Some versions expose <select> elements
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
    """Block until Discord sends us somewhere useful (or we time out).

    Returns a partial result dict (without email/username, added by caller).
    """
    try:
        # Give the user up to 3 minutes to solve any captcha
        await asyncio.wait_for(
            _poll_for_success(page),
            timeout=timeout / 1000,
        )
        return {"success": True, "note": "Account created – check your inbox to verify."}
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Timed out waiting for registration to complete (180 s).",
        }


async def _poll_for_success(page) -> None:
    """Keep checking the page URL/content until we reach a success state."""
    while True:
        url = page.url
        # Redirected into the app proper
        if "/channels/" in url or "/app" in url:
            return
        # Email verification screen
        content = await page.content()
        if "Check your email" in content or "verify" in url.lower():
            return
        await asyncio.sleep(1)
