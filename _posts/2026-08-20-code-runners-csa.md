---
layout: post
courses: { csa: {week: 1} }
codemirror: true
title: Code Runners — CSA Arcade Edition
description: The Open Coding Society "Code Runners - Raw MD" lesson, rebuilt as an interactive arcade. Four levels, a boss fight, live hints, a quick-check quiz, and an XP bar that remembers where you left off.
permalink: /code/csa/
comments: true
type: ccc
---

<style>
/* ===== Arcade theme tokens (light default, dark override) ===== */
:root {
  --arc-bg:        #f6f7fb;
  --arc-panel:     #ffffff;
  --arc-ink:       #17181d;
  --arc-muted:     #5b6070;
  --arc-line:      #e3e6ef;
  --arc-accent:    #5b4bff;
  --arc-accent-2:  #00b3a4;
  --arc-warn:      #ff8a3d;
  --arc-good:      #1aa06d;
  --arc-bad:       #d6455d;
  --arc-shadow:    0 6px 18px rgba(20, 22, 40, .08);
}
@media (prefers-color-scheme: dark) {
  :root {
    --arc-bg:      #14151b;
    --arc-panel:   #1c1e26;
    --arc-ink:     #eef0f6;
    --arc-muted:   #a3a8b8;
    --arc-line:    #2c2f3a;
    --arc-accent:  #8f83ff;
    --arc-accent-2:#37d6c6;
    --arc-shadow:  0 6px 18px rgba(0, 0, 0, .45);
  }
}

.arc-hero {
  border-radius: 16px;
  padding: 28px 26px;
  color: #fff;
  background: linear-gradient(135deg, #5b4bff 0%, #9d4bff 45%, #00b3a4 100%);
  box-shadow: var(--arc-shadow);
  margin: 8px 0 26px;
}
.arc-hero h1 { margin: 0 0 6px; font-size: 1.9rem; line-height: 1.15; color: #fff; }
.arc-hero p  { margin: 0; opacity: .95; max-width: 62ch; }
.arc-chips { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 8px; }
.arc-chip {
  font-size: .78rem; font-weight: 600; letter-spacing: .02em;
  padding: 5px 11px; border-radius: 999px;
  background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.3);
}

.arc-card {
  background: var(--arc-panel);
  border: 1px solid var(--arc-line);
  border-radius: 14px;
  padding: 18px 20px;
  margin: 22px 0;
  box-shadow: var(--arc-shadow);
  color: var(--arc-ink);
}
.arc-card h3 { margin-top: 0; }

.arc-level {
  display: inline-flex; align-items: center; gap: 9px;
  font-weight: 700; font-size: .8rem; letter-spacing: .09em; text-transform: uppercase;
  color: var(--arc-accent);
  border: 1px solid var(--arc-accent);
  border-radius: 999px; padding: 4px 12px;
  margin-bottom: 10px;
}
.arc-level.boss { color: var(--arc-warn); border-color: var(--arc-warn); }

/* XP bar */
.arc-xpwrap { margin: 10px 0 4px; }
.arc-xptrack {
  height: 16px; border-radius: 999px; overflow: hidden;
  background: var(--arc-line); border: 1px solid var(--arc-line);
}
.arc-xpfill {
  height: 100%; width: 0%;
  background: linear-gradient(90deg, var(--arc-accent), var(--arc-accent-2));
  transition: width .45s cubic-bezier(.2,.8,.2,1);
}
.arc-xplabel { font-size: .85rem; color: var(--arc-muted); margin-top: 7px; }

.arc-quests { list-style: none; padding: 0; margin: 14px 0 0; }
.arc-quests li {
  display: flex; align-items: center; gap: 11px;
  padding: 9px 12px; margin-bottom: 7px;
  border: 1px solid var(--arc-line); border-radius: 10px;
  cursor: pointer; user-select: none;
  transition: transform .12s ease, border-color .12s ease;
  color: var(--arc-ink);
}
.arc-quests li:hover { transform: translateX(3px); border-color: var(--arc-accent); }
.arc-quests li.done { border-color: var(--arc-good); }
.arc-quests li.done .arc-qtext { text-decoration: line-through; color: var(--arc-muted); }
.arc-box { font-size: 1.05rem; width: 1.3em; text-align: center; }

/* Hint / spoiler */
details.arc-hint {
  border: 1px dashed var(--arc-accent);
  border-radius: 10px; padding: 10px 14px; margin: 12px 0;
  background: color-mix(in srgb, var(--arc-accent) 7%, transparent);
}
details.arc-hint > summary { cursor: pointer; font-weight: 600; color: var(--arc-accent); }
details.arc-hint[open] > summary { margin-bottom: 8px; }

/* Quiz */
.arc-q { margin-bottom: 20px; }
.arc-q p.arc-prompt { font-weight: 600; margin-bottom: 9px; }
.arc-opt {
  display: block; width: 100%; text-align: left;
  padding: 10px 13px; margin-bottom: 7px;
  border: 1px solid var(--arc-line); border-radius: 9px;
  background: transparent; color: var(--arc-ink);
  font: inherit; cursor: pointer;
  transition: border-color .12s ease, background .12s ease;
}
.arc-opt:hover { border-color: var(--arc-accent); }
.arc-opt.right { border-color: var(--arc-good); background: color-mix(in srgb, var(--arc-good) 14%, transparent); }
.arc-opt.wrong { border-color: var(--arc-bad);  background: color-mix(in srgb, var(--arc-bad) 14%, transparent); }
.arc-feedback { font-size: .9rem; margin-top: 6px; min-height: 1.2em; color: var(--arc-muted); }

.arc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }
.arc-tile {
  border: 1px solid var(--arc-line); border-radius: 12px; padding: 14px;
  background: var(--arc-panel); color: var(--arc-ink);
}
.arc-tile .arc-emoji { font-size: 1.7rem; display: block; margin-bottom: 6px; }
.arc-tile strong { display: block; margin-bottom: 4px; }
.arc-tile span.arc-sub { font-size: .87rem; color: var(--arc-muted); }

.arc-badge {
  text-align: center; padding: 26px;
  border-radius: 16px; border: 2px dashed var(--arc-line);
  color: var(--arc-muted);
}
.arc-badge.unlocked {
  border-style: solid; border-color: var(--arc-good);
  background: color-mix(in srgb, var(--arc-good) 12%, transparent);
  color: var(--arc-ink);
}
.arc-badge .arc-seal { font-size: 3rem; display: block; margin-bottom: 8px; }

table.arc-table { width: 100%; border-collapse: collapse; font-size: .93rem; }
table.arc-table th, table.arc-table td { border: 1px solid var(--arc-line); padding: 8px 10px; text-align: left; }
table.arc-table th { background: color-mix(in srgb, var(--arc-accent) 10%, transparent); }
</style>

<div class="arc-hero">
  <h1>🕹️ Code Runners — CSA Arcade Edition</h1>
  <p>Every code block on this page is <em>alive</em>. Edit it, hit ▶, and the output appears right there — no IDE, no setup, no <code>javac</code> in a terminal. Clear four levels, survive the boss, and pass the quick check.</p>
  <div class="arc-chips">
    <span class="arc-chip">☕ Java</span>
    <span class="arc-chip">🐍 Python</span>
    <span class="arc-chip">🟨 JavaScript</span>
    <span class="arc-chip">📝 AP CSP Pseudocode</span>
    <span class="arc-chip">⏱️ ~25 min</span>
  </div>
</div>

<div class="arc-card">
  <h3 style="margin-bottom:4px;">🎯 Your Run</h3>
  <div class="arc-xpwrap">
    <div class="arc-xptrack"><div class="arc-xpfill" id="arcXpFill"></div></div>
    <div class="arc-xplabel" id="arcXpLabel">0 / 6 quests cleared — press start.</div>
  </div>
  <ul class="arc-quests" id="arcQuests">
    <li data-quest="q1"><span class="arc-box">⬜</span><span class="arc-qtext">Level 1 — Run the Python loop and change the count</span></li>
    <li data-quest="q2"><span class="arc-box">⬜</span><span class="arc-qtext">Level 2 — Fix the broken Java class</span></li>
    <li data-quest="q3"><span class="arc-box">⬜</span><span class="arc-qtext">Level 3 — Make the JavaScript loop count backwards</span></li>
    <li data-quest="q4"><span class="arc-box">⬜</span><span class="arc-qtext">Level 4 — Run the AP CSP pseudocode calculator</span></li>
    <li data-quest="q5"><span class="arc-box">⬜</span><span class="arc-qtext">Boss — Beat the Java FizzBuzz gauntlet</span></li>
    <li data-quest="q6"><span class="arc-box">⬜</span><span class="arc-qtext">Quick check — 3 / 3 on the quiz</span></li>
  </ul>
  <p class="arc-xplabel">Click a quest to mark it cleared. Your progress is saved in this browser.</p>
</div>

## 🧭 How the arcade works

<div class="arc-grid">
  <div class="arc-tile">
    <span class="arc-emoji">▶</span>
    <strong>Run</strong>
    <span class="arc-sub">Executes the editor contents and prints to the output panel below it.</span>
  </div>
  <div class="arc-tile">
    <span class="arc-emoji">💾</span>
    <strong>Save</strong>
    <span class="arc-sub">Stores your edit in browser storage, so a refresh doesn't wipe your work.</span>
  </div>
  <div class="arc-tile">
    <span class="arc-emoji">🗑</span>
    <strong>Clear</strong>
    <span class="arc-sub">Throws away your saved version and restores the original starter code.</span>
  </div>
  <div class="arc-tile">
    <span class="arc-emoji">⎘</span>
    <strong>Copy</strong>
    <span class="arc-sub">Grabs the code (or the output) to paste into your own notebook.</span>
  </div>
</div>

---

<div class="arc-level">🎮 Level 1 · Warm-up · Python</div>

## Loops that talk back

The classic starter. Run it once so you know the button works — then make it count to **10** instead of 5, and print each number with the word `step` in front of it.

{% capture challenge1 %}
<strong>🎯 Goal:</strong> count to 10 and print <code>step 0</code>, <code>step 1</code>, … <br>
<strong>🏅 Bonus:</strong> only print the <em>even</em> numbers.
{% endcapture %}

{% capture python_example %}
print("Hello, World!")
for i in range(5):
    print(i)
{% endcapture %}
{% include runners/code.html runner_id="python-main" language="python" code=python_example challenge=challenge1 challenge_number="1" %}

<details class="arc-hint">
<summary>💡 Stuck? Open a hint</summary>
<div markdown="1">
`range(5)` produces `0,1,2,3,4` — the stop value is **not** included. To print a label next to the number, use an f-string: `print(f"step {i}")`. For the bonus, `range(0, 10, 2)` steps by two.
</div>
</details>

---

<div class="arc-level">🎮 Level 2 · Debug · Java</div>

## The class that won't compile

This is the CSA level. The code below looks fine at a glance, but the compiler disagrees — there is exactly **one** character missing. Find it, run it, then extend the loop so it prints a countdown instead.

{% capture challenge2 %}
<strong>🐛 Bug:</strong> one statement is missing its terminator.<br>
<strong>🎯 Goal:</strong> compile it clean, then flip the loop into a countdown from 5 down to 1.<br>
<strong>🏅 Bonus:</strong> print <code>Liftoff!</code> after the loop finishes.
{% endcapture %}

{% capture java_example %}
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!")
        for (int i = 0; i < 5; i++) {
            System.out.println(i);
        }
    }
}
{% endcapture %}
{% include runners/code.html runner_id="java-main" language="java" code=java_example challenge=challenge2 challenge_number="2" %}

<details class="arc-hint">
<summary>💡 Hint 1 — where to look</summary>
<div markdown="1">
Java statements end in `;`. Read the error message the runner gives you: it names a **line number**. That line, or the one just above it, is where the compiler gave up.
</div>
</details>

<details class="arc-hint">
<summary>🔓 Hint 2 — the countdown</summary>
<div markdown="1">
A countdown flips all three parts of the `for` header:

```java
for (int i = 5; i > 0; i--) {
    System.out.println(i);
}
```
Start at 5, keep going while `i` is above 0, and step **down** with `i--`.
</div>
</details>

---

<div class="arc-level">🎮 Level 3 · Remix · JavaScript</div>

## Same loop, different language

Java and JavaScript share a family resemblance — the `for` header is nearly identical. Run this, then rewrite it to count **backwards** from 5. Notice how little actually changed between Level 2 and Level 3.

{% capture challenge3 %}
<strong>🎯 Goal:</strong> count down from 5 to 1 in the console output.<br>
<strong>🧠 Think:</strong> what is different between this and the Java version — and what is identical?
{% endcapture %}

{% capture js_example %}
console.log("Hello, World!");
for (let i = 0; i < 5; i++) {
    console.log(i);
}
{% endcapture %}
{% include runners/code.html runner_id="js-main" language="javascript" code=js_example challenge=challenge3 challenge_number="3" %}

<div class="arc-card" markdown="1">
### 🔍 Spot the difference

| Feature | Java | JavaScript |
|---|---|---|
| Declare the counter | `int i = 0` | `let i = 0` |
| Print | `System.out.println(x)` | `console.log(x)` |
| Loop header | `for (…; …; …)` | `for (…; …; …)` |
| Needs a class wrapper | ✅ yes | ❌ no |
| Type on the variable | ✅ required | ❌ inferred |

Same loop skeleton, different ceremony. Java asks you to declare a type and wrap everything in a class; JavaScript does not.

</div>

---

<div class="arc-level">🎮 Level 4 · AP CSP · Pseudocode</div>

## The exam's own language

AP Computer Science Principles has a standardized pseudocode that appears on the exam. The runner below actually **executes** it — arrows, `DISPLAY`, and all. Run the calculator and feed it real values when it prompts you.

{% capture challenge4 %}
<strong>🎯 Goal:</strong> run it and try <code>12 / 4</code>, then try <code>12 / 0</code> and watch the guard clause catch you.<br>
<strong>🏅 Bonus:</strong> add a <code>%</code> (remainder) branch of your own.
{% endcapture %}

{% capture csp_example %}
num1 ← INPUT("Enter first number:")
op ← INPUT("Enter operator (+, -, *, /):")
num2 ← INPUT("Enter second number:")
result ← 0
IF (op = "+")
{
    result ← num1 + num2
}
ELSE
{
    IF (op = "-")
    {
        result ← num1 - num2
    }
    ELSE
    {
        IF (op = "*")
        {
            result ← num1 * num2
        }
        ELSE
        {
            IF (op = "/")
            {
                IF (num2 ≠ 0)
                {
                    result ← num1 / num2
                }
                ELSE
                {
                    DISPLAY("Error: Division by zero")
                    result ← "undefined"
                }
            }
            ELSE
            {
                DISPLAY("Invalid operator")
                result ← "undefined"
            }
        }
    }
}

DISPLAY("Result: "+ result)
{% endcapture %}
{% include runners/code.html runner_id="csp-main" language="pseudocode" code=csp_example challenge=challenge4 challenge_number="4" %}

<details class="arc-hint">
<summary>💡 Pseudocode cheat sheet</summary>
<div markdown="1">

| Symbol | Means | Java equivalent |
|---|---|---|
| `←` | assignment | `=` |
| `=` | equality test | `==` |
| `≠` | not equal | `!=` |
| `DISPLAY(x)` | print | `System.out.println(x)` |
| `INPUT(...)` | read a value | `Scanner.nextLine()` |

The nested `IF / ELSE` ladder is doing the job of a Java `switch`. That's why it's five levels deep — pseudocode has no `switch`.
</div>
</details>

---

<div class="arc-level boss">👾 Boss Fight · Java</div>

## FizzBuzz Gauntlet

The interview classic, and a genuinely good `%` and `if/else if` workout. The skeleton is there; the logic is missing.

**Rules:** for every number from 1 to 20 —
- divisible by **3 and 5** → print `FizzBuzz`
- divisible by **3** → print `Fizz`
- divisible by **5** → print `Buzz`
- otherwise → print the number

{% capture challenge5 %}
<strong>👾 Boss HP:</strong> 20 lines of correct output.<br>
<strong>⚠️ Trap:</strong> order matters. Check the <em>most specific</em> condition first, or FizzBuzz never fires.
{% endcapture %}

{% capture boss_example %}
public class Main {
    public static void main(String[] args) {
        for (int i = 1; i <= 20; i++) {
            // TODO: replace this line with your if / else if / else ladder
            System.out.println(i);
        }
    }
}
{% endcapture %}
{% include runners/code.html runner_id="java-boss" language="java" code=boss_example challenge=challenge5 challenge_number="5" %}

<details class="arc-hint">
<summary>💡 Hint — the modulo operator</summary>
<div markdown="1">
`i % 3 == 0` is true when `i` divides evenly by 3. Combine two of those with `&&` for the FizzBuzz case.
</div>
</details>

<details class="arc-hint">
<summary>☠️ Full solution — only after you've tried</summary>
<div markdown="1">
```java
if (i % 3 == 0 && i % 5 == 0) {
    System.out.println("FizzBuzz");
} else if (i % 3 == 0) {
    System.out.println("Fizz");
} else if (i % 5 == 0) {
    System.out.println("Buzz");
} else {
    System.out.println(i);
}
```
Putting the `&&` case last would mean 15 prints `Fizz` and stops — the ladder short-circuits on the first true branch.
</div>
</details>

---

## 🧪 Quick Check

Three questions. Instant feedback, no submit button, unlimited retries.

<div class="arc-card">
  <div class="arc-q" data-q="qz1">
    <p class="arc-prompt">1. In Java, what does <code>i % 5 == 0</code> test?</p>
    <button class="arc-opt" data-correct="false">Whether <code>i</code> equals 5</button>
    <button class="arc-opt" data-correct="true">Whether <code>i</code> divides evenly by 5</button>
    <button class="arc-opt" data-correct="false">Whether <code>i</code> is less than 5</button>
    <div class="arc-feedback"></div>
  </div>

  <div class="arc-q" data-q="qz2">
    <p class="arc-prompt">2. Python's <code>range(5)</code> produces which values?</p>
    <button class="arc-opt" data-correct="false">1, 2, 3, 4, 5</button>
    <button class="arc-opt" data-correct="true">0, 1, 2, 3, 4</button>
    <button class="arc-opt" data-correct="false">0, 1, 2, 3, 4, 5</button>
    <div class="arc-feedback"></div>
  </div>

  <div class="arc-q" data-q="qz3">
    <p class="arc-prompt">3. In AP CSP pseudocode, <code>←</code> means:</p>
    <button class="arc-opt" data-correct="false">Test two values for equality</button>
    <button class="arc-opt" data-correct="false">Return a value from a procedure</button>
    <button class="arc-opt" data-correct="true">Assign a value to a variable</button>
    <div class="arc-feedback"></div>
  </div>

  <div class="arc-xplabel" id="arcQuizScore">Score: 0 / 3</div>
</div>

---

## 🛠️ Build your own runner

Every runner on this page is one Liquid include. Capture the starter code into a variable, then hand it to the component:

{% raw %}
```liquid
{% capture my_code %}
public class Main {
    public static void main(String[] args) {
        System.out.println("Your code here");
    }
}
{% endcapture %}

{% include runners/code.html
   runner_id="unique-id-here"
   language="java"
   code=my_code
   challenge=my_challenge
   challenge_number="1" %}
```
{% endraw %}

<div class="arc-card" markdown="1">
### Parameter reference

| Parameter | Required | What it does |
|---|---|---|
| `runner_id` | ✅ | Unique per page. Also becomes the browser-storage key, so duplicates will overwrite each other. |
| `language` | ✅ | `python`, `java`, `javascript`, or `pseudocode`. |
| `code` | ✅ | A captured variable holding the starter code. |
| `challenge` | — | A captured block of HTML shown in the challenge box above the editor. |
| `challenge_number` | — | Numbers the challenge box. |
| `source` | — | Captured text tucked into a collapsible "View IPYNB Source" section. |

**Gotcha:** `code=my_code` takes the variable name with **no quotes**. `code="my_code"` passes the literal string.
</div>

---

<div class="arc-badge" id="arcBadge">
  <span class="arc-seal">🔒</span>
  <strong>Run Complete badge — locked</strong>
  <div class="arc-xplabel">Clear all six quests above to unlock.</div>
</div>

<script>
(function () {
  var STORE = 'csa_arcade_v1';
  var TOTAL = 6;

  function load() {
    try { return JSON.parse(localStorage.getItem(STORE)) || {}; }
    catch (e) { return {}; }
  }
  function save(state) {
    try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {}
  }

  var state = load();
  var list  = document.getElementById('arcQuests');
  var fill  = document.getElementById('arcXpFill');
  var label = document.getElementById('arcXpLabel');
  var badge = document.getElementById('arcBadge');

  function render() {
    var done = 0;
    var items = list.querySelectorAll('li');
    for (var i = 0; i < items.length; i++) {
      var li  = items[i];
      var key = li.getAttribute('data-quest');
      var box = li.querySelector('.arc-box');
      if (state[key]) {
        li.classList.add('done');
        box.textContent = '✅';
        done++;
      } else {
        li.classList.remove('done');
        box.textContent = '⬜';
      }
    }

    var pct = Math.round((done / TOTAL) * 100);
    fill.style.width = pct + '%';

    var msg;
    if (done === 0)          { msg = '0 / ' + TOTAL + ' quests cleared — press start.'; }
    else if (done < 3)       { msg = done + ' / ' + TOTAL + ' cleared — warming up.'; }
    else if (done < TOTAL)   { msg = done + ' / ' + TOTAL + ' cleared — the boss is watching.'; }
    else                     { msg = TOTAL + ' / ' + TOTAL + ' cleared — full run. 🏆'; }
    label.textContent = msg;

    if (done === TOTAL) {
      badge.classList.add('unlocked');
      badge.querySelector('.arc-seal').textContent = '🏆';
      badge.querySelector('strong').textContent = 'Run Complete — badge unlocked!';
      badge.querySelector('.arc-xplabel').textContent =
        'Four languages, one boss, and a clean quiz. Screenshot this for your checkpoint write-up.';
    } else {
      badge.classList.remove('unlocked');
      badge.querySelector('.arc-seal').textContent = '🔒';
      badge.querySelector('strong').textContent = 'Run Complete badge — locked';
      badge.querySelector('.arc-xplabel').textContent =
        (TOTAL - done) + ' quest' + (TOTAL - done === 1 ? '' : 's') + ' to go.';
    }
  }

  list.addEventListener('click', function (ev) {
    var li = ev.target.closest('li[data-quest]');
    if (!li) return;
    var key = li.getAttribute('data-quest');
    state[key] = !state[key];
    save(state);
    render();
  });

  /* ---- quiz ---- */
  var answered = {};
  var scoreEl  = document.getElementById('arcQuizScore');

  function scoreQuiz() {
    var n = 0;
    for (var k in answered) { if (answered[k]) n++; }
    scoreEl.textContent = 'Score: ' + n + ' / 3';
    if (n === 3 && !state.q6) {
      state.q6 = true;
      save(state);
      render();
    }
    return n;
  }

  var questions = document.querySelectorAll('.arc-q');
  for (var qi = 0; qi < questions.length; qi++) {
    (function (q) {
      var fb = q.querySelector('.arc-feedback');
      q.addEventListener('click', function (ev) {
        var btn = ev.target.closest('.arc-opt');
        if (!btn) return;
        var opts = q.querySelectorAll('.arc-opt');
        for (var i = 0; i < opts.length; i++) {
          opts[i].classList.remove('right', 'wrong');
        }
        var correct = btn.getAttribute('data-correct') === 'true';
        btn.classList.add(correct ? 'right' : 'wrong');
        fb.textContent = correct ? '✅ Correct.' : '❌ Not quite — try another.';
        answered[q.getAttribute('data-q')] = correct;
        scoreQuiz();
      });
    })(questions[qi]);
  }

  render();
  scoreQuiz();
})();
</script>
