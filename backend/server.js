require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");

const authRoutes = require("./routes/auth");
const diaryRoutes = require("./routes/diary");
const chatRoutes = require("./routes/chat");
const miscRoutes = require("./routes/misc");

if (!process.env.JWT_SECRET) {
  console.warn("⚠️  JWT_SECRET not set in .env — using an insecure default for local dev only.");
  process.env.JWT_SECRET = "dev-only-insecure-secret";
}

const app = express();
app.use(cors());
app.use(express.json());
app.use("/uploads", express.static(path.join(__dirname, "uploads")));
app.use(express.static(path.join(__dirname, "..", "frontend")));

app.use("/api/auth", authRoutes);
app.use("/api/diary", diaryRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api", miscRoutes);

app.get("/api/health", (req, res) => res.json({ ok: true, name: "Mithra API" }));

const PORT = process.env.PORT || 4000;
app.listen(PORT, "0.0.0.0", () => console.log(`Mithra backend running on http://localhost:${PORT}`));
