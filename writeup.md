# Storing Text in DNA: Channel, Design and Evidence

*ENGS 27 Final Project · Helin Wang · final solution: v11. Citations refer to the course notes by section and page. A dagger (†) marks a method or fact that is not from the lecture notes.*

## 1. What we learned about the channel

We tested about 4,500 distinct strands on the live server. Four findings shaped the design.

**Breaks depend on the two bases before a junction.** We recorded 913,300 breaks from 2,892 surviving strands and tabulated each one by the bases around it. A junction right after **CC** or **GG** breaks with probability about **0.42**, while a junction after any of the other 14 base pairs breaks with probability only about **0.011**. That is roughly a 38-fold difference. Neither the third base back nor the two bases after the junction changed these rates. A test on long G and C runs showed that neighbouring hot junctions break independently. So each junction behaves like an independent Bernoulli trial, and between hot sites the distance to the next break is geometric *(§2.4.1, p. 33; §2.4.2, p. 34)*.

**Some strands are deleted outright, deterministically.** About **2.9%** of random strands (74 of 2,584) never return a single read. This is a fixed property of the sequence, not bad luck. The 17 lost strands we retested returned 0 reads in 255 of 255 requests, while 30 survivors returned reads in 450 of 450. The deletion rule looks like a hash of the whole strand†. One base changed almost anywhere in a deleted strand (295 of 300 single-base edits) brings it back, and no content feature we checked (composition, motifs, length, reverse complement) predicts deletion. A design cannot avoid deletion, only survive it.

**Reads carry substitution errors.** Our first full design (v5) failed live with only 47% accuracy even though no strand was lost. Diagnosis showed about **0.5% substitutions per base**, spread evenly along the strand, with no insertions or deletions. At that rate only about $0.995^{300} \approx 22\%$ of whole 300-base reads are error-free (we saw 12 of 84). So no single read can be trusted.

**Strands don't interact.** A strand's read lengths and start positions were the same whether it was sent alone, in a batch of 20, or among 500 others. Read counts per surviving strand also look binomial with equal picking probability *(§2.4.1, p. 33)*. So each strand could be designed and analysed on its own.

## 2. How the design responds

The final encoder, v11, has three layers. Compression shrinks the text, a constrained code writes it as bases the channel treats gently, and redundancy across reads and across strands repairs what the channel still damages.

**Compression.** English is far from random, and a character is much easier to predict once the previous two are known. We model the text as a Markov chain whose state is the last two characters *(§6.2.1, pp. 101–102)*, and give every pair its own Huffman code *(§3.2.5, p. 54)*. The codes are built from character counts in 7 public-domain books†. A character that a pair's table has never seen is sent as an escape, then coded by the previous character alone. If that fails it is coded by a single table, and as a last resort by its UTF-8 bytes†, so any input text can be encoded. On a held-out book this costs **2.99 bits per character**, against 4.43 for a single Huffman table. This is the drop from entropy to conditional entropy that the notes predict for a source with memory *(§3.1.4, p. 47; Remark 3.2.7, p. 56)*.

**Writing bases.** Because breaks concentrate after CC and GG, the encoder never writes either pair. Counting the strings without CC or GG gives a limit of 1.8325 bits per base *(§6.1.4, p. 99)*. We reach **1.820** by ranking† each group of bits to an allowed 28-base block, with each block's ranking conditioned on the base before it so the joins are safe too. Every junction is then a cold one, with only about a 1% chance of breaking, so a 300-base strand still comes back whole in about 4.7% of reads. Each strand holds a 12-bit index and a count of its data bits. The bits are scrambled with a pattern seeded by the index, so repeated text never produces identical strands. The last strand is trimmed to the fewest bases that hold its bits†, so short passages don't pay for padding.

**Repairing reads.** The decoder keeps the full-length reads, groups them by Hamming distance and takes a majority vote at every position *(§3.3.2, pp. 58–59)*. With roughly 30 whole reads per strand at 4 reads per character, a 0.5% error rate is outvoted easily.

**Surviving deletion.** A deleted strand is lost on every run, so for each passage the encoder may add parity strands across the data strands. The options are none, one XOR strand, or a shortened or extended Hamming code *(§3.3.3–3.3.4, p. 59; Remark 3.3.5, p. 61)*. The decoder treats deleted strands as erasures at known positions and solves the parity checks for them†. Parity costs density on every run, so the encoder chooses the option with the highest expected score. It models the number of deleted strands as Binomial(strands, 0.029) *(§2.4.1, p. 33)*. In practice short passages get no parity and longer ones get one or more parity strands.

## 3. Evidence

All scores below are live-channel runs at 4 reads per character. The score is density × (1 − H(e))†, where H is the binary entropy *(§3.1.3, p. 46)*.

| Passage (chars) | v0 baseline | v6 (Huffman, no CC/GG, vote) | v10 (+ parity, trimming) | **v11 (+ order-2 context)** |
|---|---|---|---|---|
| short 1 (69) | — | 1.840 | 2.952 | **3.887** |
| short 2 (170) | — | 2.267 | 3.002 | **3.853** |
| SAMPLE (446) | 0.866 | 2.973 | 0.824 (1 strand deleted) | **4.482** |
| long 1 (742) | — | 2.827 | 3.095 | **4.374** |
| long 2 (1,814) | — | 1.446 (2 deleted) | 1.307 (2 deleted) | **4.002** |
| Mean of five | — | 2.270 | 2.236 | **4.120** |

Each version answered a specific measured failure. The baseline wrote 8 bits per character on short strands and lost 2 of its 113 strands to deletion. v5 failed on substitution errors. v6 fixed that with position-wise voting and decoded `SAMPLE` exactly, more than tripling the baseline's score. v6 still lost two deleted strands of `long 2` on every run, which motivated parity. v10 removed padding and enlarged the blocks, raising density on every passage. But its new sequences happened to hit three deleted strands, which shows how much a single deletion can cost. v11's context coding raised density by 30–42% on every passage, matching the offline projection, and **all five passages decoded exactly**. The mean rose from 2.24 to 4.12.

Part of v11's live result is luck: none of its strands for these passages was lost beyond what parity could rebuild. Averaged over deletions we can't predict, its expected mean is **3.88**. We also measured a pruned order-3 model, which would add about 10% density but more than double the size of the code table. We kept v11, whose tables are smaller and have been tested end to end on the live channel. The main remaining risks are deletion and text that differs from the training books, such as names, numbers and technical vocabulary. Unseen characters cost escapes there, but they still decode correctly.
