const express = require("express");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");
const { isNegativeSentiment, getMithraReply, getCrisisReply, detectMessageLanguage } = require("../ai");
const { detectTone, formatForSpeech, VOICE_STATES } = require("../voice_session");
const { routeIntent, INTENT_TYPES } = require("../intent_router");

const router = express.Router();

// --- Chat screen -> send button next to "Type msg" / Voice input ---
router.post("/message", requireAuth, async (req, res) => {
  const { message } = req.body;
  if (!message || !message.trim()) return res.status(400).json({ error: "message is required" });

  // Get user preferred language (from request or database profile)
  let language = req.body.language;
  if (!language) {
    try {
      const userRow = db.prepare("SELECT language FROM users WHERE id = ?").get(req.userId);
      if (userRow && userRow.language) language = userRow.language;
    } catch (_) {}
  }

  const effectiveLang = detectMessageLanguage(message, language || "English");

  // =========================================================================
  // CENTRAL INTENT ROUTER (Action Priority Order)
  // 1. SAFETY
  // 2. USER COMMAND (STOP_TTS, STOP_FOCUS, START_FOCUS)
  // 3. MODE CONTROL
  // 4. NAVIGATION / DATA ACTION (NAV_*, DELETE_TO_TRASH, RESTORE_ITEM, DELETE_FOREVER, EMPTY_TRASH)
  // 5. NORMAL AI CONVERSATION (Qwen3-4B)
  // =========================================================================
  const intent = routeIntent(message, effectiveLang);
  console.log(`[ACTION ROUTER] UserID: ${req.userId} | Intent: ${intent.type} | Priority: ${intent.priority} | Msg: "${message}"`);

  // PRIORITY 1: SAFETY (Immediate Crisis Guardrail)
  if (intent.type === INTENT_TYPES.SAFETY) {
    const finalLang = intent.detected_language || effectiveLang;
    const reply = getCrisisReply(finalLang);

    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'user', ?, 'active')").run(
      req.userId,
      message
    );
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'mithra', ?, 'active')").run(
      req.userId,
      reply
    );

    // Auto-log to diary for safety tracking
    db.prepare(
       "INSERT INTO diary_entries (user_id, type, content, mood, auto_logged, status) VALUES (?, 'auto', ?, 'low', 1, 'active')"
    ).run(req.userId, `[Crisis Safety Guardrail] Auto-logged from chat: "${message}"`);

    const speechText = formatForSpeech(reply, finalLang);

    return res.json({
      intent: intent.type,
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

  // PRIORITY 2: USER COMMANDS
  if (intent.type === INTENT_TYPES.STOP_TTS) {
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'user', ?, 'active')").run(req.userId, message);
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'mithra', ?, 'active')").run(req.userId, intent.reply);
    return res.json({
      intent: intent.type,
      action: "STOP_TTS",
      reply: intent.reply,
      speechText: "",
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.IDLE,
      autoLoggedToDiary: false,
      focusState: null,
      crisis: { risk_detected: false }
    });
  }

  if (intent.type === INTENT_TYPES.STOP_FOCUS) {
    try {
      db.prepare("UPDATE focus_sessions SET completed = 1 WHERE user_id = ? AND completed = 0").run(req.userId);
    } catch (_) {}
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'user', ?, 'active')").run(req.userId, message);
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'mithra', ?, 'active')").run(req.userId, intent.reply);
    return res.json({
      intent: intent.type,
      action: "STOP_FOCUS",
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.SPEAKING,
      autoLoggedToDiary: false,
      focusState: intent.focusState,
      crisis: { risk_detected: false }
    });
  }

  if (intent.type === INTENT_TYPES.START_FOCUS) {
    let sessionId = null;
    try {
      const info = db.prepare(
        "INSERT INTO focus_sessions (user_id, duration_seconds, completed) VALUES (?, ?, ?)"
      ).run(req.userId, intent.durationMinutes * 60, 0);
      sessionId = info.lastInsertRowid;
    } catch (_) {}
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'user', ?, 'active')").run(req.userId, message);
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'mithra', ?, 'active')").run(req.userId, intent.reply);
    return res.json({
      intent: intent.type,
      action: "START_FOCUS",
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.FOCUS,
      autoLoggedToDiary: false,
      focusState: { ...intent.focusState, sessionId },
      crisis: { risk_detected: false }
    });
  }

  // PRIORITY 4: NAVIGATION & DATA ACTIONS
  if (intent.type.startsWith("NAV_")) {
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'user', ?, 'active')").run(req.userId, message);
    db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'mithra', ?, 'active')").run(req.userId, intent.reply);
    return res.json({
      intent: intent.type,
      action: "NAVIGATE",
      target: intent.target,
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.SPEAKING,
      autoLoggedToDiary: false,
      focusState: null,
      crisis: { risk_detected: false }
    });
  }

  if (intent.type === INTENT_TYPES.DELETE_TO_TRASH) {
    const now = Math.floor(Date.now() / 1000);
    if (intent.targetType === "diary") {
      const last = db.prepare("SELECT id FROM diary_entries WHERE user_id = ? AND (status IS NULL OR status = 'active') ORDER BY id DESC LIMIT 1").get(req.userId);
      if (last) {
        db.prepare("UPDATE diary_entries SET status = 'trashed', deleted_at = ?, trashed_by = ? WHERE id = ?").run(now, req.userId, last.id);
      }
    } else {
      const last = db.prepare("SELECT id FROM chat_messages WHERE user_id = ? AND sender = 'user' AND (status IS NULL OR status = 'active') ORDER BY id DESC LIMIT 1").get(req.userId);
      if (last) {
        db.prepare("UPDATE chat_messages SET status = 'trashed', deleted_at = ?, trashed_by = ? WHERE id = ?").run(now, req.userId, last.id);
      }
    }
    return res.json({
      intent: intent.type,
      action: "DELETE_TO_TRASH",
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.SPEAKING,
      autoLoggedToDiary: false,
      focusState: null,
      crisis: { risk_detected: false }
    });
  }

  if (intent.type === INTENT_TYPES.RESTORE_ITEM) {
    const trashedDiary = db.prepare("SELECT id FROM diary_entries WHERE user_id = ? AND status = 'trashed' ORDER BY deleted_at DESC LIMIT 1").get(req.userId);
    if (trashedDiary) {
      db.prepare("UPDATE diary_entries SET status = 'active', deleted_at = NULL, trashed_by = NULL WHERE id = ?").run(trashedDiary.id);
    } else {
      const trashedChat = db.prepare("SELECT id FROM chat_messages WHERE user_id = ? AND status = 'trashed' ORDER BY deleted_at DESC LIMIT 1").get(req.userId);
      if (trashedChat) {
        db.prepare("UPDATE chat_messages SET status = 'active', deleted_at = NULL, trashed_by = NULL WHERE id = ?").run(trashedChat.id);
      }
    }
    return res.json({
      intent: intent.type,
      action: "RESTORE_ITEM",
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.SPEAKING,
      autoLoggedToDiary: false,
      focusState: null,
      crisis: { risk_detected: false }
    });
  }

  if (intent.type === INTENT_TYPES.DELETE_FOREVER) {
    db.prepare("DELETE FROM diary_entries WHERE user_id = ? AND status = 'trashed' ORDER BY deleted_at DESC LIMIT 1").run(req.userId);
    db.prepare("DELETE FROM chat_messages WHERE user_id = ? AND status = 'trashed' ORDER BY deleted_at DESC LIMIT 1").run(req.userId);
    return res.json({
      intent: intent.type,
      action: "DELETE_FOREVER",
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.SPEAKING,
      autoLoggedToDiary: false,
      focusState: null,
      crisis: { risk_detected: false }
    });
  }

  if (intent.type === INTENT_TYPES.EMPTY_TRASH) {
    db.prepare("DELETE FROM diary_entries WHERE user_id = ? AND status = 'trashed'").run(req.userId);
    db.prepare("DELETE FROM chat_messages WHERE user_id = ? AND status = 'trashed'").run(req.userId);
    return res.json({
      intent: intent.type,
      action: "EMPTY_TRASH",
      reply: intent.reply,
      speechText: formatForSpeech(intent.reply, effectiveLang),
      language: effectiveLang,
      tone: "CALM",
      voiceState: VOICE_STATES.SPEAKING,
      autoLoggedToDiary: false,
      focusState: null,
      crisis: { risk_detected: false }
    });
  }

  // PRIORITY 5: NORMAL AI CONVERSATION (Qwen3-4B via FastAPI)
  // Query conversation history BEFORE inserting current user message (excluding trashed messages)
  const history = db
    .prepare(
      "SELECT sender, message FROM chat_messages WHERE user_id = ? AND (status IS NULL OR status = 'active') ORDER BY id DESC LIMIT 6"
    )
    .all(req.userId)
    .reverse();

  console.log(`[CHAT REQUEST] UserID: ${req.userId} | Message: "${message}" | HistoryLen: ${history.length}`);

  db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'user', ?, 'active')").run(
    req.userId,
    message
  );

  const reply = await getMithraReply(message, history, effectiveLang);

  console.log(`[CHAT RESPONSE] UserID: ${req.userId} | Lang: ${effectiveLang} | Reply: "${reply.substring(0, 80).replace(/\n/g, ' ')}..."`);

  db.prepare("INSERT INTO chat_messages (user_id, sender, message, status) VALUES (?, 'mithra', ?, 'active')").run(
    req.userId,
    reply
  );

  // Auto-upload negative conv to diary
  let autoLogged = false;
  if (isNegativeSentiment(message)) {
    db.prepare(
      "INSERT INTO diary_entries (user_id, type, content, mood, auto_logged, status) VALUES (?, 'auto', ?, 'low', 1, 'active')"
    ).run(req.userId, `Auto-logged from chat: "${message}"`);
    autoLogged = true;
  }

  const tone = detectTone(message, effectiveLang);
  const speechText = formatForSpeech(reply, effectiveLang);

  res.json({
    intent: intent.type,
    reply,
    speechText,
    language: effectiveLang,
    tone,
    voiceState: VOICE_STATES.SPEAKING,
    autoLoggedToDiary: autoLogged,
    focusState: null,
    crisis: { risk_detected: false }
  });
});

// chat history for the chat screen (excludes trashed messages)
router.get("/history", requireAuth, (req, res) => {
  const rows = db
    .prepare("SELECT * FROM chat_messages WHERE user_id = ? AND (status IS NULL OR status = 'active') ORDER BY created_at ASC")
    .all(req.userId);
  res.json(rows);
});

module.exports = router;
