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
            return
        nxt = first_visible(page, advance, 3000)
        if not nxt:
            notify("Stopped on an unexpected step - finish manually")
            return
        nxt.click()
        time.sleep(1.5)

def main():
    subprocess.Popen(["caffeinate", "-i", "-w", str(__import__("os").getpid())])
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        page = ctx.new_page()
        while True:
            try:
                page.goto(URL, wait_until="domcontentloaded")
                buy = page.locator("#buy-now-button, input[name='submit.buy-now']").first
                price = price_of(page)
                print(time.strftime("%H:%M:%S"), "buy-now" if buy.count() else "out", price, flush=True)
                if buy.count() and buy.is_visible():
                    buy.click()
                    checkout(page)
                    return
            except Exception as e:
                print("error:", e, flush=True)
            time.sleep(random.uniform(*INTERVAL))
if __name__ == "__main__":
    main()
