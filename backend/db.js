// db.js — SQLite database setup for Mithra
const path = require("path");
let db;
try {
  const Database = require("better-sqlite3");
  db = new Database(path.join(__dirname, "mithra.db"));
  db.pragma("journal_mode = WAL");
} catch (err) {
  const { DatabaseSync } = require("node:sqlite");
  db = new DatabaseSync(path.join(__dirname, "mithra.db"));
  db.exec("PRAGMA journal_mode = WAL;");
}

db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  language TEXT DEFAULT 'English',
  reset_token TEXT,
  reset_token_expires INTEGER,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS diary_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,              -- 'write' | 'record' | 'upload' | 'auto'
  content TEXT,                    -- text content (for 'write' and AI notes)
  file_path TEXT,                  -- stored file for 'record' / 'upload'
  mood TEXT,                       -- detected mood tag, if any
  auto_logged INTEGER DEFAULT 0,   -- 1 if the AI logged this automatically
  created_at INTEGER DEFAULT (strftime('%s','now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  sender TEXT NOT NULL,            -- 'user' | 'mithra'
  message TEXT NOT NULL,
  created_at INTEGER DEFAULT (strftime('%s','now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS focus_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  duration_seconds INTEGER NOT NULL,
  completed INTEGER DEFAULT 0,
  created_at INTEGER DEFAULT (strftime('%s','now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS emergency_contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  phone TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
`);
// Add trash metadata columns if they do not exist yet
const migrations = [
  "ALTER TABLE diary_entries ADD COLUMN status TEXT DEFAULT 'active';",
  "ALTER TABLE diary_entries ADD COLUMN deleted_at INTEGER;",
  "ALTER TABLE diary_entries ADD COLUMN trashed_by INTEGER;",
  "ALTER TABLE chat_messages ADD COLUMN status TEXT DEFAULT 'active';",
  "ALTER TABLE chat_messages ADD COLUMN deleted_at INTEGER;",
  "ALTER TABLE chat_messages ADD COLUMN trashed_by INTEGER;"
];

for (const sql of migrations) {
  try {
    db.exec(sql);
  } catch (_) {
    // Column already exists
  }
}

// 30-day Trash auto-cleanup retention policy
function cleanupExpiredTrash(retentionDays = 30) {
  try {
    const cutoff = Math.floor(Date.now() / 1000) - (retentionDays * 86400);
    db.prepare("DELETE FROM diary_entries WHERE status = 'trashed' AND deleted_at < ?").run(cutoff);
    db.prepare("DELETE FROM chat_messages WHERE status = 'trashed' AND deleted_at < ?").run(cutoff);
  } catch (err) {
    console.error("[TRASH CLEANUP ERROR]", err.message);
  }
}

cleanupExpiredTrash();

db.cleanupExpiredTrash = cleanupExpiredTrash;

module.exports = db;
