import asyncio
import json
import urllib.request
import websockets
import base64
import os
import subprocess
import tempfile
import time

CDP_HTTP = "http://localhost:9222/json"

async def run_tests():
    print("=" * 60, flush=True)
    print("       MITHRA LOGIN PASSWORD EYE TOGGLE VERIFICATION", flush=True)
    print("=" * 60, flush=True)

    # Launch Chrome headless with remote debugging port
    temp_profile = tempfile.mkdtemp()
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    print(f"Launching Chrome: {chrome_path} on port 9222...", flush=True)
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={temp_profile}",
        "http://localhost:4000/login.html"
    ])

    try:
        # Wait for CDP endpoint to become ready
        targets = []
        for _ in range(30):
            try:
                with urllib.request.urlopen(CDP_HTTP, timeout=1) as resp:
                    targets = json.loads(resp.read().decode())
                    if targets:
                        break
            except Exception:
                await asyncio.sleep(0.5)

        target = None
        for t in targets:
            if t.get("type") == "page":
                target = t
                break
        if not target:
            target = targets[0]

        ws_url = target["webSocketDebuggerUrl"]
        print(f"Connected to Chrome CDP: {ws_url} (target: {target.get('title')}, {target.get('url')})", flush=True)

        async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
            msg_id = 0

            async def send_cmd(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=15)
                    res = json.loads(raw)
                    if res.get("id") == msg_id:
                        return res.get("result", {})

            async def eval_js(expression):
                res = await send_cmd("Runtime.evaluate", {
                    "expression": expression,
                    "returnByValue": True,
                    "awaitPromise": True
                })
                if "exceptionDetails" in res:
                    print("JS Exception:", res["exceptionDetails"], flush=True)
                return res.get("result", {}).get("value")

            # Navigate to login.html
            print("\n[Step 1] Navigating to http://localhost:4000/login.html...", flush=True)
            await send_cmd("Page.navigate", {"url": "http://localhost:4000/login.html"})
            await asyncio.sleep(2.0)

            url = await eval_js("window.location.href")
            title = await eval_js("document.title")
            print(f"Navigated to: {url} ('{title}')", flush=True)

            # 2. Check initial UI state
            print("\n[Step 2] Checking initial password field UI...", flush=True)
            check1 = await eval_js("""
            (() => {
                const toggleBtn = document.getElementById('toggle1');
                const pwInput = document.getElementById('password');
                const wrap = document.querySelector('.pw-wrap');

                if (!toggleBtn || !pwInput || !wrap) {
                    return { error: 'elements not found', url: window.location.href, title: document.title, body: document.body.innerHTML };
                }

                const btnText = toggleBtn.textContent.trim();
                const hasSvg = !!toggleBtn.querySelector('svg');
                const inputType = pwInput.type;
                const ariaLabel = toggleBtn.getAttribute('aria-label');
                const title = toggleBtn.getAttribute('title');

                // Bounding box metrics
                const wrapRect = wrap.getBoundingClientRect();
                const inputRect = pwInput.getBoundingClientRect();
                const btnRect = toggleBtn.getBoundingClientRect();

                // Check if button is vertically centered and inside the right side of the input
                const isInsideInput = (btnRect.right <= inputRect.right + 2) && (btnRect.left > inputRect.left);
                const inputCenterY = inputRect.top + inputRect.height / 2;
                const btnCenterY = btnRect.top + btnRect.height / 2;
                const isVerticallyCentered = Math.abs(inputCenterY - btnCenterY) < 4;

                return {
                    btnText,
                    hasSvg,
                    inputType,
                    ariaLabel,
                    title,
                    isInsideInput,
                    isVerticallyCentered,
                    btnRect,
                    inputRect
                };
            })()
            """)
            print("Initial state check:", json.dumps(check1, indent=2), flush=True)

            assert check1["btnText"] == "", f"'show' text is still present! Text: '{check1['btnText']}'"
            assert check1["hasSvg"], "No eye SVG icon found inside toggle button!"
            assert check1["inputType"] == "password", f"Default input type is not password: {check1['inputType']}"
            assert check1["isInsideInput"], "Toggle button is not inside the input field!"
            assert check1["isVerticallyCentered"], "Toggle button is not vertically centered!"
            print("CONFIRMED: 'show' text is completely removed; eye SVG is vertically centered inside input.", flush=True)

            # 3. Enter sample password and click eye toggle to show
            print("\n[Step 3] Clicking eye toggle to reveal password...", flush=True)
            await eval_js("""
                document.getElementById('password').value = 'MithraSecure2026!';
                document.getElementById('toggle1').click();
            """)
            await asyncio.sleep(0.3)

            check2 = await eval_js("""
            (() => {
                const toggleBtn = document.getElementById('toggle1');
                const pwInput = document.getElementById('password');
                const svg = toggleBtn.querySelector('svg');
                return {
                    inputType: pwInput.type,
                    ariaLabel: toggleBtn.getAttribute('aria-label'),
                    title: toggleBtn.getAttribute('title'),
                    isEyeOff: svg ? (svg.innerHTML.includes('line') || svg.classList.contains('eye-off-icon')) : false
                };
            })()
            """)
            print("After click 1 (revealed):", json.dumps(check2, indent=2), flush=True)
            assert check2["inputType"] == "text", f"Password input did not switch to 'text': {check2['inputType']}"
            assert check2["isEyeOff"], "Eye icon did not switch to eye-off SVG!"
            assert check2["ariaLabel"] == "Hide password", "Aria-label did not update to 'Hide password'!"
            print("CONFIRMED: Password revealed (type='text') and icon switched to eye-off.", flush=True)

            # 4. Click eye toggle again to hide
            print("\n[Step 4] Clicking eye toggle again to hide password...", flush=True)
            await eval_js("document.getElementById('toggle1').click();")
            await asyncio.sleep(0.3)

            check3 = await eval_js("""
            (() => {
                const toggleBtn = document.getElementById('toggle1');
                const pwInput = document.getElementById('password');
                const svg = toggleBtn.querySelector('svg');
                return {
                    inputType: pwInput.type,
                    ariaLabel: toggleBtn.getAttribute('aria-label'),
                    title: toggleBtn.getAttribute('title'),
                    isEyeClosed: svg ? (!svg.innerHTML.includes('line')) : false
                };
            })()
            """)
            print("After click 2 (hidden):", json.dumps(check3, indent=2), flush=True)
            assert check3["inputType"] == "password", f"Password input did not switch back to 'password': {check3['inputType']}"
            assert check3["isEyeClosed"], "Icon did not switch back to standard eye SVG!"
            assert check3["ariaLabel"] == "Show password", "Aria-label did not update back to 'Show password'!"
            print("CONFIRMED: Password hidden (type='password') and icon switched back to eye.", flush=True)

            # 5. Capture screenshot of the login password field
            screenshot_data = await send_cmd("Page.captureScreenshot", {"format": "png"})
            artifact_path = os.path.join(r"C:\Users\anand\.gemini\antigravity-ide\brain\a91e385c-c6de-40af-8547-c85261077a7b", "login_eye_verified.png")
            with open(artifact_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data["data"]))
            print(f"Login screenshot saved to: {artifact_path}", flush=True)

            # 6. Test Login form submission regression test
            print("\n[Step 5] Testing Login submission regression test...", flush=True)
            await eval_js("""
                document.getElementById('email').value = 'test@example.com';
                document.getElementById('password').value = 'password123';
                document.getElementById('submitBtn').click();
            """)
            
            login_success = False
            for _ in range(15):
                await asyncio.sleep(0.5)
                url = await eval_js("window.location.pathname")
                if "chat.html" in url:
                    login_success = True
                    print(f"Login succeeded! Redirected to: {url}", flush=True)
                    break

            assert login_success, "Login form submission failed or did not redirect to chat.html!"
            print("CONFIRMED: Login regression test passed.", flush=True)

            print("\n" + "=" * 60, flush=True)
            print("          ALL LOGIN EYE TESTS PASSED", flush=True)
            print("=" * 60, flush=True)

    finally:
        print("Closing Chrome...", flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(run_tests())
