const express = require("express");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");
const { isNegativeSentiment, getMithraReply, detectFocusIntent, detectCrisisIntent, getCrisisReply, detectMessageLanguage } = require("../ai");
const { detectTone, formatForSpeech, VOICE_STATES } = require("../voice_session");

const router = express.Router();

// --- Chat screen -> send button next to "Type msg" ---
router.post("/message", requireAuth, async (req, res) => {
  const { message } = req.body;
  if (!message || !message.trim()) return res.status(400).json({ error: "message is required" });

  // 1. DETERMINISTIC HIGH-RISK CRISIS GUARDRAIL — Evaluated BEFORE Qwen
  const crisisResult = detectCrisisIntent(message);
  if (crisisResult && crisisResult.risk_detected) {
    let language = req.body.language;
    if (!language) {
      try {
        const userRow = db.prepare("SELECT language FROM users WHERE id = ?").get(req.userId);
        if (userRow && userRow.language) language = userRow.language;
      } catch (_) {}
    }
    const finalLang = crisisResult.detected_language || language || "English";
    const reply = getCrisisReply(finalLang);

    db.prepare("INSERT INTO chat_messages (user_id, sender, message) VALUES (?, 'user', ?)").run(
      req.userId,
      message
    );
    db.prepare("INSERT INTO chat_messages (user_id, sender, message) VALUES (?, 'mithra', ?)").run(
      req.userId,
      reply
    );

    // Auto-log to diary for safety tracking
    db.prepare(
       "INSERT INTO diary_entries (user_id, type, content, mood, auto_logged) VALUES (?, 'auto', ?, 'low', 1)"
    ).run(req.userId, `[Crisis Safety Guardrail] Auto-logged from chat: "${message}"`);

    const speechText = formatForSpeech(reply, finalLang);

    return res.json({
      reply,
      speechText,
      language: finalLang,
      tone: "DISTRESSED",
      voiceState: VOICE_STATES.SAFETY,
      autoLoggedToDiary: true,
      focusState: null,
      crisis: {
        risk_detected: true,
        risk_level: "high",
        safety_mode: true,
        trigger: "self_harm_intent",
        response_mode: "crisis"
      }
    });
  }

  db.prepare("INSERT INTO chat_messages (user_id, sender, message) VALUES (?, 'user', ?)").run(
    req.userId,
    message
  );

  const history = db
    .prepare(
      "SELECT sender, message FROM chat_messages WHERE user_id = ? ORDER BY created_at DESC LIMIT 4"
    )
    .all(req.userId)
    .reverse();
  // Get user preferred language (from request or database profile)
  let language = req.body.language;
  if (!language) {
    try {
      const userRow = db.prepare("SELECT language FROM users WHERE id = ?").get(req.userId);
      if (userRow && userRow.language) language = userRow.language;
    } catch (_) {}
  }

  const effectiveLang = detectMessageLanguage(message, language || "English");
  const reply = await getMithraReply(message, history, effectiveLang);

  db.prepare("INSERT INTO chat_messages (user_id, sender, message) VALUES (?, 'mithra', ?)").run(
    req.userId,
    reply
  );

  // "Isolated zone out / depressed / negative conv -> AI automatically uploads to diary"
  let autoLogged = false;
  if (isNegativeSentiment(message)) {
    db.prepare(
      "INSERT INTO diary_entries (user_id, type, content, mood, auto_logged) VALUES (?, 'auto', ?, 'low', 1)"
    ).run(req.userId, `Auto-logged from chat: "${message}"`);
    autoLogged = true;
  }

  // Contextual Mithra Mode (Focus / Quiet state)
  const focusIntent = detectFocusIntent(message);
  let focusSessionId = null;
  if (focusIntent) {
    try {
      const info = db.prepare(
        "INSERT INTO focus_sessions (user_id, duration_seconds, completed) VALUES (?, ?, ?)"
      ).run(req.userId, focusIntent.durationMinutes * 60, 0);
      focusSessionId = info.lastInsertRowid;
    } catch (_) {}
  }

  const tone = detectTone(message, effectiveLang);
  const speechText = formatForSpeech(reply, effectiveLang);
  const voiceState = focusIntent ? VOICE_STATES.FOCUS : VOICE_STATES.SPEAKING;

  res.json({
    reply,
    speechText,
    language: effectiveLang,
    tone,
    voiceState,
    autoLoggedToDiary: autoLogged,
    focusState: focusIntent ? { ...focusIntent, sessionId: focusSessionId } : null
  });
});

// chat history for the chat screen
router.get("/history", requireAuth, (req, res) => {
  const rows = db
    .prepare("SELECT * FROM chat_messages WHERE user_id = ? ORDER BY created_at ASC")
    .all(req.userId);
  res.json(rows);
});

module.exports = router;
