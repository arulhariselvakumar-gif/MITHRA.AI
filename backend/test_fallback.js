// test_fallback.js — test graceful fallback when FastAPI is unreachable
const { getMithraReply } = require("./ai");

async function testFallback() {
  console.log("--- Testing Offline Fallback Behavior ---");
  process.env.FASTAPI_URL = "http://127.0.0.1:9999"; // Deliberately unreachable port

  try {
    const t0 = Date.now();
    const reply = await getMithraReply("I am feeling really sad today and need someone to talk to", []);
    const elapsed = Date.now() - t0;
    console.log(`Fallback response received in ${elapsed}ms:`);
    console.log(`Reply: "${reply}"`);

    if (reply && reply.length > 0) {
      console.log("[PASS] Offline fallback test SUCCESSFUL: Server handled failure gracefully without crashing.");
      process.exit(0);
    } else {
      console.error("[FAIL] Empty fallback reply received.");
      process.exit(1);
    }
  } catch (err) {
    console.error("[FAIL] getMithraReply threw an uncaught error:", err);
    process.exit(1);
  }
}

testFallback();
