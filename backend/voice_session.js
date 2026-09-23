/**
 * voice_session.js — Mithra AI Voice-First Companion Architecture
 * 
 * Provides:
 * 1. Conversational Tone & Emotional Signal Detection (Conversational cues, NOT medical diagnoses)
 * 2. Speech-Friendly Text Serialization (TTS preparation, Markdown/emoji cleanup, natural cadence)
 * 3. Voice Session State Machine abstractions for Web & Native Mobile integration
 */

// Voice Session State Machine Constants
const VOICE_STATES = {
  IDLE: "IDLE",                 // Standing by, microphone closed
  LISTENING: "LISTENING",       // Active VAD / microphone capture
  THINKING: "THINKING",         // Inference & Safety Guardrail processing
  SPEAKING: "SPEAKING",         // TTS active audio output
  INTERRUPTED: "INTERRUPTED",   // User spoke while Mithra was speaking (barge-in)
  QUIET: "QUIET",               // Muted / silent companion mode
  FOCUS: "FOCUS",               // Timed focus session (e.g. 25 min quiet study)
  SAFETY: "SAFETY"              // Deterministic safety SOS mode (overrides all)
};

/**
 * Detects the user's conversational tone and emotional signals.
 * CRITICAL: These are conversational tone signals to adapt warmth, pacing, and style.
 * They are NOT medical or clinical diagnoses.
 * 
 * @param {string} text - User message
 * @param {string} language - Target language
 * @returns {string} - Detected tone key: CASUAL, FORMAL, SERIOUS, PLAYFUL, SAD, FRUSTRATED, ANGRY, CONFUSED, DISTRESSED, or NEUTRAL
 */
function detectTone(text, language = "English") {
  if (!text) return "NEUTRAL";
  const t = text.toLowerCase();

  // 1. ANGRY / FRUSTRATED
  if (
    /\b(pissed\s+off|furious|irritated|angry|fed\s+up|hate\s+this|annoyed|bullshit|gussa|kaduppu|erichal)\b/i.test(t) ||
    t.includes("seriously pissed") || t.includes("so annoyed") || t.includes("romba kadup")
  ) {
    return t.includes("pissed") || t.includes("angry") || t.includes("gussa") ? "ANGRY" : "FRUSTRATED";
  }

  // 2. DISTRESSED (Severe non-suicidal emotional heaviness)
  if (
    /\b(panic|overwhelmed|hyperventilating|shaking|can't\s+take\s+this|too\s+much|breaking\s+down|tanaav|bayama)\b/i.test(t) ||
    t.includes("heart is racing") || t.includes("cant breath") || t.includes("can't breathe")
  ) {
    return "DISTRESSED";
  }

  // 3. SAD / HURT
  if (
    /\b(crying|tears|heartbroken|hopeless|sad|grief|pain|alone|lonely|udaas|dukhi|azhugai|valikudhu)\b/i.test(t) ||
    t.includes("want to cry") || t.includes("feel empty")
  ) {
    return "SAD";
  }

  // 4. SERIOUS
  if (
    /\b(serious|important|matter\s+of|need\s+to\s+talk\s+about\s+something|urgent|critical|grave)\b/i.test(t) ||
    t.includes("talk about something important") || t.includes("serious matter")
  ) {
    return "SERIOUS";
  }

  // 5. FORMAL
  if (
    /\b(kindly|regards|furthermore|regarding|would\s+like\s+to\s+discuss|inquire|assist|pleased)\b/i.test(t) ||
    t.startsWith("i would like to") || t.startsWith("dear")
  ) {
    return "FORMAL";
  }

  // 6. PLAYFUL
  if (
    /\b(haha|hahaha|lol|lmao|joke|funny|rofl|kidding|fun|chutkula|comedy)\b/i.test(t) ||
    t.includes("tell me a joke") || t.includes("just kidding")
  ) {
    return "PLAYFUL";
  }

  // 7. CONFUSED
  if (
    /\b(confused|don't\s+understand|dont\s+get\s+it|what\s+do\s+you\s+mean|lost|puriyala|samajh\s+nahi)\b/i.test(t)
  ) {
    return "CONFUSED";
  }

  // 8. CASUAL (Friendly colloquial slang: "bro", "dost", "mokka", "cool", "machan", "yaar")
  if (
    /\b(bro|dost|machan|machi|yaar|dude|mokka|semma|sup|hey|yo|chill|vibes)\b/i.test(t) ||
    t.includes("semma mokka") || t.includes("ennachu bro")
  ) {
    return "CASUAL";
  }

  return "NEUTRAL";
}

/**
 * Transforms standard chat/markdown responses into natural, speech-friendly text for Text-to-Speech (TTS).
 * 
 * Rules:
 * - Strips all markdown elements (bold, italic, headers, blockquotes, code blocks)
 * - Converts bullet points into natural spoken commas/pauses
 * - Strips emojis so TTS engines don't speak unicode descriptions aloud ("blue heart", "sparkles")
 * - Expands contractions or formats numbers naturally
 * - Removes URLs and technical markers
 * 
 * @param {string} text - Raw textual response from Qwen/Mithra
 * @param {string} language - Target language
 * @returns {string} - Clean, speech-friendly spoken text
 */
function formatForSpeech(text, language = "English") {
  if (!text) return "";
  let spoken = text;

  // 1. Remove Markdown code blocks & inline code
  spoken = spoken.replace(/```[\s\S]*?```/g, " ");
  spoken = spoken.replace(/`([^`]+)`/g, "$1");

  // 2. Remove Markdown headers (e.g. "### Header")
  spoken = spoken.replace(/^#{1,6}\s+/gm, "");

  // 3. Remove Markdown bold/italic (*, **, _, __)
  spoken = spoken.replace(/\*\*([^*]+)\*\*/g, "$1");
  spoken = spoken.replace(/\*([^*]+)\*/g, "$1");
  spoken = spoken.replace(/__([^_]+)__/g, "$1");
  spoken = spoken.replace(/_([^_]+)_/g, "$1");

  // 4. Remove Markdown bullet points (- Item, * Item) and numbered lists (1. Item)
  spoken = spoken.replace(/^\s*[-*•]\s+/gm, "");
  spoken = spoken.replace(/^\s*\d+\.\s+/gm, "");

  // 5. Remove URLs
  spoken = spoken.replace(/https?:\/\/\S+/gi, "");

  // 6. Remove Emojis (Ranges for all common pictographs, symbols, hearts, transport, emoticons)
  spoken = spoken.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{2300}-\u{23FF}\u{2B50}\u{2B55}\u{2934}\u{2935}]/gu, "");

  // 7. Remove brackets and parentheses used for notes or citations (e.g. "[1]", "(Toll-Free)")
  spoken = spoken.replace(/\[[^\]]*\]/g, "");

  // 8. Clean up phone number pauses for natural speech (e.g., "14416 / 1800-891-4416" -> "14416, or 1800-891-4416")
  spoken = spoken.replace(/\s*\/\s*/g, ", or ");

  // 9. Normalize multiple line breaks and whitespace to clean conversational pauses
  spoken = spoken.replace(/\n{2,}/g, ". ");
  spoken = spoken.replace(/\n/g, ", ");
  spoken = spoken.replace(/\s{2,}/g, " ").trim();

  // 10. Ensure the spoken string doesn't end with an awkward dangling comma
  spoken = spoken.replace(/,\s*$/, ".");

  return spoken;
}

module.exports = {
  VOICE_STATES,
  detectTone,
  formatForSpeech
};
