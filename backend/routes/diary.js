const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");

const router = express.Router();

const uploadDir = path.join(__dirname, "..", "uploads");
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const unique = `${Date.now()}-${Math.round(Math.random() * 1e9)}${path.extname(file.originalname)}`;
    cb(null, unique);
  },
});
const upload = multer({ storage, limits: { fileSize: 25 * 1024 * 1024 } });

// --- Diary screen -> "Write" button ---
router.post("/write", requireAuth, (req, res) => {
  const { content, mood } = req.body;
  if (!content) return res.status(400).json({ error: "content is required" });

  const info = db
    .prepare(
      "INSERT INTO diary_entries (user_id, type, content, mood) VALUES (?, 'write', ?, ?)"
    )
    .run(req.userId, content, mood || null);

  res.json(getEntry(info.lastInsertRowid));
});

// --- Diary screen -> "Record" button (voice note) ---
router.post("/record", requireAuth, upload.single("audio"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No audio file received" });

  const info = db
    .prepare(
      "INSERT INTO diary_entries (user_id, type, file_path, content) VALUES (?, 'record', ?, ?)"
    )
    .run(req.userId, `/uploads/${req.file.filename}`, req.body.note || null);

  res.json(getEntry(info.lastInsertRowid));
});

// --- Diary screen -> "upload in diary" button ---
router.post("/upload", requireAuth, upload.single("file"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file received" });

  const info = db
    .prepare(
      "INSERT INTO diary_entries (user_id, type, file_path, content) VALUES (?, 'upload', ?, ?)"
    )
    .run(req.userId, `/uploads/${req.file.filename}`, req.body.caption || null);

  res.json(getEntry(info.lastInsertRowid));
});

// list all entries for the diary screen feed (excludes trashed items)
router.get("/", requireAuth, (req, res) => {
  const rows = db
    .prepare("SELECT * FROM diary_entries WHERE user_id = ? AND (status IS NULL OR status = 'active') ORDER BY created_at DESC")
    .all(req.userId);
  res.json(rows);
});

// Soft-delete: Move diary entry to Trash
router.delete("/:id", requireAuth, (req, res) => {
  const now = Math.floor(Date.now() / 1000);
  const info = db
    .prepare("UPDATE diary_entries SET status = 'trashed', deleted_at = ?, trashed_by = ? WHERE id = ? AND user_id = ?")
    .run(now, req.userId, req.params.id, req.userId);
  res.json({ ok: true, trashed: info.changes > 0, id: req.params.id });
});

function getEntry(id) {
  return db.prepare("SELECT * FROM diary_entries WHERE id = ?").get(id);
}

module.exports = router;
