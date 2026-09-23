import asyncio
import json
import base64
import httpx
import websockets

CDP_HTTP = "http://127.0.0.1:9222"
ARTIFACTS_DIR = r"C:\Users\anand\.gemini\antigravity-ide\brain\a91e385c-c6de-40af-8547-c85261077a7b"

class CDPClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.req_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=20*1024*1024)

    async def send(self, method, params=None):
        self.req_id += 1
        msg_id = self.req_id
        payload = {"id": msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(payload))
        while True:
            resp = await self.ws.recv()
            data = json.loads(resp)
            if data.get("id") == msg_id:
                if "error" in data:
                    raise Exception(f"CDP error {method}: {data['error']}")
                return data.get("result", {})

    async def eval_js(self, expression):
        res = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    async def capture_screenshot(self, filename):
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        img_bytes = base64.b64decode(res["data"])
        out_path = f"{ARTIFACTS_DIR}\\{filename}"
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        print(f"  [Screenshot saved] -> {out_path}")

    async def close(self):
        if self.ws:
            await self.ws.close()

async def create_new_target(url="about:blank"):
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{CDP_HTTP}/json/new?{url}")
        target = r.json()
        return target["webSocketDebuggerUrl"], target["id"]

async def close_target(target_id):
    async with httpx.AsyncClient() as client:
        await client.get(f"{CDP_HTTP}/json/close/{target_id}")

import subprocess
import os

async def main():
    print("=== STARTING BROWSER CDP VERIFICATION ===\n")
    
    edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    edge_cmd = [
        edge_bin,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        f"--user-data-dir={os.environ.get('TEMP', '.')}\\edge_verify_{int(asyncio.get_event_loop().time())}"
    ]
    edge_proc = subprocess.Popen(edge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for CDP endpoint to become ready
    for _ in range(20):
        await asyncio.sleep(0.5)
        try:
            async with httpx.AsyncClient(timeout=1.0) as cl:
                r = await cl.get(f"{CDP_HTTP}/json/version")
                if r.status_code == 200:
                    break
        except Exception:
            pass

    import atexit
    atexit.register(lambda: edge_proc.terminate() if edge_proc.poll() is None else None)

    # ---------------------------------------------------------
    # TEST 1: LOGIN PASSWORD EYE TOGGLE
    # ---------------------------------------------------------
    print(">>> 1. Testing Login Password Eye Toggle (login.html)...")
    ws_url, tid = await create_new_target("about:blank")
    cdp = CDPClient(ws_url)
    await cdp.connect()
    await cdp.send("Page.enable")
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/login.html"})
    await asyncio.sleep(1.2)

    # Verify initial state
    init_type = await cdp.eval_js("document.getElementById('password').type")
    has_toggle = await cdp.eval_js("!!document.getElementById('toggle1')")
    toggle_text = await cdp.eval_js("document.getElementById('toggle1').textContent.trim()")
    has_svg = await cdp.eval_js("!!document.querySelector('#toggle1 svg')")
    aria_init = await cdp.eval_js("document.getElementById('toggle1').getAttribute('aria-label')")

    print(f"  Initial input type: '{init_type}' (expected: 'password')")
    print(f"  Toggle button present: {has_toggle}")
    print(f"  Toggle text content: '{toggle_text}' (expected: empty, no 'show' text)")
    print(f"  Inline SVG icon present: {has_svg}")
    print(f"  Aria-label: '{aria_init}'")

    assert init_type == "password", "Login password type should initially be password"
    assert toggle_text == "", "Login toggle should not have 'show' text"
    assert has_svg is True, "Login toggle must contain SVG"

    # Click eye toggle -> reveals password
    await cdp.eval_js("document.getElementById('password').value = 'SecretTest123'")
    await cdp.eval_js("document.getElementById('toggle1').click()")
    await asyncio.sleep(0.2)

    revealed_type = await cdp.eval_js("document.getElementById('password').type")
    revealed_aria = await cdp.eval_js("document.getElementById('toggle1').getAttribute('aria-label')")
    print(f"  After 1st click input type: '{revealed_type}' (expected: 'text')")
    print(f"  After 1st click aria-label: '{revealed_aria}'")
    assert revealed_type == "text", "Password should be revealed as text"

    # Click eye toggle again -> hides password
    await cdp.eval_js("document.getElementById('toggle1').click()")
    await asyncio.sleep(0.2)

    hidden_type = await cdp.eval_js("document.getElementById('password').type")
    hidden_aria = await cdp.eval_js("document.getElementById('toggle1').getAttribute('aria-label')")
    print(f"  After 2nd click input type: '{hidden_type}' (expected: 'password')")
    print(f"  After 2nd click aria-label: '{hidden_aria}'")
    assert hidden_type == "password", "Password should be hidden again"

    await cdp.capture_screenshot("login_eye_verified.png")
    print("  [LOGIN EYE TEST] -> PASS\n")
    await cdp.close()
    await close_target(tid)

    # ---------------------------------------------------------
    # TEST 2: SIGNUP PASSWORD EYE TOGGLE & FORM SUBMISSION
    # ---------------------------------------------------------
    print(">>> 2. Testing Signup Password Eye Toggle & Registration (signup.html)...")
    ws_url, tid = await create_new_target("about:blank")
    cdp = CDPClient(ws_url)
    await cdp.connect()
    await cdp.send("Page.enable")
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/signup.html"})
    await asyncio.sleep(1.2)

    # Verify initial state
    s_init_type = await cdp.eval_js("document.getElementById('password').type")
    s_has_toggle = await cdp.eval_js("!!document.getElementById('toggle1')")
    s_toggle_text = await cdp.eval_js("document.getElementById('toggle1').textContent.trim()")
    s_has_svg = await cdp.eval_js("!!document.querySelector('#toggle1 svg')")

    print(f"  Initial input type: '{s_init_type}' (expected: 'password')")
    print(f"  Toggle button present: {s_has_toggle}")
    print(f"  Toggle text content: '{s_toggle_text}' (expected: empty, no 'show' text)")
    print(f"  Inline SVG icon present: {s_has_svg}")

    assert s_init_type == "password", "Signup password type should initially be password"
    assert s_toggle_text == "", "Signup toggle should not have 'show' text"
    assert s_has_svg is True, "Signup toggle must contain SVG"

    # Type password and click toggle
    await cdp.eval_js("document.getElementById('password').value = 'NewUserPass456'")
    await cdp.eval_js("document.getElementById('toggle1').click()")
    await asyncio.sleep(0.2)

    s_revealed_type = await cdp.eval_js("document.getElementById('password').type")
    print(f"  After 1st click input type: '{s_revealed_type}' (expected: 'text')")
    assert s_revealed_type == "text", "Signup password should be revealed as text"

    # Click toggle again
    await cdp.eval_js("document.getElementById('toggle1').click()")
    await asyncio.sleep(0.2)

    s_hidden_type = await cdp.eval_js("document.getElementById('password').type")
    print(f"  After 2nd click input type: '{s_hidden_type}' (expected: 'password')")
    assert s_hidden_type == "password", "Signup password should be hidden as password"

    # Test full signup submission
    new_user_email = f"signup_eye_test_{asyncio.get_event_loop().time()}@example.com"
    await cdp.eval_js(f"document.getElementById('name').value = 'Signup Eye Tester'")
    await cdp.eval_js(f"document.getElementById('email').value = '{new_user_email}'")
    await cdp.capture_screenshot("signup_eye_verified.png")

    # Click submit
    print("  Submitting signup form...")
    await cdp.eval_js("document.getElementById('signupForm').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))")
    await asyncio.sleep(1.5)

    current_url = await cdp.eval_js("window.location.href")
    has_token = await cdp.eval_js("!!localStorage.getItem('token') || !!localStorage.getItem('mithra_token')")
    print(f"  Post-signup URL: '{current_url}', Session created: {has_token}")
    assert "language.html" in current_url or has_token or "chat.html" in current_url, "Signup must successfully register user"

    print("  [SIGNUP EYE & FLOW TEST] -> PASS\n")
    await cdp.close()
    await close_target(tid)

    # ---------------------------------------------------------
    # TEST 3: CHAT CRISIS DETECTION & SAFETY / SOS UI
    # ---------------------------------------------------------
    print(">>> 3. Testing Chat Crisis Detection & SOS Action Card (chat.html)...")
    ws_url, tid = await create_new_target("about:blank")
    cdp = CDPClient(ws_url)
    await cdp.connect()
    await cdp.send("Page.enable")
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/login.html"})
    await asyncio.sleep(1.2)

    # Login with the user created in signup test
    await cdp.eval_js(f"document.getElementById('email').value = '{new_user_email}'")
    await cdp.eval_js("document.getElementById('password').value = 'NewUserPass456'")
    await cdp.eval_js("document.getElementById('loginForm').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))")
    await asyncio.sleep(1.5)

    # Navigate to chat.html
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/chat.html"})
    await asyncio.sleep(1.5)

    # Send "naa saava poren"
    print("  Sending high-risk Tanglish crisis message: 'naa saava poren'")
    await cdp.eval_js("document.getElementById('msgInput').value = 'naa saava poren'")
    await cdp.eval_js("document.getElementById('sendBtn').click()")

    # Wait for response (deterministic guardrail responds in < 50ms)
    await asyncio.sleep(1.2)

    # Verify Safety card and responses
    has_safety_card = await cdp.eval_js("!!document.querySelector('.safety-card')")
    safety_title = await cdp.eval_js("document.querySelector('.safety-card-title') ? document.querySelector('.safety-card-title').textContent : ''")
    has_telemanas = await cdp.eval_js("!!document.querySelector('.safety-btn-telemanas')")
    has_emergency = await cdp.eval_js("!!document.querySelector('.safety-btn-emergency')")
    has_sos = await cdp.eval_js("!!document.querySelector('.safety-btn-sos')")
    nav_sos_alert = await cdp.eval_js("document.getElementById('navSos') ? document.getElementById('navSos').classList.contains('sos-alert') : false")

    # Get last bubble text
    last_mithra_msg = await cdp.eval_js("""
        (() => {
            const bubbles = document.querySelectorAll('.bubble.mithra');
            return bubbles.length > 0 ? bubbles[bubbles.length - 1].textContent : '';
        })()
    """)

    print(f"  Safety card present: {has_safety_card}")
    print(f"  Safety card title: '{safety_title}'")
    print(f"  Tele-MANAS (14416) button present: {has_telemanas}")
    print(f"  Emergency (112) button present: {has_emergency}")
    print(f"  SOS Emergency Contacts button present: {has_sos}")
    print(f"  Navbar SOS alert highlight active: {nav_sos_alert}")
    clean_msg = last_mithra_msg[:80].encode('ascii', errors='replace').decode('ascii')
    print(f"  Last Mithra message snippet: {clean_msg}...")

    assert has_safety_card is True, "Safety card must be displayed"
    assert has_telemanas is True, "Tele-MANAS button must be present"
    assert has_emergency is True, "Emergency 112 button must be present"
    assert has_sos is True, "SOS button must be present"
    assert "Kayala padatheenga bro" not in last_mithra_msg, "Must not contain normal Qwen canned response"
    assert ("Tele-MANAS" in last_mithra_msg or "14416" in last_mithra_msg), "Mithra reply must provide crisis support resources"

    await cdp.capture_screenshot("chat_crisis_sos_verified.png")
    print("  [CHAT CRISIS SAFETY UI TEST] -> PASS\n")

    # ---------------------------------------------------------
    # TEST 4: VOICE MODE TOGGLE & STATE TRANSITIONS
    # ---------------------------------------------------------
    print(">>> 4. Testing Hands-free Voice Mode Toggle & State Machine (chat.html)...")
    has_voice_btn = await cdp.eval_js("!!document.getElementById('voiceModeBtn')")
    init_voice_lbl = await cdp.eval_js("document.getElementById('voiceModeLabel').textContent")
    print(f"  Voice Mode toggle button present: {has_voice_btn}")
    print(f"  Initial Voice Mode label: '{init_voice_lbl}'")

    # Click Voice Mode toggle -> ON
    await cdp.eval_js("document.getElementById('voiceModeBtn').click()")
    await asyncio.sleep(0.3)
    active_lbl = await cdp.eval_js("document.getElementById('voiceModeLabel').textContent")
    has_active_cls = await cdp.eval_js("document.getElementById('voiceModeBtn').classList.contains('active')")
    status_text = await cdp.eval_js("document.getElementById('voiceStatusBar').textContent")
    print(f"  After toggle ON label: '{active_lbl}'")
    print(f"  Active class present: {has_active_cls}")
    clean_status = status_text.encode('ascii', errors='replace').decode('ascii')
    print(f"  Status bar message: '{clean_status}'")

    assert has_voice_btn is True, "Voice Mode button must exist"
    assert "On" in active_lbl, "Voice Mode button should show 'Voice: On'"
    assert has_active_cls is True, "Voice Mode button should have active class"

    await cdp.capture_screenshot("chat_voice_mode_verified.png")

    # Click Voice Mode toggle -> OFF
    await cdp.eval_js("document.getElementById('voiceModeBtn').click()")
    await asyncio.sleep(0.3)
    off_lbl = await cdp.eval_js("document.getElementById('voiceModeLabel').textContent")
    print(f"  After toggle OFF label: '{off_lbl}'")
    assert "Off" in off_lbl, "Voice Mode button should show 'Voice: Off'"
    print("  [VOICE MODE TOGGLE TEST] -> PASS\n")

    await cdp.close()
    await close_target(tid)

    print(">>> ALL BROWSER UI TESTS PASSED SUCCESSFULLY! <<<")
    try:
        edge_proc.terminate()
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())
