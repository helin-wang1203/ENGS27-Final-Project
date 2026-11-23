#!/usr/bin/env python3
"""Build the local project site from Project_notes.md and the notebook.

    python site/build.py        build once, then open site/index.html
    python site/serve.py        serve at http://localhost:8027 and rebuild on every save

What it makes (all inside site/):
  index.html      the Findings log as a step-by-step timeline (one step per "### " entry)
  <section>.html  one page per other "## " section of Project_notes.md
  notebook.html   every notebook cell with its saved outputs
  figures/        a snapshot of every plot saved in the notebook. Files are named by plot
                  title plus a hash of the image, and are never overwritten or deleted, so a
                  figure cited in a finding survives re-running the cell.

Writing for the site, in Project_notes.md:
  Figure     ![caption](site/figures/<file>.png)   (copy the line from the Lab notebook page)
  Output     @notebook-output <cell id>   on a line of its own: that cell's saved HTML output
  Sequence   inline code that is only A/C/G/T is coloured automatically. For a ruler, use:

      ```dna
      @cut 60               bar before base 60 (0-based, like the notebook)
      @mark 30-89           underline bases 30..89
      @start 60             coordinate of the first base shown (default 0)
      strand 67: CGAGACC...
      read:      CGAGTCC... further rows are compared with the first; mismatches are boxed
      ```

Uses only the standard library. Pygments is used for code colouring when it is installed.
"""
import base64
import datetime
import hashlib
import html
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
NOTES = ROOT / "Project_notes.md"
NOTEBOOK = ROOT / "ENG_27_Project_Starter.ipynb"
FIGDIR = SITE / "figures"

try:
    from pygments import highlight as _pyg_highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import PythonLexer, get_lexer_by_name
except ImportError:  # the site still builds, code is just uncoloured
    _pyg_highlight = None

esc = html.escape


def slugify(text, limit=60):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit].strip("-") or "x"


# ----------------------------------------------------------------------------- code

def highlight_code(code, lang="python"):
    if _pyg_highlight and lang:
        try:
            lexer = PythonLexer() if lang in ("python", "py") else get_lexer_by_name(lang)
            return f'<pre class="hl"><code>{_pyg_highlight(code, lexer, HtmlFormatter(nowrap=True))}</code></pre>'
        except Exception:
            pass
    return f'<pre class="plain"><code>{esc(code)}</code></pre>'


def pygments_css():
    if not _pyg_highlight:
        return ""
    light = HtmlFormatter(style="default", nobackground=True).get_style_defs(".hl")
    try:
        dark = HtmlFormatter(style="github-dark", nobackground=True).get_style_defs(".hl")
    except Exception:
        dark = HtmlFormatter(style="monokai", nobackground=True).get_style_defs(".hl")
    return f"{light}\n@media (prefers-color-scheme: dark) {{\n{dark}\n}}"


# ----------------------------------------------------------------------------- DNA

def base_span(ch, extra=""):
    cls = f"b-{ch}" if ch in "ACGT" else "b-N"
    return f'<span class="{cls}{extra}">{esc(ch)}</span>'


def render_dna_inline(seq, tail=""):
    return f'<code class="dna">{"".join(base_span(c) for c in seq)}{esc(tail)}</code>'


def render_dna_block(src, width=60):
    seqs, cuts, marks, start = [], set(), [], 0
    for line in src.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("@"):
            parts = line[1:].split()
            try:
                if parts[0] == "cut":
                    cuts.update(int(x) for x in parts[1:])
                elif parts[0] == "mark":
                    a, b = parts[1].split("-")
                    marks.append((int(a), int(b)))
                elif parts[0] == "start":
                    start = int(parts[1])
            except (IndexError, ValueError):
                pass
            continue
        label, _, seq = line.rpartition(":")
        seqs.append((label.strip(), re.sub(r"\s+", "", seq).upper()))
    if not seqs:
        return ""
    labw = max(len(l) for l, _ in seqs)
    pad = labw + 2 if labw else 0
    longest = max(len(s) for _, s in seqs)
    ref = seqs[0][1]
    rows = []
    for off in range(0, longest, width):
        end = min(off + width, longest)
        ruler = " " * pad + " ".join(str(start + g).ljust(10) for g in range(off, end, 10))
        rows.append(f'<span class="ruler">{ruler.rstrip()}</span>')
        for si, (label, seq) in enumerate(seqs):
            out = [f'<span class="lab">{esc(label.ljust(pad))}</span>'] if pad else []
            for i in range(off, min(end, len(seq))):
                if i > off and i % 10 == 0:
                    out.append(" ")
                if start + i in cuts:
                    out.append('<i class="cut"></i>')
                extra = ""
                if any(a <= start + i <= b for a, b in marks):
                    extra += " mk"
                if si and i < len(ref) and seq[i] != ref[i]:
                    extra += " mm"
                out.append(base_span(seq[i], extra))
            rows.append("".join(out))
        rows.append("")
    n = f"{longest} bases" if len(seqs) == 1 else f"{len(seqs)} sequences"
    return f'<div class="dna-block"><pre>{chr(10).join(rows).rstrip()}</pre><div class="dna-meta">{n}</div></div>'


# ----------------------------------------------------------------------------- math
# A small TeX-to-MathML converter covering what the notes and notebook use.

TEX_SYMBOLS = {
    "times": "×", "cdot": "⋅", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "approx": "≈",
    "neq": "≠", "ne": "≠", "infty": "∞", "to": "→", "sum": "∑", "prod": "∏", "pm": "±",
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "lambda": "λ",
    "mu": "μ", "pi": "π", "sigma": "σ", "theta": "θ", "ldots": "…", "dots": "…", "cdots": "⋯",
}
TEX_SPACES = {"qquad": "2em", "quad": "1em", ",": "0.17em", ";": "0.28em", " ": "0.28em"}
TEX_SKIP = {"left", "right", "bigl", "bigr", "Bigl", "Bigr", "big", "Big", "displaystyle"}
TEX_FUNCS = {"log", "ln", "exp", "min", "max", "Pr"}


def tex_to_mathml(tex, block=False):
    texts = []

    def stash(m):
        texts.append(m.group(1))
        return f"\x00{len(texts) - 1}\x00"

    tex = re.sub(r"\\(?:text|mathrm|operatorname)\{([^}]*)\}", stash, tex)
    toks = re.findall(r"\x00\d+\x00|\\[a-zA-Z]+|\\.|\d+(?:\.\d+)?|[a-zA-Z]|\S", tex)
    pos = 0

    def atom():
        nonlocal pos
        t = toks[pos]
        pos += 1
        if t == "{":
            inner = seq("}")
            return f"<mrow>{inner}</mrow>"
        if t.startswith("\x00"):
            return f"<mtext>{esc(texts[int(t.strip(chr(0)))])}</mtext>"
        if t.startswith("\\"):
            name = t[1:]
            if name == "frac":
                a, b = operand(), operand()
                return f"<mfrac>{a}{b}</mfrac>"
            if name == "sqrt":
                return f"<msqrt>{operand()}</msqrt>"
            if name in TEX_SPACES:
                return f'<mspace width="{TEX_SPACES[name]}"/>'
            if name in TEX_SKIP:
                return ""
            if name in TEX_SYMBOLS:
                s = TEX_SYMBOLS[name]
                return f"<mi>{s}</mi>" if s.isalpha() else f"<mo>{s}</mo>"
            if name in TEX_FUNCS:
                return f'<mi mathvariant="normal">{name}</mi>'
            return f"<mi>{esc(name)}</mi>"
        if t[0].isdigit():
            return f"<mn>{t}</mn>"
        if t.isalpha():
            return f"<mi>{t}</mi>"
        fixed = ' stretchy="false"' if t in "()[]|" else ""
        return f"<mo{fixed}>{esc({'-': '−'}.get(t, t))}</mo>"

    def operand():
        return atom() if pos < len(toks) else "<mrow></mrow>"

    def seq(stop=None):
        nonlocal pos
        out = []
        while pos < len(toks):
            if toks[pos] == stop:
                pos += 1
                break
            if toks[pos] in "^_" and out:
                base, sub, sup = out.pop(), None, None
                while pos < len(toks) and toks[pos] in "^_":
                    kind = toks[pos]
                    pos += 1
                    if kind == "^":
                        sup = operand()
                    else:
                        sub = operand()
                if sub and sup:
                    out.append(f"<msubsup>{base}{sub}{sup}</msubsup>")
                elif sup:
                    out.append(f"<msup>{base}{sup}</msup>")
                else:
                    out.append(f"<msub>{base}{sub}</msub>")
                continue
            a = atom()
            if a:
                out.append(a)
        return "".join(out)

    body = seq()
    disp = ' display="block"' if block else ""
    return f"<math{disp}><mrow>{body}</mrow></math>"


# ----------------------------------------------------------------------------- markdown
# A small Markdown renderer for the subset the notes use: headings, nested lists, tables,
# fenced code, block quotes, rules, images, links, bold, italic, code and $math$.

DNA_INLINE = re.compile(r"^([ACGT]{6,})(…|\.\.\.)?$")


def render_inline(text):
    stash = []

    def keep(markup):
        stash.append(markup)
        return f"\x00{len(stash) - 1}\x00"

    def code(m):
        body = m.group(2).strip() if m.group(2).strip() else m.group(2)
        d = DNA_INLINE.match(body)
        return keep(render_dna_inline(d.group(1), d.group(2) or "") if d else f"<code>{esc(body)}</code>")

    text = re.sub(r"(`+)(.+?)\1", code, text, flags=re.S)
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(tex_to_mathml(m.group(1), True)), text, flags=re.S)
    text = re.sub(r"(?<![\\\w])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)", lambda m: keep(tex_to_mathml(m.group(1))), text)
    text = re.sub(r"\\([*_$`\\#\[\]()])", lambda m: keep(esc(m.group(1))), text)
    text = esc(text, quote=False)

    def image(m):
        alt, src = m.group(1), m.group(2).strip()
        shown = src[len("site/"):] if src.startswith("site/") else src
        cap = f"<figcaption>{alt}</figcaption>" if alt else ""
        return keep(f'<figure class="fig"><a href="{esc(shown)}"><img src="{esc(shown)}" alt="{esc(alt)}" '
                    f'loading="lazy"></a>{cap}</figure>')

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{esc(m.group(2))}">{m.group(1)}</a>', text)
    text = re.sub(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"(?<![\*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?!\*)", r"<em>\1</em>", text, flags=re.S)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    for _ in range(3):  # stashed markup can sit inside other stashed markup
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


LIST_ITEM = re.compile(r"^( *)([-*+]|\d+[.)])( +)(.*)$")
FENCE = re.compile(r"^( *)(```+|~~~+)\s*([\w+-]*)\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
HRULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _cells(row):
    row = row.strip()
    row = row[1:] if row.startswith("|") else row
    row = row[:-1] if row.endswith("|") and not row.endswith("\\|") else row
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def render_blocks(lines, in_item=False):
    out, i, n = [], 0, len(lines)
    first_para = in_item  # the first paragraph of a list item is rendered without <p>
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith("<!--"):
            while i < n and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = FENCE.match(line)
        if m:
            ind, mark, lang = len(m.group(1)), m.group(2), m.group(3)
            body, i = [], i + 1
            while i < n and not lines[i].strip().startswith(mark):
                body.append(lines[i][min(ind, _indent(lines[i])):])
                i += 1
            i += 1
            code = "\n".join(body)
            out.append(render_dna_block(code) if lang == "dna" else highlight_code(code, lang))
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level, title = len(m.group(1)), m.group(2)
            out.append(f'<h{level} id="{slugify(re.sub(r"[`*]", "", title))}">{render_inline(title)}</h{level}>')
            i += 1
            continue
        if HRULE.match(line):
            out.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith(">"):
            body = []
            while i < n and lines[i].lstrip().startswith(">"):
                body.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{render_blocks(body)}</blockquote>")
            continue
        if "|" in line and i + 1 < n and TABLE_SEP.match(lines[i + 1]) and "-" in lines[i + 1]:
            head = _cells(line)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            th = "".join(f"<th>{render_inline(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        m = LIST_ITEM.match(line)
        if m:
            base = len(m.group(1))
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < n:
                m = LIST_ITEM.match(lines[i])
                if not m or len(m.group(1)) != base or m.group(2)[0].isdigit() != ordered:
                    break
                content_col = base + len(m.group(2)) + len(m.group(3))
                body = [m.group(4)]
                i += 1
                while i < n:
                    if not lines[i].strip():
                        j = i
                        while j < n and not lines[j].strip():
                            j += 1
                        if j < n and _indent(lines[j]) > base:
                            body.append("")
                            i = j
                            continue
                        break
                    if _indent(lines[i]) <= base:
                        break
                    body.append(lines[i][min(content_col, _indent(lines[i])):])
                    i += 1
                items.append(f"<li>{render_blocks(body, in_item=True)}</li>")
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue
        para = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not (
            FENCE.match(lines[i]) or LIST_ITEM.match(lines[i]) or re.match(r"^#{1,6}\s", lines[i])
            or lines[i].lstrip().startswith(">") or HRULE.match(lines[i])
        ):
            para.append(lines[i].strip())
            i += 1
        body = render_inline("\n".join(para))
        out.append(body if first_para else f"<p>{body}</p>")
        first_para = False
    return "\n".join(out)


def render_md(text):
    out = render_blocks(text.splitlines())
    # consecutive figures sit side by side
    out = re.sub(r'((?:<figure class="fig">.*?</figure>\s*)+)', r'<div class="figs">\1</div>', out, flags=re.S)
    out = re.sub(r'<p>\s*(<div class="figs">.*?</div>)\s*</p>', r"\1", out, flags=re.S)
    # citations of the course notes, and "not from the lecture notes" flags
    out = re.sub(r"<em>(\(?Notes[ ,]§)", r'<em class="cite">\1', out)
    out = re.sub(r"<(li|p)>(\s*⚠️)", r'<\1 class="flag">\2', out)
    return out


def split_sections(text, level):
    """Split markdown at headings of the given level. Returns [(title or None, body)]."""
    marker, parts, title, cur, fenced = "#" * level + " ", [], None, [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith(marker):
            parts.append((title, cur))
            title, cur = line[len(marker):].strip(), []
        else:
            cur.append(line)
    parts.append((title, cur))
    cleaned = []
    for title, body in parts:
        while body and (not body[-1].strip() or HRULE.match(body[-1])):
            body.pop()
        cleaned.append((title, "\n".join(body)))
    return cleaned


# ----------------------------------------------------------------------------- notebook

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SCORE_LINE = re.compile(r"(\d+) strands, (\d+) bases: density ([\d.]+), accuracy ([\d.]+), SCORE ([\d.]+)")


def cell_source(cell):
    src = cell.get("source", "")
    return src if isinstance(src, str) else "".join(src)


def _text(value):
    return value if isinstance(value, str) else "".join(value)


def export_figures(nb):
    """Save every PNG output to site/figures/ (never overwriting). Returns {(cell, k): (file, title)}."""
    FIGDIR.mkdir(exist_ok=True)
    figs = {}
    for ci, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        pngs = [o["data"]["image/png"] for o in cell.get("outputs", []) if "image/png" in o.get("data", {})]
        if not pngs:
            continue
        src = cell_source(cell)
        titles = re.findall(r"""title\(\s*f?["'](.+?)["']\s*\)""", src)
        first = next((l.strip("# ").strip() for l in src.splitlines() if l.strip()), f"cell {ci}")
        for k, b64 in enumerate(pngs):
            data = base64.b64decode(_text(b64))
            digest = hashlib.sha1(data).hexdigest()[:6]
            if len(titles) == len(pngs):
                title = titles[k]
                name = f"{slugify(title, 48)}-{digest}.png"
            else:
                title = f"{first[:60]} ({k + 1})"
                name = f"{slugify(first, 40)}-{k + 1}-{digest}.png"
            path = FIGDIR / name
            if not path.exists():
                path.write_bytes(data)
            figs[(ci, k)] = (name, title)
    return figs


def render_notebook(nb, figs):
    out = []
    for ci, cell in enumerate(nb["cells"]):
        src = cell_source(cell)
        if not src.strip():
            continue
        if cell["cell_type"] == "markdown":
            out.append(f'<div class="nb-md">{render_md(src)}</div>')
            continue
        if cell["cell_type"] != "code":
            continue
        count = cell.get("execution_count")
        first = next((l for l in src.splitlines() if l.strip()), "")
        parts, k = [], 0
        for o in cell.get("outputs", []):
            kind, data = o.get("output_type"), o.get("data", {})
            if kind == "stream":
                parts.append(f'<pre class="out">{esc(ANSI.sub("", _text(o.get("text", ""))))}</pre>')
            elif kind == "error":
                tb = ANSI.sub("", "\n".join(o.get("traceback", []))) or f'{o.get("ename")}: {o.get("evalue")}'
                parts.append(f'<pre class="out err">{esc(tb)}</pre>')
            elif "image/png" in data:
                name, title = figs[(ci, k)]
                k += 1
                embed = f"![{title}](site/figures/{name})"
                parts.append(
                    f'<figure class="fig nbfig"><a href="figures/{name}"><img src="figures/{name}" alt="{esc(title)}" '
                    f'loading="lazy"></a><figcaption><span>{esc(title)}</span>'
                    f'<button class="copy" data-copy="{esc(embed)}" title="Copy a Markdown line that embeds this '
                    f'figure in Project_notes.md">Copy embed</button></figcaption></figure>')
            elif "text/html" in data:
                parts.append(f'<div class="out-html">{_text(data["text/html"])}</div>')
            elif "text/plain" in data:
                parts.append(f'<pre class="out">{esc(_text(data["text/plain"]))}</pre>')
        label = f"In [{count}]" if count else "Not run"
        outputs = "".join(parts) if parts else '<p class="nb-empty">No saved output for this cell.</p>'
        out.append(
            f'<section class="nb-cell" id="cell-{ci}"><details class="code"><summary><span class="nb-count">{label}'
            f'</span><code>{esc(first[:110])}</code></summary>{highlight_code(src)}</details>'
            f'<div class="nb-out">{outputs}</div></section>')
    return "\n".join(out)


NB_OUTPUT = re.compile(r"^@notebook-output[ \t]+(\S+)[ \t]*$", flags=re.M)


def embed_notebook_outputs(body, nb):
    """Render a notes section, replacing each "@notebook-output <cell id>" line with that cell's saved HTML output."""
    by_id = {c.get("id"): c for c in nb["cells"]}
    chunks = []

    def stash(m):
        cell = by_id.get(m.group(1))
        html_parts = [_text(o["data"]["text/html"]) for o in (cell or {}).get("outputs", [])
                      if "text/html" in o.get("data", {})]
        if html_parts:
            chunks.append(f'<div class="out-html embed">{"".join(html_parts)}</div>')
        else:
            chunks.append(f'<p class="nb-empty">No saved HTML output in notebook cell <code>{esc(m.group(1))}</code>. '
                          'Run that cell and save the notebook.</p>')
        return f"\n\nNBOUTPUT{len(chunks) - 1}X\n\n"

    rendered = render_md(NB_OUTPUT.sub(stash, body))
    for i, chunk in enumerate(chunks):
        rendered = re.sub(rf"<p>\s*NBOUTPUT{i}X\s*</p>", lambda _m: chunk, rendered)
    return rendered


def latest_evaluation(nb):
    """The saved output of the notebook's evaluate(...) calls, as table rows."""
    for cell in nb["cells"]:
        src = cell_source(cell)
        if cell["cell_type"] != "code" or "def evaluate" not in src:
            continue
        text = "".join(_text(o.get("text", "")) for o in cell.get("outputs", []) if o.get("output_type") == "stream")
        runs = SCORE_LINE.findall(text)
        calls = re.findall(r"^evaluate\(\s*\w+\s*,\s*(.+?)\)\s*$", src, flags=re.M)
        if not runs:
            return ""
        rows = ""
        for i, (strands, bases, density, acc, score) in enumerate(runs):
            who = calls[i] if len(calls) == len(runs) else f"run {i + 1}"
            rows += (f"<tr><td><code>{esc(who)}</code></td><td>{strands}</td><td>{bases}</td><td>{density}</td>"
                     f"<td>{float(acc) * 100:.2f}%</td><td><strong>{score}</strong></td></tr>")
        return (
            '<section class="panel"><h2>Latest evaluation</h2>'
            '<div class="tw"><table class="num"><thead><tr><th>Channel</th><th>Strands</th><th>Bases</th>'
            f'<th>Density</th><th>Accuracy</th><th>Score</th></tr></thead><tbody>{rows}</tbody></table></div>'
            '<p class="fine">Saved output of the notebook\'s <code>evaluate</code> cell for the current '
            '<code>solution.py</code>, on the notebook\'s sample passage. ⚠️ <strong>Not from the lecture notes:'
            '</strong> the score, density × (1 − H(e)), is the project\'s own definition.</p></section>')
    return ""


# ----------------------------------------------------------------------------- pages

STEP_TITLE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*[·:|-]\s*(.*)$")

RELOAD_JS = """
document.addEventListener('click', function (e) {
  var b = e.target.closest('button.copy');
  if (!b) return;
  navigator.clipboard.writeText(b.dataset.copy).then(function () {
    var old = b.textContent; b.textContent = 'Copied'; setTimeout(function () { b.textContent = old; }, 1200);
  });
});
if (location.protocol.indexOf('http') === 0) {
  var key = 'scroll:' + location.pathname, seen = null;
  try { var y = sessionStorage.getItem(key); if (y) { scrollTo(0, +y); sessionStorage.removeItem(key); } } catch (e) {}
  setInterval(function () {
    fetch('/__version', {cache: 'no-store'}).then(function (r) { return r.ok ? r.text() : null; }).then(function (v) {
      if (v === null) return;
      if (seen !== null && v !== seen) {
        try { sessionStorage.setItem(key, String(scrollY)); } catch (e) {}
        location.reload();
      }
      seen = v;
    }).catch(function () {});
  }, 1200);
}
"""


def page(title, site_title, nav, active, body, subnav=()):
    links = []
    for href, label in nav:
        cur = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
        if href == active and subnav:
            subs = "".join(f'<a href="#{a}">{l}</a>' for a, l in subnav)
            links.append(f'<div class="subnav">{subs}</div>')
    built = datetime.datetime.now().strftime("%b %-d, %H:%M:%S")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(site_title)}</title>
<link rel="stylesheet" href="style.css">
<style>{pygments_css()}</style>
</head>
<body>
<aside class="side">
  <a class="brand" href="index.html"><span class="helix" aria-hidden="true"><i class="b-A">A</i><i class="b-C">C</i><i class="b-G">G</i><i class="b-T">T</i></span>{esc(site_title)}</a>
  <nav>{''.join(links)}</nav>
  <p class="built">Built {built}<br>from Project_notes.md and the notebook</p>
</aside>
<main>
{body}
</main>
<script>{RELOAD_JS}</script>
</body>
</html>
"""


def plain(markup):
    return re.sub(r"<[^>]+>", "", markup)


def build():
    notes = NOTES.read_text(encoding="utf-8")
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    figs = export_figures(nb)

    sections = split_sections(notes, 2)
    preamble = sections[0][1]
    m = re.search(r"^# (.+)$", preamble, flags=re.M)
    doc_title = m.group(1).strip() if m else "Project notes"
    site_title = doc_title.split(":")[-1].strip() if ":" in doc_title else doc_title
    intro = render_md(re.sub(r"^# .+$", "", preamble, count=1, flags=re.M))

    findings, others = None, []
    for title, body in sections[1:]:
        clean = re.sub(r"^\d+\.\s*", "", title)
        if "findings log" in clean.lower():
            findings = body
        else:
            others.append((clean, slugify(clean) + ".html", body))

    nav = [("index.html", "Findings")] + [(href, esc(t)) for t, href, _ in others] + [("notebook.html", "Lab notebook")]
    written = []

    def write(name, markup):
        (SITE / name).write_text(markup, encoding="utf-8")
        written.append(name)

    # Findings timeline
    steps = [(t, b) for t, b in split_sections(findings or "", 3) if t]
    cards, subnav = [], []
    for num, (raw, body) in enumerate(steps, 1):
        date, kicker, title = "", "", raw
        m = STEP_TITLE.match(raw)
        if m:
            date, title = m.group(1), m.group(2)
        if ": " in title and len(title.split(": ", 1)[0]) <= 40:
            kicker, title = title.split(": ", 1)
        try:
            shown = datetime.date.fromisoformat(date).strftime("%b %-d, %Y") if date else ""
        except ValueError:
            shown = date
        meta = " · ".join(x for x in (shown, esc(kicker)) if x)
        title_html = render_inline(title)
        subnav.append((f"step-{num}", f"{num}. {plain(title_html)}"))
        cards.append(
            f'<article class="step" id="step-{num}"><div class="step-num">{num}</div>'
            f'<header><p class="step-meta">{meta}</p><h2>{title_html}</h2></header>'
            f'<div class="prose">{render_md(body)}</div></article>')
    if not cards:
        cards.append('<p class="nb-empty">No findings yet. Add a "### YYYY-MM-DD · title" entry to the '
                     'Findings log in Project_notes.md.</p>')
    count = f"{len(steps)} step{'s' if len(steps) != 1 else ''} so far"
    home = (
        f'<header class="hero"><p class="eyebrow">ENGS 27 final project · findings log</p><h1>{esc(doc_title)}</h1>'
        f'<div class="prose intro">{intro}</div></header>'
        f'{latest_evaluation(nb)}'
        f'<div class="timeline-head"><h2>Step by step</h2><span>{count}</span></div>'
        f'<div class="timeline">{"".join(cards)}</div>')
    write("index.html", page("Findings", site_title, nav, "index.html", home, subnav))

    # One page per other section of the notes
    for title, href, body in others:
        rendered = embed_notebook_outputs(body, nb)
        sub = [(a, plain(l)) for a, l in re.findall(r'<h3 id="([^"]+)">(.*?)</h3>', rendered)]
        content = (f'<header class="hero"><p class="eyebrow">Project notes</p><h1>{esc(title)}</h1></header>'
                   f'<div class="prose">{rendered}</div>')
        write(href, page(title, site_title, nav, href, content, sub))

    # The notebook, cell by cell
    content = (
        '<header class="hero"><p class="eyebrow">Lab notebook</p><h1>Notebook cells and saved outputs</h1>'
        f'<p class="lede">Read from <code>{esc(NOTEBOOK.name)}</code> as last saved. Every plot is also saved to '
        '<code>site/figures/</code>; use <em>Copy embed</em> to paste it into a finding.</p></header>'
        f'{render_notebook(nb, figs)}')
    write("notebook.html", page("Lab notebook", site_title, nav, "notebook.html", content))

    missing = sorted({s for s in re.findall(r"!\[[^\]]*\]\((site/[^)]+)\)", notes) if "<" not in s and not (ROOT / s).exists()})
    for s in missing:
        print(f"  warning: Project_notes.md embeds a missing image: {s}")
    return written


if __name__ == "__main__":
    pages = build()
    print(f"built {len(pages)} pages in {SITE}: {', '.join(pages)}")
