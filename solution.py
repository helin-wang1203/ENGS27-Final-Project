import collections
import heapq
import random

STRAND = 300        # bases per strand
BLOCK = 14          # bases per ranked block; a strand is 21 blocks of 14 plus one of 6
INDEX_BITS = 12     # strand number: data strands 0, 1, 2, ...; the top value marks the parity strand
LENGTH_BITS = 10    # how many data bits this strand holds (the rest is padding)
NEXT = {"A": "ACGT", "C": "AGT", "G": "ACT", "T": "ACGT"}   # allowed next base: never CC or GG
START = "A"         # stands in for the base before a strand's first base (allows all four)

# English character counts from 5,031,639 characters of 7 public-domain books
# (see the char-freq cell; saved in english_char_freq.json).
FREQ = {
    ' ': 831681, 'e': 507095, 't': 350899, 'a': 309919, 'o': 287961, 'n': 272640, 'i': 260155,
    's': 254029, 'r': 236246, 'h': 229505, 'l': 160461, 'd': 155936, 'c': 106679, 'u': 106486,
    'm': 94384, 'f': 93341, '\n': 89078, 'w': 81362, 'y': 73787, 'g': 72144, ',': 67099,
    'p': 65662, 'b': 59431, 'v': 42653, '.': 40638, 'k': 23583, 'I': 20228, 'T': 9378, '-': 9247,
    ';': 7535, 'x': 7174, 'A': 5863, 'M': 5629, 'S': 5215, '“': 5056, 'H': 4966, '”': 4584,
    'W': 4265, 'q': 4264, 'B': 4162, 'E': 3668, 'C': 3659, 'j': 3046, 'z': 2787, 'L': 2753,
    'O': 2669, 'N': 2581, '’': 2333, '"': 2284, 'P': 2213, 'F': 2061, 'D': 2052, '?': 2025,
    "'": 1965, 'R': 1857, ':': 1807, '1': 1760, 'G': 1701, '!': 1329, 'Y': 1289, '0': 1140,
    '2': 1053, '—': 1024, '8': 1005, 'J': 962, '3': 958, 'K': 840, '4': 791, ')': 766, '(': 765,
    'V': 674, '9': 636, '[': 614, ']': 614, '5': 601, '7': 534, '6': 499, 'U': 496, '‘': 468,
    'æ': 208, 'X': 200, 'Z': 113, 'Q': 85, '*': 42, '£': 37, 'ä': 33, '/': 25, 'ö': 22, '&': 22,
    'é': 21, '$': 21, '°': 18, '½': 15, 'œ': 14, 'ê': 8, 'à': 6, '¾': 6, 'Æ': 6, '–': 5, '^': 5,
    'ü': 4, 'â': 4, '{': 4, '}': 4, 'î': 3, 'ß': 2, '·': 2, 'ë': 1, '>': 1, '+': 1, '=': 1, 'è': 1,
}

def _huffman(freq):
    """Huffman's algorithm (Notes §3.2.5, p. 54): repeatedly merge the two lightest groups.
    A tree is a character (leaf) or a pair (left, right). Ties are broken by the order groups
    were made, so encode and decode always build the same tree. Returns {char: "0101..."}."""
    heap = [(count, order, ch) for order, (ch, count) in enumerate(freq.items())]
    heapq.heapify(heap)
    order = len(heap)
    while len(heap) > 1:
        w1, _, a = heapq.heappop(heap)
        w2, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, order, (a, b)))
        order += 1
    code, stack = {}, [(heap[0][2], "")]
    while stack:                      # walk the tree: left adds "0", right adds "1"
        node, path = stack.pop()
        if isinstance(node, tuple):
            stack += [(node[0], path + "0"), (node[1], path + "1")]
        else:
            code[node] = path
    return code

ESC = "<ESC>"     # extra symbol: "the next character isn't in FREQ; its UTF-8 bytes follow"
HUFFMAN = _huffman({**FREQ, ESC: 1})                  # char -> codeword (bits as "0"/"1")
HUFFMAN_INV = {bits: ch for ch, bits in HUFFMAN.items()}  # codeword -> char, for decoding

def char_to_bits(text):
    """The whole compression step: text -> one string of "0"/"1" bits.
    Each character becomes its Huffman codeword. A character not in FREQ becomes the ESC
    codeword followed by its UTF-8 bytes, 8 bits each (UTF-8's first byte says how many bytes
    follow, so the decoder knows where the character ends)."""
    out = []
    for ch in text:
        if ch in HUFFMAN:
            out.append(HUFFMAN[ch])
        else:
            out.append(HUFFMAN[ESC] + "".join(f"{b:08b}" for b in ch.encode("utf-8")))
    return "".join(out)

def bits_to_char(bits):
    """Undo char_to_bits: a string of "0"/"1" bits -> text.
    Reads bits until they match a codeword; the code is prefix-free, so the first match is the
    right one (Notes §3.2.3, p. 52). After ESC, reads one UTF-8 character: its first byte says
    how many bytes it has. Leftover bits at the end that don't finish a codeword are ignored,
    and damaged UTF-8 becomes "\ufffd" instead of crashing. It can't tell padding from data:
    padding that happens to spell a codeword decodes as extra characters, so pass only the real
    bits (the caller must know where they end)."""
    out, cur, i = [], "", 0
    while i < len(bits):
        cur += bits[i]
        i += 1
        if cur not in HUFFMAN_INV:
            continue
        sym, cur = HUFFMAN_INV[cur], ""
        if sym != ESC:
            out.append(sym)
            continue
        if i + 8 > len(bits):
            break
        first = int(bits[i:i + 8], 2)
        n = 1 if first < 0x80 else 2 if first < 0xE0 else 3 if first < 0xF0 else 4
        raw = bytes(int(bits[j:j + 8], 2) for j in range(i, min(i + 8 * n, len(bits) - 7), 8))
        out.append(raw.decode("utf-8", errors="replace"))
        i += 8 * n
    return "".join(out)

# ---- bits <-> bases with no CC or GG anywhere ------------------------------------------------
# WAYS[n][p] = number of n-base strings with no CC or GG that can follow base p. Counted one base
# at a time, as in Notes §6.1.4 (p. 99): WAYS[n][p] = sum of WAYS[n-1][b] over allowed next b.
WAYS = [{p: 1 for p in NEXT}]
for _n in range(1, BLOCK + 1):
    WAYS.append({p: sum(WAYS[_n - 1][b] for b in NEXT[p]) for p in NEXT})

def _block_bits(n):
    """Bits an n-base block can always hold, whatever base comes before it."""
    return min(WAYS[n].values()).bit_length() - 1

BLOCK_SIZES = [BLOCK] * (STRAND // BLOCK) + ([STRAND % BLOCK] if STRAND % BLOCK else [])
STRAND_BITS = sum(_block_bits(n) for n in BLOCK_SIZES)
DATA_BITS = STRAND_BITS - INDEX_BITS - LENGTH_BITS
assert DATA_BITS < 2 ** LENGTH_BITS
PARITY = 2 ** INDEX_BITS - 1       # index of the parity strand (4095), never used for data

def _unrank(v, prev, n):
    """Number v -> the v-th allowed n-base string after base prev (A < C < G < T order)."""
    out = []
    for left in range(n - 1, -1, -1):
        for b in NEXT[prev]:
            if v < WAYS[left][b]:
                out.append(b)
                prev = b
                break
            v -= WAYS[left][b]
    return "".join(out)

def _rank(seq, prev):
    """Undo _unrank: add up the sizes of the groups skipped at each position."""
    v = 0
    for i, c in enumerate(seq):
        if c not in NEXT[prev]:
            raise ValueError("CC or GG, or not a base")
        for b in NEXT[prev]:
            if b == c:
                break
            v += WAYS[len(seq) - i - 1][b]
        prev = c
    return v

def bits_to_bases(bits):
    """STRAND_BITS bits -> one STRAND-base strand with no CC or GG. Each block is ranked after
    the last base of the block before it, so the joins are safe too."""
    out, prev, i = [], START, 0
    for n in BLOCK_SIZES:
        k = _block_bits(n)
        block = _unrank(int(bits[i:i + k], 2), prev, n)
        out.append(block)
        prev, i = block[-1], i + k
    return "".join(out)

def bases_to_bits(seq):
    """Undo bits_to_bases. Raises ValueError if seq can't be a strand (wrong length, CC or GG,
    or a block number too big for its bits)."""
    if len(seq) != STRAND:
        raise ValueError("wrong length")
    out, prev, i = [], START, 0
    for n in BLOCK_SIZES:
        k = _block_bits(n)
        v = _rank(seq[i:i + n], prev)
        if v >= 2 ** k:
            raise ValueError("block number out of range")
        out.append(format(v, f"0{k}b"))
        prev, i = seq[i + n - 1], i + n
    return "".join(out)

# ---- strands ---------------------------------------------------------------------------------
# A strand's bits: [index: INDEX_BITS][count of data bits: LENGTH_BITS][data][zero padding].
# Characters are never split across strands, so each strand decodes on its own and a lost
# strand costs only its own characters. Everything after the index is scrambled with a pattern
# seeded by the index, so two strands never look alike even if their data is the same
# (repeated text); otherwise decode's grouping could merge them.
#
# One extra PARITY strand, whatever the text's length: its bits after the index are the XOR,
# column by column, of every data strand's bits after the index (before scrambling). So every
# column has even parity (Notes §3.3.3 Parity Checks, p. 59). If one strand is deleted, the
# decoder knows which index is missing, and XOR-ing everything that came back rebuilds it.

def _scramble(bits, i):
    """XOR bits with a fixed pseudo-random pattern chosen by strand index i. Doing it twice
    gives back the original bits, so the same function also unscrambles."""
    key = random.Random(i).getrandbits(len(bits))
    return format(int(bits, 2) ^ key, f"0{len(bits)}b")

def encode(text):
    chunks, cur = [], ""
    for ch in text:
        code = char_to_bits(ch)
        if len(cur) + len(code) > DATA_BITS:
            chunks.append(cur)
            cur = ""
        cur += code
    chunks.append(cur)
    if len(chunks) > PARITY:
        raise ValueError("text too long for INDEX_BITS")
    strands, parity = [], 0
    for i, data in enumerate(chunks):
        rest = (format(len(data), f"0{LENGTH_BITS}b") + data).ljust(STRAND_BITS - INDEX_BITS, "0")
        parity ^= int(rest, 2)                            # running XOR of every data strand
        strands.append(bits_to_bases(format(i, f"0{INDEX_BITS}b") + _scramble(rest, i)))
    rest = format(parity, f"0{STRAND_BITS - INDEX_BITS}b")
    strands.append(bits_to_bases(format(PARITY, f"0{INDEX_BITS}b") + _scramble(rest, PARITY)))
    return strands

def _rebuild(best):
    """If exactly one data strand is missing and the parity strand came back, put the missing
    strand back into best (index -> (copies, unscrambled bits)). XOR of the parity strand and
    every data strand that came back equals the missing strand; all zeros means none is missing.
    The missing index is the one gap in 0, 1, 2, ...; with no gap, it's the one after the last."""
    if PARITY not in best:
        return
    x = int(best.pop(PARITY)[1], 2)
    for _, rest in best.values():
        x ^= int(rest, 2)
    if x == 0:
        return                                            # nothing missing
    top = max(best, default=-1)
    gaps = [i for i in range(top + 1) if i not in best]
    if len(gaps) > 1:
        return                                            # two or more lost: parity can't help
    rest = format(x, f"0{STRAND_BITS - INDEX_BITS}b")
    if int(rest[:LENGTH_BITS], 2) <= DATA_BITS:           # a sane count, so trust the rebuild
        best[gaps[0] if gaps else top + 1] = (0, rest)

def _within(a, b, limit):
    """True if a and b differ in at most `limit` positions (Hamming distance, Notes §3.3.2, p. 58)."""
    d = 0
    for x, y in zip(a, b):
        if x != y:
            d += 1
            if d > limit:
                return False
    return True

def _groups(reads, limit):
    """Group same-length reads so each group holds the copies of one strand. A read joins the
    first group whose first read it is within `limit` of. Copies of one strand differ in a few
    positions (substitution errors, about 0.5% per base on the live channel); different strands
    differ in most positions, so a loose limit still separates them."""
    groups = []
    for r in reads:
        for g in groups:
            if _within(r, g[0], limit):
                g.append(r)
                break
        else:
            groups.append([r])
    return groups

def _consensus(group):
    """Majority vote at every position (Notes §3.3.2, p. 59)."""
    return "".join(collections.Counter(col).most_common(1)[0][0] for col in zip(*group))

def decode(reads):
    full = [r for r in reads if len(r) == STRAND]          # only whole strands are used
    best = {}                                             # strand index -> (copies, bits)
    for g in _groups(full, STRAND // 10):
        try:
            bits = bases_to_bits(_consensus(g))
        except ValueError:                                # consensus isn't a valid strand
            continue
        i = int(bits[:INDEX_BITS], 2)
        if i not in best or len(g) > best[i][0]:          # two groups claim one index: keep the bigger
            best[i] = (len(g), _scramble(bits[INDEX_BITS:], i))
    _rebuild(best)                                        # one lost strand: rebuild it from parity
    out = []
    for i in sorted(best):                                # a strand that never came back is skipped
        rest = best[i][1]                                 # unscrambled: [count][data][padding]
        n = int(rest[:LENGTH_BITS], 2)
        out.append(bits_to_char(rest[LENGTH_BITS:LENGTH_BITS + n]))
    return "".join(out)
