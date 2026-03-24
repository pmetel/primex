import asyncio
from playwright.async_api import async_playwright
import http.server
import threading
import socket
import os

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

PORT = find_free_port()

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def run_server():
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

async def test_clamping():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"http://localhost:{PORT}/primex.html", wait_until="domcontentloaded")

        print("Testing Width Clamping (Max 1600)...")
        await page.fill("#inw", "9999")
        await page.dispatch_event("#inw", "change")
        val = await page.input_value("#inw")
        print(f"Width value after 9999: {val}")
        assert val == "1600"

        print("Testing Height Clamping (Max 1600)...")
        await page.fill("#inh", "2000")
        await page.dispatch_event("#inh", "change")
        val = await page.input_value("#inh")
        print(f"Height value after 2000: {val}")
        assert val == "1600"

        print("Testing Scale Clamping (Max 10)...")
        await page.fill("#ins", "50")
        await page.dispatch_event("#ins", "change")
        val = await page.input_value("#ins")
        print(f"Scale value after 50: {val}")
        assert val == "10"

        print("Testing Step Clamping (Max 1000)...")
        await page.fill("#instep", "5000")
        await page.dispatch_event("#instep", "change")
        val = await page.input_value("#instep")
        print(f"Step value after 5000: {val}")
        assert val == "1000"

        print("Testing Min Clamping (Min 1)...")
        await page.fill("#inw", "0")
        await page.dispatch_event("#inw", "change")
        val = await page.input_value("#inw")
        print(f"Width value after 0: {val}")
        assert val == "1"

        print("Testing XSS in tooltip (using textContent)...")
        await page.mouse.move(10, 10)
        content = await page.evaluate("document.getElementById('tooltip-status').innerHTML")
        print(f"Tooltip Status HTML: {content}")
        # The previous version used innerHTML = '<span>...</span>'
        # The new version uses textContent = '...'
        # So we should not see <span> in innerHTML
        assert "<span>" not in content

        print("Tests passed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_clamping())
