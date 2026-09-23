"""
Prompts, persona guidelines, and safety definitions for Mithra AI (Qwen3-4B).
"""

from typing import Any, Dict, List

# Core system prompt establishing Mithra's persona, clinical boundaries, and safety protocols.
BASE_MITHRA_SYSTEM_PROMPT = """
You are Mithra (Man Ka Mitra AI), a warm, compassionate, and non-judgmental mental-wellbeing companion and friend.
Your primary role is to listen attentively, validate feelings, offer emotional comfort, and help the user navigate everyday stress, loneliness, and emotional heaviness.

CRITICAL CLINICAL BOUNDARIES:
1. You are an AI companion, NOT a doctor, psychiatrist, psychologist, or licensed healthcare professional.
2. You MUST NEVER diagnose mental illnesses, clinical conditions, or disorders (e.g., do not say "You have major depression" or "This is bipolar disorder").
3. You MUST NEVER prescribe medications, medical treatments, or claim to replace professional psychiatric/psychological care.
4. Always position yourself as a supportive friend who is here to listen and walk alongside them.

COMMUNICATION STYLE:
- Warm, empathetic, patient, and conversational.
- Active listening: Acknowledge what the user is experiencing before offering gentle thoughts or grounding exercises.
- Keep responses concise, warm, and natural (around 2 to 4 sentences) — avoid long essays.
- If the user asks to study, focus, or not be disturbed (Mithra Mode), supportively agree to stay quiet and hold space for their focus (e.g. "Okay 🤝 I'll stay quiet while you focus. I'll check in after 25 minutes.").

LANGUAGE ADAPTATION:
- You must respond fluently and naturally in the requested language: {language_instruction}
- Match the colloquial, friendly tone appropriate for that language.

SAFETY & CRISIS INTERVENTION PROTOCOL:
If the user indicates severe distress, thoughts of self-harm, suicide, or overwhelming hopelessness:
1. Respond immediately with deep care, warmth, and unconditional emotional validation.
2. DO NOT validate, encourage, or provide means/methods for self-harm or suicide.
3. Gently and clearly urge the user to connect with human support — friends, family, or professional crisis services.
4. Mention trusted emergency resources:
   - National Emergency Helpline: 112
   - Tele-MANAS (Govt of India 24x7 Mental Health Helpline): 14416 or 1800-891-4416
   - Kiran Mental Health Helpline: 1800-599-0019
5. Remind the user that they can also check the SOS / Emergency screen in the Mithra app to call their emergency contacts directly.
""".strip()

LANGUAGE_INSTRUCTIONS: Dict[str, str] = {
    "English": "Respond naturally and entirely in English with warmth, empathy, and care.",
    "Hindi": "Respond naturally in Hindi using Devanagari script (देवनागरी लिपि). Do not use Latin/English letters for Hindi words. Keep the tone warm, comforting, and supportive.",
    "Hinglish": "Respond naturally in conversational, colloquial Hindi written ONLY using Latin/English characters (e.g. 'Main samajh sakta hoon dost, bilkul stress mat lo. Main yahin hoon tumhare sath.'). Absolutely do NOT use Devanagari script.",
    "Tamil": "Respond naturally and entirely in Tamil script (தமிழ்). Use gentle, reassuring, and empathetic phrases.",
    "Tanglish": "Respond naturally in friendly colloquial Tanglish (Tamil words written ONLY using Latin/English characters, e.g. 'Kavala padatheenga bro, naan kooda irukken. Enna aachu, sollunga?'). Absolutely do NOT use Tamil script.",
    "Telugu": "Respond naturally in Telugu script (తెలుగు). Use comforting, supportive words.",
}

def normalize_language_name(language: str) -> str:
    """Normalizes language string across scripts and variations."""
    if not language:
        return "English"
    l = str(language).strip()
    low = l.lower()
    if low == "english":
        return "English"
    if low in ("tamil", "தமிழ்"):
        return "Tamil"
    if low == "tanglish":
        return "Tanglish"
    if low in ("hindi", "हिंदी"):
        return "Hindi"
    if low == "hinglish":
        return "Hinglish"
    if low in ("telugu", "తెలుగు"):
        return "Telugu"
    return l.capitalize()

# Distress / self-harm keywords for deterministic safety detection across all supported languages
CRISIS_KEYWORDS = [
    # English
    "suicide", "kill myself", "end my life", "end it all", "want to die",
    "self harm", "self-harm", "cutting myself", "hang myself", "take all my pills",
    "don't want to live", "dont want to live", "no reason to live", "better off dead",
    "can't go on anymore", "cant go on anymore", "hate living",
    # Hinglish & Romanized Hindi
    "zindagi khatam", "khatam karna", "khatm karna", "khatam kar dunga", "khatam kar dungi",
    "apni jaan lena", "apni jaan de", "jaan de dunga", "jaan de dungi",
    "mar jana chahta", "mar jana chahti", "marne ka man", "marne ka mann",
    "marna chahta", "marna chahti", "khudkushi", "khud khushi", "aatmhatya", "aatmahatya",
    "nahi jeena", "nahi jeena chahta", "nahi jeena chahti",
    # Hindi Devanagari
    "आत्महत्या", "खुदकुशी", "ज़िंदगी खत्म", "जिंदगी खत्म", "जान देना", "जान लेना",
    "मरना चाहता", "मरना चाहती", "मर जाना", "जीना नहीं चाहता", "जीना नहीं चाहती",
    "सब खत्म करना", "मर जाऊं", "मर जाऊँ",
    # Tamil script & Tanglish
    "தற்கொலை", "உயிரை மாய்த்து", "சாக வேண்டும்", "சாக தோன்றுகிறது",
    "tharkolai", "uyira maaikka", "uyir vida", "saaganum", "vaazha pidikkala"
]


def detect_crisis_intent(text: str) -> bool:
    """Checks if message contains self-harm or severe crisis signals."""
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in CRISIS_KEYWORDS)


def get_crisis_response(language: str) -> str:
    """Provides immediate, deterministic safety guidance in the user's chosen language."""
    norm_lang = normalize_language_name(language).lower()

    if "tanglish" in norm_lang:
        return (
            "Bro, neenga romba kashtathula irukeenga nu puriyudhu 💙 Please don't be alone right now. "
            "Ungaloda uyir romba mukkiyam. App la irukura SOS screen la unga emergency contact ku call pannunga, "
            "illana trusted person kitta pesunga.\n\n"
            "Udanadi udhavikku 24x7 free Tele-MANAS helpline: 14416 / 1800-891-4416 ku call panni pesunga, "
            "illana emergency 112 ku call pannunga. Naanga ungaluku support panna inga irukkom."
        )
    if "tamil" in norm_lang:
        return (
            "நண்பா, நீங்கள் மிகவும் கடினமான சூழலில் இருக்கிறீர்கள் என்பதை என்னால் உணர முடிகிறது 💙 "
            "நீங்கள் தனியாக இல்லை, உங்கள் உயிர் மிக மதிப்புமிக்கது. தயவுசெய்து மித்ரா ஆப்பில் உள்ள SOS பக்கத்தில் உங்கள் "
            "குடும்பத்தினர் அல்லது நண்பர்களுக்கு அழையுங்கள்.\n\n"
            "உடனடி இலவச உதவிக்கு 24x7 Tele-MANAS உதவி எண் 14416 / 1800-891-4416 அல்லது அவசர உதவி எண் 112-ஐ அழையுங்கள். "
            "உங்களுக்கு உதவ பலர் எப்போதும் தயாராக இருக்கிறார்கள்."
        )
    if "hinglish" in norm_lang:
        return (
            "Hey dost, main samajh sakta hoon ki is waqt sab kuch bahut heavy aur mushkil lag raha hai 💙 "
            "Lekin please yaad rakho, aap bilkul akele nahi ho aur aapki zindagi bahut keemti hai. "
            "Please abhi kisi apne ya trusted person se baat karo ya Mithra app ke SOS section me jakar apne emergency contact ko call karo.\n\n"
            "Turant madad ke liye 24x7 free national mental health helpline Tele-MANAS: 14416 / 1800-891-4416 par call karein, "
            "ya emergency helpline 112 par call karein. Help available hai aur log aapko support karna chahte hain."
        )
    if "hindi" in norm_lang:
        return (
            "नमस्ते दोस्त 💙 मैं समझ सकता हूँ कि इस समय सब कुछ बहुत भारी और कष्टदायी लग रहा है। "
            "कृपया याद रखें कि आप बिल्कुल अकेले नहीं हैं और आपकी ज़िंदगी बहुत अनमोल है। "
            "कृपया इस कठिन समय में किसी अपने, विश्वसनीय व्यक्ति या डॉक्टर से बात करें, या मिथ्रा ऐप के SOS स्क्रीन पर जाकर अपने इमरजेंसी कॉन्टैक्ट को कॉल करें।\n\n"
            "तत्काल सहायता के लिए 24x7 निःशुल्क सरकारी हेल्पलाइन Tele-MANAS: 14416 / 1800-891-4416 या आपातकालीन नंबर 112 पर तुरंत कॉल करें। "
            "मदद उपलब्ध है और आपकी सुरक्षा अत्यंत महत्वपूर्ण है।"
        )
    if "telugu" in norm_lang:
        return (
            "మిత్రమా 💙 మీరు చాలా క్లిష్టమైన పరిస్థితిలో ఉన్నారని నేను అర్థం చేసుకోగలను. "
            "మీరు ఒంటరిగా లేరు, మీ జీవితం చాలా విలువైనది. దయచేసి మిథ్రా యాప్‌లోని SOS విభాగానికి వెళ్లి మీ కుటుంబ సభ్యులకు లేదా "
            "స్నేహితులకు కాల్ చేయండి.\n\n"
            "24x7 ఉచిత మానసిక సహాయం కోసం Tele-MANAS: 14416 / 1800-891-4416 లేదా 112 కి కాల్ చేయండి."
        )
    # Default English
    return (
        "I hear how overwhelming and painful things feel right now, and I want you to know you don't have to carry this alone 💙 "
        "Your life and safety matter deeply. Please reach out to a trusted person, family member, or professional support right now. "
        "You can open the SOS / Emergency screen in the Mithra app to call your emergency contact.\n\n"
        "Immediate support is available 24/7:\n"
        "- Tele-MANAS (Toll-Free): 14416 / 1800-891-4416\n"
        "- National Emergency: 112\n"
        "Please connect with them right away — you are not alone, and help is available."
    )


# Strict language contract for Tanglish mode
TANGLISH_SYSTEM_PROMPT = """
You are Mithra, a warm, compassionate friend and peer companion.

LANGUAGE MODE: TANGLISH

You MUST reply in natural, colloquial Tanglish (Tamil language written primarily using the Latin/English alphabet, naturally mixed with common English words).

Tanglish requirements:
- Use Latin/English script ONLY. Absolutely do NOT use Tamil Unicode script (தமிழ்).
- Primarily express the sentence structure and vocabulary in conversational Tamil.
- English words are allowed naturally where commonly used in everyday Tanglish (e.g. "feel aagudhu", "stress", "heavy", "mind").
- Do NOT produce predominantly English sentences.
- Do NOT simply insert 1-2 Tamil words into an English sentence.
- Do NOT translate the user's message into formal English.
- Do NOT sound like a therapist, textbook, or translator.
- Match the user's casualness and slang (e.g. "bro", "da", "machan").
- Keep the response conversational, warm, and friend-like (2 to 3 sentences).
- If the user says "bro", "da", "machan", naturally match the tone.
- Prefer Tamil grammatical structure written in Latin script.
- At least approximately 70–80% of the response MUST be conversational Tamil in Latin script rather than English.

BAD Examples (DO NOT DO THIS):
- "I understand that you're feeling overwhelmed. It's okay to feel this way."
- "Manasu sari illa, bro. It's okay to feel heavy."

GOOD Examples (DO THIS):
- "Puriyudhu bro, romba stress ah feel aagudhu pola. Enna aachu nu sollunga, naan kekkuren."
- "Aiyo bro, semma heavy ah irukku pola. Konjam breathe pannunga. Enna problem nu sollunga, pesalaam."
- "Kavala padatheenga da, naan un kooda irukken. Manasula enna thonudho appadiye share pannu."
- "Aiyo bro, puriyudhu. Enna aachu, en ivlo mokka aachu innaki? Sollu bro, kekkuren."
""".strip()

# Strict language contract for Hinglish mode
HINGLISH_SYSTEM_PROMPT = """
You are Mithra, a warm, compassionate friend and peer companion.

LANGUAGE MODE: HINGLISH

You MUST reply in natural, colloquial Hinglish (conversational Hindi written primarily using the Latin/English alphabet, naturally mixed with common English words).

Hinglish requirements:
- Use Latin/English script ONLY. Absolutely do NOT use Hindi Devanagari script (देवनागरी).
- Primarily express the sentence structure and vocabulary in conversational Hindi.
- English words are allowed naturally where commonly used in everyday Hinglish (e.g. "stress", "heavy", "feel", "problem", "mood").
- Do NOT produce predominantly English sentences.
- Do NOT simply insert 1-2 Hindi words into an English sentence.
- Do NOT translate the user's message into formal English.
- Do NOT sound like a therapist or textbook.
- Match the user's casualness and slang (e.g. "bro", "yaar", "dost").
- Keep the response conversational, warm, and friend-like (2 to 3 sentences).
- If the user says "bro", "yaar", naturally match the tone.
- At least approximately 70–80% of the response MUST be conversational Hindi in Latin script rather than English.

BAD Examples (DO NOT DO THIS):
- "I understand that you're feeling very stressed. It's okay to feel this way."
- "Stress mat lo. Everything will be fine, you are strong."

GOOD Examples (DO THIS):
- "Samajh sakta hoon bro, kaafi stress ho raha hai na. Kya hua? Batao, main sun raha hoon."
- "Arey yaar, itna pareshan mat ho. Main yahin hoon tumhare sath. Thoda paani piyo aur batao kya chal raha hai."
- "Dost, tension mat le, main sun raha hoon na. Aaram se bata kya baat hai, saath milkar handle karenge."
""".strip()

import re

TANGLISH_KEYWORDS_SET = {
    "enakku", "enaku", "unaku", "unakku", "ungalukku", "ungaluku", "romba", "irukku", "iruku",
    "irukken", "irukom", "irundha", "irundhal", "enna", "ennachu", "aachu", "aachi", "sollu",
    "sollunga", "sollren", "venum", "venda", "vendam", "mudiyala", "mudiyadhu", "mudiyum",
    "theriyala", "therila", "theriyum", "theriyuma", "pannunga", "pannu", "pannitu", "panreenga",
    "pochu", "poren", "pooren", "varen", "vaanga", "pesanum", "pesalaam", "pesa",
    "kekkuren", "kekalaam", "kekka", "manasu", "kashtama", "kashtam", "kavala",
    "bayama", "santhosham", "machan", "machi", "thala", "da", "paa", "illa", "illai",
    "illana", "podhum", "puriyudhu", "puriyala", "aagudhu", "aagura", "maari", "mari",
    "kooda", "kitta", "kittayum", "yaar", "azhugai", "valikudhu", "konjam", "nalla", "seri",
    "thookam", "udambu", "paravala", "paathu", "vittutu", "semma", "mokka", "bro", "bore",
    "innaiki", "innaki"
}

HINGLISH_KEYWORDS_SET = {
    "mujhe", "mera", "meri", "mere", "tum", "tumhara", "tumhari", "tumhare",
    "aap", "aapka", "aapke", "aapki", "hum", "humara", "kya", "hai", "hain",
    "ho", "hoon", "raha", "rahi", "rahe", "karna", "karo", "karein", "karun",
    "bahut", "bohot", "nahi", "nahin", "accha", "acha", "kaisi", "kaise", "kaisa", "kyun",
    "pareshan", "chinta", "sath", "dost", "bhai", "samajh", "kuch", "kisi", "zindagi", "mann",
    "chahiye", "pata", "yaar", "bro", "tension"
}

ENGLISH_COMMON_WORDS = {
    "i", "me", "my", "myself", "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "they", "them", "their", "it", "its", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "can", "could", "will", "would", "shall", "should",
    "may", "might", "must", "today", "yesterday", "tomorrow", "now", "feeling", "feel",
    "stressed", "happy", "sad", "angry", "tired", "very", "really", "so", "too", "much",
    "help", "please", "talk", "with", "about", "because", "and", "but", "or", "not", "the",
    "a", "an", "to", "for", "in", "on", "at", "by", "from", "up", "down", "over", "under", "meeting"
}

def detect_message_language(text: str, user_selected_language: str = None) -> str:
    """Lightweight deterministic language detector evaluated before calling Qwen."""
    if not text or not text.strip():
        return normalize_language_name(user_selected_language) if user_selected_language else "English"

    # 1. Script checks
    if any('\u0B80' <= c <= '\u0BFF' for c in text):
        return "Tamil"
    if any('\u0900' <= c <= '\u097F' for c in text):
        return "Hindi"
    if any('\u0C00' <= c <= '\u0C7F' for c in text):
        return "Telugu"

    lower = text.lower()
    words = re.findall(r'[a-zA-Z]+', lower)
    words_set = set(words)

    # 2. Tanglish scoring
    tanglish_matches = words_set.intersection(TANGLISH_KEYWORDS_SET)
    tanglish_score = len(tanglish_matches) * 2

    # Tanglish particles and colloquial patterns
    if re.search(r'\b(stress|tired|heavy|sad|tension|bore|lonely|empty|upset|mokka)\s+(ah|a|day)\b', lower):
        tanglish_score += 3
    if re.search(r'\b(semma\s+mokka|feel\s+aagudhu|feel\s+aagura|irukku\s+pola|irukken\s+bro|enna\s+aachu|pesa\s+mudiyala|kooda\s+irukken|kavala\s+padatheenga|yaar\s+kittayum|thookam\s+varala)\b', lower):
        tanglish_score += 3
    # Suffix check (e.g. mudiyala, pannunga, sollunga, aachu)
    for w in words_set:
        if len(w) > 5 and (w.endswith("mudiyala") or w.endswith("sollunga") or w.endswith("pannunga") or w.endswith("aagudhu")):
            tanglish_score += 2

    # 3. Hinglish scoring
    hinglish_matches = words_set.intersection(HINGLISH_KEYWORDS_SET)
    hinglish_score = len(hinglish_matches) * 2
    if re.search(r'\b(ho\s+raha|ho\s+rahi|kar\s+raha|nahi\s+hai|mat\s+lo|kuch\s+nahi|mann\s+nahi|lag\s+raha|baat\s+karo|kya\s+hua|kya\s+chal\s+raha)\b', lower):
        hinglish_score += 3

    # 4. English scoring
    english_matches = words_set.intersection(ENGLISH_COMMON_WORDS)
    english_score = len(english_matches)

    # Multi-signal evaluation
    if tanglish_score >= 3 and tanglish_score > hinglish_score:
        return "Tanglish"
    if hinglish_score >= 3 and hinglish_score > tanglish_score:
        return "Hinglish"

    # If predominantly English tokens and zero Tanglish/Hinglish indicators
    if english_score >= 2 and tanglish_score == 0 and hinglish_score == 0:
        return "English"

    # If user explicitly chose a language and no conflicting signals
    if user_selected_language:
        norm = normalize_language_name(user_selected_language)
        if norm in ("Tanglish", "Hinglish", "Tamil", "Hindi", "Telugu"):
            return norm

    return "English"


def get_system_prompt(language: str = "English") -> str:
    """Returns the formatted system prompt with language instructions."""
    norm_lang = normalize_language_name(language)
    if norm_lang == "Tanglish":
        return TANGLISH_SYSTEM_PROMPT
    if norm_lang == "Hinglish":
        return HINGLISH_SYSTEM_PROMPT

    instruction = LANGUAGE_INSTRUCTIONS.get(
        norm_lang,
        f"Respond in natural, fluent {norm_lang} with empathy and warmth."
    )
    return BASE_MITHRA_SYSTEM_PROMPT.format(language_instruction=instruction)


def build_prompt_messages(message: str, history: List[Any], language: str = "English") -> List[Dict[str, str]]:
    """Builds the full OpenAI / Transformers chat template message list."""
    effective_lang = detect_message_language(message, language)
    messages = [
        {"role": "system", "content": get_system_prompt(effective_lang)}
    ]
    
    for turn in history:
        if isinstance(turn, dict):
            role = turn.get("role", "user")
            # Normalize role names
            if role in ["mithra", "bot"]:
                role = "assistant"
            content = turn.get("content") or turn.get("message") or ""
            if content:
                messages.append({"role": role, "content": str(content)})
                
    messages.append({"role": "user", "content": message})
    return messages
