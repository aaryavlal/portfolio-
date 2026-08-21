---
layout: post
title: Week 1 Checkpoint — Java Toolchain Setup & Lesson Remix
description: Getting every Java tool the portfolio README asks for onto WSL/Ubuntu, the four things that broke along the way, and rebuilding the Code Runners lesson as an interactive arcade.
permalink: /checkpoints/week-1/
comments: true
type: ccc
courses: { csa: {week: 1} }
categories: [Tools]
toc: true
---

## Part 1 — Java Toolchain Setup

### Where I started

I worked straight off the portfolio `README.md`. Scanning it for anything Java-related, the README asks for:

- A **JDK** — implied everywhere, since IJava is a JShell wrapper
- **Jupyter**, because the Java kernels are registered against it
- **Coursier** (`cs`) — `sudo apt install coursier`, then `cs install --channel=… ijava`
- **JBang** — `sudo apt install jbang` / `snap install jbang --classic`, then `jbang app install ijava`
- The resulting kernels showing up in `jupyter kernelspec list`, specifically `java` and `jbang-ijava`

My environment is Windows 11 → WSL2 → Ubuntu 24.04, with the portfolio's own `venv/` as the Python environment.

### The first pass — what was already working, what wasn't

I ran every version check before installing anything, so I would know what I actually had to fix:

```shell
aaryav@DESKTOP:~/csa/portfolio$ java -version
openjdk version "21.0.11" 2026-04-21
OpenJDK Runtime Environment (build 21.0.11+10-1-24.04.2-Ubuntu)
OpenJDK 64-Bit Server VM (build 21.0.11+10-1-24.04.2-Ubuntu, mixed mode, sharing)

aaryav@DESKTOP:~/csa/portfolio$ javac -version
javac 21.0.11

aaryav@DESKTOP:~/csa/portfolio$ jbang --version
0.97.0

aaryav@DESKTOP:~/csa/portfolio$ echo $JAVA_HOME

aaryav@DESKTOP:~/csa/portfolio$ cs --version
cs: invalid option: -
```

Scoreboard after round one:

| Tool | Status | Problem |
|---|---|---|
| JDK 21 (`java`, `javac`) | ✅ Pass | — |
| JBang | ✅ Pass | Installed, but zero apps registered |
| `JAVA_HOME` | ❌ Fail | Unset entirely |
| Coursier | ❌ Fail | `cs` resolved to something that isn't Coursier |
| `jupyter kernelspec` | ❌ Fail | Subcommand didn't exist |
| `jbang-ijava` kernel | ❌ Fail | Not installed |

That gave me four things to chase down — which turned into five separate errors, because two of them broke twice. None of the README's copy-paste commands fixed any of them on their own.

---

### 🐛 Error 1 — `cs` was Csound, not Coursier

`cs --version` printed `cs: invalid option: -`, which is not a Coursier error message at all. So I asked the shell what `cs` actually was:

```shell
aaryav@DESKTOP:~$ which -a cs
/usr/bin/cs
/bin/cs

aaryav@DESKTOP:~$ dpkg -S $(readlink -f $(which cs))
csound: /usr/bin/cs
```

**Diagnosis.** `cs` on my machine belongs to **Csound**, the audio synthesis language, which had come along as a dependency of something else. Coursier was never installed — the name just happened to already be taken. The README's `sudo apt install coursier` would not have fixed this either: even if it installed, the Csound binary at `/usr/bin/cs` would keep winning depending on PATH order.

**Solution.** Install the real Coursier launcher into my user directory and shadow the Csound binary using PATH precedence, rather than deleting Csound (which other things depend on).

```shell
aaryav@DESKTOP:~$ mkdir -p ~/.local/share/coursier/bin
aaryav@DESKTOP:~$ curl -fL "https://github.com/coursier/launchers/raw/master/cs-x86_64-pc-linux.gz" \
    | gzip -d > ~/.local/share/coursier/bin/cs
aaryav@DESKTOP:~$ chmod +x ~/.local/share/coursier/bin/cs
aaryav@DESKTOP:~$ ln -sf ~/.local/share/coursier/bin/cs ~/.local/bin/cs
aaryav@DESKTOP:~$ hash -r
```

This works because `~/.local/bin` is already **first** in my PATH on Ubuntu, ahead of `/usr/bin`:

```shell
aaryav@DESKTOP:~$ echo $PATH | tr ':' '\n' | head -3
/home/aaryav/.local/bin
/home/aaryav/.nvm/versions/node/v24.16.0/bin
/home/aaryav/.cargo/bin
```

**Then a second, smaller trip-up.** `cs --version` still printed a usage screen instead of a version. Modern Coursier moved that behind a subcommand:

```shell
aaryav@DESKTOP:~$ cs --version
Usage: /home/aaryav/.local/bin/cs <COMMAND>
Coursier is the Scala application and artifact manager.

aaryav@DESKTOP:~$ cs version
2.1.25-M26
```

It is `cs version`, not `cs --version`. Small thing, but I would have kept thinking the install was broken.

---

### 🐛 Error 2 — `jupyter kernelspec` did not exist

Next I tried to list my kernels, straight out of the README:

```shell
aaryav@DESKTOP:~/csa/portfolio$ jupyter kernelspec list
usage: jupyter [-h] [--version] [--config-dir] [--data-dir] [--runtime-dir]
               [--paths] [--json] [--debug]
               [subcommand]

Available subcommands: bundlerextension execute migrate nbextension notebook
serverextension troubleshoot

Jupyter command `jupyter-kernelspec` not found.
```

**Diagnosis.** I was hitting `/usr/bin/jupyter` — the ancient apt-packaged Jupyter that ships with Ubuntu (`jupyter_client 7.4.9`, no `jupyter_server`, no JupyterLab). The `jupyter-kernelspec` entry point simply isn't in that package.

My instinct was `pip install jupyter_client`, but on Ubuntu 24.04 that hits the `externally-managed-environment` wall (PEP 668) — and it would have been the wrong fix anyway.

**Solution.** The portfolio repo already ships a proper `venv/`. I just wasn't in it. Activating it swapped me onto a modern Jupyter:

```shell
aaryav@DESKTOP:~/csa/portfolio$ source venv/bin/activate

(venv) aaryav@DESKTOP:~/csa/portfolio$ which jupyter
/home/aaryav/csa/portfolio/venv/bin/jupyter

(venv) aaryav@DESKTOP:~/csa/portfolio$ jupyter kernelspec list
Available kernels:
  java       /home/aaryav/csa/portfolio/venv/share/jupyter/kernels/java
  python3    /home/aaryav/csa/portfolio/venv/share/jupyter/kernels/python3
  jslab      /home/aaryav/.local/share/jupyter/kernels/jslab
  tslab      /home/aaryav/.local/share/jupyter/kernels/tslab
```

**Lesson learned:** every Jupyter and kernel command in this project has to be run with the venv active. Outside it, you are talking to a different Jupyter that knows about none of this. The `java` (IJava 1.3.0) kernel had actually been there the whole time — I just couldn't see it. `jbang-ijava` was genuinely missing.

---

### 🐛 Error 3 — `jbang app install ijava` doesn't exist anymore

Straight from the README:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ jbang app install ijava
[jbang] [ERROR] Script or alias could not be found or read: 'ijava'
[jbang] Run with --verbose for more details
```

**Diagnosis.** `ijava` used to be an alias in the `jbangdev` catalog. It isn't there now — I checked:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ jbang alias list jbangdev | grep -iE "ijava|jupyter"
jbang-jupyter@jbangdev = https://github.com/jbangdev/jbang-jupyter/releases/download/...
trylink@jbangdev = https://github.com/jbangdev/jbang-catalog/blob/HEAD/jupyter/trylink.java
```

The README is stale here. JBang's Jupyter support moved to a dedicated installer in the **`jupyter-java`** catalog: `install-kernel@jupyter-java`.

**Then it stalled on a trust prompt.** JBang refuses to auto-run scripts from untrusted URLs, and in a non-interactive shell that prompt times out and dies with a confusing NPE:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ jbang install-kernel@jupyter-java --help
[jbang] https://github.com/jupyter-java/jbang-catalog/blob/HEAD/installkernel.java
        is not from a trusted source thus not running it automatically.
...
[jbang] [ERROR] Cannot invoke "java.lang.Throwable.printStackTrace()" because
        the return value of "java.lang.Exception.getCause()" is null
```

**Solution.** Trust the org once, then install:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ jbang trust add https://github.com/jupyter-java/
[jbang] Adding [https://github.com/jupyter-java/] to /home/aaryav/.jbang/trusted-sources.json

(venv) aaryav@DESKTOP:~/csa/portfolio$ jbang install-kernel@jupyter-java \
    --kernel-dir=jbang-ijava --name="JBang IJava" IJAVA
JBang IJava kernel installed to /home/aaryav/.local/share/jupyter/kernels/jbang-ijava/kernel.json
For more information on this specific kernel: https://github.com/SpencerPark/IJava

Brought to you by https://github.com/jupyter-java
```

`--kernel-dir=jbang-ijava` is what makes it show up under the exact name the README's example output uses.

---

### 🐛 Error 4 — the installed kernel died instantly

`jupyter kernelspec list` now showed `jbang-ijava`, so I assumed I was done. I wasn't. Running an actual Java cell against it:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name=jbang-ijava javatest.ipynb
...
RuntimeError: Kernel died before replying to kernel_info
```

**Diagnosis.** "Kernel died before replying" tells you nothing, so I pulled the launch command straight out of the generated `kernel.json` and ran it by hand:

```json
"argv": [
  "/snap/bin/jbang", "--java", "11+", "--ea",
  "-R-ea", "-R--add-opens", "-Rjava.base/jdk.internal.misc=ALL-UNNAMED",
  "-R--illegal-access=permit",
  "com.github.waikato.thirdparty:ijava:1.3.0", "{connection_file}"
]
```

```shell
(venv) aaryav@DESKTOP:~$ /snap/bin/jbang --java 11+ --ea -R-ea -R--add-opens \
    -Rjava.base/jdk.internal.misc=ALL-UNNAMED -R--illegal-access=permit \
    com.github.waikato.thirdparty:ijava:1.3.0 conn.json
Unknown options: '-R-ea', '-R--add-opens', '-Rjava.base/jdk.internal.misc=ALL-UNNAMED', '-R--illegal-access=permit'
Usage: jbang run -o [-hin] [--[no-]cds] [--ea] [--esa] --fresh ...
```

There it is. The installer wrote a `kernel.json` using the modern `-R` shorthand for JVM runtime options, but my snap-installed **JBang 0.97.0 doesn't understand `-R`** — it wants `--java-options=`. Jupyter never surfaced this because a kernel's stderr is swallowed on startup failure.

**A second problem in the same file:** `--illegal-access=permit` was **removed** from the JVM in Java 17. On Java 21 it's a hard startup failure, so it had to go too.

**And a third:** my first fix pinned `--java 17`, which sent JBang off to download a JDK it couldn't get:

```shell
[jbang] Downloading JDK 17. Be patient, this can take several minutes...
[jbang] [ERROR] Required Java version not possible to download or install.
        You can run with '--java 21' to force using the default installed Java.
[jbang] [ERROR] Unable to download or install JDK version 17
```

Snap confinement blocks the JDK download. The error message conveniently tells you the fix.

**Solution.** Hand-edit `~/.local/share/jupyter/kernels/jbang-ijava/kernel.json` — swap `-R` for `--java-options=`, drop the dead `--illegal-access` flag, and pin to the JDK 21 I already have:

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

For completeness I tried the README's Coursier route to IJava as well:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ cs install \
    --channel=https://github.com/SpencerPark/IJava/releases/latest/download/channel.json ijava
...
Caused by: coursier.cache.ArtifactError$NotFound: not found:
  https://github.com/SpencerPark/IJava/releases/latest/download/channel.json
```

**Diagnosis.** SpencerPark/IJava's latest release no longer publishes a `channel.json`, so the URL 404s. This is a stale link in the README, not a broken Coursier install — `cs version` proves Coursier itself is fine.

**Solution.** I didn't need it. The README offers Coursier and JBang as **alternatives** ("Or for jbang-ijava"), and the `java` kernel from IJava 1.3.0 was already registered in the venv while the JBang route now covers `jbang-ijava`. Coursier stays installed and verified because the README lists it as a required tool.

---

### Persisting the environment

`JAVA_HOME` was still empty, and I didn't want the Coursier PATH fix to vanish on the next shell. Both went into `~/.bashrc`:

```bash
# --- CSA / Open Coding Society Java toolchain ---
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH="$HOME/.local/share/coursier/bin:$PATH"
```

---

### ✅ Final version checks — all passing

Full terminal output after everything above:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ java -version
openjdk version "21.0.11" 2026-04-21
OpenJDK Runtime Environment (build 21.0.11+10-1-24.04.2-Ubuntu)
OpenJDK 64-Bit Server VM (build 21.0.11+10-1-24.04.2-Ubuntu, mixed mode, sharing)

(venv) aaryav@DESKTOP:~/csa/portfolio$ javac -version
javac 21.0.11

(venv) aaryav@DESKTOP:~/csa/portfolio$ echo $JAVA_HOME
/usr/lib/jvm/java-21-openjdk-amd64

(venv) aaryav@DESKTOP:~/csa/portfolio$ which -a cs && cs version
/home/aaryav/.local/bin/cs
/usr/bin/cs
/bin/cs
2.1.25-M26

(venv) aaryav@DESKTOP:~/csa/portfolio$ jbang --version
0.97.0

(venv) aaryav@DESKTOP:~/csa/portfolio$ jupyter --version
Selected Jupyter core packages...
IPython          : 9.16.1
ipykernel        : 7.3.0
ipywidgets       : 8.1.8
jupyter_client   : 8.9.1
jupyter_core     : 5.9.1
jupyter_server   : 2.20.0
jupyterlab       : 4.6.3
nbclient         : 0.11.0
nbconvert        : 7.17.1
nbformat         : 5.11.1
notebook         : 7.6.2
qtconsole        : not installed
traitlets        : 5.16.1

(venv) aaryav@DESKTOP:~/csa/portfolio$ jupyter kernelspec list
Available kernels:
  java           /home/aaryav/csa/portfolio/venv/share/jupyter/kernels/java
  python3        /home/aaryav/csa/portfolio/venv/share/jupyter/kernels/python3
  jbang-ijava    /home/aaryav/.local/share/jupyter/kernels/jbang-ijava
  jslab          /home/aaryav/.local/share/jupyter/kernels/jslab
  tslab          /home/aaryav/.local/share/jupyter/kernels/tslab
```

### Proving the kernels actually run Java

A version number only proves a binary exists. I executed a real Java cell against **both** kernels:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ cat javatest.ipynb
# one code cell:
# System.out.println("Java kernel OK: " + System.getProperty("java.version"));

(venv) aaryav@DESKTOP:~/csa/portfolio$ jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name=java --stdout javatest.ipynb
Java kernel OK: 21.0.11

(venv) aaryav@DESKTOP:~/csa/portfolio$ jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name=jbang-ijava --stdout javatest.ipynb
Java kernel OK: 21.0.11
INFO: Running loop shutdown callback.
INFO: Loop stopped.
```

Both Java kernels execute real code on JDK 21. Setup verified.

> 📸 **Screenshot placeholder — Terminal: final version checks**
>
> _Insert screenshot of the full `java -version` → `jupyter kernelspec list` run here._

---

### Takeaways

1. **Run all version checks before installing anything.** Half of what the README told me to install was already there; two of the "missing" tools were actually PATH problems wearing a costume.
2. **`which -a` is the first debugging move.** `cs` existing does not mean Coursier exists.
3. **READMEs go stale faster than code.** Three of the five failures were dead commands and dead URLs, not a broken machine.
4. **Read the actual error, not the wrapper's error.** "Kernel died before replying to kernel_info" is useless; running the `kernel.json` `argv` by hand named the exact bad flag in one line.
5. **A generated config file is still just a file.** `install-kernel` produced a `kernel.json` that didn't match my JBang version — hand-editing it was the fix, not reinstalling.

---
---

## Part 2 — Remixing the Code Runners Lesson

### What I started from

The source lesson lives in the Open Coding Society **pages** repo at
[`pages.opencodingsociety.com/code/csa/`](https://pages.opencodingsociety.com/code/csa/) —
titled **"Code Runners - Raw MD"**, source file
`_posts/Foundation/C-github_pages/2026-08-03-code-runner-examples.md`.

The original is functional and genuinely useful, but it is a **reference page**, not a lesson. It reads like documentation:

- Four `## Heading` → code runner → one sentence of explanation, repeated
- Every runner ships **working** code, so there is nothing to actually *do* — you press ▶ and it prints `Hello, World!` and 0–4
- No challenges, no hints, no checks for understanding
- No sense of progress or completion
- Plain Minima defaults, no visual identity

I transferred it into my portfolio at
[`/portfolio/code/csa/`](/portfolio/code/csa/), source file
`_posts/2026-08-20-code-runners-csa.md`, and rebuilt it as
**"Code Runners — CSA Arcade Edition."**

> 📸 **Screenshot placeholder — BEFORE**
>
> _Insert screenshot of the original `pages.opencodingsociety.com/code/csa/` page here — plain headings, four runners, no styling._

> 📸 **Screenshot placeholder — AFTER**
>
> _Insert screenshot of my `/portfolio/code/csa/` page here — gradient hero, XP bar, quest list._

---

### What I changed

#### 1. A gradient hero banner instead of a bare `<h1>`

The original opens with a Minima-default heading and a paragraph. Mine opens with a full-width gradient card carrying the title, the pitch, and pill-shaped chips for each language plus an estimated time. It tells you what you're in for before you scroll.

> 📸 **Screenshot placeholder — Hero banner**
>
> _Insert screenshot of the gradient hero with the ☕/🐍/🟨/📝 language chips._

#### 2. An XP bar and a quest checklist that remember you

This is the change I'm happiest with. Under the hero there's a six-item quest list and a gradient progress bar. Clicking a quest toggles it ⬜ → ✅, the bar animates, and the status message escalates as you go — *"warming up"* → *"the boss is watching"* → *"full run. 🏆"*

The whole thing persists to `localStorage`, so closing the tab and coming back keeps your progress. It's about 60 lines of vanilla JavaScript with no dependencies.

> 📸 **Screenshot placeholder — XP bar partially filled**
>
> _Insert screenshot showing ~3/6 quests checked with the progress bar mid-fill._

#### 3. Every runner now has something broken or missing in it

This is the biggest pedagogical change. The original's code all works, which means running it teaches you nothing. I turned each one into a task:

| Level | Original | My version |
|---|---|---|
| 1 · Python | Prints 0–4 | Same starter, but you must extend it to 10 and add labels |
| 2 · Java | Working `Hello, World!` | **Missing a semicolon** — you have to read the compiler error and fix it, then flip the loop into a countdown |
| 3 · JavaScript | Prints 0–4 | Rewrite it backwards, then compare it side-by-side with the Java version |
| 4 · Pseudocode | Calculator | Same, but you're told to deliberately try `12 / 0` and watch the guard clause fire |
| **Boss** | *(did not exist)* | **New FizzBuzz gauntlet** with a `// TODO` skeleton |

Each one uses the runner component's `challenge` and `challenge_number` parameters — which the original page never used at all, despite documenting them.

> 📸 **Screenshot placeholder — Java level with the challenge box**
>
> _Insert screenshot of Level 2 showing the 🐛 challenge box above the editor._

#### 4. Progressive hints in collapsible spoilers

Every level has `<details>` blocks styled as dashed purple hint cards. The Java levels have **two tiers** — a nudge first ("read the line number the compiler gives you"), then the mechanism. The boss fight has a third tier with the full solution, explicitly labelled ☠️ *only after you've tried*.

This keeps the page useful whether you're stuck or cruising, without spoiling anything by default.

> 📸 **Screenshot placeholder — Hints open and closed**
>
> _Insert screenshot showing one collapsed hint and one expanded hint side by side._

#### 5. A boss fight

FizzBuzz from 1 to 20, given as a `for` loop with a `// TODO` where the logic goes. The challenge box calls out the actual trap — *order matters; check the most specific condition first* — because the classic failure mode is putting the `&&` branch last and never printing `FizzBuzz` at all. The 👾 level badge is orange instead of purple so it reads as a step up.

> 📸 **Screenshot placeholder — Boss fight**
>
> _Insert screenshot of the FizzBuzz boss level with its orange 👾 badge._

#### 6. A self-grading quiz

Three multiple-choice questions with **no submit button**. Click an answer and it turns green or red immediately with feedback text. Unlimited retries. Getting all three right auto-completes the sixth quest and can unlock the badge.

> 📸 **Screenshot placeholder — Quiz with right and wrong answers**
>
> _Insert screenshot showing one ✅ green correct answer and one ❌ red incorrect answer._

#### 7. An unlockable completion badge

The page ends with a 🔒 dashed-border card that counts down your remaining quests. Clear all six and it flips to a solid green 🏆 **"Run Complete — badge unlocked!"** card. Small thing, but it gives the page an actual ending instead of trailing off into documentation.

> 📸 **Screenshot placeholder — Badge locked vs unlocked**
>
> _Insert both states side by side._

#### 8. Comparison tables instead of paragraphs

The original explains things in prose. I replaced the explanations with three reference tables:

- **Java vs JavaScript** — what actually differs between Levels 2 and 3
- **Pseudocode cheat sheet** — `←`, `=`, `≠`, `DISPLAY`, `INPUT` mapped to their Java equivalents
- **Parameter reference** — every `runners/code.html` argument, including the `code=my_code` vs `code="my_code"` gotcha the original doesn't mention

#### 9. A theme-aware design system

The original inherits Minima and stops there. Mine defines a small CSS token set (`--arc-accent`, `--arc-panel`, `--arc-line`, …) at `:root` with a `prefers-color-scheme: dark` override, so every card, badge, hint, and quiz button re-colors correctly in dark mode instead of turning into black-text-on-black.

> 📸 **Screenshot placeholder — Light vs dark mode**
>
> _Insert the same section of the page in both themes._

---

### What I had to debug in the rebuild

Two Jekyll/kramdown problems, both worth writing down:

**A markdown table with an empty first header cell silently isn't a table.** My Java-vs-JavaScript comparison started as `| | Java | JavaScript |`. Kramdown refused to parse it, rendered the whole thing as one paragraph, and — adding insult — converted my `|---|---|---|` separator row into em dashes (`|—|—|—|`). Giving the first column an actual name (`| Feature | Java | JavaScript |`) fixed it instantly.

**A table needs a blank line before a closing `</div>`.** Inside a `<div markdown="1">` block, ending the table immediately above `</div>` also broke parsing. The two tables that worked happened to have trailing prose after them. Adding a blank line (and a closing sentence) made the third one parse.

I found both by building locally and grepping the output rather than trusting the page to look right:

```shell
(venv) aaryav@DESKTOP:~/csa/portfolio$ bundle exec jekyll build
                    done in 27.226 seconds.

(venv) aaryav@DESKTOP:~/csa/portfolio$ grep -c "<table" _site/code/csa/index.html
3
(venv) aaryav@DESKTOP:~/csa/portfolio$ grep -c "code-runner-container" _site/code/csa/index.html
5
```

Three tables, five runners, exactly as intended.

---

### Summary of the remix

| | Original | Arcade Edition |
|---|---|---|
| Code runners | 4 | 5 (added a boss) |
| Challenges | 0 | 5 |
| Hints | 0 | 5 collapsible, tiered |
| Quiz questions | 0 | 3, self-grading |
| Progress tracking | none | XP bar + 6 quests, saved locally |
| Reference tables | 0 | 3 |
| Custom CSS | none | ~150 lines, light + dark |
| Broken-on-purpose code | none | Levels 2 and 5 |

The runner component itself is untouched — every change is in the lesson markdown. That was deliberate: the point was to show that the *same* include can carry a much better lesson if the page around it does some work.
