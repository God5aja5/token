from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import subprocess
import random
import json
import re

app = Flask(__name__)

# Ensure Playwright browsers are installed at runtime
def ensure_playwright_installed():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Error installing Playwright browsers: {e}")

ensure_playwright_installed()

def run_playwright_task():
    random_texts = [
        "Make a simple calculator in Python",
        "Generate a todo list app in React",
        "Write HTML for a login form",
        "Give me CSS for a navbar"
    ]
    message = random.choice(random_texts)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            curl_command = None
            tokens = {}

            # Intercept network requests
            def handle_request(request):
                nonlocal curl_command, tokens
                url = request.url
                if "trigger?" in url and request.method == "POST":
                    headers = request.headers
                    post_data = request.post_data or ""

                    curl_command = {
                        "url": url,
                        "method": "POST",
                        "headers": headers,
                        "data": post_data
                    }

                    try:
                        body = json.loads(post_data)
                        for key, val in body.items():
                            if isinstance(val, str):
                                if re.match(r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$", val) or len(val) > 20:
                                    tokens[key] = val
                    except:
                        pass

            page.on("request", handle_request)

            # Visit site
            page.goto("https://workik.com/ai-code-generator", timeout=60000)
            page.wait_for_timeout(6000)

            # Click GPT 4.1 Mini button
            try:
                page.click("//span[contains(text(),'GPT 4.1 Mini')]", timeout=5000)
            except:
                pass

            # Type random message
            input_box = page.locator("div[contenteditable='true']")
            input_box.fill(message)

            # Click Send button
            send_btn = page.locator("button.MuiButtonBase-root.css-11uhnn1")
            send_btn.click()

            page.wait_for_timeout(10000)

            browser.close()

            return {
                "message_sent": message,
                "curl": curl_command,
                "tokens": tokens
            }

    except Exception as e:
        return {"error": str(e)}


@app.route("/token", methods=["GET"])
def get_token():
    result = run_playwright_task()
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
