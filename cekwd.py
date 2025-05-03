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
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"https://{situs}/#/index?category=lottery", wait_until="domcontentloaded", timeout=60000)

        try:
            page.get_by_role("img", name="close").click()
        except:
            pass

        with page.expect_popup() as popup_info:
            page.get_by_role("heading", name="HOKI DRAW").click()
        page1 = popup_info.value

        page1.locator("input#loginUser").wait_for()
        page1.locator("input#loginUser").type(userid, delay=100)
        page1.locator("input#loginPsw").type(pw, delay=120)
        page1.locator("div.login-btn").click()

        try:
            page1.get_by_role("link", name="Saya Setuju").click()
        except:
            pass

        time.sleep(3)  # tunggu saldo muncul

        saldo_text = page1.locator("span.overage-num").inner_text().strip()
        saldo_value = parse_saldo(saldo_text)

        # Ambil status paling atas dari halaman hasil
        page1.get_by_role("link", name="TRANSAKSI HISTORY TRANSAKSI").click()
        time.sleep(3)
        rows = page1.query_selector_all("table tbody tr")
        status_text = "-"
        if rows:
            cols = rows[0].query_selector_all("td")
            if len(cols) >= 6:
                raw_status = cols[5].inner_text().strip()
                if "WIN" in raw_status.upper():
                    status_text = "Menang"
                else:
                    status_text = "Tidak ada Kemenangan"


        pesan = (
            f"<b>[STATUS]</b>\n"
            f"👤 {userid}\n"
            f"💰 SALDO: <b>Rp {saldo_value:,.0f}</b>\n"
            f"🎯 <b>{status_text}</b>\n"
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
                continue  # <-- Lewati baris komentar
            parts = baris.strip().split('|')
            if len(parts) != 4:
                continue
            situs, userid, bet_raw, bet_raw2 = parts
            run(playwright, situs.strip(), userid.strip(), bet_raw.strip(), bet_raw2.strip())

if __name__ == "__main__":
    main()
