import asyncio
import json
import base64
import os
import subprocess
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
        print(f"  [Screenshot saved] -> {out_path}", flush=True)

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

async def main():
    print("=== STARTING PICK MY HOBBY VERIFICATION ===\n", flush=True)

    edge_bin = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    edge_cmd = [
        edge_bin,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        f"--user-data-dir={os.environ.get('TEMP', '.')}\\edge_hobby_{int(asyncio.get_event_loop().time())}"
    ]
    edge_proc = subprocess.Popen(edge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

    ws_url, tid = await create_new_target("about:blank")
    cdp = CDPClient(ws_url)
    await cdp.connect()
    await cdp.send("Page.enable")

    # 1. Login first to get authenticated session
    print("[1] Logging in to access Home...", flush=True)
    user_email = f"hobby_user_{int(asyncio.get_event_loop().time())}@test.com"
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/signup.html"})
    await asyncio.sleep(1.2)
    await cdp.eval_js(f"document.getElementById('name').value = 'Hobby User'")
    await cdp.eval_js(f"document.getElementById('email').value = '{user_email}'")
    await cdp.eval_js(f"document.getElementById('password').value = 'HobbyPass123'")
    await cdp.eval_js("document.getElementById('signupForm').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))")
    await asyncio.sleep(1.5)

    # 2. Test Home opens normally & "Pick my hobby" is visible
    print("[2] Navigating to Home (chat.html)...", flush=True)
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/chat.html"})
    await asyncio.sleep(1.5)

    is_heading_visible = await cdp.eval_js("!!document.querySelector('.hobby-heading') && document.querySelector('.hobby-heading').textContent.trim() === 'Pick my hobby'")
    subtext = await cdp.eval_js("document.querySelector('.hobby-sub') ? document.querySelector('.hobby-sub').textContent.trim() : ''")
    chips_count = await cdp.eval_js("document.querySelectorAll('.hobby-chip').length")
    print(f"  Heading 'Pick my hobby' visible: {is_heading_visible}", flush=True)
    print(f"  Supporting text: '{subtext}'", flush=True)
    print(f"  Hobby chips count: {chips_count} (expected: 7)", flush=True)

    assert is_heading_visible, "Heading 'Pick my hobby' is not visible"
    assert "Choose what you enjoy" in subtext, "Supporting text missing or incorrect"
    assert chips_count >= 7, f"Expected at least 7 chips, found {chips_count}"

    # 3. Click 'Listening to music' -> selected state appears
    print("\n[3] Testing 'Listening to music' selection...", flush=True)
    await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').click()")
    await asyncio.sleep(0.3)

    music_selected = await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').classList.contains('selected')")
    music_aria = await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').getAttribute('aria-pressed')")
    hobbies_storage = await cdp.eval_js("localStorage.getItem('mithra_hobbies')")
    print(f"  Music selected class: {music_selected}", flush=True)
    print(f"  Music aria-pressed: {music_aria}", flush=True)
    print(f"  localStorage 'mithra_hobbies': {hobbies_storage}", flush=True)
    assert music_selected is True, "Music should have 'selected' class"
    assert music_aria == "true", "Music should have aria-pressed='true'"
    assert "music" in json.loads(hobbies_storage), "music should be saved in localStorage"

    # 4. Click 'Drawing' -> both can remain selected (multi-select)
    print("\n[4] Testing multi-select with 'Drawing'...", flush=True)
    await cdp.eval_js("document.querySelector('[data-hobby=\"drawing\"]').click()")
    await asyncio.sleep(0.3)

    drawing_selected = await cdp.eval_js("document.querySelector('[data-hobby=\"drawing\"]').classList.contains('selected')")
    music_still_selected = await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').classList.contains('selected')")
    hobbies_storage = await cdp.eval_js("localStorage.getItem('mithra_hobbies')")
    print(f"  Drawing selected class: {drawing_selected}", flush=True)
    print(f"  Music still selected: {music_still_selected}", flush=True)
    print(f"  localStorage 'mithra_hobbies': {hobbies_storage}", flush=True)
    assert drawing_selected is True, "Drawing should be selected"
    assert music_still_selected is True, "Music should remain selected (multi-select)"
    stored_list = json.loads(hobbies_storage)
    assert "music" in stored_list and "drawing" in stored_list, "Both music and drawing must be in localStorage"

    # 5. Refresh page -> selections remain
    print("\n[5] Refreshing page to verify persistence...", flush=True)
    await cdp.send("Page.reload")
    await asyncio.sleep(1.5)

    music_post_refresh = await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').classList.contains('selected')")
    drawing_post_refresh = await cdp.eval_js("document.querySelector('[data-hobby=\"drawing\"]').classList.contains('selected')")
    print(f"  Music selected post-refresh: {music_post_refresh}", flush=True)
    print(f"  Drawing selected post-refresh: {drawing_post_refresh}", flush=True)
    assert music_post_refresh is True, "Music should remain selected after reload"
    assert drawing_post_refresh is True, "Drawing should remain selected after reload"

    # 6. Unselect Music -> Drawing remains selected
    print("\n[6] Unselecting 'Music'...", flush=True)
    await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').click()")
    await asyncio.sleep(0.3)

    music_after_unselect = await cdp.eval_js("document.querySelector('[data-hobby=\"music\"]').classList.contains('selected')")
    drawing_after_unselect = await cdp.eval_js("document.querySelector('[data-hobby=\"drawing\"]').classList.contains('selected')")
    hobbies_storage = await cdp.eval_js("localStorage.getItem('mithra_hobbies')")
    print(f"  Music selected after unselect: {music_after_unselect}", flush=True)
    print(f"  Drawing selected after unselect: {drawing_after_unselect}", flush=True)
    print(f"  localStorage: {hobbies_storage}", flush=True)
    assert music_after_unselect is False, "Music should be unselected"
    assert drawing_after_unselect is True, "Drawing must remain selected"
    assert "drawing" in json.loads(hobbies_storage), "Drawing must remain in localStorage"
    assert "music" not in json.loads(hobbies_storage), "Music must be removed from localStorage"

    # 7 & 8. Navigate away from Home (e.g. to Diary) and return -> Drawing remains selected
    print("\n[7 & 8] Navigating to Diary and returning Home...", flush=True)
    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/diary.html"})
    await asyncio.sleep(1.2)
    diary_url = await cdp.eval_js("window.location.href")
    print(f"  Navigated to: {diary_url}", flush=True)

    await cdp.send("Page.navigate", {"url": "http://127.0.0.1:4000/chat.html"})
    await asyncio.sleep(1.5)

    drawing_after_nav = await cdp.eval_js("document.querySelector('[data-hobby=\"drawing\"]').classList.contains('selected')")
    print(f"  Drawing selected after returning Home: {drawing_after_nav}", flush=True)
    assert drawing_after_nav is True, "Drawing should remain selected after navigation"

    # Capture Desktop Screenshot
    await cdp.capture_screenshot("home_pick_my_hobby_desktop.png")

    # 9. Test at ~390px mobile width -> no horizontal overflow
    print("\n[9] Testing at 390px mobile viewport...", flush=True)
    await cdp.send("Emulation.setDeviceMetricsOverride", {
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    await asyncio.sleep(0.5)

    doc_scroll_width = await cdp.eval_js("document.documentElement.scrollWidth")
    win_inner_width = await cdp.eval_js("window.innerWidth")
    hobby_scroll_width = await cdp.eval_js("document.getElementById('hobbySection').scrollWidth")
    hobby_client_width = await cdp.eval_js("document.getElementById('hobbySection').clientWidth")
    print(f"  Window width: {win_inner_width}px, Document scrollWidth: {doc_scroll_width}px", flush=True)
    print(f"  HobbySection clientWidth: {hobby_client_width}px, scrollWidth: {hobby_scroll_width}px", flush=True)

    has_overflow = doc_scroll_width > win_inner_width or hobby_scroll_width > hobby_client_width
    print(f"  Horizontal overflow detected: {has_overflow}", flush=True)
    assert not has_overflow, "Horizontal overflow detected on mobile viewport!"

    await cdp.capture_screenshot("home_pick_my_hobby_mobile_390px.png")

    # 10. Ask MITHRA regression test -> sending message still works
    print("\n[10] Testing Ask MITHRA regression (sending message)...", flush=True)
    await cdp.eval_js("document.getElementById('msgInput').value = 'Hey Mithra, testing hobby integration'")
    await cdp.eval_js("document.getElementById('sendBtn').click()")
    # Wait for response
    await asyncio.sleep(8.0)

    bubble_count = await cdp.eval_js("document.querySelectorAll('.bubble').length")
    last_mithra_reply = await cdp.eval_js("""
        (() => {
            const bubbles = document.querySelectorAll('.bubble.mithra');
            return bubbles.length > 0 ? bubbles[bubbles.length - 1].textContent : '';
        })()
    """)
    print(f"  Total bubbles: {bubble_count}", flush=True)
    print(f"  Last reply snippet: {last_mithra_reply[:60]}...", flush=True)
    assert bubble_count >= 2, "Expected at least 2 bubbles after sending"
    assert len(last_mithra_reply) > 0, "Mithra reply must not be empty"

    print("\n>>> ALL 10 TESTS PASSED! <<<", flush=True)
    await cdp.close()
    await close_target(tid)
    edge_proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
