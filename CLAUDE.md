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

| Notebook reference | Topic | Notes section | Confidence |
|---|---|---|---|
| Lecture 9 | Binary entropy H(e) in the score | §3.1.3 Entropy (p. 46) | inferred |
| Lectures 9 & 10 | Compression, Huffman | §3.2 Compression; §3.2.5 Huffman Coding (p. 54) | Lec 10 confirmed by notes §0.2 |
| Lecture 11 | Redundancy, parity checks | §3.3 Error Correction; §3.3.3 Parity Checks (p. 59) | confirmed by notes §0.2 |
| Lectures 6 & 7 | Coverage, coupon collector | §2.4.5 Collecting Everything (p. 36) | inferred |
| Lectures 7 & 23 | Strand length vs. surviving whole | §2.4.2 Geometric (p. 34); possibly §7.1 Poisson/Exponential (p. 123) | inferred |
| Lecture 15 | Assembling overlapping reads, de Bruijn graphs | §5.1.7 De Bruijn Graphs (p. 85) | inferred |
| Lecture 18 | Constrained codes; counting allowed strings | §6.1.4 Counting Writable Strings (p. 99) | inferred |
| Problem Set 6 | Avoiding repeats | Not in the notes (problem set not in repo) | n/a |

**Known gaps (not in the notes; always flag these):**
- **Edit distance** is defined only in the project notebook. The notes mention deletions and Levenshtein in passing in §3.3.5 Comments and Further Reading (p. 61), but don't develop them.
- **Binary entropy as written in the grading formula:** the notes cover general entropy in §3.1.3. Confirm that the binary special case appears there before citing it directly.
- **DNA sequencing and synthesis background** is general domain knowledge, not course material.
- **Majority voting, reverse-complement issues, and any library or algorithm not in the notes.**

## Working conventions

- **No solutions yet.** The user is building understanding first. Explain what to do and why, but don't give answers to the Part 1 questions or design choices for `solution.py` until the user explicitly asks.
- **`Project_notes.md` is a growing notebook.** Add new sections before the "Findings log" section and keep it as the last section. Apply the citation rules above inside it.
- **`solution.py` is generated** by the `%%writefile solution.py` cell in the notebook. Edit that cell, not the file directly.
- The write-up must be **one page** and evidence-based, so preserve plots and numbers from experiments.
