# ev-gen — Discord Account Generator (Educational)

> **⚠️ DISCLAIMER:** This project is provided **for educational purposes only**.  
> Creating multiple Discord accounts may violate [Discord's Terms of Service](https://discord.com/terms).  
> You are solely responsible for how you use this software.

---

## Features

| Feature | Details |
|---|---|
| **Interactive CLI** | Prompts for Gmail, Gmail password, Discord password, and account count |
| **Gmail + alias trick** | Derives unique registration addresses from one inbox (`user+1@gmail.com`, `user+2@gmail.com`, …) |
| **Manual CAPTCHA solving** | Headed browser stays visible — solve hCaptcha in the Codespace preview tab |
| **Auto Gmail verification** | Logs into Gmail, finds the Discord verification email, and clicks the link automatically |
| **Manual verification fallback** | If auto-verification fails, the script pauses and guides you to verify manually, then press Enter |
| **Token capture** | Intercepts the Discord `/auth/register` API response to extract the auth token (localStorage fallback included) |
| **Output files** | `tokens.txt` (one token per line) and `acc.txt` (`email:password:token` per line) |

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| pip | any recent |

---

## Setup (Codespace / local)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download the Playwright browser binary
playwright install chromium

# 3. Run the generator
python main.py
```

---

## Usage walkthrough

```
$ python main.py
=======================================================
   Discord Account Generator  •  Educational Use Only
=======================================================
⚠️  DISCLAIMER …

Enter your Gmail address: tanmayyyy38@gmail.com
  (Gmail password is used only to open your inbox and click the
   Discord verification link — it is never stored or sent anywhere.)
Enter your Gmail password: ••••••••
Enter password for new Discord accounts: ••••••••
How many accounts to create? (1–50): 3

  Will create 3 account(s) using these emails:
    • tanmayyyy38+1@gmail.com
    • tanmayyyy38+2@gmail.com
    • tanmayyyy38+3@gmail.com

Proceed? (y/n): y

  Starting browser… open the Codespace 'Ports' / preview tab …

[1/3] Creating account → tanmayyyy38+1@gmail.com
  → Navigating to Discord registration page…
  → Filling registration form…
  → If a CAPTCHA appears, solve it in the browser / Codespace preview tab…
  → Logging into Gmail…
  → Searching Gmail for verification email (attempt 1/12)…
  ✓ Auto-verified: tanmayyyy38+1@gmail.com
  ✓ Created  username=EpicFox3821  token=mfa.AbCdEf…  [verified ✓]

[2/3] Creating account → tanmayyyy38+2@gmail.com
  …
  ⚠  Auto-verification failed for: tanmayyyy38+2@gmail.com
  Please verify the account manually:
    1. Look at the browser window (or Codespace preview tab)
    2. Open Gmail and find the Discord 'Verify Email' message
    3. Click the 'Verify Email' button inside that email
    4. Return here and press Enter to continue
       — or type  skip  and press Enter to skip this account —
  Done? [Enter to confirm / 'skip' to skip]:
  ✓ Manual verification confirmed.

  💾 Saved 3 token(s) to tokens.txt  and  acc.txt

=======================================================
  Summary
=======================================================
  ✓ Successful : 3
  ✗ Failed     : 0

  Created accounts:
    • tanmayyyy38+1@gmail.com  username=EpicFox3821  [✓ verified]
    • tanmayyyy38+2@gmail.com  username=DarkOwl5544  [✓ verified]
    • tanmayyyy38+3@gmail.com  username=WarmAce9901  [✓ verified]
```

---

## Output files

| File | Format | Notes |
|---|---|---|
| `tokens.txt` | `<token>` (one per line) | Appended on every run |
| `acc.txt` | `email:password:token` (one per line) | Appended on every run |

---

## Verification flow

```
Register account
      │
      ▼
Auto-verify (Gmail Playwright login → inbox search → click link)
      │
      ├─ success ──▶ continue
      │
      └─ failure ──▶ Print manual instructions
                          │
                          ├─ user presses Enter ──▶ confirmed, continue
                          └─ user types "skip"  ──▶ skip, continue
```

---

## Codespace CAPTCHA / Gmail guide

1. Open the **Ports** tab in VS Code (or the Codespace web UI).
2. Forward or open the port shown by the headed Chromium window.
3. Solve hCaptcha when Discord shows it — the script waits up to **3 minutes**.
4. For Gmail 2FA — complete it in the same browser window; the script waits up to **2 minutes**.

---

## Project structure

```
ev-gen/
├── main.py           # Entry point – CLI, alias generation, file saving
├── discord_gen.py    # Playwright registration + token extraction
├── gmail_verifier.py # Gmail login + auto-verify + manual fallback
├── requirements.txt  # Python dependencies
├── tokens.txt        # (generated) one token per line
├── acc.txt           # (generated) email:password:token per line
└── README.md
```

---

## License

MIT