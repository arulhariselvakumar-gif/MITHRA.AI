const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const crypto = require("crypto");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");
const { normalizeLanguage } = require("../ai");

const router = express.Router();

function signToken(userId) {
  return jwt.sign({ userId }, process.env.JWT_SECRET, { expiresIn: "30d" });
}

function publicUser(u) {
  return { id: u.id, name: u.name, email: u.email, language: u.language };
}

// --- Sign up screen -> "Sign up" button ---
router.post("/signup", (req, res) => {
  const { name, email, password } = req.body;
  if (!name || !email || !password) {
    return res.status(400).json({ error: "Name, email and password are required" });
  }
  const existing = db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) return res.status(409).json({ error: "An account with this email already exists" });

  const hash = bcrypt.hashSync(password, 10);
  const info = db
    .prepare("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)")
    .run(name, email, hash);

  const user = db.prepare("SELECT * FROM users WHERE id = ?").get(info.lastInsertRowid);
  const token = signToken(user.id);
  res.json({ token, user: publicUser(user) });
});

// --- Login screen -> "Login" button ---
router.post("/login", (req, res) => {
  const { email, password } = req.body;
  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email);
  if (!user || !bcrypt.compareSync(password || "", user.password_hash)) {
    return res.status(401).json({ error: "Incorrect email or password" });
  }
  const token = signToken(user.id);
  res.json({ token, user: publicUser(user) });
});

// --- Login screen -> "forgot password?" link ---
router.post("/forgot-password", (req, res) => {
  const { email } = req.body;
  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email);
  // Always respond success (don't leak whether an email exists)
  if (!user) return res.json({ ok: true });

  const token = crypto.randomBytes(24).toString("hex");
  const expires = Date.now() + 1000 * 60 * 30; // 30 minutes
  db.prepare("UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?").run(
    token,
    expires,
    user.id
  );

  // In production this would be emailed. For the prototype we return it
  // directly so the "Reset password" screen can be demoed end-to-end.
  res.json({ ok: true, devResetToken: token });
});

// --- Reset password screen -> "Reset" button ---
router.post("/reset-password", (req, res) => {
  const { token, newPassword } = req.body;
  if (!token || !newPassword) return res.status(400).json({ error: "Missing token or new password" });

  const user = db.prepare("SELECT * FROM users WHERE reset_token = ?").get(token);
  if (!user || !user.reset_token_expires || user.reset_token_expires < Date.now()) {
    return res.status(400).json({ error: "Reset link is invalid or expired" });
  }

  const hash = bcrypt.hashSync(newPassword, 10);
  db.prepare(
    "UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?"
  ).run(hash, user.id);

  res.json({ ok: true });
});

// --- current user (used to keep the app logged in) ---
router.get("/me", requireAuth, (req, res) => {
  const user = db.prepare("SELECT * FROM users WHERE id = ?").get(req.userId);
  res.json({ user: publicUser(user) });
});

// --- Language selection screen -> choose language buttons ---
router.post("/language", requireAuth, (req, res) => {
  const { language } = req.body;
  if (!language) return res.status(400).json({ error: "language is required" });
  const norm = normalizeLanguage(language);
  db.prepare("UPDATE users SET language = ? WHERE id = ?").run(norm, req.userId);
  const updatedUser = db.prepare("SELECT * FROM users WHERE id = ?").get(req.userId);
  res.json({ ok: true, language: norm, user: publicUser(updatedUser) });
});

module.exports = router;
