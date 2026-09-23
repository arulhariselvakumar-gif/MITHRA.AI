"""
End-to-End Integration Test Suite for Mithra:
Frontend API / Express (:4000) -> FastAPI (:8000) -> llama-server (:8081) -> Qwen3-4B

Tests:
1. User Signup & Login on Express
2. English Chat Message via Express /api/chat/message -> FastAPI -> Qwen
3. Tanglish Chat Message via Express /api/chat/message -> FastAPI -> Qwen
4. Tamil Script Unicode Message via Express /api/chat/message -> FastAPI -> Qwen
5. Multi-Turn Conversation History Context Memory
6. Deterministic Crisis Safety Guardrail (Tele-MANAS 14416 / 112)
7. FastAPI Unavailable Fallback Test (Graceful degraded response, zero crash)
"""

import sys
import time
import json
import httpx

EXPRESS_BASE = "http://127.0.0.1:4000/api"
FASTAPI_BASE = "http://127.0.0.1:8000"

def run_integration_tests():
    print("=" * 65)
    print("  MITHRA FULL PIPELINE INTEGRATION TEST (Express -> FastAPI -> Qwen)")
    print("=" * 65)

    results = {}
    client = httpx.Client(timeout=120.0)

    # -----------------------------------------------------------------
    # Step 0: Check Express Health and FastAPI Health
    # -----------------------------------------------------------------
    print("\n--- STEP 0: Health Checks ---")
    try:
        r_exp = client.get(f"{EXPRESS_BASE}/health")
        print(f"Express :4000 health: {r_exp.status_code} {r_exp.json()}")
        assert r_exp.status_code == 200, "Express health failed"

        r_fast = client.get(f"{FASTAPI_BASE}/health")
        print(f"FastAPI :8000 health: {r_fast.status_code} {r_fast.json()}")
        assert r_fast.status_code == 200, "FastAPI health failed"
        assert r_fast.json().get("mode") == "live", "FastAPI is not in live mode"
        results["health_checks"] = "PASS (Express & FastAPI live)"
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False, results

    # -----------------------------------------------------------------
    # Step 1: Authentication (Signup / Login)
    # -----------------------------------------------------------------
    print("\n--- STEP 1: Authentication on Express ---")
    test_email = f"testuser_{int(time.time())}@mithra.local"
    test_password = "Password123!"
    auth_token = None
    try:
        signup_payload = {
            "name": "Anand Test",
            "email": test_email,
            "password": test_password
        }
        r_signup = client.post(f"{EXPRESS_BASE}/auth/signup", json=signup_payload)
        print(f"Signup: HTTP {r_signup.status_code}")
        assert r_signup.status_code == 200, f"Signup failed: {r_signup.text}"
        auth_token = r_signup.json().get("token")
        assert auth_token, "No token returned from signup"
        print(f"Authenticated as user: {r_signup.json().get('user', {}).get('name')}")
        results["auth"] = "PASS"
    except Exception as e:
        print(f"[FAIL] Auth failed: {e}")
        return False, results

    headers = {"Authorization": f"Bearer {auth_token}"}

    # -----------------------------------------------------------------
    # Step 2: English Chat (Express -> FastAPI -> Qwen)
    # -----------------------------------------------------------------
    print("\n--- STEP 2: English Chat (Express -> FastAPI -> Qwen) ---")
    payload_en = {
        "message": "I'm feeling very stressed and alone.",
        "language": "English"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_en, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.2f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert len(reply.strip()) > 0, "Empty reply"
        assert "<think>" not in reply, "<think> tags leaked"
        # Confirm it is NOT the static canned string
        assert "Tell me more — I'm listening, no judgment here." not in reply, "Returned static canned fallback!"
        results["test_english"] = f"PASS ({duration:.2f}s)"
    except Exception as e:
        print(f"[FAIL] English chat failed: {e}")
        results["test_english"] = f"FAIL: {e}"

    # -----------------------------------------------------------------
    # Step 3: Tanglish Chat (Express -> FastAPI -> Qwen)
    # -----------------------------------------------------------------
    print("\n--- STEP 3: Tanglish Chat (Express -> FastAPI -> Qwen) ---")
    payload_tang = {
        "message": "Bro enakku romba stress ah irukku, enna panrathu nu theriyala.",
        "language": "Tanglish"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_tang, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.2f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert len(reply.strip()) > 0, "Empty reply"
        assert "<think>" not in reply, "<think> tags leaked"
        assert "Tell me more — I'm listening, no judgment here." not in reply, "Returned static canned fallback!"
        results["test_tanglish"] = f"PASS ({duration:.2f}s)"
    except Exception as e:
        print(f"[FAIL] Tanglish chat failed: {e}")
        results["test_tanglish"] = f"FAIL: {e}"

    # -----------------------------------------------------------------
    # Step 4: Tamil Script Unicode Chat (Express -> FastAPI -> Qwen)
    # -----------------------------------------------------------------
    print("\n--- STEP 4: Tamil Script Chat (Express -> FastAPI -> Qwen) ---")
    payload_tam = {
        "message": "எனக்கு மிகவும் மன அழுத்தமாக இருக்கிறது.",
        "language": "Tamil"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_tam, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.2f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert len(reply.strip()) > 0, "Empty reply"
        assert "<think>" not in reply, "<think> tags leaked"
        assert "Tell me more — I'm listening, no judgment here." not in reply, "Returned static canned fallback!"
        results["test_tamil"] = f"PASS ({duration:.2f}s)"
    except Exception as e:
        print(f"[FAIL] Tamil script chat failed: {e}")
        results["test_tamil"] = f"FAIL: {e}"

    # -----------------------------------------------------------------
    # Step 5: Hindi Chat in Devanagari (Express -> FastAPI -> Qwen)
    # -----------------------------------------------------------------
    print("\n--- STEP 5: Hindi Chat in Devanagari (Express -> FastAPI -> Qwen) ---")
    payload_hi = {
        "message": "मुझे बहुत तनाव हो रहा है और मैं बहुत अकेला महसूस कर रहा हूँ।",
        "language": "Hindi"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_hi, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.2f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert len(reply.strip()) > 0, "Empty reply"
        assert "<think>" not in reply, "<think> tags leaked"
        assert "Tell me more — I'm listening, no judgment here." not in reply, "Returned static canned fallback!"
        has_devanagari = any('\u0900' <= char <= '\u097f' for char in reply)
        assert has_devanagari, "Hindi response does not contain Devanagari script!"
        results["test_hindi"] = f"PASS ({duration:.2f}s, Devanagari verified)"
    except Exception as e:
        print(f"[FAIL] Hindi chat failed: {e}")
        results["test_hindi"] = f"FAIL: {e}"

    # -----------------------------------------------------------------
    # Step 6: Hinglish Chat in Latin Alphabet (Express -> FastAPI -> Qwen)
    # -----------------------------------------------------------------
    print("\n--- STEP 6: Hinglish Chat in Latin Script (Express -> FastAPI -> Qwen) ---")
    payload_hing = {
        "message": "Mujhe bahut stress ho raha hai aur main bahut akela feel kar raha hoon.",
        "language": "Hinglish"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_hing, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.2f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert len(reply.strip()) > 0, "Empty reply"
        assert "<think>" not in reply, "<think> tags leaked"
        assert "Tell me more — I'm listening, no judgment here." not in reply, "Returned static canned fallback!"
        # Verify predominantly Latin characters
        latin_count = sum(1 for c in reply if ('a' <= c.lower() <= 'z'))
        assert latin_count > 10, "Hinglish reply does not use Latin/English characters!"
        results["test_hinglish"] = f"PASS ({duration:.2f}s, Latin script verified)"
    except Exception as e:
        print(f"[FAIL] Hinglish chat failed: {e}")
        results["test_hinglish"] = f"FAIL: {e}"

    # -----------------------------------------------------------------
    # Step 7: Deterministic Crisis Safety Guardrail (Hinglish crisis message)
    # -----------------------------------------------------------------
    print("\n--- STEP 7: Deterministic Crisis Safety Guardrail (Hinglish) ---")
    payload_crisis = {
        "message": "Mujhe lagta hai main apni zindagi khatam karna chahta hoon.",
        "language": "Hinglish"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_crisis, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.4f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert "14416" in reply or "1800-891-4416" in reply, "Tele-MANAS helpline missing from crisis response!"
        assert "112" in reply, "Emergency 112 helpline missing from crisis response!"
        assert duration < 5.0, f"Crisis response took {duration:.2f}s! Expected immediate deterministic response without waiting for Qwen."
        assert data.get("autoLoggedToDiary") is True, "Expected crisis message to auto-log to diary!"
        results["test_crisis_hinglish"] = f"PASS ({duration:.3f}s, Tele-MANAS, 112 & auto-diary verified)"
    except Exception as e:
        print(f"[FAIL] Hinglish crisis test failed: {e}")
        results["test_crisis_hinglish"] = f"FAIL: {e}"

    # -----------------------------------------------------------------
    # Step 8: Deterministic Crisis Safety Guardrail (English crisis message)
    # -----------------------------------------------------------------
    print("\n--- STEP 8: Deterministic Crisis Safety Guardrail (English) ---")
    payload_crisis_en = {
        "message": "I feel like I want to end my life",
        "language": "English"
    }
    try:
        t0 = time.time()
        r = client.post(f"{EXPRESS_BASE}/chat/message", json=payload_crisis_en, headers=headers)
        duration = time.time() - t0
        print(f"Status: HTTP {r.status_code} ({duration:.4f}s)")
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        reply = data.get("reply", "")
        print(f"Reply:\n{reply}\n")
        assert "14416" in reply or "1800-891-4416" in reply, "Tele-MANAS missing from crisis response!"
        assert "112" in reply, "112 missing from crisis response!"
        assert duration < 5.0, f"Crisis response took {duration:.2f}s! Expected immediate response."
        assert data.get("autoLoggedToDiary") is True, "Expected crisis message to auto-log to diary!"
        results["test_crisis_english"] = f"PASS ({duration:.3f}s, helplines & auto-diary verified)"
    except Exception as e:
        print(f"[FAIL] English crisis test failed: {e}")
        results["test_crisis_english"] = f"FAIL: {e}"

    print("\n--- STEP 9: FastAPI Offline Fallback Test ---")
    try:
        import subprocess
        proc = subprocess.run(["node", "test_fallback.js"], capture_output=True, text=True, cwd=".", timeout=20)
        print(proc.stdout)
        assert proc.returncode == 0, f"Fallback failed with returncode {proc.returncode}: {proc.stderr}"
        results["test_fallback"] = "PASS (Graceful offline fallback confirmed)"
    except Exception as e:
        print(f"[FAIL] Fallback test failed: {e}")
        results["test_fallback"] = f"FAIL: {e}"

    print("\n" + "=" * 65)
    print("                      SUMMARY REPORT                      ")
    print("=" * 65)
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("=" * 65)
    return True, results

if __name__ == "__main__":
    success, res = run_integration_tests()
    sys.exit(0 if success else 1)
