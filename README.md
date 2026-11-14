# ENGS 27 Final Project: Storing Text in DNA

Encode English text as DNA strands and recover it from random fragments ("reads") returned by the course's sequencing channel.

## What's here

| File | What it is |
|---|---|
| `ENG_27_Project_Starter.ipynb` | The project notebook: the task, the channel experiments, and the cell that writes `solution.py` |
| `Project_notes.md` | Running notes and the Findings log, one entry per experiment |
| `ENGS_27_Notes (10).pdf` | The course lecture notes, the primary source for methods |
| `site/` | A local website that shows the notes, the findings and the notebook's saved outputs |
| `CLAUDE.md` | Working conventions and citation rules for Claude Code |

## The project site

The site turns `Project_notes.md` and the notebook into pages you read in a browser: the Findings log as a step-by-step timeline, the other notes sections, and every notebook cell with its saved output.

### Start the server

From the project folder:

```
.venv/bin/python site/serve.py
```

This builds the site, opens http://localhost:8027 in your browser, and keeps running. Stop it with Ctrl-C.

| Option | Effect |
|---|---|
| `--port 9000` | Serve on a different port (use this if 8027 is taken) |
| `--no-open` | Don't open a browser tab |

The server is only reachable from this computer.

### Keeping it up to date

While the server runs, it rebuilds whenever `Project_notes.md` or the notebook is **saved**, and open pages reload on their own. Running a notebook cell isn't enough: save the notebook (Cmd+S) for its new output to appear.

To build the pages once without a server:

```
.venv/bin/python site/build.py
```

Then open `site/index.html`.

### Requirements

Python 3 only. The site uses the standard library, plus Pygments for code colouring when it is installed (it is in this project's `.venv`). No other packages are needed.

### Adding to the site

- **Findings:** add an entry to the Findings log in `Project_notes.md`. The rules are in that file's "How to log a finding" section.
- **Plots:** each build saves every notebook plot to `site/figures/`. These snapshots are never overwritten and are tracked in git. The generated `.html` pages are not tracked.
