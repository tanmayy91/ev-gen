# ev-gen — Discord Account Generator (Educational)

> **⚠️ DISCLAIMER:** This project is provided **for educational purposes only**.  
> Creating multiple Discord accounts may violate [Discord's Terms of Service](https://discord.com/terms).  
> You are solely responsible for how you use this software.

---

## 📱 Android APK — Download

The GitHub Actions workflow automatically builds a debug APK on every push.

### How to get the APK

1. Go to the **Actions** tab of this repository:  
   `https://github.com/tanmayy91/ev-gen/actions`
2. Click the latest **"Build APK"** workflow run.
3. If the run shows **"Action required"**, click **"Approve and run"** (repo owner only — required once for new workflows).
4. Wait for the build to finish (≈ 5–8 minutes).
5. Under **Artifacts**, download **`DiscordGen-debug`** (a `.zip` containing `app-debug.apk`).
6. Unzip and install the APK on your Android phone (enable *Install unknown apps* in Settings → Security).

> Artifacts are kept for **90 days**.

---

## Features

### Android app (APK)

| Feature | Details |
|---|---|
| **Terminal-style input** | Enter Gmail address, Gmail password, Discord password, and account count (1–50) |
| **Gmail + alias trick** | Generates unique 4-char random aliases: `user+a3kj@gmail.com`, `user+bq9x@gmail.com`, … |
| **Built-in browser** | Full-screen WebView opens `discord.com/register` directly in the app |
| **Auto form fill** | JS injection fills email, username, password, and date of birth automatically |
| **Manual CAPTCHA** | hCaptcha is left for the user to solve manually in the in-app browser |
| **Email verification** | After registration, the browser opens Gmail so you can verify the email, then tap "Verification Done → Next Account" |
| **Token capture** | Intercepts Discord's `/auth/register` fetch response to extract the auth token |
| **Download screen** | View `tokens.txt` and `acc.txt` content inside the app; share/download via any Android app |
| **Live progress log** | Scrollable terminal-style log at the bottom of the main screen |

### Python CLI (Codespace / desktop)

| Feature | Details |
|---|---|
| **Interactive CLI** | Prompts for Gmail, Gmail password, Discord password, and account count |
| **Gmail + alias trick** | Derives unique registration addresses from one inbox |
| **Manual CAPTCHA solving** | Headed browser stays visible — solve hCaptcha in the Codespace preview tab |
| **Auto Gmail verification** | Logs into Gmail, finds the Discord verification email, and clicks the link automatically |
| **Token capture** | Intercepts the Discord `/auth/register` API response to extract the auth token |
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
├── app/                          # Android app (Kotlin)
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/evgen/discordgen/
│       │   ├── MainActivity.kt           # Input UI + live log
│       │   ├── DiscordWebViewActivity.kt # Built-in browser + token capture
│       │   ├── AliasGenerator.kt         # Gmail+ alias generation
│       │   ├── TokenStore.kt             # tokens.txt / acc.txt file I/O
│       │   └── DownloadActivity.kt       # View & share output files
│       └── res/
│           ├── layout/                   # XML layouts
│           ├── values/                   # Strings, colors, themes
│           └── xml/file_provider_paths.xml
├── .github/workflows/build-apk.yml  # CI: builds & uploads debug APK
├── main.py           # Python CLI – Entry point
├── discord_gen.py    # Playwright registration + token extraction
├── gmail_verifier.py # Gmail login + auto-verify + manual fallback
├── requirements.txt  # Python dependencies
└── README.md
```

---

## License

MIT