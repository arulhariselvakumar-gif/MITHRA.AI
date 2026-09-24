// intent_router.js — Central Mithra Intent / Action Router
// Used by BOTH text and voice input to produce normalized intents.
// Strict Action Priority:
// 1. SAFETY (Crisis Guardrail)
// 2. USER COMMAND (STOP_TTS, STOP_FOCUS, START_FOCUS)
// 3. MODE CONTROL
// 4. NAVIGATION / DATA ACTION (NAV_*, DELETE_TO_TRASH, RESTORE_ITEM, DELETE_FOREVER, EMPTY_TRASH)
// 5. NORMAL AI CONVERSATION (Qwen3-4B)

const { detectCrisisIntent } = require("./ai");

const INTENT_TYPES = {
  SAFETY: "SAFETY",
  STOP_TTS: "STOP_TTS",
  STOP_FOCUS: "STOP_FOCUS",
  START_FOCUS: "START_FOCUS",
  NAV_HOME: "NAV_HOME",
  NAV_DIARY: "NAV_DIARY",
  NAV_SOS: "NAV_SOS",
  NAV_PROFILE: "NAV_PROFILE",
  DELETE_TO_TRASH: "DELETE_TO_TRASH",
  RESTORE_ITEM: "RESTORE_ITEM",
  DELETE_FOREVER: "DELETE_FOREVER",
  EMPTY_TRASH: "EMPTY_TRASH",
  NORMAL_CONVERSATION: "NORMAL_CONVERSATION"
};

function normalizeText(text) {
  if (!text) return "";
  return text
    .toLowerCase()
    .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"'’]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Central Intent Router
 * Evaluates in strict priority order.
 * Works across English, Tamil, Tanglish, Hindi, and Hinglish.
 */
function routeIntent(text, language = "English") {
  const raw = (text || "").trim();
  const t = normalizeText(raw);

  // -------------------------------------------------------------------------
  // PRIORITY 1: SAFETY (Crisis Guardrail)
  // Deterministic interception before any command or LLM logic
  // -------------------------------------------------------------------------
  const crisisResult = detectCrisisIntent(raw);
  if (crisisResult && crisisResult.risk_detected) {
    return {
      priority: 1,
      type: INTENT_TYPES.SAFETY,
      action: "SAFETY_INTERVENE",
      risk_detected: true,
      detected_language: crisisResult.detected_language || language,
      reason: "Self-harm or crisis indicator detected"
    };
  }

  // -------------------------------------------------------------------------
  // PRIORITY 2: USER COMMANDS
  // (STOP_TTS, STOP_FOCUS, START_FOCUS)
  // -------------------------------------------------------------------------

  // 2A. STOP_TTS (Immediate audio silence)
  // English: "stop talking", "silent", "voice off", "don't speak", "stop", "be quiet"
  // Tanglish: "pesadha", "pesuradha niruthu", "voice off pannu", "voice off pannunga", "stop pannu", "silent ah iru"
  // Tamil: "பேசாதே", "பேசுவதை நிறுத்து", "அமைதியாக இரு"
  // Hinglish: "bolna band karo", "chup ho jao", "chup raho", "voice band karo", "awaz band karo", "mat bolo"
  // Hindi: "चुप रहो", "बोलना बंद करो", "शांत रहो"
  const isStopTts = (
    /^(stop|silent|quiet|shh|chup)$/.test(t) ||
    /\b(stop\s+talking|voice\s+off|don\s*t\s+speak|dont\s+speak|stop\s+speaking|be\s+quiet|shut\s+up|pause\s+voice)\b/.test(t) ||
    /\b(pesadha|pesuradha\s+niruthu|pesura\s+niruthu|voice\s+off\s+pannu|voice\s+off\s+pannunga|silent\s+ah\s+iru|pesama\s+iru)\b/.test(t) ||
    /\b(bolna\s+band\s+karo|chup\s+ho\s+jao|chup\s+raho|voice\s+band\s+karo|awaz\s+band\s+karo|mat\s+bolo)\b/.test(t) ||
    /[\u0B80-\u0BFF]/.test(raw) && /\b(பேசாதே|நிறுத்து|அமைதி)\b/.test(raw) ||
    /[\u0900-\u097F]/.test(raw) && /\b(चुप|बंद\s+करो|शांत)\b/.test(raw)
  );
  if (isStopTts) {
    return {
      priority: 2,
      type: INTENT_TYPES.STOP_TTS,
      action: "STOP_TTS",
      reply: "Voice stopped. I'm listening silently 🤫",
      speechText: ""
    };
  }

  // 2B. STOP_FOCUS (Stop timer, cancel quiet mode, no emotional reply)
  // English: "stop focus", "focus off", "stop timer", "cancel focus", "end focus"
  // Tanglish: "timer stop pannu", "focus mode off pannu", "focus off pannu", "focus mudikalam", "naan mudichiten", "focus stop pannu"
  // Tamil: "கவனம் நிறுத்து", "நேரத்தை நிறுத்து", "முடித்துவிட்டேன்"
  // Hinglish: "focus band karo", "focus off karo", "timer band karo", "padhai khatam", "padh liya"
  // Hindi: "टाइमर बंद करो", "फोकस बंद करो", "पढ़ाई पूरी हुई"
  const isStopFocus = (
    /\b(stop\s+focus|focus\s+off|stop\s+timer|cancel\s+focus|end\s+focus|exit\s+focus)\b/.test(t) ||
    (/\b(focus|timer|padhai|study)\b/.test(t) && /\b(off|stop|band|rok|mudikalam|mudichiko|mudichidu|mudichiten|vendam|venda|close|cancel)\b/.test(t)) ||
    /\b(timer\s+stop\s+pannu|focus\s+mode\s+off\s+pannu|focus\s+off\s+pannu|focus\s+band\s+karo|timer\s+band\s+karo)\b/.test(t) ||
    /\b(naan\s+mudichiten|naa\s+mudichiten|padichu\s+mudichiten|padhai\s+khatam)\b/.test(t)
  );
  if (isStopFocus) {
    let reply = "Sure, Focus Mode is turned off. Hope you had a productive session!";
    if (language.toLowerCase().includes("tanglish")) {
      reply = "Seri bro, Focus Mode-ah off panniten. Naan un kooda thaan irukken, enna vishayam sollunga, pesalaam.";
    } else if (language.toLowerCase().includes("hinglish")) {
      reply = "Sure dost, Focus Mode off kar diya. Kaisa raha aapka session? Ab kuch baat karni hai?";
    }
    return {
      priority: 2,
      type: INTENT_TYPES.STOP_FOCUS,
      action: "STOP_FOCUS",
      reply,
      focusState: {
        active: false,
        durationMinutes: 0,
        status: "FOCUS_OFF"
      }
    };
  }

  // 2C. START_FOCUS (Start quiet focus timer)
  // English: "25 minutes focus", "don't disturb me", "I'm going to study", "focus mode on"
  // Tanglish: "25 mins padikka poren", "disturb pannadha", "konjam neram disturb pannadha", "focus mode on"
  // Hinglish: "mujhe disturb mat karo", "padhai karne ja raha hoon", "focus on karo"
  const isStartFocus = (
    /\b(focus\s+mode\s+on|start\s+focus|focus\s+on)\b/.test(t) ||
    (/\b(focus|study|padhai|padikka)\b/.test(t) && !/\b(off|stop|band|mudikalam|mudichiten)\b/.test(t)) ||
    /\b(don\s*t\s+disturb|dont\s+disturb|disturb\s+pannadha|disturb\s+mat\s+karo)\b/.test(t)
  );
  if (isStartFocus) {
    const match = t.match(/(\d+)\s*(?:minute|min|mins)/);
    const minutes = match ? parseInt(match[1], 10) : 25;
    let reply = `Okay 🤝 I'll stay quiet while you focus for ${minutes} minutes. I'll check in when the timer ends.`;
    if (language.toLowerCase().includes("tanglish")) {
      reply = `Okay bro 🤝 ${minutes} mins Focus Mode start panniyachu. Neenga amaidhiya padunga, naan disturb panna maatten.`;
    } else if (language.toLowerCase().includes("hinglish")) {
      reply = `Theek hai dost 🤝 ${minutes} minute ka focus timer shuru ho gaya hai. Aap aaram se padhai karo, main disturb nahi karunga.`;
    }
    return {
      priority: 2,
      type: INTENT_TYPES.START_FOCUS,
      action: "START_FOCUS",
      durationMinutes: minutes,
      reply,
      focusState: {
        active: true,
        durationMinutes: minutes,
        status: "FOCUS_QUIET"
      }
    };
  }

  // -------------------------------------------------------------------------
  // PRIORITY 4: NAVIGATION & DATA ACTIONS
  // (NAV_*, DELETE_TO_TRASH, RESTORE_ITEM, DELETE_FOREVER, EMPTY_TRASH)
  // -------------------------------------------------------------------------

  // 4A. Navigation Commands
  if (/\b(go\s+home|open\s+home|home\s+screen|home\s+page|home\s+ku\s+po)\b/.test(t) || t === "home") {
    return {
      priority: 4,
      type: INTENT_TYPES.NAV_HOME,
      action: "NAVIGATE",
      target: "chat.html",
      reply: "Taking you to Home 🏠"
    };
  }

  if (/\b(open\s+diary|show\s+my\s+diary|show\s+diary|go\s+to\s+diary|diary\s+open\s+pannu|diary\s+dikhao|diary\s+kholo|diary\s+screen)\b/.test(t) || t === "diary") {
    return {
      priority: 4,
      type: INTENT_TYPES.NAV_DIARY,
      action: "NAVIGATE",
      target: "diary.html",
      reply: "Opening your Diary 📖"
    };
  }

  if (/\b(open\s+sos|emergency\s+page|open\s+emergency|sos\s+ku\s+po|sos\s+screen|sos\s+open\s+pannu|emergency\s+kholo|sos\s+dikhao)\b/.test(t) || t === "sos") {
    return {
      priority: 4,
      type: INTENT_TYPES.NAV_SOS,
      action: "NAVIGATE",
      target: "emergency.html",
      reply: "Opening SOS Emergency Contacts 🚨"
    };
  }

  if (/\b(open\s+profile|show\s+profile|profile\s+page|profile\s+open\s+pannu|profile\s+dikhao|profile\s+kholo)\b/.test(t) || t === "profile") {
    return {
      priority: 4,
      type: INTENT_TYPES.NAV_PROFILE,
      action: "NAVIGATE",
      target: "profile.html",
      reply: "Opening your Profile 👤"
    };
  }

  // 4B. Data / Trash Commands
  // EMPTY_TRASH
  if (/\b(empty\s+trash|trash\s+clear\s+pannu|clear\s+trash|trash\s+saaf\s+karo|pura\s+trash\s+delete)\b/.test(t)) {
    return {
      priority: 4,
      type: INTENT_TYPES.EMPTY_TRASH,
      action: "EMPTY_TRASH",
      reply: "Trash has been completely emptied 🗑️."
    };
  }

  // DELETE_FOREVER (Permanent deletion)
  if (/\b(delete\s+forever|permanently\s+delete|delete\s+permanently|kandippa\s+delete\s+pannu|hamesha\s+ke\s+liye\s+delete)\b/.test(t)) {
    return {
      priority: 4,
      type: INTENT_TYPES.DELETE_FOREVER,
      action: "DELETE_FOREVER",
      reply: "Item permanently deleted from Trash."
    };
  }

  // RESTORE_ITEM
  if (/\b(restore\s+this|restore\s+that|restore\s+item|restore\s+diary|restore\s+chat|restore\s+pannu|wapas\s+lao|restore\s+karo|trash\s+la\s+irundhu\s+eduthu)\b/.test(t)) {
    return {
      priority: 4,
      type: INTENT_TYPES.RESTORE_ITEM,
      action: "RESTORE_ITEM",
      reply: "Item restored from Trash ♻️."
    };
  }

  // DELETE_TO_TRASH (Soft delete / move to trash)
  if (
    /\b(delete\s+this\s+chat|delete\s+this\s+diary|delete\s+today\s*s\s+diary|delete\s+chat|delete\s+diary|move\s+to\s+trash|move\s+this\s+to\s+trash|trash\s+la\s+podu|delete\s+pannu|isko\s+delete\s+karo)\b/.test(t) ||
    (/^delete\b/.test(t) && !/\b(forever|permanently)\b/.test(t))
  ) {
    const isDiary = /\b(diary)\b/.test(t);
    return {
      priority: 4,
      type: INTENT_TYPES.DELETE_TO_TRASH,
      action: "DELETE_TO_TRASH",
      targetType: isDiary ? "diary" : "chat",
      reply: isDiary ? "Diary entry moved to Trash 🗑️. You can restore it anytime." : "Chat message moved to Trash 🗑️. You can restore it anytime."
    };
  }

  // -------------------------------------------------------------------------
  // PRIORITY 5: NORMAL AI CONVERSATION
  // Passed to Qwen3-4B with speaker-perspective and emotional awareness
  // -------------------------------------------------------------------------
  return {
    priority: 5,
    type: INTENT_TYPES.NORMAL_CONVERSATION,
    action: "GENERATE_AI_REPLY"
  };
}

module.exports = {
  INTENT_TYPES,
  routeIntent,
  normalizeText
};
