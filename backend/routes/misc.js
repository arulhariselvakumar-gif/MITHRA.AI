const express = require("express");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");

const router = express.Router();

// --- Focus screen -> timer finishes / is stopped ---
router.post("/focus/session", requireAuth, (req, res) => {
  const { durationSeconds, completed } = req.body;
  db.prepare(
    "INSERT INTO focus_sessions (user_id, duration_seconds, completed) VALUES (?, ?, ?)"
  ).run(req.userId, durationSeconds || 0, completed ? 1 : 0);
  res.json({ ok: true });
});

router.get("/focus/sessions", requireAuth, (req, res) => {
  const rows = db
    .prepare("SELECT * FROM focus_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 20")
    .all(req.userId);
  res.json(rows);
});

// --- Emergency screen -> "Calling ..." button / manage contacts ---
router.get("/emergency/contacts", requireAuth, (req, res) => {
  const rows = db
    .prepare("SELECT * FROM emergency_contacts WHERE user_id = ?")
    .all(req.userId);
  res.json(rows);
});

router.post("/emergency/contacts", requireAuth, (req, res) => {
  const { name, phone } = req.body;
  if (!name || !phone) return res.status(400).json({ error: "name and phone are required" });
  const info = db
    .prepare("INSERT INTO emergency_contacts (user_id, name, phone) VALUES (?, ?, ?)")
    .run(req.userId, name, phone);
  res.json({ id: info.lastInsertRowid, name, phone });
});

module.exports = router;
