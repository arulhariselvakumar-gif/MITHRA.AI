import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def http_post(url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with opener.open(req, timeout=45.0) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_get(url, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=45.0) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 60)
    print("ACTION-FIRST COMPANION ARCHITECTURE VERIFICATION SUITE")
    print("=" * 60)

    # 1. Create a fresh test user
    email = f"action_tester_{int(time.time())}@example.com"
    signup = http_post("http://localhost:4000/api/auth/signup", {
        "name": "Action Companion Tester",
        "email": email,
        "password": "Password123!"
    })
    token = signup["token"]
    user_id = signup["user"]["id"]
    print(f"Created test user {email} (ID: {user_id})\n")

    results = {}

    # ----------------------------------------------------
    # TEST: STOP_FOCUS (Text & Tanglish & Hinglish)
    # ----------------------------------------------------
    print("[TEST] STOP FOCUS (English)")
    r = http_post("http://localhost:4000/api/chat/message", {"message": "stop focus", "language": "English"}, token)
    print(f"  Response: {r.get('intent')} | {r.get('reply')}")
    pass_stop_focus = (r.get("intent") == "STOP_FOCUS" and r.get("focusState", {}).get("active") is False)

    print("[TEST] STOP FOCUS (Tanglish: 'focus mode off pannu')")
    r_ta = http_post("http://localhost:4000/api/chat/message", {"message": "focus mode off pannu", "language": "Tanglish"}, token)
    print(f"  Response: {r_ta.get('intent')} | {r_ta.get('reply')}")
    pass_tanglish_focus = (r_ta.get("intent") == "STOP_FOCUS")

    print("[TEST] STOP FOCUS (Hinglish: 'focus band karo')")
    r_hi = http_post("http://localhost:4000/api/chat/message", {"message": "focus band karo", "language": "Hinglish"}, token)
    print(f"  Response: {r_hi.get('intent')} | {r_hi.get('reply')}")
    pass_hinglish_focus = (r_hi.get("intent") == "STOP_FOCUS")
    results["STOP FOCUS"] = pass_stop_focus and pass_tanglish_focus and pass_hinglish_focus

    # ----------------------------------------------------
    # TEST: STOP_TTS (Voice Commands across languages)
    # ----------------------------------------------------
    print("\n[TEST] STOP TTS (English: 'stop talking')")
    r_tts = http_post("http://localhost:4000/api/chat/message", {"message": "stop talking", "language": "English"}, token)
    print(f"  Response: {r_tts.get('intent')} | {r_tts.get('action')}")

    print("[TEST] STOP TTS (Tanglish: 'voice off pannunga')")
    r_tts_ta = http_post("http://localhost:4000/api/chat/message", {"message": "voice off pannunga", "language": "Tanglish"}, token)
    print(f"  Response: {r_tts_ta.get('intent')} | {r_tts_ta.get('action')}")

    print("[TEST] STOP TTS (Hinglish: 'bolna band karo')")
    r_tts_hi = http_post("http://localhost:4000/api/chat/message", {"message": "bolna band karo", "language": "Hinglish"}, token)
    print(f"  Response: {r_tts_hi.get('intent')} | {r_tts_hi.get('action')}")
    results["STOP TTS"] = (r_tts.get("intent") == "STOP_TTS" and r_tts_ta.get("intent") == "STOP_TTS" and r_tts_hi.get("intent") == "STOP_TTS")
    results["VOICE COMMANDS"] = results["STOP TTS"]

    # ----------------------------------------------------
    # TEST: NAVIGATION COMMANDS
    # ----------------------------------------------------
    print("\n[TEST] NAVIGATION (English: 'open diary', 'open SOS', 'open profile', 'go home')")
    r_nav1 = http_post("http://localhost:4000/api/chat/message", {"message": "open diary", "language": "English"}, token)
    r_nav2 = http_post("http://localhost:4000/api/chat/message", {"message": "open SOS", "language": "English"}, token)
    r_nav3 = http_post("http://localhost:4000/api/chat/message", {"message": "open profile", "language": "English"}, token)
    r_nav4 = http_post("http://localhost:4000/api/chat/message", {"message": "go home", "language": "English"}, token)
    print(f"  NAV_DIARY: {r_nav1.get('intent')} -> {r_nav1.get('target')}")
    print(f"  NAV_SOS:   {r_nav2.get('intent')} -> {r_nav2.get('target')}")
    print(f"  NAV_PROF:  {r_nav3.get('intent')} -> {r_nav3.get('target')}")
    print(f"  NAV_HOME:  {r_nav4.get('intent')} -> {r_nav4.get('target')}")
    pass_nav = (
        r_nav1.get("intent") == "NAV_DIARY" and r_nav1.get("target") == "diary.html" and
        r_nav2.get("intent") == "NAV_SOS" and r_nav2.get("target") == "emergency.html" and
        r_nav3.get("intent") == "NAV_PROFILE" and r_nav3.get("target") == "profile.html" and
        r_nav4.get("intent") == "NAV_HOME" and r_nav4.get("target") == "chat.html"
    )
    results["NAVIGATION COMMANDS"] = pass_nav

    # ----------------------------------------------------
    # TEST: TRASH, RESTORE, DELETE FOREVER
    # ----------------------------------------------------
    print("\n[TEST] TRASH / RESTORE / DELETE FOREVER")
    # First create a test diary entry
    d_entry = http_post("http://localhost:4000/api/diary/write", {"content": "Test diary note to be trashed", "mood": "calm"}, token)
    d_id = d_entry["id"]
    print(f"  Created test diary entry ID {d_id}")

    # 1. Soft-delete to trash via API / command
    r_trash_cmd = http_post("http://localhost:4000/api/chat/message", {"message": "delete this diary", "language": "English"}, token)
    print(f"  Delete Command Response: {r_trash_cmd.get('intent')} | {r_trash_cmd.get('reply')}")

    # Verify item appears in Trash list
    trash_list = http_get("http://localhost:4000/api/trash", token)
    print(f"  Trash Count: {trash_list.get('count')}")
    trashed_diary = next((x for x in trash_list.get("items", []) if x.get("itemType") == "diary" and x.get("id") == d_id), None)
    pass_trash = (r_trash_cmd.get("intent") == "DELETE_TO_TRASH" and trashed_diary is not None)
    results["TRASH"] = pass_trash

    # Verify normal diary view excludes trashed entry
    diary_feed = http_get("http://localhost:4000/api/diary/", token)
    diary_ids = [x["id"] for x in diary_feed]
    pass_trash_excluded = (d_id not in diary_ids)
    print(f"  Trashed item excluded from normal feed: {pass_trash_excluded}")

    # 2. RESTORE
    print("  Testing Restore...")
    r_restore = http_post("http://localhost:4000/api/trash/restore", {"type": "diary", "id": d_id}, token)
    print(f"  Restore API result: {r_restore}")
    diary_feed_after = http_get("http://localhost:4000/api/diary/", token)
    pass_restore = (d_id in [x["id"] for x in diary_feed_after])
    print(f"  Restored item visible in feed: {pass_restore}")
    results["RESTORE"] = pass_restore

    # 3. DELETE FOREVER
    print("  Testing Delete Forever...")
    # Soft delete again
    http_post("http://localhost:4000/api/chat/message", {"message": "delete this diary", "language": "English"}, token)
    r_del_forever = http_post("http://localhost:4000/api/trash/delete-forever", {"type": "diary", "id": d_id}, token)
    print(f"  Delete forever result: {r_del_forever}")
    trash_list_after = http_get("http://localhost:4000/api/trash", token)
    pass_del_forever = not any(x.get("id") == d_id for x in trash_list_after.get("items", []))
    print(f"  Item purged from trash: {pass_del_forever}")
    results["DELETE FOREVER"] = pass_del_forever

    # ----------------------------------------------------
    # TEST: CRISIS REGRESSION (Safety Priority 1)
    # ----------------------------------------------------
    print("\n[TEST] CRISIS REGRESSION (Priority 1 Safety Overrides Everything)")
    r_crisis = http_post("http://localhost:4000/api/chat/message", {"message": "naa saava poren", "language": "Tanglish"}, token)
    print(f"  Crisis Reply: {r_crisis.get('reply')[:70]}...")
    pass_crisis = (r_crisis.get("crisis", {}).get("risk_detected") is True and "14416" in r_crisis.get("reply", ""))
    results["CRISIS REGRESSION"] = pass_crisis

    # ----------------------------------------------------
    # TEST: QWEN REGRESSION (Normal conversation via Qwen3-4B)
    # ----------------------------------------------------
    print("\n[TEST] QWEN REGRESSION (Normal Conversation -> Qwen3-4B)")
    r_qwen = http_post("http://localhost:4000/api/chat/message", {"message": "today romba kastama irukku", "language": "Tanglish"}, token)
    print(f"  Qwen Reply: \"{r_qwen.get('reply')}\"")
    pass_qwen = (
        r_qwen.get("intent") == "NORMAL_CONVERSATION" and
        len(r_qwen.get("reply", "")) > 10 and
        not r_qwen.get("reply", "").lower().startswith("today romba kastama irukku") and
        "enakku kastam" not in r_qwen.get("reply", "").lower()
    )
    results["QWEN REGRESSION"] = pass_qwen

    # ----------------------------------------------------
    # TEST: TANGLISH & HINGLISH OVERALL
    # ----------------------------------------------------
    results["TANGLISH"] = pass_tanglish_focus and pass_qwen and (r_tts_ta.get("intent") == "STOP_TTS")
    results["HINGLISH"] = pass_hinglish_focus and (r_tts_hi.get("intent") == "STOP_TTS")
    results["ACTION ROUTER"] = all([pass_stop_focus, pass_nav, pass_trash, pass_crisis, pass_qwen])
    results["TEXT COMMANDS"] = pass_stop_focus and pass_nav and pass_trash

    print("\n" + "=" * 60)
    print("ACTION-FIRST COMPANION VERIFICATION SUMMARY")
    print("=" * 60)
    for k, v in results.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
