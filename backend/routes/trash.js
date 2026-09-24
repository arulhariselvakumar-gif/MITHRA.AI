// routes/trash.js — Phone-gallery style application-level Trash API
const express = require("express");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");

const router = express.Router();

// 1. GET /api/trash — List all trashed items (diary entries + chat messages)
router.get("/", requireAuth, (req, res) => {
  // Prune expired trash entries first
  if (db.cleanupExpiredTrash) db.cleanupExpiredTrash(30);

  const trashedDiary = db
    .prepare(
      "SELECT id, 'diary' AS itemType, content, file_path, mood, deleted_at, trashed_by, created_at FROM diary_entries WHERE user_id = ? AND status = 'trashed' ORDER BY deleted_at DESC"
    )
    .all(req.userId);

  const trashedChats = db
    .prepare(
      "SELECT id, 'chat' AS itemType, message AS content, NULL AS file_path, NULL AS mood, deleted_at, trashed_by, created_at FROM chat_messages WHERE user_id = ? AND status = 'trashed' ORDER BY deleted_at DESC"
    )
    .all(req.userId);

  const items = [...trashedDiary, ...trashedChats].sort((a, b) => (b.deleted_at || 0) - (a.deleted_at || 0));

  res.json({
    retentionDays: 30,
    count: items.length,
    items
  });
});

// 2. POST /api/trash/restore — Restore an item from Trash
router.post("/restore", requireAuth, (req, res) => {
  const { type, id } = req.body;
  if (!type || !id) return res.status(400).json({ error: "type and id are required" });

  const now = Math.floor(Date.now() / 1000);
  if (type === "diary") {
    const info = db
      .prepare("UPDATE diary_entries SET status = 'active', deleted_at = NULL, trashed_by = NULL WHERE id = ? AND user_id = ?")
      .run(id, req.userId);
    return res.json({ ok: true, restored: info.changes > 0, type, id });
  } else if (type === "chat") {
    const info = db
      .prepare("UPDATE chat_messages SET status = 'active', deleted_at = NULL, trashed_by = NULL WHERE id = ? AND user_id = ?")
      .run(id, req.userId);
    return res.json({ ok: true, restored: info.changes > 0, type, id });
  }

  res.status(400).json({ error: "Invalid type. Must be 'diary' or 'chat'" });
});

// 3. POST /api/trash/delete-forever — Permanently delete an item from Trash
router.post("/delete-forever", requireAuth, (req, res) => {
  const { type, id } = req.body;
  if (!type || !id) return res.status(400).json({ error: "type and id are required" });

  if (type === "diary") {
    const info = db
      .prepare("DELETE FROM diary_entries WHERE id = ? AND user_id = ? AND status = 'trashed'")
      .run(id, req.userId);
    return res.json({ ok: true, deletedForever: info.changes > 0, type, id });
  } else if (type === "chat") {
    const info = db
      .prepare("DELETE FROM chat_messages WHERE id = ? AND user_id = ? AND status = 'trashed'")
      .run(id, req.userId);
    return res.json({ ok: true, deletedForever: info.changes > 0, type, id });
  }

  res.status(400).json({ error: "Invalid type. Must be 'diary' or 'chat'" });
});

// 4. POST /api/trash/empty — Empty entire Trash for authenticated user
router.post("/empty", requireAuth, (req, res) => {
  const diaryInfo = db
    .prepare("DELETE FROM diary_entries WHERE user_id = ? AND status = 'trashed'")
    .run(req.userId);

  const chatInfo = db
    .prepare("DELETE FROM chat_messages WHERE user_id = ? AND status = 'trashed'")
    .run(req.userId);

  res.json({
    ok: true,
    emptied: true,
    deletedDiaryCount: diaryInfo.changes,
    deletedChatCount: chatInfo.changes
  });
});

module.exports = router;
