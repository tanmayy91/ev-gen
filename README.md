# ev-gen — Discord Account Generator (Educational)

> **⚠️ DISCLAIMER:** This project is provided **for educational purposes only**.  
> Creating multiple Discord accounts may violate [Discord's Terms of Service](https://discord.com/terms).  
> You are solely responsible for how you use this software.

---

## Features

- **Interactive CLI** — prompts you for your Gmail, a password, and account count
- **Gmail + alias trick** — derives unique registration addresses from a single inbox  
  `tanmayyyy38@gmail.com` → `tanmayyyy38+1@gmail.com`, `tanmayyyy38+2@gmail.com`, …
- **Human-in-the-loop CAPTCHA** — opens a real headed browser; solve any hCaptcha challenge from the Codespace **Ports / Preview** tab
- **Runs in GitHub Codespaces** — no local setup required

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 + |
| pip | any recent |

---

## Setup (Codespace / local)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download the Playwright browser binaries
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

⚠️  DISCLAIMER
   This tool is provided for EDUCATIONAL PURPOSES ONLY.
   …

Enter your Gmail address: tanmayyyy38@gmail.com
Enter password for new Discord accounts: ••••••••
How many accounts to create? (1–50): 3

  Will create 3 account(s) using these emails:
    • tanmayyyy38+1@gmail.com
    • tanmayyyy38+2@gmail.com
    • tanmayyyy38+3@gmail.com

Proceed? (y/n): y

  Starting browser… open the Codespace 'Ports' / preview tab if you need to interact with a CAPTCHA.

[1/3] Creating account → tanmayyyy38+1@gmail.com
  → Navigating to Discord registration page…
  → Filling registration form…
  → If a CAPTCHA appears in the browser, please solve it in the Codespace preview tab, then wait…
  ✓ Success! Username: EpicFox3821  (Account created – check your inbox to verify.)
…
```

---

## Codespace CAPTCHA guide

1. Open the **Ports** tab in VS Code (or the Codespace web UI).
2. Forward port **6080** (VNC) or use the built-in **Simple Browser** to view the headed Chromium window.
3. Solve the hCaptcha when prompted, then the script continues automatically.

---

## Project structure

```
ev-gen/
├── main.py          # Entry point – CLI, email alias generation
├── discord_gen.py   # Playwright automation core
├── requirements.txt # Python dependencies
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE) for details.