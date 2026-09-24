// scripts/inject-env.js
// Netlify build script: injects MITHRA_API_URL environment variable into frontend/js/config.js

const fs = require("fs");
const path = require("path");

const apiUrl = (process.env.MITHRA_API_URL || process.env.API_URL || "").trim().replace(/\/+$/, "");
const targetFile = path.join(__dirname, "..", "frontend", "js", "config.js");

const fileContent = `// Auto-configured by Netlify build (scripts/inject-env.js)
// Environment variable: MITHRA_API_URL

window.MITHRA_CONFIG = window.MITHRA_CONFIG || {
  API_URL: ${JSON.stringify(apiUrl)}
};
`;

try {
  fs.writeFileSync(targetFile, fileContent, "utf8");
  console.log(`[Netlify Build] Successfully configured MITHRA_API_URL: "${apiUrl || '(empty - defaulting to local dev / runtime config)'}"`);
} catch (err) {
  console.error("[Netlify Build] Failed to write config.js:", err);
  process.exit(1);
}
