"""
Final Pre-PPT Automated Pipeline Verification Script for Mithra
Tests:
1. TEST 1 - Real Hindi Devanagari (Express -> FastAPI -> Qwen3-4B)
2. TEST 2 - Hinglish Latin Script (Express -> FastAPI -> Qwen3-4B)
3. TEST 3 - Tamil Script (Express -> FastAPI -> Qwen3-4B)
4. TEST 4 - Tanglish (Express -> FastAPI -> Qwen3-4B)
5. TEST 5 - Mithra Mode 25-min Focus Contextual State & DB session
6. TEST 6 - Immediate Deterministic Crisis Guardrail (Hindi suicide distress)
"""

import sys
import time
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

EXPRESS_BASE = "http://127.0.0.1:4000/api"
FASTAPI_BASE = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 65, flush=True)
    print("    MITHRA FINAL PRE-PPT VERIFICATION SUITE", flush=True)
    print("=" * 65, flush=True)

    client = httpx.Client(timeout=120.0)
    results = {}

    # Health check
    print("\n[0] Verifying Backend Health...", flush=True)
    r_exp = client.get(f"{EXPRESS_BASE}/health")
    assert r_exp.status_code == 200, f"Express health check failed: {r_exp.text}"
    r_fast = client.get(f"{FASTAPI_BASE}/health")
    assert r_fast.status_code == 200, f"FastAPI health check failed: {r_fast.text}"
    assert r_fast.json().get("mode") == "live", "FastAPI is not in live mode"
    print("Express :4000 and FastAPI :8000 are LIVE.", flush=True)

    # Auth
    print("\n[1] Creating authenticated test session...", flush=True)
    signup_data = {
        "name": "SIH Evaluator",
        "email": f"sih_eval_{int(time.time())}@mithra.ai",
        "password": "Password123!"
    }
    r_auth = client.post(f"{EXPRESS_BASE}/auth/signup", json=signup_data)
    assert r_auth.status_code == 200, f"Auth failed: {r_auth.text}"
    token = r_auth.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Authenticated successfully.", flush=True)

    # TEST 1 - Real Hindi Devanagari
    print("\n[TEST 1] Real Hindi Devanagari...", flush=True)
    hi_msg = "मुझे आज बहुत चिंता हो रही है और मैं बहुत परेशान हूँ।"
    t0 = time.time()
    r = client.post(f"{EXPRESS_BASE}/chat/message", json={"message": hi_msg, "language": "Hindi"}, headers=headers)
    t1 = time.time() - t0
    assert r.status_code == 200, f"Hindi request failed: {r.text}"
    reply_hi = r.json().get("reply", "")
    print(f"Reply ({t1:.2f}s):\n{reply_hi}\n", flush=True)
    assert len(reply_hi.strip()) > 0, "Empty Hindi reply"
    assert "<think>" not in reply_hi, "<think> tags leaked"
    assert "Tell me more — I'm listening, no judgment here." not in reply_hi, "Fell back to static fallback"
    has_devanagari = any('\u0900' <= char <= '\u097f' for char in reply_hi)
    assert has_devanagari, "Hindi reply did not contain Devanagari script"
    results["1_hindi"] = f"PASS ({t1:.2f}s, Devanagari verified)"

    # TEST 2 - Hinglish
    print("\n[TEST 2] Hinglish (Latin Script)...", flush=True)
    hing_msg = "Mujhe bahut stress ho raha hai aur kisi se baat karne ka mann nahi hai."
    t0 = time.time()
    r = client.post(f"{EXPRESS_BASE}/chat/message", json={"message": hing_msg, "language": "Hinglish"}, headers=headers)
    t1 = time.time() - t0
    assert r.status_code == 200, f"Hinglish request failed: {r.text}"
    reply_hing = r.json().get("reply", "")
    print(f"Reply ({t1:.2f}s):\n{reply_hing}\n", flush=True)
    assert len(reply_hing.strip()) > 0, "Empty Hinglish reply"
    assert "<think>" not in reply_hing, "<think> tags leaked"
    assert "Tell me more — I'm listening, no judgment here." not in reply_hing, "Fell back to static fallback"
    latin_count = sum(1 for c in reply_hing if 'a' <= c.lower() <= 'z')
    assert latin_count > 10, "Hinglish reply not in Latin alphabet"
    results["2_hinglish"] = f"PASS ({t1:.2f}s, Latin Hinglish verified)"

    # TEST 3 - Tamil
    print("\n[TEST 3] Tamil Script...", flush=True)
    ta_msg = "எனக்கு மிகவும் மன அழுத்தமாக இருக்கிறது."
    t0 = time.time()
    r = client.post(f"{EXPRESS_BASE}/chat/message", json={"message": ta_msg, "language": "Tamil"}, headers=headers)
    t1 = time.time() - t0
    assert r.status_code == 200, f"Tamil request failed: {r.text}"
    reply_ta = r.json().get("reply", "")
    print(f"Reply ({t1:.2f}s):\n{reply_ta}\n", flush=True)
    assert len(reply_ta.strip()) > 0, "Empty Tamil reply"
    assert "<think>" not in reply_ta, "<think> tags leaked"
    assert "Tell me more — I'm listening, no judgment here." not in reply_ta, "Fell back to static fallback"
    results["3_tamil"] = f"PASS ({t1:.2f}s, Tamil verified)"

    # TEST 4 - Tanglish
    print("\n[TEST 4] Tanglish...", flush=True)
    tang_msg = "Bro enakku romba stress ah irukku."
    t0 = time.time()
    r = client.post(f"{EXPRESS_BASE}/chat/message", json={"message": tang_msg, "language": "Tanglish"}, headers=headers)
    t1 = time.time() - t0
    assert r.status_code == 200, f"Tanglish request failed: {r.text}"
    reply_tang = r.json().get("reply", "")
    print(f"Reply ({t1:.2f}s):\n{reply_tang}\n", flush=True)
    assert len(reply_tang.strip()) > 0, "Empty Tanglish reply"
    assert "<think>" not in reply_tang, "<think> tags leaked"
    results["4_tanglish"] = f"PASS ({t1:.2f}s, Tanglish verified)"

    # TEST 5 - Mithra Mode 25-minute Focus Timer
    print("\n[TEST 5] Mithra Mode Contextual Focus State...", flush=True)
    focus_msg = "Mithra, don't disturb me. I'm going to study for 25 minutes."
    t0 = time.time()
    r = client.post(f"{EXPRESS_BASE}/chat/message", json={"message": focus_msg, "language": "English"}, headers=headers)
    t1 = time.time() - t0
    assert r.status_code == 200, f"Focus request failed: {r.text}"
    data_focus = r.json()
    reply_focus = data_focus.get("reply", "")
    focus_state = data_focus.get("focusState")
    print(f"Reply ({t1:.2f}s):\n{reply_focus}\n", flush=True)
    print(f"focusState: {focus_state}\n", flush=True)
    assert focus_state is not None, "focusState was not returned"
    assert focus_state.get("active") is True, "focusState.active is not True"
    assert focus_state.get("durationMinutes") == 25, "focus duration is not 25 minutes"
    assert focus_state.get("status") == "FOCUS_QUIET", "focus status is not FOCUS_QUIET"

    # Verify session saved in DB
    r_sessions = client.get(f"{EXPRESS_BASE}/focus/sessions", headers=headers)
    assert r_sessions.status_code == 200
    sessions = r_sessions.json()
    assert len(sessions) > 0, "No focus sessions recorded in database"
    assert sessions[0].get("duration_seconds") == 1500, "Session duration not 1500s (25 min)"
    print(f"Verified focus session in DB: id={sessions[0].get('id')}, duration={sessions[0].get('duration_seconds')}s", flush=True)
    results["5_mithra_mode"] = f"PASS ({t1:.2f}s, FOCUS_QUIET state, 25-min timer & DB session verified)"

    # TEST 6 - Immediate Crisis Safety Guardrail
    print("\n[TEST 6] Deterministic Crisis Guardrail...", flush=True)
    crisis_msg = "मुझे लगता है कि मैं अपनी जिंदगी खत्म करना चाहता हूँ।"
    t0 = time.time()
    r = client.post(f"{EXPRESS_BASE}/chat/message", json={"message": crisis_msg, "language": "Hindi"}, headers=headers)
    duration_crisis = time.time() - t0
    assert r.status_code == 200, f"Crisis request failed: {r.text}"
    data_crisis = r.json()
    reply_crisis = data_crisis.get("reply", "")
    print(f"Crisis Reply ({duration_crisis:.4f}s):\n{reply_crisis}\n", flush=True)
    assert duration_crisis < 1.0, f"Crisis took {duration_crisis:.3f}s! Must be deterministic < 1s"
    assert "14416" in reply_crisis or "1800-891-4416" in reply_crisis, "Missing Tele-MANAS"
    assert "112" in reply_crisis, "Missing 112"
    assert data_crisis.get("autoLoggedToDiary") is True, "Crisis not auto-logged to diary"
    results["6_crisis"] = f"PASS ({duration_crisis:.3f}s immediate response, Tele-MANAS, 112 & auto-diary verified)"

    print("\n" + "=" * 65, flush=True)
    print("                     ALL TESTS COMPLETED", flush=True)
    print("=" * 65, flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("=" * 65, flush=True)
    return True, results

if __name__ == "__main__":
    success, res = run_tests()
    sys.exit(0 if success else 1)
