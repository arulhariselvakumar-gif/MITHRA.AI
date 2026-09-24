"""
QwenModelService: CPU inference management for Qwen3-4B GGUF via llama-server with graceful DEMO fallback.
"""

import os
import re
import time
import signal
import logging
import subprocess
import threading
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

from app.prompts import (
    build_prompt_messages,
    detect_crisis_intent,
    get_crisis_response,
    detect_message_language,
    validate_speaker_perspective,
)

load_dotenv()

logger = logging.getLogger("mithra_ai")
logging.basicConfig(level=logging.INFO)


def devanagari_to_hinglish(text: str) -> str:
    """Converts Devanagari script to readable phonetic Hinglish (Latin characters)."""
    consonants = {
        'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
        'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
        'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
        'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
        'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
        'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'd', 'ढ़': 'dh', 'फ़': 'f'
    }
    vowels = {
        'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
        'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au'
    }
    matras = {
        'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
        'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', '्': ''
    }
    specials = {
        'ं': 'n', 'ँ': 'n', 'ः': 'h', '।': '.', '॥': '.'
    }

    result = []
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if i + 1 < n and text[i + 1] == '़':
            combined = char + '़'
            if combined in consonants:
                char = combined
                i += 1

        if char in consonants:
            base = consonants[char]
            if i + 1 < n and text[i + 1] in matras:
                m = text[i + 1]
                i += 1
                result.append(base + matras[m])
            elif i + 1 < n and text[i + 1] == '्':
                i += 1
                result.append(base)
            else:
                if i + 1 == n or text[i + 1] in ' \t\n.,!?;:':
                    result.append(base)
                else:
                    result.append(base + 'a')
        elif char in vowels:
            result.append(vowels[char])
        elif char in matras:
            result.append(matras[char])
        elif char in specials:
            result.append(specials[char])
        else:
            result.append(char)
        i += 1

    out = "".join(result)
    replacements = [
        ("aapakaa", "aapka"), ("aapake", "aapke"), ("aapakee", "aapki"),
        ("tumhaaraa", "tumhara"), ("tumhaare", "tumhare"), ("tumhaaree", "tumhari"),
        ("honaa", "hona"), ("rahaa", "raha"), ("rahee", "rahi"), ("rahe", "rahe"),
        ("hotaa", "hota"), ("hotee", "hoti"), ("hote", "hote"),
        ("karanaa", "karna"), ("karane", "karne"),
        ("kahaa", "kaha"), ("jaananaa", "jaanna"), ("chaahataa", "chahta"), ("chaahatee", "chahti"),
        ("hoon.", "hoon."), ("hain.", "hain.")
    ]
    for old, new in replacements:
        out = out.replace(old, new)
    return out


class QwenModelService:
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "Qwen3-4B")
        self.model_path = os.getenv("MODEL_PATH", r"C:\Users\anand\models\qwen3-4b-q4_k_m\Qwen3-4B-Q4_K_M.gguf")
        self.server_path = os.getenv("LLAMA_SERVER_PATH", r"C:\Users\anand\bin\llama_cpp\llama-server.exe")
        self.host = os.getenv("LLAMA_HOST", "127.0.0.1")
        self.port = int(os.getenv("LLAMA_PORT", "8081"))
        self.threads = int(os.getenv("CPU_THREADS", "6"))
        self.context_size = int(os.getenv("CONTEXT_SIZE", "2048"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "512"))
        self.demo_mode_forced = os.getenv("DEMO_MODE", "false").strip().lower() in ("true", "1", "yes")

        self._lock = threading.Lock()
        self.process: Optional[subprocess.Popen] = None
        self.is_live: bool = False
        self.last_error: Optional[str] = None
        self.load_time_seconds: float = 0.0

    @property
    def server_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def initialize(self) -> None:
        """Starts llama-server and verifies live Qwen inference."""
        if self.demo_mode_forced:
            logger.info("[QWEN] DEMO_MODE is explicitly enabled via environment. Skipping live model startup.")
            self.is_live = False
            return

        # 1. Verify model file exists
        if not os.path.exists(self.model_path):
            self.last_error = f"Model file not found at: {self.model_path}"
            logger.warning(f"[QWEN] {self.last_error}. Entering DEMO MODE.")
            self.is_live = False
            return

        # 2. Verify llama-server executable exists
        if not os.path.exists(self.server_path):
            self.last_error = f"llama-server executable not found at: {self.server_path}"
            logger.warning(f"[QWEN] {self.last_error}. Entering DEMO MODE.")
            self.is_live = False
            return

        # 2b. Check if an instance is already running and healthy on host:port
        try:
            client = httpx.Client(timeout=2.0)
            r = client.get(f"{self.server_url}/health")
            if r.status_code == 200 and r.json().get("status") in ("ok", "ready"):
                logger.info(f"[QWEN] Existing llama-server found running on {self.server_url}. Verifying live inference...")
                if self._verify_live_inference():
                    logger.info("[QWEN] Successfully attached to existing llama-server. Model is LIVE.")
                    self.is_live = True
                    return
        except Exception:
            pass

        # 3. Launch llama-server subprocess
        cmd = [
            self.server_path,
            "-m", self.model_path,
            "-c", str(self.context_size),
            "-t", str(self.threads),
            "--host", self.host,
            "--port", str(self.port),
            "-ngl", "0",              # CPU inference only
            "--reasoning", "off",     # Non-thinking conversational mode for fast, clean companion replies
        ]

        logger.info(f"[QWEN] Launching llama-server on {self.host}:{self.port} with {self.threads} CPU threads...")
        start_t = time.time()

        try:
            # On Windows, create a separate process group so Ctrl+C won't immediately terminate both
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags
            )
        except Exception as exc:
            self.last_error = f"Failed to start llama-server process: {exc}"
            logger.error(f"[QWEN] {self.last_error}. Entering DEMO MODE.")
            self.is_live = False
            return

        # 4. Wait for llama-server readiness
        is_ready = self._wait_for_health(timeout=60.0)
        if not is_ready:
            self.last_error = "llama-server failed to respond to health checks within timeout"
            logger.error(f"[QWEN] {self.last_error}. Entering DEMO MODE.")
            self.shutdown()
            self.is_live = False
            return

        # 5. LIVE VERIFICATION: Perform an actual test inference before declaring LIVE mode
        logger.info("[QWEN] Performing verification inference to confirm live generation capability...")
        verification_ok = self._verify_live_inference()
        if verification_ok:
            self.load_time_seconds = time.time() - start_t
            self.is_live = True
            logger.info(f"[QWEN] Live Qwen3-4B inference verified successfully in {self.load_time_seconds:.2f}s! (mode = live)")
        else:
            self.last_error = "Verification inference failed after server started"
            logger.error(f"[QWEN] {self.last_error}. Entering DEMO MODE.")
            self.is_live = False

    def _wait_for_health(self, timeout: float = 60.0) -> bool:
        """Polls the llama-server /health endpoint until it is ready."""
        deadline = time.time() + timeout
        client = httpx.Client(timeout=2.0)
        while time.time() < deadline:
            # Check if process terminated prematurely
            if self.process and self.process.poll() is not None:
                out = self._read_process_output()
                self.last_error = f"llama-server exited prematurely with code {self.process.returncode}. Log: {out}"
                logger.error(f"[QWEN] {self.last_error}")
                return False

            try:
                r = client.get(f"{self.server_url}/health")
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") in ("ok", "ready", "loading model"):
                        if data.get("status") in ("ok", "ready"):
                            return True
            except Exception:
                pass
            time.sleep(1.0)
        return False

    def _verify_live_inference(self) -> bool:
        """Sends a minimal prompt to confirm real token generation."""
        try:
            client = httpx.Client(timeout=30.0)
            payload = {
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 16,
                "temperature": 0.1,
                "stream": False
            }
            res = client.post(f"{self.server_url}/v1/chat/completions", json=payload)
            if res.status_code == 200:
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content.strip()) > 0:
                    return True
            logger.warning(f"[QWEN] Verification response error: {res.status_code} {res.text}")
            return False
        except Exception as e:
            logger.warning(f"[QWEN] Verification inference call failed: {e}")
            return False

    def _read_process_output(self) -> str:
        """Reads recent stdout/stderr lines from the subprocess."""
        if not self.process:
            return ""
        try:
            out, _ = self.process.communicate(timeout=1.0)
            return (out or "")[-1000:]
        except Exception:
            return ""

    def generate(self, message: str, history: List[Any], language: str = "English") -> str:
        """
        Main inference entrypoint:
        1. Deterministic crisis safety check outside LLM.
        2. If LIVE: runs real Qwen inference with thinking tag sanitization.
        3. If DEMO: returns deterministic multilingual companion reply.
        """
        # Step 1: External Crisis Safety Guardrail
        if detect_crisis_intent(message):
            logger.info("[SAFETY] Deterministic crisis safety guardrail activated.")
            return get_crisis_response(language)

        # Step 2: If live mode is not active, route to demo fallback
        if not self.is_live or not self.process or self.process.poll() is not None:
            if self.process and self.process.poll() is not None:
                logger.warning("[QWEN] Detected dead llama-server process during request. Switching to DEMO MODE.")
                self.is_live = False
            return _generate_demo_reply(message, language)

        # Step 3: Execute real Qwen3-4B inference via llama-server
        try:
            effective_lang = detect_message_language(message, language)
            logger.info(f"[INFERENCE REQUEST] lang={effective_lang} histLen={len(history)} msg='{message}'")
            messages = build_prompt_messages(message, history, effective_lang)
            # Tanglish and Hinglish require ~110 tokens for a natural conversational multi-sentence response without cutoff
            token_limit = 110 if ("tanglish" in effective_lang.lower() or "hinglish" in effective_lang.lower()) else min(self.max_tokens, 75)
            payload = {
                "messages": messages,
                "max_tokens": token_limit,
                "temperature": 0.7,
                "top_p": 0.9,
                "stream": False
            }

            # 120s timeout and serialize CPU inference with lock
            with self._lock:
                with httpx.Client(timeout=120.0) as client:
                    res = client.post(f"{self.server_url}/v1/chat/completions", json=payload)
                    if res.status_code != 200:
                        raise RuntimeError(f"llama-server returned HTTP {res.status_code}: {res.text}")

                    data = res.json()
                    raw_reply = data["choices"][0]["message"]["content"]

            # Step 4: Sanitize Thinking Mode (<think>...</think>) tags for conversational safety
            clean_reply = self._sanitize_thinking_tags(raw_reply)

            # Step 5: If Hinglish was requested and Qwen generated Devanagari script, normalize to Latin alphabet
            if "hinglish" in effective_lang.lower() and any('\u0900' <= char <= '\u097f' for char in clean_reply):
                clean_reply = devanagari_to_hinglish(clean_reply)

            # Step 6: If Tanglish was requested, ensure no Tamil Unicode script leaked into Latin Tanglish output
            if "tanglish" in effective_lang.lower():
                clean_reply = re.sub(r'[\u0B80-\u0BFF]+', '', clean_reply).strip()

            if not clean_reply:
                logger.warning("[QWEN] Model returned empty reply after sanitization. Falling back to DEMO.")
                return _generate_demo_reply(message, effective_lang)

            # Step 7: Strict speaker perspective validation and physical safety checks
            validated_reply = validate_speaker_perspective(clean_reply, message, effective_lang)
            logger.info(f"[INFERENCE RESPONSE] reply='{validated_reply[:100]}...'")
            return validated_reply

        except Exception as exc:
            logger.error(f"[QWEN] LIVE INFERENCE FAILED: {exc}")
            logger.error("[QWEN] Falling back to DEMO MODE.")
            self.last_error = str(exc)
            return _generate_demo_reply(message, language)

    @staticmethod
    def _sanitize_thinking_tags(text: str) -> str:
        """Removes internal reasoning/chain-of-thought blocks."""
        if not text:
            return ""
        # Remove complete <think>...</think> or <thought>...</thought> blocks
        cleaned = re.sub(r"<(thought|think)>.*?</\1>", "", text, flags=re.DOTALL)
        # In case the generation ended prematurely without closing tag
        if "<think>" in cleaned:
            cleaned = cleaned.split("<think>")[0]
        if "<thought>" in cleaned:
            cleaned = cleaned.split("<thought>")[0]
        return cleaned.strip()

    def shutdown(self) -> None:
        """Terminates the llama-server subprocess cleanly without leaving orphans."""
        if not self.process:
            return
        logger.info("[QWEN] Terminating llama-server process...")
        try:
            if os.name == "nt":
                # Send CTRL_BREAK_EVENT to the process group or terminate directly
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)

            self.process.wait(timeout=5.0)
            logger.info("[QWEN] llama-server terminated cleanly.")
        except subprocess.TimeoutExpired:
            logger.warning("[QWEN] llama-server did not terminate within 5s; killing forcefully.")
            self.process.kill()
        except Exception as exc:
            logger.warning(f"[QWEN] Error during process cleanup: {exc}")
        finally:
            self.process = None
            self.is_live = False

    def get_status(self) -> Dict[str, Any]:
        """Returns health metadata strictly matching the API contract."""
        return {
            "status": "ok",
            "model": self.model_name,
            "mode": "live" if self.is_live else "demo",
            "load_time_seconds": round(self.load_time_seconds, 2),
            "last_error": self.last_error
        }


# Global singleton instance
service = QwenModelService()


def load_model() -> None:
    service.initialize()


def shutdown_model() -> None:
    service.shutdown()


def generate_reply(message: str, history: List[Any], language: str = "English") -> str:
    return service.generate(message, history, language)


def get_status() -> Dict[str, Any]:
    return service.get_status()


def _generate_demo_reply(message: str, language: str) -> str:
    """
    Deterministic multilingual fallback engine.
    Ensures Mithra is always accessible with compassionate, safe responses.
    """
    lang = (language or "English").strip().lower()
    text = message.strip().lower()

    is_chest = any(w in text for w in ["nenju vali", "nenju valikudhu", "nenjula vali", "chest pain", "seene me dard", "pada pada"])
    is_focus_off = ("focus" in text) and any(w in text for w in ["off", "stop", "end", "cancel", "mudikalam", "mudichiko", "mudichidu", "vendam", "venda", "band", "hatao"])
    is_focus_on = (not is_focus_off) and any(w in text for w in ["focus", "study", "don't disturb", "dont disturb", "padhai", "padhna"])
    is_companion = any(w in text for w in ["kooda iruppiya", "kooda irupiya", "kooda irupia", "saath rahoge", "stay with me", "with me"])
    is_tired = any(w in text for w in ["tired", "thookam", "exhausted", "energy illa", "thak gaya", "thak gayi"])
    is_family = any(w in text for w in ["family", "veetla", "ghar me", "parivar"])
    is_stressed = any(w in text for w in ["stress", "stressed", "anxious", "anxiety", "overwhelm", "pressure", "heavy", "kashtam", "तनाव", "परेशान"])
    is_lonely = any(w in text for w in ["lonely", "alone", "nobody", "isolated", "akela", "अकेला"])
    is_greeting = any(text.startswith(w) for w in ["hi", "hello", "hey", "vanakkam", "namaste", "halo"])

    if is_focus_off:
        if "tanglish" in lang:
            return "Seri bro, Focus Mode-ah off panniten. Naan un kooda thaan irukken, enna vishayam sollunga, pesalaam."
        if "hinglish" in lang:
            return "Theek hai dost, Focus Mode off kar diya hai. Main yahin hoon, aaram se baat karo."
        if "tamil" in lang:
            return "சரி நண்பா, Focus Mode முடித்துவிட்டேன். என்னிடம் பேசலாம்."
        if "hindi" in lang:
            return "ठीक है दोस्त, फोकस मोड बंद कर दिया है। मैं सुनने के लिए तैयार हूँ।"
        return "Okay, I've turned off Focus Mode. I'm right here whenever you want to talk."

    if is_focus_on:
        return "Okay 🤝 I'll stay quiet while you focus. I'll check in after 25 minutes."

    if is_chest:
        if "tanglish" in lang:
            return "Unakku nenju valikudha bro? Idhu physical symptom, please neglect pannadheenga. Vali heavy-ah illana pada-pada-nu irundha udane doctor-ai paakkunga illana emergency 112 ku call pannunga. Naan un kooda irukken, amaidhiyaa deep breath eduthukonga."
        if "hinglish" in lang:
            return "Aapke seene me dard ho raha hai kya dost? Ye physical symptom hai, please ise ignore mat karo. Agar dard zyada hai toh turant kisi doctor ko dikhao ya emergency 112 par call karo. Main aapke sath hoon, aaram se saans lo."
        return "Are you having chest pain? That sounds like a physical symptom that shouldn't be ignored. If the pain is sharp or heavy, please see a doctor or contact emergency services (112) right away. I'm here with you, try to take slow, gentle breaths."

    if is_companion:
        if "tanglish" in lang:
            return "Of course bro, naan un kooda irukken. Neenga thaniya illa, enna aachu nu sollunga."
        if "hinglish" in lang:
            return "Of course dost, main hamesha tumhare sath hoon. Tension mat lo, batao kya hua."
        return "Of course, I am right here with you. You're not alone, tell me what's on your mind."

    if "tanglish" in lang:
        if is_tired:
            return "Nee romba tired ah irukka pola. Konjam rest eduthuko bro."
        if is_family:
            return "Unnoda family la problem aacha bro? Sollu, enna nadandhudhu?"
        if is_stressed:
            return "Unakku romba stress ah irukku pola bro. Enna aachu? Sollu, naan kekkuren."
        if is_lonely:
            return "Aiyo bro, alone ah feel aagudhu pola. Kooda naan irukken da. Enna aachu nu pesalaam, sollunga."
        if is_greeting:
            return "Hey bro! Naan Mithra — unga AI dost. Innaiki kaisa feel aagudhu? Enna vishayam, sollunga?"
        return "Puriyudhu bro, naan un kooda dhaan irukken. Manasula enna thonudho appadiye share pannu, naan kekkuren."

    if "tamil" in lang:
        if is_stressed:
            return (
                "இன்று மிகவும் மன அழுத்தமாக உணர்கிறீர்களா நண்பா? 💙 உங்கள் உணர்வுகளை என்னால் புரிந்து கொள்ள முடிகிறது. "
                "சிறிது நேரம் ஆழமாக மூச்சை உள்ளிழுத்து மெதுவாக வெளிவிடுங்கள். உங்கள் மனதை பாரமாக்கும் விஷயங்களை என்னிடம் பகிர்ந்து கொள்ளுங்கள், "
                "நான் உங்களுக்காக கேட்க காத்திருக்கிறேன்."
            )
        if is_lonely:
            return "நீங்கள் தனியாக இருப்பதாக உணர வேண்டாம் நண்பா 💙 நான் எப்போதும் உங்கள் துணைக்கு இருக்கிறேன். என்னிடம் பேசுங்கள்."
        if is_greeting:
            return "வணக்கம்! நான் மித்ரா — உங்கள் தோழன். இன்று உங்கள் நாள் எப்படி செல்கிறது? என்னிடம் எதைப் பற்றி பேச விரும்புகிறீர்கள்?"
        return "நண்பா, நான் எப்போதும் உங்களுக்கு ஒரு நல்ல நண்பனாக துணையாக இருப்பேன். உங்கள் மனதில் உள்ளதை தயங்காமல் சொல்லுங்கள்."

    if "hinglish" in lang:
        if is_stressed:
            return (
                "Hey dost, main samajh sakta hoon 💙 Aaj ka din lagta hai sach me kafi stressful raha hai. "
                "Ek gehri saans lo aur thoda pani piyo. Sab kuch ek hi din me theek karna zaroori nahi hai. "
                "Kya chal raha hai dimaag me? Agar batana chahte ho toh main yahin hoon, aaram se share karo."
            )
        if is_lonely:
            return (
                "Akela feel karna sach me bahut mushkil hota hai 💙 Lekin please yaad rakho main aapke sath hoon. "
                "Aap bilkul akele nahi ho. Kya baat hai, share karna chahoge? Main sun raha hoon."
            )
        if is_greeting:
            return "Hey! Main Mithra hoon — aapka AI dost. Kaise ho aaj? Sab theek chal raha hai na?"
        return "Main sun raha hoon dost. Bina kisi judgment ke aap jo bhi share karna chahte ho, khulkar bolo."

    if "hindi" in lang:
        if is_stressed:
            return (
                "नमस्ते दोस्त 💙 मैं समझ सकता हूँ कि आज का दिन आपके लिए काफी तनावपूर्ण रहा है। "
                "कृपया एक गहरी सांस लें और थोड़ा सा विश्राम करें। खुद पर बहुत ज्यादा दबाव मत बनाइए। "
                "क्या आप बताना चाहेंगे कि किस बात से आपको इतनी परेशानी हो रही है? मैं आपको सुनने के लिए यहाँ हूँ।"
            )
        if is_lonely:
            return (
                "अकेलापन महसूस होना बहुत कष्टकारी हो सकता है 💙 लेकिन कृपया याद रखें कि मैं आपके साथ हूँ। "
                "आप बिल्कुल अकेले नहीं हैं। क्या आप बताना चाहेंगे कि आपको कैसा लग रहा है? मैं सुन रहा हूँ।"
            )
        if is_greeting:
            return "नमस्ते! मैं मिथ्रा हूँ — आपका मानसिक संबल और दोस्त। आज आप कैसा महसूस कर रहे हैं?"
        return "मैं आपकी बात ध्यान से सुन रहा हूँ। आप बेझिझक अपनी भावनाएं मेरे साथ साझा कर सकते हैं।"

    if "telugu" in lang:
        if is_stressed:
            return (
                "నమస్కారం మిత్రమా 💙 ఈ రోజు మీరు చాలా ఒత్తిడికి గురవుతున్నారని నేను అర్థం చేసుకోగలను. "
                "కాస్త సమయం తీసుకొని ప్రశాంతంగా శ్వాస తీసుకోండి. సమస్య ఎంత పెద్దదైనా మీరు ఒంటరిగా ఎదుర్కోవాల్సిన అవసరం లేదు. "
                "మీ మనసులో ఉన్న భారాన్ని నాతో పంచుకోవాలనుకుంటున్నారా? నేను వినడానికి సిద్ధంగా ఉన్నాను."
            )
        if is_greeting:
            return "నమస్కారం! నేను మిథ్రా — మీ AI మిత్రుడిని. ఈ రోజు మీ మనసు ఎలా ఉంది? నాతో ఏదైనా మాట్లాడాలనుకుంటున్నారా?"
        return "నేను మీ పక్కనే ఉన్నాను మిత్రమా. మీకు ఏమనిపిస్తుందో స్వేచ్ఛగా నాతో చెప్పండి."

    # Default English
    if is_stressed:
        return (
            "I hear you, and I'm really glad you reached out 💙 It takes courage to admit when things feel heavy. "
            "Please take a gentle breath right now — you don't have to figure everything out this very moment. "
            "What feels like the biggest source of stress today? I'm right here with you to listen, without any judgment."
        )
    if is_lonely:
        return (
            "Feeling alone is one of the hardest things we can experience 💙 I want you to know that right now, in this moment, "
            "you are seen and heard. I'm here to keep you company. Want to talk about what's making you feel this way?"
        )
    if is_greeting:
        return "Hey there! I'm Mithra — your AI companion. How are you feeling today? I'm here whenever you want to talk."

    return (
        "I'm listening closely 💙 Whatever is on your mind, you can share it here safely. "
        "Take your time — I'm here to support you."
    )
