function normalizeCrisisText(text) {
  if (!text) return "";
  let s = text.toLowerCase();
  s = s.replace(/(.)\1{2,}/g, "$1$1");
  s = s.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?"'’]/g, " ");
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

const tanglishPatterns = [
  /\b(na|naa|naan|nan)\s+(saava|saaga|sethu|seththu|sethtu)\s+(poren|poga\s+poren|poganum|ponum)\b/,
  /\b(saava|saaga|sethu|seththu)\s+(poren|poga\s+poren|poganum)\b/,
  /\b(enakku|enaku)\s+(saaganum|saavanum|sethu\s+poganum|seththu\s+poganum)\b/,
  /\b(enakku|enaku|manasula)?\s*(saava|saaga)\s+(thonudhu|thonuthu|thondhu)\b/,
  /\b(life|vaazhkai|vaazhka)\s*(ah|a)?\s*(mudichikalam|mudichukalam|mudikalam|mudikalaam|mudichikalaam|mudikkanum|end\s+pannikalam)\b/,
  /\b(na|naa|naan)\s+(seththudren|sethudren|seththuruven|sethuruven|seththuduren)\b/,
  /\btharkolai\b/,
  /\buyira?\s+(maaikka|maaikkanum|vida|vidanum)\b/
];

const tamilPhrases = [
  "சாக போறேன்", "சாகப் போறேன்", "சாகபோறேன்", "சாக வேண்டும்", "சாகவேண்டும்",
  "சாக தோன்றுகிறது", "சாக தோணுது", "சாகத் தோணுது", "சாகத்தோணுது",
  "செத்துப் போகப் போறேன்", "செத்து போக போறேன்", "செத்துப்போகப்போறேன்", "செத்து போகனும்", "செத்துப்போகனும்",
  "வாழ்க்கையை முடித்துக் கொள்ள", "என் வாழ்க்கையை முடிச்சிக்கிறேன்", "வாழ்க்கைய முடிச்சிக்கலாம்", "வாழ்க்கையை முடிச்சிக்கலாம்",
  "தற்கொலை", "உயிரை மாய்த்து", "உயிர் விட"
];

function isCrisis(text) {
  const norm = normalizeCrisisText(text);
  if (tanglishPatterns.some(r => r.test(norm))) return true;
  if (tamilPhrases.some(p => norm.includes(p) || text.includes(p))) return true;
  return false;
}

const testPositive = [
  "naa saava poren",
  "naan saava poren",
  "na saava poren",
  "naa saaga poren",
  "naan saaga poren",
  "naa seththu poga poren",
  "naan seththu poga poren",
  "naan seththu poganum",
  "naa seththu poganum",
  "enaku saaganum",
  "enakku saaganum",
  "enakku saava thonudhu",
  "enaku saava thonuthu",
  "saaga thonudhu",
  "saava thonudhu",
  "life ah mudichikalam",
  "life mudichikalam",
  "naan seththudren",
  "naan seththuruven",
  "சாக போறேன்",
  "செத்துப் போகப் போறேன்",
  "வாழ்க்கையை முடித்துக் கொள்ள"
];

const testNegative = [
  "naa romba tired ah irukken",
  "exam stress ah irukku",
  "today mood sari illa",
  "romba kashtama irukku",
  "movie la oru death scene pathom",
  "news la death pathi pesinanga"
];

console.log("=== POSITIVE CRISIS TESTS ===");
let allPosPassed = true;
for (const p of testPositive) {
  const res = isCrisis(p);
  console.log(`${res ? "PASS" : "FAIL"}: "${p}"`);
  if (!res) allPosPassed = false;
}

console.log("\n=== NEGATIVE NON-CRISIS TESTS ===");
let allNegPassed = true;
for (const p of testNegative) {
  const res = isCrisis(p);
  console.log(`${!res ? "PASS" : "FAIL (False Positive)"}: "${p}"`);
  if (res) allNegPassed = false;
}

if (allPosPassed && allNegPassed) {
  console.log("\n>>> ALL REGEX PATTERNS PASSED 100% <<<");
  process.exit(0);
} else {
  console.error("\n>>> SOME TESTS FAILED <<<");
  process.exit(1);
}
