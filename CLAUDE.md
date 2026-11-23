# CLAUDE.md: ENGS 27 Final Project (Storing Text in DNA)

## Primary source

**The course lecture notes are the primary source for this project:**
`ENGS_27_Notes (10).pdf`, *Discrete and Probabilistic Systems: ENGS 27 Course Notes*, Prof. Bijan Mazaheri, Thayer School of Engineering, Dartmouth College, Fall 2026. The PDF has 141 pages.

The project spec is `ENG_27_Project_Starter.ipynb`. It's the authority on the task, the deliverables and the grading. For methods, techniques, formulas and concepts, use the lecture notes.

## Citation rules (always follow)

1. **Ground explanations in the lecture notes first.** When explaining a method, technique, formula or concept, use the notes' treatment, terminology and notation where they cover it.
2. **Cite the notes by section and page.** The notes are organized by chapter and section, not by lecture number. Cite like this: *(Notes §3.2.5 Huffman Coding, p. 54)*.
3. **Flag anything that isn't from the lecture notes explicitly.** Whenever a method, technique, formula or concept is used that doesn't appear in the notes, say so in place, for example:
   > ⚠️ **Not from the lecture notes:** edit distance is defined in the project notebook, not in the notes.

   This applies to replies, to `Project_notes.md`, to code comments and to the write-up. Sources to name include the project notebook, problem sets, general CS or biology knowledge, outside papers and libraries.
4. **Verify before citing.** Search the PDF (for example `pdftotext "ENGS_27_Notes (10).pdf" - | grep -n -i "<term>"`) and don't cite a section from memory. If a concept is only *mentioned* in passing (for example in a "Further Reading" box) and not developed, say so.
5. **Lecture numbers vs. sections:** the notebook refers to "Lecture N". Use the mapping below, and treat entries marked *inferred* as best guesses, not confirmed.

## Notebook lecture references → notes sections

**Page numbers:** cite the *printed* page numbers (the ones in the notes' table of contents). The PDF page index is the printed page + 7 because of the front matter.

Confirmations come from the notes' own lecture references in §0.2 (p. 1), §0.3 (p. 2) and the table in §0.4 (p. 3).

| Notebook reference | Topic | Notes section | Confidence |
|---|---|---|---|
| Lecture 9 | Binary entropy H(e) in the score | §3.1.3 Entropy (p. 46); the binary formula appears there | confirmed (§0.4 ties entropy and Wordle to Lec 9) |
| Lectures 9 & 10 | Compression, Huffman | §3.2 Compression (p. 50); §3.2.5 Huffman Coding (p. 54) | confirmed (§0.2) |
| Lecture 11 | Redundancy, parity checks | §3.3 Error Correction (p. 57); §3.3.3 Parity Checks (p. 59) | confirmed (§0.2) |
| Lectures 6 & 7 | Coverage, coupon collector | §2.4.5 Collecting Everything (p. 36), which includes the Lander–Waterman sequencing model | confirmed (§0.4 ties sequencing coverage to Lec 7) |
| Lectures 7 & 23 | Strand length vs. surviving whole | §2.4.2 Geometric (p. 34); §2.4.3 (p. 35); possibly §7.1 Poisson/Exponential (p. 123) | Lec 7 confirmed; Lec 23 inferred |
| Lecture 15 | Assembling overlapping reads, de Bruijn graphs | §5.1.7 De Bruijn Graphs (p. 85) | confirmed (§0.4: "assembling a genome from short reads, and storing data in DNA (15)") |
| Lecture 18 | Constrained codes; counting allowed strings | §6.1.4 Counting Writable Strings (p. 99) | likely (§0.3: Lec 18 starts the Markov chain unit, and §6.1 opens it) |
| Problem Set 6 | Avoiding repeats | PS6 covers Markov chains, Lec 18–20 (§0.3); the problem set itself isn't in the repo | flag as not from notes |

**In the notes (cite these, don't flag them):**
- Shotgun sequencing, reads as fragments, and coverage: §2.4.5, p. 36.
- Majority vote over repeated copies: §3.3.2, p. 59.
- Hamming distance: §3.3.2, p. 58.
- The noisy-channel framing: §3.3.1, p. 57.

**Known gaps (not in the notes; always flag these):**
- **Edit distance** is defined only in the project notebook. The notes mention deletions and Levenshtein in passing in §3.3.5 Comments and Further Reading (p. 61), but don't develop them.
- **The scoring formula** density × (1 − H(e)) is the project's own definition.
- **DNA synthesis, storage, and lab handling** are general domain knowledge, not course material.
- **Text → bytes (UTF-8/ASCII), the 2-bits-per-base mapping, and per-strand indices** come from general computing and the notebook baseline.
- **Log-scale plots to test for a geometric distribution,** and other data-analysis techniques the notes don't present.
- **Reverse-complement issues, and any library or algorithm not in the notes.**

## Working conventions

- **No solutions yet.** The user is building understanding first. Explain what to do and why, but don't give answers to the Part 1 questions or design choices for `solution.py` until the user explicitly asks.
- **`Project_notes.md` is a growing notebook.** Add new sections before the "Findings log" section and keep it as the last section. Apply the citation rules above inside it.
- **Log findings by the rules in `Project_notes.md`, section "How to log a finding".** Read that section before adding or editing an entry in the Findings log.
- **Every strand sent to the live channel goes into `tested_strands.ipynb`.** When an experiment tests a new sequence, append one item per sequence to the `tested_strands` list in that notebook's code cell, in the same session as the experiment:
  - **Format:** `{"sequence": "<bases>", "deleted": <True/False>, "length": <len(sequence)>}`.
  - **`deleted` is `True` only if the strand meets Appendix B's "What counts as confirmed" rule** in `Project_notes.md`: 0 reads, sent alone, to at least two separate requests of at least 1000 reads. Every `True` item must also be in Appendix B, and every Appendix B strand must be `True`.
  - **No duplicates.** If the sequence is already in the list, don't add it again. Update `deleted` only if the new result changes it, and note the change in the Findings log.
  - Take sequences from the experiment's code or saved output, never retyped by hand. Strands from `LocalChannel` don't go in.
  - **Keep `tested_strands.csv` in step.** It's a copy of the same list (columns `sequence`, `deleted`, `length`). After every change to `tested_strands.ipynb`, regenerate the CSV from it, and check both have the same rows.
- **`solution.py` is generated** by the `%%writefile solution.py` cell in the notebook. Edit that cell, not the file directly.
- **Record every change to the `solution.py` cell** in `Project_notes.md`, section "Solution walkthrough and history", table "History of changes to `solution.py`": one row per change, next version number, with date, what changed, why, and the `evaluate` scores (write "not run" if missing). Then remind the user to re-run the `solution-walkthrough` cell and save the notebook, so the walkthrough on the site matches. If the design no longer fits the walkthrough's step-by-step trace, update that cell's trace.
- The write-up must be **one page** and evidence-based, so preserve plots and numbers from experiments.
