import collections

INDEX, PAYLOAD = 6, 4          # bases of index, bytes of payload per strand
BASES = "ACGT"

def _to_bases(data):
    return "".join(BASES[(byte >> s) & 3] for byte in data for s in (6, 4, 2, 0))

def _to_bytes(bases):
    vals = [BASES.index(c) for c in bases]
    return bytes(vals[i] << 6 | vals[i + 1] << 4 | vals[i + 2] << 2 | vals[i + 3] for i in range(0, len(vals), 4))

def _index(i):
    return "".join(BASES[(i >> (2 * s)) & 3] for s in reversed(range(INDEX)))

def encode(text):
    data = text.encode("utf-8")
    data = len(data).to_bytes(4, "big") + data
    data += bytes(-len(data) % PAYLOAD)
    return [_index(i) + _to_bases(data[p:p + PAYLOAD])
            for i, p in enumerate(range(0, len(data), PAYLOAD))]

def decode(reads):
    full = INDEX + 4 * PAYLOAD
    votes = collections.defaultdict(collections.Counter)
    for r in reads:
        if len(r) == full:
            i = int("".join(str(BASES.index(c)) for c in r[:INDEX]), 4)
            votes[i][r[INDEX:]] += 1
    if not votes:
        return ""
    chunks = [_to_bytes(votes[i].most_common(1)[0][0]) if votes[i] else bytes(PAYLOAD)
              for i in range(max(votes) + 1)]
    data = b"".join(chunks)
    n = int.from_bytes(data[:4], "big")
    return data[4:4 + n].decode("utf-8", errors="replace")
