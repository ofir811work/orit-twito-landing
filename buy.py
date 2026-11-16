"""Attach to your running Chrome (logged in to amazon.in), reload the product page
until Buy Now is available at <= MAX_PRICE, click it, and continue to checkout.

Setup (once, on the Mac):
  pip3 install playwright
  1. Quit Chrome completely (Cmd+Q).
  2. Start it with a debug port and a dedicated profile folder:
       /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
         --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-amz"
  3. In that window log in to amazon.in once (the session is kept in that folder).
Run: python3 buy.py
"""
import random
import re
import subprocess
import time
from playwright.sync_api import sync_playwright

ASIN = "B07K6RYVJ5"
URL = f"https://www.amazon.in/dp/{ASIN}?psc=1"
AUTO_PLACE_ORDER = True    # True = click "Place your order" too. False = stop on the review page and alert you.
INTERVAL = (15, 30)
CDP = "http://localhost:9222"
NUM = "123"                # 3-digit code for the payment step; edit locally on the Mac
USE_HOURS = False          # False = check all the time. True = only between START and END (Mac local time)
START = "09:00"            # HH:MM; END earlier than START means overnight, e.g. 22:00 -> 02:00
END = "23:00"

def log(*args):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *args, flush=True)


def in_window():
    if not USE_HOURS:
        return True
    now = time.strftime("%H:%M")
    return START <= now < END if START <= END else (now >= START or now < END)

def notify(msg):
    print(msg, flush=True)
    subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "Amazon" sound name "Glass"'])
    subprocess.Popen(["say", msg])

def price_of(page):
    for sel in ("span.a-price span.a-offscreen", ".a-price-whole"):
        loc = page.locator(sel).first
        if loc.count():
            digits = re.sub(r"[^\d.]", "", loc.inner_text().split(".")[0]) or None
            if digits:
                return int(digits)
    return None

def first_visible(page, selectors, timeout=8000):
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for s in selectors:
            loc = page.locator(s).first
            if loc.count() and loc.is_visible():
                return loc
        time.sleep(0.2)
    return None

NUM_FIELD = ['input[name*="cvv" i]', 'input[name*="cvc" i]', 'input[name*="VerificationNumber" i]',
             'input[placeholder*="CVV" i]', 'input[aria-label*="CVV" i]', 'input[aria-label*="security code" i]']


def fill_num(page):
    f = first_visible(page, NUM_FIELD, 1500)
    if f and not f.input_value():
        f.fill(NUM)
        return True
    return False

def checkout(page):
    # Buy Now may land on a "choose address / payment" step; click through the Continue/Deliver buttons.
    advance = ['input[name="ppw-widgetEvent:SetPaymentPlanSelectContinueEvent"]',
               'input[name="ppw-widgetEvent:UseSelectedPaymentMethodEvent"]',
               'input[data-testid="Address_selectShipToThisAddress"]',
               'input[name="shipToThisAddressButton"]', 'text=Deliver to this address',
               'text=Use this payment method', 'text=Continue']
    place = ['#placeOrder', 'input[name="placeYourOrder1"]', 'text=Place your order',
             'text=Place order and pay']
    for _ in range(8):
        page.wait_for_load_state("domcontentloaded")
        btn = first_visible(page, place, 3000)
        if btn:
            if AUTO_PLACE_ORDER:
                btn.click()
                notify("Order placed")
            else:
                notify("At final review page - check and press Place your order")
            return True
        fill_num(page)
        nxt = first_visible(page, advance, 3000)
        if not nxt:
            return False  # no CVV / address / payment / place-order step: the "quantity 0" dead end
        nxt.click()
        time.sleep(1.5)
    return False

def main():
    subprocess.Popen(["caffeinate", "-ism", "-w", str(__import__("os").getpid())])
    log("started", URL, f"hours {START}-{END}" if USE_HOURS else "hours: always")
    checks = tries = 0    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        page = ctx.new_page()
            if not in_window():
                log(f"outside {START}-{END}, waiting...")
                time.sleep(60)
                continue
            try:
                checks += 1
                page.goto(URL, wait_until="domcontentloaded")
                buy = page.locator("#buy-now-button, input[name='submit.buy-now']").first
                found = buy.count() and buy.is_visible()
                log(f"check #{checks}:", "BUY NOW visible" if found else "not available", f"price={price_of(page)}")
                if found:
                    tries += 1
                    log(f"clicking Buy Now (attempt #{tries})")
                    buy.click()
                    if checkout(page):
                        log("done")
                        return
                    log("dead end after Buy Now, retrying now")
                    continue  # straight back to the product page, no sleep
            except Exception as e:
                log("error:", e)
            wait = random.uniform(*INTERVAL)
            log(f"next check in {wait:.0f}s")
            time.sleep(wait)

if __name__ == "__main__":
    main()
