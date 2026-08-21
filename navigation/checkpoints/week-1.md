---
layout: post
title: Week 1 Checkpoint, Java Toolchain Setup & Lesson Remix
description: Getting every Java tool the portfolio README asks for onto WSL/Ubuntu, the four things that broke along the way, and rebuilding the Code Runners lesson as an interactive arcade.
permalink: /checkpoints/week-1/
comments: true
---

## Part 1 — Java Toolchain Setup

### Where I started

Working off the portfolio `README.md`, the Java requirements are: a **JDK**, **Jupyter**, **Coursier** (`cs`), **JBang**, and two kernels registered in `jupyter kernelspec list` — `java` and `jbang-ijava`.

Environment: Windows 11 → WSL2 → Ubuntu 24.04, using the portfolio's own `venv/`.

I ran every version check *before* installing anything, so I'd know what actually needed fixing:

| Tool | Status | Problem |
|---|---|---|
| JDK 21 (`java`, `javac`) | ✅ Pass | — |
| JBang 0.97.0 | ✅ Pass | Installed, zero apps registered |
| `JAVA_HOME` | ❌ Fail | Unset entirely |
| Coursier | ❌ Fail | `cs` resolved to something that isn't Coursier |
| `jupyter kernelspec` | ❌ Fail | Subcommand didn't exist |
| `jbang-ijava` kernel | ❌ Fail | Not installed |

Four things to chase, which became five errors — two broke twice. None of the README's copy-paste commands fixed any of them on their own.

---

### 🐛 Error 1 — `cs` was Csound, not Coursier

`cs --version` printed `cs: invalid option: -`, which isn't a Coursier message at all. So I asked the shell what `cs` was:

```shell
$ dpkg -S $(readlink -f $(which cs))
csound: /usr/bin/cs
```

**Diagnosis.** `cs` belongs to **Csound**, pulled in as somebody's dependency. Coursier was never installed — the name was just taken. `sudo apt install coursier` wouldn't have fixed it either: `/usr/bin/cs` would keep winning on PATH order.

**Solution.** Install the real launcher into my user dir and shadow Csound via PATH precedence, rather than deleting Csound (other things need it):

```shell
$ mkdir -p ~/.local/share/coursier/bin
$ curl -fL "https://github.com/coursier/launchers/raw/master/cs-x86_64-pc-linux.gz" \
    | gzip -d > ~/.local/share/coursier/bin/cs
$ chmod +x ~/.local/share/coursier/bin/cs
$ ln -sf ~/.local/share/coursier/bin/cs ~/.local/bin/cs && hash -r
```

This works because `~/.local/bin` is already first in PATH on Ubuntu, ahead of `/usr/bin`.

**Then a smaller trip-up.** `cs --version` still printed a usage screen — modern Coursier moved it behind a subcommand. It's `cs version`, not `cs --version` (`2.1.25-M26`). Small, but I'd have kept thinking the install was broken.

---

### 🐛 Error 2 — `jupyter kernelspec` did not exist

```shell
$ jupyter kernelspec list
Jupyter command `jupyter-kernelspec` not found.
```

**Diagnosis.** I was hitting `/usr/bin/jupyter` — Ubuntu's ancient apt-packaged Jupyter (`jupyter_client 7.4.9`, no `jupyter_server`, no Lab). That package has no `jupyter-kernelspec` entry point. My instinct was `pip install jupyter_client`, but 24.04 blocks that with `externally-managed-environment` (PEP 668) — and it was the wrong fix anyway.

**Solution.** The repo already ships a proper `venv/`. I just wasn't in it:

```shell
$ source venv/bin/activate
(venv) $ jupyter kernelspec list
  java       .../portfolio/venv/share/jupyter/kernels/java
  python3    .../portfolio/venv/share/jupyter/kernels/python3
  jslab, tslab ...
```

**Lesson:** every Jupyter and kernel command here has to run with the venv active — outside it you're talking to a different Jupyter that knows about none of this. The `java` (IJava 1.3.0) kernel had been there all along; I just couldn't see it. `jbang-ijava` was genuinely missing.

---

### 🐛 Error 3 — `jbang app install ijava` doesn't exist anymore

```shell
(venv) $ jbang app install ijava
[jbang] [ERROR] Script or alias could not be found or read: 'ijava'
```

**Diagnosis.** `ijava` used to be an alias in the `jbangdev` catalog; `jbang alias list jbangdev` shows it's gone. The README is stale — JBang's Jupyter support moved to a dedicated installer in the **`jupyter-java`** catalog: `install-kernel@jupyter-java`.

**Then it stalled on a trust prompt.** JBang won't auto-run scripts from untrusted URLs, and in a non-interactive shell the prompt times out and dies with a confusing NPE (`Cannot invoke "java.lang.Throwable.printStackTrace()"`).

**Solution.** Trust the org once, then install:

```shell
(venv) $ jbang trust add https://github.com/jupyter-java/
(venv) $ jbang install-kernel@jupyter-java \
    --kernel-dir=jbang-ijava --name="JBang IJava" IJAVA
JBang IJava kernel installed to ~/.local/share/jupyter/kernels/jbang-ijava/kernel.json
```

`--kernel-dir=jbang-ijava` is what makes it appear under the exact name the README's example output uses.

---

### 🐛 Error 4 — the installed kernel died instantly

`kernelspec list` now showed `jbang-ijava`, so I assumed I was done. Running a real Java cell against it:

```shell
RuntimeError: Kernel died before replying to kernel_info
```

**Diagnosis.** That message tells you nothing, so I pulled the `argv` out of the generated `kernel.json` and ran it by hand:

```shell
$ /snap/bin/jbang --java 11+ --ea -R-ea -R--add-opens \
    -Rjava.base/jdk.internal.misc=ALL-UNNAMED -R--illegal-access=permit \
    com.github.waikato.thirdparty:ijava:1.3.0 conn.json
Unknown options: '-R-ea', '-R--add-opens', ...
```

There it is — the installer wrote `kernel.json` using the modern `-R` shorthand for JVM options, but my snap-installed **JBang 0.97.0 doesn't understand `-R`**; it wants `--java-options=`. Jupyter never surfaced this because kernel stderr is swallowed on startup failure.

**Two more problems in the same file:** `--illegal-access=permit` was *removed* from the JVM in Java 17, so it's a hard failure on 21. And my first fix pinned `--java 17`, which sent JBang off to download a JDK that snap confinement blocks (`Unable to download or install JDK version 17` — the error helpfully names the fix).

**Solution.** Hand-edit `~/.local/share/jupyter/kernels/jbang-ijava/kernel.json` — swap `-R` for `--java-options=`, drop the dead flag, pin to the JDK 21 I already have:

```json
{
  "argv" : [
    "/snap/bin/jbang",
    "--java", "21",
    "--java-options=-ea",
    "--java-options=--add-opens=java.base/jdk.internal.misc=ALL-UNNAMED",
    "com.github.waikato.thirdparty:ijava:1.3.0",
    "{connection_file}"
  ],
  "display_name" : "JBang IJava",
  "language" : "java",
  "interrupt_mode" : "message",
  "env" : { "IJAVA_COMPILER_OPTS" : "" }
}
```

---

### 🐛 Error 5 (bonus) — the README's Coursier IJava channel is a dead link

```shell
(venv) $ cs install --channel=https://github.com/SpencerPark/IJava/releases/latest/download/channel.json ijava
coursier.cache.ArtifactError$NotFound: not found: .../channel.json
```

**Diagnosis.** SpencerPark/IJava's latest release no longer publishes a `channel.json`, so the URL 404s. Stale README link, not a broken Coursier — `cs version` proves Coursier is fine.

**Solution.** Didn't need it. The README offers Coursier and JBang as *alternatives*, the `java` kernel was already registered in the venv, and JBang now covers `jbang-ijava`. Coursier stays installed and verified because the README lists it as required.

---

### Persisting the environment

`JAVA_HOME` was still empty and the Coursier PATH fix would vanish on the next shell, so both went into `~/.bashrc`:

```bash
# --- CSA / Open Coding Society Java toolchain ---
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH="$HOME/.local/share/coursier/bin:$PATH"
```

---

### ✅ Final checks — all passing

```shell
(venv) $ java -version        # openjdk 21.0.11
(venv) $ javac -version       # javac 21.0.11
(venv) $ echo $JAVA_HOME      # /usr/lib/jvm/java-21-openjdk-amd64
(venv) $ cs version           # 2.1.25-M26  (from ~/.local/bin/cs, shadowing /usr/bin/cs)
(venv) $ jbang --version      # 0.97.0
(venv) $ jupyter --version    # jupyter_core 5.9.1, jupyterlab 4.6.3, nbconvert 7.17.1

(venv) $ jupyter kernelspec list
  java           .../portfolio/venv/share/jupyter/kernels/java
  python3        .../portfolio/venv/share/jupyter/kernels/python3
  jbang-ijava    ~/.local/share/jupyter/kernels/jbang-ijava
  jslab, tslab   ...
```

**Proving the kernels actually run Java.** A version number only proves a binary exists, so I executed a real cell against *both* kernels:

```shell
(venv) $ jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name=java --stdout javatest.ipynb
Java kernel OK: 21.0.11

(venv) $ jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name=jbang-ijava --stdout javatest.ipynb
Java kernel OK: 21.0.11
```

Both execute real code on JDK 21. Setup verified.

> 📸 **Screenshot placeholder — Terminal: final version checks**

---

### Takeaways

1. **Run every version check before installing anything.** Half of what the README said to install was already there; two "missing" tools were PATH problems in a costume.
2. **`which -a` is the first debugging move.** `cs` existing does not mean Coursier exists.
3. **READMEs go stale faster than code.** Three of five failures were dead commands and dead URLs, not a broken machine.
4. **Read the real error, not the wrapper's.** "Kernel died before replying" is useless; running the `kernel.json` `argv` by hand named the bad flag in one line.
5. **A generated config file is still just a file.** Hand-editing `kernel.json` was the fix, not reinstalling.

---
---

## Part 2 — Remixing the Code Runners Lesson

### What I started from

The source lesson is **"Code Runners - Raw MD"** in the Open Coding Society **pages** repo
([`pages.opencodingsociety.com/code/csa/`](https://pages.opencodingsociety.com/code/csa/), file `_posts/Foundation/C-github_pages/2026-08-03-code-runner-examples.md`).

It's functional and useful, but it's a **reference page, not a lesson**: four `## Heading` → runner → one sentence of explanation, repeated; every runner ships *working* code so there's nothing to do; no challenges, hints, checks for understanding, or sense of progress; plain Minima defaults.

I rebuilt it in my portfolio at [`/portfolio/code/csa/`](/portfolio/code/csa/) (`_posts/2026-08-20-code-runners-csa.md`) as **"Code Runners — CSA Arcade Edition."**

> 📸 **Screenshot placeholders — BEFORE (plain original) and AFTER (gradient hero, XP bar, quest list)**

---

### What I changed

**1. A gradient hero banner instead of a bare `<h1>`.** Full-width gradient card with the title, the pitch, and pill chips for each language plus an estimated time — you know what you're in for before you scroll.

**2. An XP bar and a quest checklist that remember you.** The change I'm happiest with: a six-item quest list and gradient progress bar. Clicking a quest toggles ⬜ → ✅, the bar animates, and the status escalates — *"warming up"* → *"the boss is watching"* → *"full run. 🏆"* It persists to `localStorage`, so closing the tab keeps your progress. ~60 lines of vanilla JS, no dependencies.

**3. Every runner now has something broken or missing.** The biggest pedagogical change — the original's code all works, so running it teaches nothing. Each one is now a task:

| Level | Original | My version |
|---|---|---|
| 1 · Python | Prints 0–4 | Same starter, extend to 10 and add labels |
| 2 · Java | Working `Hello, World!` | **Missing a semicolon** — read the compiler error, fix it, then flip the loop into a countdown |
| 3 · JavaScript | Prints 0–4 | Rewrite it backwards, then compare side-by-side with Java |
| 4 · Pseudocode | Calculator | Same, but deliberately try `12 / 0` and watch the guard clause fire |
| **Boss** | *(did not exist)* | **New FizzBuzz gauntlet** with a `// TODO` skeleton |

Each uses the runner component's `challenge` and `challenge_number` parameters — which the original documented but never used.

**4. Progressive hints in collapsible spoilers.** `<details>` blocks styled as dashed purple hint cards. Java levels get **two tiers** — a nudge ("read the line number the compiler gives you"), then the mechanism. The boss has a third tier with the full solution, labelled ☠️ *only after you've tried*. Useful whether you're stuck or cruising, spoiling nothing by default.

**5. A boss fight.** FizzBuzz 1–20 as a `for` loop with a `// TODO`. The challenge box names the actual trap — *order matters; check the most specific condition first* — because the classic failure is putting the `&&` branch last and never printing `FizzBuzz`. Its 👾 badge is orange instead of purple so it reads as a step up.

**6. A self-grading quiz.** Three multiple-choice questions with **no submit button** — click an answer and it turns green or red immediately with feedback. Unlimited retries; all three correct auto-completes the sixth quest.

**7. An unlockable completion badge.** A 🔒 dashed card counts down remaining quests, then flips to a solid green 🏆 *"Run Complete — badge unlocked!"* Small, but it gives the page an ending instead of trailing off into documentation.

**8. Comparison tables instead of paragraphs.** Three reference tables replace the prose: **Java vs JavaScript** (what actually differs between Levels 2 and 3), a **pseudocode cheat sheet** (`←`, `=`, `≠`, `DISPLAY`, `INPUT` → Java), and a **parameter reference** for every `runners/code.html` argument, including the `code=my_code` vs `code="my_code"` gotcha the original never mentions.

**9. A theme-aware design system.** A small CSS token set (`--arc-accent`, `--arc-panel`, `--arc-line`, …) at `:root` with a `prefers-color-scheme: dark` override, so every card, badge, hint, and quiz button re-colors correctly instead of turning into black-text-on-black.

> 📸 **Screenshot placeholders — hero, XP bar mid-fill, Java challenge box, hints open/closed, boss fight, quiz right vs wrong, badge locked vs unlocked, light vs dark**

---

### What I had to debug in the rebuild

Two kramdown problems worth writing down:

**A table with an empty first header cell silently isn't a table.** My Java-vs-JavaScript comparison started as `| | Java | JavaScript |`. Kramdown refused to parse it, rendered the whole thing as one paragraph, and converted my `|---|---|---|` separator into em dashes. Naming the first column (`| Feature | Java | JavaScript |`) fixed it instantly.

**A table needs a blank line before a closing `</div>`.** Inside a `<div markdown="1">`, ending a table immediately above `</div>` also broke parsing. The two tables that worked happened to have trailing prose; adding a blank line and a closing sentence made the third parse.

I found both by building locally and grepping the output rather than trusting the page to look right:

```shell
(venv) $ bundle exec jekyll build          # done in 27.226 seconds
(venv) $ grep -c "<table" _site/code/csa/index.html               # 3
(venv) $ grep -c "code-runner-container" _site/code/csa/index.html # 5
```

Three tables, five runners, exactly as intended.

---

### Summary of the remix

| Metric | Original | Arcade Edition |
|---|---|---|
| Code runners | 4 | 5 (added a boss) |
| Challenges | 0 | 5 |
| Hints | 0 | 5 collapsible, tiered |
| Quiz questions | 0 | 3, self-grading |
| Progress tracking | none | XP bar + 6 quests, saved locally |
| Reference tables | 0 | 3 |
| Custom CSS | none | ~150 lines, light + dark |
| Broken-on-purpose code | none | Levels 2 and 5 |

The runner component itself is untouched — every change is in the lesson markdown. That was deliberate: the point was to show the *same* include can carry a much better lesson if the page around it does some work.
