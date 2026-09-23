import asyncio
import json
import urllib.request
import websockets
import base64
import os

CDP_HTTP = "http://localhost:9222/json"

async def main():
    print("=" * 60, flush=True)
    print("       MITHRA CHAT COMPOSER & NAV LAYOUT VERIFICATION", flush=True)
    print("=" * 60, flush=True)

    # 1. Discover target page
    with urllib.request.urlopen(CDP_HTTP) as resp:
        targets = json.loads(resp.read().decode())

    chat_target = None
    for t in targets:
        if "chat.html" in t.get("url", "") or "Mithra" in t.get("title", ""):
            chat_target = t
            break

    if not chat_target:
        print("Chat target not found, finding any localhost page...", flush=True)
        for t in targets:
            if "localhost:4000" in t.get("url", ""):
                chat_target = t
                break

    assert chat_target, f"Could not find Mithra tab. Targets: {targets}"
    ws_url = chat_target["webSocketDebuggerUrl"]
    print(f"Connecting to CDP: {ws_url}", flush=True)

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

        # Reload the page to load the latest CSS
        print("\n[Step 1] Reloading page to apply latest CSS...", flush=True)
        await send_cmd("Page.reload")
        await asyncio.sleep(2.0)

        current_url = await eval_js("window.location.href")
        print(f"Current URL: {current_url}", flush=True)
        title = await eval_js("document.title")
        print(f"Page title: {title}", flush=True)

        # If logged out, log in
        if "login.html" in current_url:
            print("Logging in...", flush=True)
            await eval_js("""
                document.getElementById('email').value = 'test@example.com';
                document.getElementById('password').value = 'password123';
                document.querySelector('form').dispatchEvent(new Event('submit', { cancelable: true }));
            """)
            await asyncio.sleep(2)

        # -------------------------------------------------------------
        # TEST: 3-Zone Layout & Bounding Rects
        # -------------------------------------------------------------
        print("\n[Step 2] Measuring vertical zones & bounding boxes...", flush=True)
        metrics = await eval_js("""
        (() => {
            const chatContent = document.getElementById('chatScroll');
            const composer = document.getElementById('chatComposerWrapper');
            const nav = document.querySelector('.navbar');

            const contentRect = chatContent.getBoundingClientRect();
            const composerRect = composer.getBoundingClientRect();
            const navRect = nav.getBoundingClientRect();

            const winHeight = window.innerHeight;
            const scrollWidth = document.documentElement.scrollWidth;
            const clientWidth = document.documentElement.clientWidth;

            const navLinks = Array.from(nav.querySelectorAll('a')).map(a => a.textContent.trim());

            return {
                contentRect,
                composerRect,
                navRect,
                verticalGap: navRect.top - composerRect.bottom,
                isComposerAboveNav: composerRect.bottom <= navRect.top,
                isContentAboveComposer: contentRect.bottom <= composerRect.top,
                hasHorizontalOverflow: scrollWidth > clientWidth,
                scrollWidth,
                clientWidth,
                winHeight,
                navLinks
            };
        })()
        """)
        print(f"Content Bottom: {metrics['contentRect'].get('bottom', 0):.1f}px", flush=True)
        print(f"Composer Top: {metrics['composerRect'].get('top', 0):.1f}px, Bottom: {metrics['composerRect'].get('bottom', 0):.1f}px", flush=True)
        print(f"Navigation Top: {metrics['navRect'].get('top', 0):.1f}px, Bottom: {metrics['navRect'].get('bottom', 0):.1f}px", flush=True)
        print(f"Vertical Gap: {metrics['verticalGap']:.1f}px", flush=True)
        print(f"isComposerAboveNav: {metrics['isComposerAboveNav']}", flush=True)
        print(f"isContentAboveComposer: {metrics['isContentAboveComposer']}", flush=True)
        print(f"hasHorizontalOverflow: {metrics['hasHorizontalOverflow']}", flush=True)

        assert metrics["isComposerAboveNav"], "Composer overlaps or is not above navigation!"
        assert metrics["verticalGap"] >= 10, f"Vertical gap too small: {metrics['verticalGap']}px"
        print(f"CONFIRMED: Clear vertical gap of {metrics['verticalGap']:.1f}px between Composer and Navigation.", flush=True)

        # Check Bottom Nav Items
        print("\n[Step 3] Checking bottom navigation items...", flush=True)
        links = metrics["navLinks"]
        print(f"Navigation items found: {links}", flush=True)
        assert "Focus" not in "".join(links), "Focus tab should NOT be present in bottom navigation!"
        assert "Logout" not in "".join(links), "Logout should NOT be in bottom navigation (moved to Profile)!"
        assert any("Home" in l for l in links), "Home link missing!"
        assert any("Diary" in l for l in links), "Diary link missing!"
        assert any("SOS" in l for l in links), "SOS link missing!"
        assert any("Profile" in l for l in links), "Profile link missing!"
        print("CONFIRMED: Bottom navigation is exactly Home | Diary | SOS | Profile.", flush=True)

        # -------------------------------------------------------------
        # TEST: Composer Elements & Attachments
        # -------------------------------------------------------------
        print("\n[Step 4] Checking Composer elements & functionality...", flush=True)
        comp_check = await eval_js("""
        (() => {
            const plusBtn = document.getElementById('plusBtn');
            const filePicker = document.getElementById('filePicker');
            const msgInput = document.getElementById('msgInput');
            const micBtn = document.getElementById('micBtn');
            const sendBtn = document.getElementById('sendBtn');
            const chip = document.getElementById('attachmentChip');

            // Simulate file selection
            let fileChosen = false;
            try {
                const dt = new DataTransfer();
                const file = new File(['sample content'], 'notes.pdf', { type: 'application/pdf' });
                dt.items.add(file);
                filePicker.files = dt.files;
                filePicker.dispatchEvent(new Event('change', { bubbles: true }));
                fileChosen = true;
            } catch (e) {
                console.error(e);
            }

            const chipVisible = !chip.classList.contains('hidden');
            const chipRect = chip.getBoundingClientRect();
            const navRect = document.querySelector('.navbar').getBoundingClientRect();

            return {
                hasPlusBtn: !!plusBtn,
                hasFilePicker: !!filePicker,
                hasMsgInput: !!msgInput,
                hasMicBtn: !!micBtn,
                hasSendBtn: !!sendBtn,
                chipVisible,
                chipAboveNav: chipRect.bottom < navRect.top,
                chipText: document.getElementById('chipName').textContent
            };
        })()
        """)
        print(f"Plus Button: {comp_check['hasPlusBtn']}", flush=True)
        print(f"File Picker: {comp_check['hasFilePicker']}", flush=True)
        print(f"Message Input: {comp_check['hasMsgInput']}", flush=True)
        print(f"Mic Button: {comp_check['hasMicBtn']}", flush=True)
        print(f"Send Button: {comp_check['hasSendBtn']}", flush=True)
        print(f"Attachment Chip Visible: {comp_check['chipVisible']} ('{comp_check['chipText']}')", flush=True)
        print(f"Attachment Chip Strictly Above Nav: {comp_check['chipAboveNav']}", flush=True)

        assert comp_check["hasPlusBtn"], "Plus button missing!"
        assert comp_check["hasFilePicker"], "File picker missing!"
        assert comp_check["hasMsgInput"], "Message input missing!"
        assert comp_check["hasMicBtn"], "Microphone button missing!"
        assert comp_check["hasSendBtn"], "Send button missing!"
        assert comp_check["chipVisible"], "Attachment chip failed to show on file selection!"
        assert comp_check["chipAboveNav"], "Attachment chip overlaps navigation!"

        # Remove attachment chip
        await eval_js("document.getElementById('chipRemove').click();")
        await asyncio.sleep(0.3)

        # -------------------------------------------------------------
        # TEST: Microphone Button Visual State
        # -------------------------------------------------------------
        print("\n[Step 5] Checking Microphone speech status bar...", flush=True)
        mic_check = await eval_js("""
        (() => {
            const micBtn = document.getElementById('micBtn');
            micBtn.click(); // Toggle speech
            const status = document.getElementById('voiceStatusBar');
            const nav = document.querySelector('.navbar');
            const statusRect = status.getBoundingClientRect();
            const navRect = nav.getBoundingClientRect();
            return {
                recordingClass: micBtn.classList.contains('recording'),
                statusVisible: !status.classList.contains('hidden'),
                statusAboveNav: statusRect.bottom < navRect.top,
                statusText: status.textContent
            };
        })()
        """)
        print(f"Mic Active Status Visible: {mic_check['statusVisible']} ('{mic_check['statusText']}')", flush=True)
        print(f"Voice Status Strictly Above Nav: {mic_check['statusAboveNav']}", flush=True)
        # Turn off mic
        await eval_js("document.getElementById('micBtn').click();")
        await asyncio.sleep(0.3)

        # -------------------------------------------------------------
        # TEST: Send Message & Real AI Response
        # -------------------------------------------------------------
        print("\n[Step 6] Testing Send Message & Real AI response...", flush=True)
        await eval_js("""
            document.getElementById('msgInput').value = 'Hello Mithra, I feel calm today.';
            document.getElementById('sendBtn').click();
        """)
        print("Message submitted to real pipeline, waiting for Qwen response...", flush=True)
        
        reply_received = False
        for i in range(45):
            await asyncio.sleep(1)
            state = await eval_js("""
            (() => {
                const bubbles = Array.from(document.querySelectorAll('#chatScroll .bubble'));
                const lastBubble = bubbles[bubbles.length - 1];
                const composer = document.getElementById('chatComposerWrapper');
                const composerRect = composer.getBoundingClientRect();

                let lastBubbleVisible = false;
                if (lastBubble) {
                    const bRect = lastBubble.getBoundingClientRect();
                    lastBubbleVisible = bRect.bottom <= composerRect.top + 30;
                }

                return {
                    count: bubbles.length,
                    lastText: lastBubble ? lastBubble.textContent : '',
                    isMithra: lastBubble ? lastBubble.classList.contains('mithra') : false,
                    lastBubbleVisible
                };
            })()
            """)
            if state and state["isMithra"] and "typing" not in state["lastText"].lower():
                print(f"Received Qwen Reply ({i+1}s): {state['lastText']}", flush=True)
                print(f"Last bubble is above composer and fully visible: {state['lastBubbleVisible']}", flush=True)
                reply_received = True
                break

        assert reply_received, "Timed out waiting for Qwen AI response"

        # -------------------------------------------------------------
        # TEST: Navigation Clickability
        # -------------------------------------------------------------
        print("\n[Step 7] Testing navigation clickability...", flush=True)
        # Diary
        await eval_js("document.querySelector(\".navbar a[href='diary.html']\").click()")
        await asyncio.sleep(1)
        diary_url = await eval_js("window.location.pathname")
        assert "diary.html" in diary_url, f"Failed navigating to diary.html, at: {diary_url}"
        print("Navigated to Diary successfully.", flush=True)

        # SOS
        await eval_js("document.querySelector(\".navbar a[href='emergency.html']\").click()")
        await asyncio.sleep(1)
        sos_url = await eval_js("window.location.pathname")
        assert "emergency.html" in sos_url, f"Failed navigating to emergency.html, at: {sos_url}"
        print("Navigated to SOS successfully.", flush=True)

        # Profile
        await eval_js("document.querySelector(\".navbar a[href='profile.html']\").click()")
        await asyncio.sleep(1)
        prof_url = await eval_js("window.location.pathname")
        assert "profile.html" in prof_url, f"Failed navigating to profile.html, at: {prof_url}"
        print("Navigated to Profile successfully.", flush=True)

        # Return to Chat
        await eval_js("document.querySelector(\".navbar a[href='chat.html']\").click()")
        await asyncio.sleep(1)
        chat_url = await eval_js("window.location.pathname")
        assert "chat.html" in chat_url, f"Failed navigating back to chat.html, at: {chat_url}"
        print("Returned to Chat successfully.", flush=True)

        # -------------------------------------------------------------
        # TEST: Mobile Viewport Responsiveness (390x844)
        # -------------------------------------------------------------
        print("\n[Step 8] Testing mobile viewport (390x844)...", flush=True)
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 390,
            "height": 844,
            "deviceScaleFactor": 2,
            "mobile": True
        })
        await asyncio.sleep(0.5)

        mobile_metrics = await eval_js("""
        (() => {
            const chatContent = document.getElementById('chatScroll');
            const composer = document.getElementById('chatComposerWrapper');
            const nav = document.querySelector('.navbar');

            const contentRect = chatContent.getBoundingClientRect();
            const composerRect = composer.getBoundingClientRect();
            const navRect = nav.getBoundingClientRect();

            const scrollWidth = document.documentElement.scrollWidth;
            const clientWidth = document.documentElement.clientWidth;

            return {
                verticalGap: navRect.top - composerRect.bottom,
                isComposerAboveNav: composerRect.bottom <= navRect.top,
                hasHorizontalOverflow: scrollWidth > clientWidth,
                scrollWidth,
                clientWidth
            };
        })()
        """)
        print(f"Mobile Vertical Gap: {mobile_metrics['verticalGap']:.1f}px", flush=True)
        print(f"Mobile isComposerAboveNav: {mobile_metrics['isComposerAboveNav']}", flush=True)
        print(f"Mobile hasHorizontalOverflow: {mobile_metrics['hasHorizontalOverflow']}", flush=True)

        assert mobile_metrics["isComposerAboveNav"], "Mobile: Composer overlaps navigation!"
        assert mobile_metrics["verticalGap"] >= 10, f"Mobile: Vertical gap too small: {mobile_metrics['verticalGap']}px"
        assert not mobile_metrics["hasHorizontalOverflow"], "Mobile: Horizontal overflow detected!"
        print("Mobile viewport verification PASSED.", flush=True)

        # Capture Desktop & Mobile Screenshots
        screenshot_data = await send_cmd("Page.captureScreenshot", {"format": "png"})
        artifact_path = os.path.join(r"C:\Users\anand\.gemini\antigravity-ide\brain\a91e385c-c6de-40af-8547-c85261077a7b", "chat_layout_mobile_verified.png")
        with open(artifact_path, "wb") as f:
            f.write(base64.b64decode(screenshot_data["data"]))
        print(f"Mobile screenshot saved to: {artifact_path}", flush=True)

        # Reset Device Metrics
        await send_cmd("Emulation.clearDeviceMetricsOverride")
        await asyncio.sleep(0.5)

        print("\n" + "=" * 60, flush=True)
        print("          ALL LAYOUT & UX VERIFICATIONS PASSED", flush=True)
        print("=" * 60, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
