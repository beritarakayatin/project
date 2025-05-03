import os
import time
from datetime import datetime
import pytz
import requests
from playwright.sync_api import sync_playwright

# Ambil dari environment
pw = os.getenv("pw")
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

wib = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M WIB")

def baca_file(file_name: str) -> str:
    with open(file_name, 'r') as file:
        return file.read().strip()

def kirim_telegram(pesan: str):
    print(pesan)
    if telegram_token and telegram_chat_id:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                data={
                    "chat_id": telegram_chat_id,
                    "text": pesan,
                    "parse_mode": "HTML"
                }
            )
            if response.status_code != 200:
                print(f"Gagal kirim ke Telegram. Status: {response.status_code}")
        except Exception as e:
            print("Error saat kirim ke Telegram:", e)

def parse_saldo(text: str) -> float:
    text = text.replace("Rp.", "").replace("Rp", "").strip().replace(",", "")
    return float(text)

def run(playwright, situs, userid, *_):
    cek_saldo_dan_status(playwright, situs, userid)

def cek_saldo_dan_status(playwright, situs, userid):
    try:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 🔹 1️⃣ LOGIN dan cek saldo di halaman /mine
        page.goto(f"https://{situs}/#/mine", wait_until="domcontentloaded", timeout=60000)

        page.locator("input#loginUser").wait_for()
        page.locator("input#loginUser").type(userid, delay=100)
        page.locator("input#loginPsw").type(pw, delay=120)
        page.locator("div.login-btn").click()

        try:
            page.get_by_role("link", name="Saya Setuju").click()
        except:
            pass

        time.sleep(3)

        # 🔹 2️⃣ Ambil saldo dari <li class="myPurse">
        saldo_text = page.locator(".myPurse span i").inner_text().strip()
        saldo_value = parse_saldo(saldo_text)

        # 🔹 3️⃣ Ambil Nama Permainan terbaru dari betRecords
        page.goto(f"https://{situs}/#/betRecords")
        page.get_by_text("Togel").click()

        page.locator(".list .ls-list-item").first.wait_for(timeout=10000)
        first_item = page.locator(".list .ls-list-item").first
        nama_permainan = first_item.locator("li").nth(2).inner_text().strip()

        # 🔹 4️⃣ Cek apakah ada kata 'Menang'
        if "Menang" in nama_permainan:
            status_permainan = "🏆 Menang"
        else:
            status_permainan = "🥲 Tidak menang"

        # 🔹 5️⃣ Kirim pesan Telegram
        pesan = (
            f"<b>[STATUS]</b>\n"
            f"👤 {userid}\n"
            f"💰 SALDO: <b>Rp {saldo_value:,.0f}</b>\n"
            f"{status_permainan}\n"
            f"⌚ {wib}"
        )
        kirim_telegram(pesan)

        context.close()
        browser.close()

    except Exception as e:
        kirim_telegram(f"<b>[ERROR]</b>\n👤 {userid}\n❌ {e}\n⌚ {wib}")

def main():
    bets = baca_file("multi.txt").splitlines()
    with sync_playwright() as playwright:
        for baris in bets:
            if '|' not in baris:
                continue
            if baris.strip().startswith("#"):
                continue  # Lewati baris komentar
            parts = baris.strip().split('|')
            if len(parts) != 4:
                continue
            situs, userid, bet_raw, bet_raw2 = parts
            run(playwright, situs.strip(), userid.strip(), bet_raw.strip(), bet_raw2.strip())

if __name__ == "__main__":
    main()
