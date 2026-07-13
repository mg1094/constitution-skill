const { JSDOM } = require("jsdom");
const fs = require("fs");
const path = require("path");

const htmlPath = path.resolve(__dirname, "..", "web", "index.html");
const html = fs.readFileSync(htmlPath, "utf-8");

function createWindow() {
  const dom = new JSDOM(html, {
    url: "http://localhost/",
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
  });
  const window = dom.window;
  // Mock clipboard
  let clipboardText = "";
  window.navigator.clipboard = {
    writeText: async (text) => { clipboardText = text; return Promise.resolve(); },
    readText: async () => clipboardText,
  };
  window.alert = (msg) => { throw new Error(`alert called: ${msg}`); };
  window.print = () => {};
  return { dom, window, document: window.document };
}

function assert(cond, msg) {
  if (!cond) throw new Error(`ASSERT FAIL: ${msg}`);
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

(async () => {
  console.log("Test 1: Start page renders start button");
  {
    const { document } = createWindow();
    const btn = document.querySelector(".btn-primary");
    assert(btn, "start button exists");
    assert(/开\s*始\s*辨\s*识|继\s*续\s*上\s*次\s*测\s*试/.test(btn.textContent), `start button text ok, got "${btn.textContent.trim()}"`);
  }

  console.log("Test 2: localStorage saves progress after selecting an answer");
  {
    const { window, document } = createWindow();
    const btn = document.querySelector(".btn-primary");
    btn.click();
    await wait(50);
    const option = document.querySelector(".option");
    assert(option, "option exists");
    option.click();
    await wait(400); // auto-next timeout 280ms
    const raw = window.localStorage.getItem("tcm_quiz_progress");
    assert(raw, "progress saved");
    const data = JSON.parse(raw);
    assert(data.currentIdx === 1, `currentIdx should be 1, got ${data.currentIdx}`);
    assert(data.answers[0] === 1, `first answer should be 1, got ${data.answers[0]}`);
  }

  console.log("Test 3: Resume quiz restores progress");
  {
    const { window, document } = createWindow();
    window.localStorage.setItem(
      "tcm_quiz_progress",
      JSON.stringify({ currentIdx: 2, answers: [1, 2, null].concat(new Array(42).fill(null)) })
    );
    window.renderStart();
    const resumeBtn = document.querySelector(".btn-primary");
    assert(/继\s*续\s*上\s*次\s*测\s*试/.test(resumeBtn.textContent), `resume button shown, got "${resumeBtn.textContent.trim()}"`);
    resumeBtn.click();
    await wait(50);
    const progressQ = document.querySelector(".progress-q strong");
    assert(progressQ && progressQ.textContent === "3", `should resume at question 3, got ${progressQ && progressQ.textContent}`);
  }

  console.log("Test 4: Restart clears progress");
  {
    const { window, document } = createWindow();
    window.localStorage.setItem(
      "tcm_quiz_progress",
      JSON.stringify({ currentIdx: 5, answers: new Array(45).fill(1) })
    );
    window.renderStart();
    const ghost = document.querySelector(".btn-ghost");
    assert(ghost, "restart button exists");
    ghost.click();
    await wait(50);
    assert(window.localStorage.getItem("tcm_quiz_progress") === null, "progress cleared");
    const progressQ = document.querySelector(".progress-q strong");
    assert(progressQ && progressQ.textContent === "1", `after restart should be at question 1, got ${progressQ && progressQ.textContent}`);
  }

  console.log("Test 5: Keyboard 1-5 selects answer");
  {
    const { window, document } = createWindow();
    document.querySelector(".btn-primary").click();
    await wait(50);
    const event = new window.KeyboardEvent("keydown", { key: "3", bubbles: true });
    document.dispatchEvent(event);
    await wait(400);
    const raw = window.localStorage.getItem("tcm_quiz_progress");
    assert(raw, "progress saved after keyboard");
    const data = JSON.parse(raw);
    assert(data.answers[0] === 3, `keyboard answer should be 3, got ${data.answers[0]}`);
  }

  console.log("Test 6: Share report copies markdown to clipboard");
  {
    const { window, document } = createWindow();
    document.querySelector(".btn-primary").click();
    await wait(100);
    for (let i = 0; i < 45; i++) {
      window.selectOption(3);
      await wait(350);
    }
    // Last question does not auto-next, trigger manually
    window.next();
    await wait(100);
    const shareBtn = document.querySelector(".btn-share");
    assert(shareBtn, `share button exists, got buttons: ${Array.from(document.querySelectorAll(".btn-full")).map((b) => b.textContent.trim()).join(", ")}`);
    shareBtn.click();
    await wait(50);
    const text = await window.navigator.clipboard.readText();
    assert(/中医体质检测报告/.test(text), "clipboard contains report title");
    assert(/主体质/.test(text), "clipboard contains main type");
    assert(/九维得分/.test(text), "clipboard contains scores");
  }

  console.log("\nAll tests passed ✅");
  process.exit(0);
})().catch((err) => {
  console.error("\nTest failed ❌");
  console.error(err);
  process.exit(1);
});
