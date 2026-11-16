#!/usr/bin/env python3
"""
Deploy CareerSniper to Railway or Render via their CLIs.
Run: python deploy.py
"""
import subprocess, sys, os, webbrowser

PLATFORM = os.environ.get("DEPLOY_TO", "railway")  # or "render"

def run(cmd):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode

print("""
╔══════════════════════════════════════════════╗
║   CareerSniper AI — Deployment Assistant     ║
╚══════════════════════════════════════════════╝

Choose your hosting platform:
  1. Railway (Recommended — free tier, 1-click deploy)
  2. Render  (Free tier, also beginner-friendly)
""")

choice = input("Enter 1 or 2: ").strip()

if choice == "1":
    print("\n🚂 Deploying to Railway...")
    print("\nStep 1: Install Railway CLI if needed...")
    if run("railway --version") != 0:
        print("Installing Railway CLI via npm...")
        if run("npm install -g @railway/cli") != 0:
            print("npm not found. Please install Node.js first: https://nodejs.org")
            sys.exit(1)

    print("\nStep 2: Login to Railway (browser will open)...")
    run("railway login")

    print("\nStep 3: Initialize Railway project...")
    run("railway init")

    print("\nStep 4: Deploy...")
    if run("railway up") == 0:
        print("\n✅ Deployed! Getting your public URL...")
        run("railway open")
    else:
        print("\n❌ Deploy failed. Try manually: https://railway.app")

elif choice == "2":
    print("\n🌐 Deploying to Render...")
    print("\nRender requires a GitHub repository.")
    print("Please:")
    print("  1. Push this folder to a GitHub repo")
    print("  2. Go to https://render.com → New → Web Service")
    print("  3. Connect your GitHub repo")
    print("  4. Set Build Command: pip install -r requirements.txt")
    print("  5. Set Start Command: gunicorn app:app")
    print("  6. Click Deploy!")
    webbrowser.open("https://render.com")
else:
    print("Invalid choice.")
