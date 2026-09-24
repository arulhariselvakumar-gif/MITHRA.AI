// ai.js — Mithra's "brain".
// Ships with a lightweight rule-based responder + keyword sentiment check
// (no external key needed, works offline). If AI_API_KEY is set, swap in
// a real LLM call inside callRealAI() below.

const NEGATIVE_WORDS = [
  "sad", "alone", "lonely", "depressed", "depression", "hopeless", "hurt",
  "cry", "crying", "worthless", "tired of", "give up", "no one cares",
  "hate myself", "can't do this", "cant do this", "empty", "numb",
  "suicide", "kill myself", "end it", "end my life", "want to die", "self harm", "self-harm",
  // Hindi & Hinglish keywords for diary auto-logging
  "zindagi khatam", "khatam karna", "khatm karna", "marna chahta", "marna chahti",
  "mar jana", "khudkushi", "aatmhatya", "tanav", "tanaav", "pareshan", "akela", "dukhi", "udaas", "udas",
  "तनाव", "अकेला", "परेशान", "दुखी", "उदास", "आत्महत्या", "मरना", "जिंदगी खत्म", "ज़िंदगी खत्म",
  // Tamil & Tanglish keywords
  "மன அழுத்தம்", "தற்கொலை", "கவலை", "tharkolai", "romba stress", "kashtam"
];

function isNegativeSentiment(text) {
  const t = (text || "").toLowerCase();
  return NEGATIVE_WORDS.some((w) => t.includes(w));
}

// Very small canned-response engine so the demo works with zero setup.
function ruleBasedReply(message, language = "English") {
  const t = (message || "").toLowerCase();
  const lang = (language || "English").toLowerCase();

  // 1. Physical chest pain symptom check (Emergency medical safety)
  if (/\b(nenju\s+vali|nenjula\s+vali|chest\s+pain|pada\s+pada|nenju\s+valikudhu)\b/.test(t)) {
    if (lang.includes("tanglish")) {
      return "Aiyo bro, unakku nenju valikudha? Please idhuku risk edukaadheenga. Modhalla amaidhiya ukkarunga. Valikudhu na udane doctor or 112 emergency ku call pannunga, illa family kitta sollunga. Naan un kooda irukken, aana please medical help mukkiyam bro.";
    }
    return "Bro, are you feeling chest pain? Please sit down, rest, and do not ignore physical pain. If it persists or feels severe, please call emergency services (112) or reach out to a doctor right away.";
  }

  // 2. Focus mode deactivation
  if (/\b(focus|study|padhai)\b/.test(t) && /\b(off|stop|end|cancel|exit|mudikalam|mudichiko|mudichidu|vendam|venda|band)\b/.test(t)) {
    if (lang.includes("tanglish")) {
      return "Sure bro, Focus Mode off panniten. Epdi irundhudhu unga focus session? Edhavadhu pesalaama?";
    }
    if (lang.includes("hinglish")) {
      return "Sure dost, Focus Mode off kar diya. Kaisa raha aapka session? Ab kuch baat karni hai?";
    }
    return "Sure, Focus Mode is now turned off. How was your session? Let me know if you need anything else.";
  }

  // 3. Companion confirmation query ("nee en kooda iruppiya?")
  if (/\b(nee|neenga)\s+(en|ennoda|engooda|en\s+kooda)\s+(iruppiya|irupeengala|irupiya|iruppa)\b/.test(t) || /\b(will\s+you\s+be\s+with\s+me)\b/.test(t)) {
    if (lang.includes("tanglish")) {
      return "Of course bro, naan un kooda irukken! Eppovum un kooda thaan iruppen, unakku thonuradha eppo venaalum enkitta sollalaam.";
    }
    if (lang.includes("hinglish")) {
      return "Of course dost, main hamesha aapke sath hoon! Jab bhi baat karni ho, main yahin hoon.";
    }
    return "Of course bro, I am right here with you! You are never alone.";
  }

  // 4. Specific Tanglish perspective responses
  if (lang.includes("tanglish")) {
    if (/\b(stress)\b/.test(t)) {
      return "Unakku romba stress ah irukku pola bro. Enna aachu? Sollu, naan kekkuren.";
    }
    if (/\b(tired)\b/.test(t)) {
      return "Nee romba tired ah irukka pola. Konjam rest eduthuko bro.";
    }
    if (/\b(family)\b/.test(t)) {
      return "Unnoda family la problem aacha bro? Sollu, enna nadandhudhu?";
    }
  }

  if (isNegativeSentiment(t)) {
    if (lang.includes("hindi")) {
      return "नमस्ते दोस्त 💙 मैं समझ सकता हूँ कि आज का दिन काफी तनावपूर्ण रहा है। आप अकेले नहीं हैं — क्या आप अपनी बात साझा करना चाहेंगे? मैंने इसे आपकी डायरी में भी सुरक्षित कर दिया है।";
    }
    if (lang.includes("hinglish")) {
      return "Hey dost 💙 Main samajh sakta hoon ki cheezein abhi thodi heavy lag rahi hain. Aap akele nahi ho — agar baat karni ho toh main yahin hoon. Maine iska ek note aapki diary me save kar diya hai.";
    }
    if (lang.includes("tanglish")) {
      return "Unakku romba heavy ah irukku pola bro. Neenga thaniya illa, naan unga kooda irukken. Enna aachu nu sollunga, pesalaam. Idhoda note-ah unga diary-la naan save panniten.";
    }
    if (lang.includes("tamil")) {
      return "நண்பா 💙 உங்கள் மன பாரத்தை என்னால் புரிந்து கொள்ள முடிகிறது. நீங்கள் தனியாக இல்லை — என்னிடம் பகிர்ந்து கொள்ளுங்கள். இதை உங்கள் நாட்குறிப்பில் குறித்து வைத்துள்ளேன்.";
    }
    return "Hey bro 💙 I'm right here with you. It sounds like things feel heavy right now. " +
      "You don't have to carry it alone — want to talk about what's going on, or just vent for a bit? " +
      "I've also saved a note of this in your diary so you can look back on how far you've come.";
  }
  if (/^(hi|hello|hey|yo)\b/.test(t)) {
    return "Hey! Main Mithra hoon — your AI dost. How are you feeling today?";
  }
  if (t.includes("focus") || t.includes("study")) {
    return "Okay 🤝 I'll stay quiet while you focus. I'll check in after 25 minutes.";
  }
  if (t.includes("thank")) {
    return "Anytime, that's what I'm here for 🙂";
  }
  return "I hear you. Tell me more — I'm listening, no judgment here.";
}

// URL for FastAPI microservice (dynamic to allow test_fallback override)
function getFastApiUrl() {
  return process.env.FASTAPI_URL || "http://127.0.0.1:8000";
}

function normalizeLanguage(lang) {
  if (!lang) return "English";
  const l = String(lang).trim();
  const lower = l.toLowerCase();
  if (lower === "english") return "English";
  if (l === "தமிழ்" || lower === "tamil") return "Tamil";
  if (lower === "tanglish") return "Tanglish";
  if (l === "हिंदी" || lower === "hindi") return "Hindi";
  if (lower === "hinglish") return "Hinglish";
  if (l === "తెలుగు" || lower === "telugu") return "Telugu";
  return l;
}

async function callFastAPIAI(message, history = [], language = "English") {
  const normLang = normalizeLanguage(language);
  const payload = {
    message,
    history: history || [],
    language: normLang,
  };

  const res = await fetch(`${getFastApiUrl()}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(120000), // 120s timeout for local CPU inference
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`FastAPI returned HTTP ${res.status}: ${errorText}`);
  }

  const data = await res.json();
  if (data && typeof data.reply === "string" && data.reply.trim().length > 0) {
    return data.reply.trim();
  }

  throw new Error("FastAPI returned empty or invalid reply");
}

function normalizeCrisisText(text) {
  if (!text) return "";
  let s = text.toLowerCase();
  // Collapse 3 or more repeated characters to 2 (e.g. "saaaava" -> "saava", "poooooren" -> "pooren")
  s = s.replace(/(.)\1{2,}/g, "$1$1");
  // Replace punctuation with spaces, preserving Tamil, Hindi, Latin letters and numbers
  s = s.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"'’]/g, " ");
  // Collapse whitespace
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

// 1. High-risk Tanglish intent patterns (e.g. "naa saava poren", "enaku saaganum", "life ah mudichikalam")
const TANGLISH_CRISIS_PATTERNS = [
  // "naa saava poren", "naan saaga poren", "na seththu poga poren", "naan seththu poganum", "na sethu poren"
  /\b(na|naa|naan|nan)\s+(saava|saaga|sethu|seththu|sethtu)\s+(poren|pooren|poga\s+poren|poga\s+pooren|poganum|ponum)\b/,
  // "saaga poren", "saava poren", "sethu poren", "seththu poren", "sethu poga poren", "seththu poga poren"
  /\b(saava|saaga|sethu|seththu|sethtu)\s+(poren|pooren|poga\s+poren|poga\s+pooren|poganum|ponum)\b/,
  // "enaku saaganum", "enakku saaganum", "enakku saavanum", "enaku saavanum"
  /\b(enakku|enaku)\s+(saaganum|saavanum|sethu\s+poganum|seththu\s+poganum|sethu\s+ponum|seththu\s+ponum)\b/,
  // "enakku saava thonudhu", "saaga thonudhu", "saava thonuthu", "saaga thonuthu"
  /\b(enakku|enaku|manasula)?\s*(saava|saaga|sethu\s+poga|seththu\s+poga)\s+(thonudhu|thonuthu|thondhu)\b/,
  // "life ah mudichikalam", "life mudichikalam", "vaazhkai ah mudichikalam"
  /\b(life|vaazhkai|vaazhka)\s*(ah|a)?\s*(mudichikalam|mudichukalam|mudikalam|mudikalaam|mudichikalaam|mudikkanum|end\s+pannikalam)\b/,
  // "naan seththudren", "naa seththuruven", "naan sethudren", "naa sethudren"
  /\b(na|naa|naan|nan)\s+(seththudren|sethudren|seththuruven|sethuruven|seththuduren|sethuduren)\b/,
  // "tharkolai"
  /\btharkolai\b/,
  // "uyira maaikka", "uyir vida", "uyira vida poren"
  /\buyira?\s+(maaikka|maaikkanum|vida|vidanum|vittudren|vida\s+poren)\b/
];

// 2. High-risk Tamil Unicode script phrases
const TAMIL_CRISIS_PHRASES = [
  "சாக போறேன்", "சாகப் போறேன்", "சாகபோறேன்", "சாக வேண்டும்", "சாகவேண்டும்",
  "சாக தோன்றுகிறது", "சாக தோணுது", "சாகத் தோணுது", "சாகத்தோணுது",
  "செத்துப் போகப் போறேன்", "செத்து போக போறேன்", "செத்துப்போகப்போறேன்", "செத்து போகனும்", "செத்துப்போகனும்",
  "வாழ்க்கையை முடித்துக் கொள்ள", "என் வாழ்க்கையை முடிச்சிக்கிறேன்", "வாழ்க்கைய முடிச்சிக்கலாம்", "வாழ்க்கையை முடிச்சிக்கலாம்",
  "தற்கொலை", "உயிரை மாய்த்து", "உயிர் விட", "உயிரை விட"
];

// 3. High-risk Hindi Devanagari phrases
const HINDI_CRISIS_PHRASES = [
  "अपनी जिंदगी खत्म", "अपनी ज़िंदगी खत्म", "ज़िंदगी खत्म करना", "जिंदगी खत्म करना",
  "आत्महत्या", "खुदकुशी",
  "मरना चाहता", "मरना चाहती", "मर जाना चाहता", "मर जाना चाहती", "मर जाने का मन",
  "जान देना चाहता", "जान लेना चाहता",
  "जीना नहीं चाहता", "जीना नहीं चाहती",
  "सब खत्म करना", "मर जाऊं", "मर जाऊँ"
];

// 4. High-risk Hinglish phrases
const HINGLISH_CRISIS_PHRASES = [
  "zindagi khatam", "zindagi khatm", "life khatam", "apni jaan lena", "apni jaan de",
  "jaan de dunga", "jaan de dungi", "mar jana chahta", "mar jana chahti",
  "marne ka man", "marne ka mann", "marna chahta", "marna chahti", "marne ja raha",
  "khudkushi", "khud khushi", "aatmhatya", "aatmahatya",
  "nahi jeena chahta", "nahi jeena chahti", "nahi jeena mujhe", "ab nahi jeena"
];

// 5. High-risk English phrases
const ENGLISH_CRISIS_PHRASES = [
  "suicide", "kill myself", "end my life", "end it all", "want to die", "wanna die",
  "want to end my life", "wanna end my life", "self harm", "self-harm",
  "cutting myself", "hang myself", "take all my pills", "take my own life",
  "don't want to live", "dont want to live", "no reason to live", "better off dead",
  "can't go on anymore", "cant go on anymore", "hate living", "slit my wrists",
  "wish i was dead", "wish i were dead"
];

function detectCrisisIntent(text) {
  if (!text) return { risk_detected: false };
  const rawLower = text.toLowerCase();
  const norm = normalizeCrisisText(text);

  // 1. Tanglish patterns
  for (const regex of TANGLISH_CRISIS_PATTERNS) {
    if (regex.test(norm)) {
      return {
        risk_detected: true,
        risk_level: "high",
        safety_mode: true,
        trigger: "self_harm_intent",
        response_mode: "crisis",
        detected_language: "Tanglish"
      };
    }
  }

  // 2. Tamil script phrases
  for (const p of TAMIL_CRISIS_PHRASES) {
    if (norm.includes(p) || rawLower.includes(p)) {
      return {
        risk_detected: true,
        risk_level: "high",
        safety_mode: true,
        trigger: "self_harm_intent",
        response_mode: "crisis",
        detected_language: "Tamil"
      };
    }
  }

  // 3. Hindi Devanagari phrases
  for (const p of HINDI_CRISIS_PHRASES) {
    if (norm.includes(p) || rawLower.includes(p)) {
      return {
        risk_detected: true,
        risk_level: "high",
        safety_mode: true,
        trigger: "self_harm_intent",
        response_mode: "crisis",
        detected_language: "Hindi"
      };
    }
  }

  // 4. Hinglish phrases
  for (const p of HINGLISH_CRISIS_PHRASES) {
    if (norm.includes(p)) {
      return {
        risk_detected: true,
        risk_level: "high",
        safety_mode: true,
        trigger: "self_harm_intent",
        response_mode: "crisis",
        detected_language: "Hinglish"
      };
    }
  }

  // 5. English phrases
  for (const p of ENGLISH_CRISIS_PHRASES) {
    if (norm.includes(p)) {
      return {
        risk_detected: true,
        risk_level: "high",
        safety_mode: true,
        trigger: "self_harm_intent",
        response_mode: "crisis",
        detected_language: "English"
      };
    }
  }

  return { risk_detected: false };
}

function getCrisisReply(language) {
  const norm = normalizeLanguage(language).toLowerCase();
  if (norm.includes("tanglish")) {
    return (
      "Bro, naan unga kooda irukken 💙 Neenga ipo romba kashtamaana nelaiyil irukkeenga nu puriyudhu.\n" +
      "Please thaniya irukka vendam. Nambikkaiyaana oruvarai udane thodarbu kollunga.\n" +
      "Ungalukku udanadi aabathu irundhal emergency help-ai thodarbu kollunga.\n\n" +
      "Udanadi 24x7 free govt helpline Tele-MANAS: 14416 / 1800-891-4416 illana emergency 112 ku call pannunga. " +
      "Mithra app la irukura SOS screen la unga emergency contacts ku call panna mudiyum."
    );
  }
  if (norm.includes("tamil")) {
    return (
      "நான் உங்களுடன் இருக்கிறேன் 💙 நீங்கள் இப்போது மிகவும் கஷ்டமான நிலையில் இருப்பது போல தெரிகிறது.\n" +
      "தயவுசெய்து தனியாக இருக்க வேண்டாம். நம்பிக்கையான ஒருவரை உடனே தொடர்பு கொள்ளுங்கள்.\n" +
      "உங்களுக்கு உடனடி ஆபத்து இருந்தால் emergency help-ஐ தொடர்பு கொள்ளுங்கள்.\n\n" +
      "உடனடி 24x7 இலவச அரசு உதவி எண் Tele-MANAS: 14416 / 1800-891-4416 அல்லது அவசர உதவி எண் 112-ஐ உடனே அழையுங்கள். " +
      "மித்ரா ஆப்பில் உள்ள SOS பக்கத்திலும் உங்கள் அவசர உதவிக் குழுவை தொடர்பு கொள்ளலாம்."
    );
  }
  if (norm.includes("hinglish")) {
    return (
      "Main aapke sath hoon 💙 Main samajh sakta hoon ki is waqt sab kuch bahut heavy aur mushkil lag raha hai.\n" +
      "Please is waqt akele mat raho. Kisi apne ya trusted person se turant baat karo.\n" +
      "Agar aapko turant khatra feel ho raha hai, toh emergency help ko contact karein.\n\n" +
      "24x7 free national helpline Tele-MANAS: 14416 / 1800-891-4416 ya emergency number 112 par call karein. " +
      "Mithra app ke SOS screen par jakar apne emergency circle se bhi connect kar sakte ho."
    );
  }
  if (norm.includes("hindi")) {
    return (
      "मैं आपके साथ हूँ 💙 मैं समझ सकता हूँ कि इस समय सब कुछ बहुत भारी और कष्टदायी लग रहा है।\n" +
      "कृपया इस समय अकेले न रहें। किसी अपने, विश्वसनीय व्यक्ति से तुरंत बात करें।\n" +
      "अगर आपको तत्काल खतरा महसूस हो रहा है, तो तुरंत emergency help से संपर्क करें।\n\n" +
      "24x7 निःशुल्क सरकारी हेल्पलाइन Tele-MANAS: 14416 / 1800-891-4416 या आपातकालीन नंबर 112 पर तुरंत कॉल करें। " +
      "आप मिथ्रा ऐप के SOS स्क्रीन पर जाकर भी अपने इमरजेंसी कॉन्टैक्ट्स को कॉल कर सकते हैं।"
    );
  }
  return (
    "I'm here with you 💙 It sounds like you're going through an extremely difficult moment right now.\n" +
    "Please don't stay alone. Reach out to someone you trust right now.\n" +
    "If you are in immediate danger, contact emergency help.\n\n" +
    "Free 24/7 confidential support is available right now:\n" +
    "• Tele-MANAS (Govt Mental Health Helpline): 14416 / 1800-891-4416\n" +
    "• National Emergency: 112\n" +
    "You can also open the SOS screen in Mithra to connect with your emergency contacts."
  );
}

const TANGLISH_KEYWORDS_SET = new Set([
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
]);

const HINGLISH_KEYWORDS_SET = new Set([
  "mujhe", "mera", "meri", "mere", "tum", "tumhara", "tumhari", "tumhare",
  "aap", "aapka", "aapke", "aapki", "hum", "humara", "kya", "hai", "hain",
  "ho", "hoon", "raha", "rahi", "rahe", "karna", "karo", "karein", "karun",
  "bahut", "bohot", "nahi", "nahin", "accha", "acha", "kaisi", "kaise", "kaisa", "kyun",
  "pareshan", "chinta", "sath", "dost", "bhai", "samajh", "kuch", "kisi", "zindagi", "mann",
  "chahiye", "pata", "yaar", "bro", "tension"
]);

const ENGLISH_COMMON_WORDS = new Set([
  "i", "me", "my", "myself", "we", "our", "you", "your", "he", "him", "his", "she", "her",
  "they", "them", "their", "it", "its", "what", "which", "who", "whom", "this", "that",
  "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
  "having", "do", "does", "did", "doing", "can", "could", "will", "would", "shall", "should",
  "may", "might", "must", "today", "yesterday", "tomorrow", "now", "feeling", "feel",
  "stressed", "happy", "sad", "angry", "tired", "very", "really", "so", "too", "much",
  "help", "please", "talk", "with", "about", "because", "and", "but", "or", "not", "the",
  "a", "an", "to", "for", "in", "on", "at", "by", "from", "up", "down", "over", "under", "meeting"
]);

function detectMessageLanguage(text, userSelectedLanguage = null) {
  if (!text || !text.trim()) {
    return userSelectedLanguage ? normalizeLanguage(userSelectedLanguage) : "English";
  }

  // 1. Script checks
  if (/[\u0B80-\u0BFF]/.test(text)) return "Tamil";
  if (/[\u0900-\u097F]/.test(text)) return "Hindi";
  if (/[\u0C00-\u0C7F]/.test(text)) return "Telugu";

  const lower = text.toLowerCase();
  const words = lower.match(/[a-zA-Z]+/g) || [];
  const wordsSet = new Set(words);

  // 2. Tanglish scoring
  let tanglishScore = 0;
  for (const w of wordsSet) {
    if (TANGLISH_KEYWORDS_SET.has(w)) tanglishScore += 2;
    if (w.length > 5 && (w.endsWith("mudiyala") || w.endsWith("sollunga") || w.endsWith("pannunga") || w.endsWith("aagudhu"))) {
      tanglishScore += 2;
    }
  }
  if (/\b(stress|tired|heavy|sad|tension|bore|lonely|empty|upset|mokka)\s+(ah|a|day)\b/.test(lower)) {
    tanglishScore += 3;
  }
  if (/\b(semma\s+mokka|feel\s+aagudhu|feel\s+aagura|irukku\s+pola|irukken\s+bro|enna\s+aachu|pesa\s+mudiyala|kooda\s+irukken|kavala\s+padatheenga|yaar\s+kittayum|thookam\s+varala)\b/.test(lower)) {
    tanglishScore += 3;
  }

  // 3. Hinglish scoring
  let hinglishScore = 0;
  for (const w of wordsSet) {
    if (HINGLISH_KEYWORDS_SET.has(w)) hinglishScore += 2;
  }
  if (/\b(ho\s+raha|ho\s+rahi|kar\s+raha|nahi\s+hai|mat\s+lo|kuch\s+nahi|mann\s+nahi|lag\s+raha|baat\s+karo|kya\s+hua|kya\s+chal\s+raha)\b/.test(lower)) {
    hinglishScore += 3;
  }

  // 4. English scoring
  let englishScore = 0;
  for (const w of wordsSet) {
    if (ENGLISH_COMMON_WORDS.has(w)) englishScore += 1;
  }

  // Multi-signal evaluation
  if (tanglishScore >= 3 && tanglishScore > hinglishScore) {
    return "Tanglish";
  }
  if (hinglishScore >= 3 && hinglishScore > tanglishScore) {
    return "Hinglish";
  }

  // If predominantly English tokens and zero Tanglish/Hinglish indicators
  if (englishScore >= 2 && tanglishScore === 0 && hinglishScore === 0) {
    return "English";
  }

  // Fallback to user selected language if chosen
  if (userSelectedLanguage) {
    const norm = normalizeLanguage(userSelectedLanguage);
    if (["Tanglish", "Hinglish", "Tamil", "Hindi", "Telugu"].includes(norm)) {
      return norm;
    }
  }

  return "English";
}

async function getMithraReply(message, history = [], language = "English") {
  // Deterministic Crisis Safety Guardrail — immediate response without waiting for LLM
  const crisisResult = detectCrisisIntent(message);
  if (crisisResult && crisisResult.risk_detected) {
    return getCrisisReply(crisisResult.detected_language || language);
  }

  const effectiveLang = detectMessageLanguage(message, language);
  try {
    const reply = await callFastAPIAI(message, history, effectiveLang);
    return reply;
  } catch (err) {
    console.warn(`[EXPRESS-AI] FastAPI microservice call failed (${err.message}). Falling back to local offline response.`);
    return ruleBasedReply(message, effectiveLang);
  }
}

function detectFocusIntent(text) {
  if (!text) return null;
  const t = text.toLowerCase();
  const hasFocus = (t.includes("don't disturb") || t.includes("dont disturb") || t.includes("study") || t.includes("focus") || t.includes("padhai"));
  if (!hasFocus) return null;

  // Check if user is asking to turn OFF, stop, cancel, or end focus mode
  const isStop = /\b(off|stop|end|cancel|exit|close|mudikalam|mudichiko|mudichidu|vendam|venda|band|khatam|rok)\b/.test(t);
  if (isStop) {
    return {
      active: false,
      durationMinutes: 0,
      status: "FOCUS_OFF"
    };
  }

  const match = t.match(/(\d+)\s*(?:minute|min)/);
  const minutes = match ? parseInt(match[1], 10) : 25;
  return {
    active: true,
    durationMinutes: minutes,
    status: "FOCUS_QUIET"
  };
}

module.exports = {
  isNegativeSentiment,
  getMithraReply,
  normalizeLanguage,
  detectCrisisIntent,
  getCrisisReply,
  detectFocusIntent,
  detectMessageLanguage
};

