# beacon

`beacon` is a study of the machinery that sits underneath DNS-based
service discovery, written as a single Python package that you can read
end to end. Service discovery looks simple from the outside: a name goes
in, an address comes out. Underneath that promise is a dense layer of
protocol detail, load balancing, failure detection, caching, consensus,
sketching, and plain algorithms, and each of those is a small world with
its own tradeoffs. This package builds those worlds one module at a
time, in isolation, so that each idea can be read, tested, and reasoned
about on its own rather than buried inside a running resolver.

The package is deliberately not a framework. Nothing here binds to a
socket or ships a daemon. Every module is a self-contained piece of
logic with a clear surface, a docstring that argues for a design and
names its honest cost, and a test file that pins the behavior down,
including the behavior at the edges where the idea stops working.

## What is inside

The `beacon` package holds a little over three hundred and eighty
modules, grouped by the problem each one addresses:

- **DNS protocol.** Happy eyeballs, EDNS and client subnet, DNS64, RPZ,
  DNSSEC with NSEC and NSEC3 and aggressive use, CDS and CDNSKEY, CAA,
  TLSA, SSHFP, DNAME, zone cuts, and ZONEMD, among others.
- **Load balancing and placement.** Maglev hashing, rendezvous and
  weighted rendezvous, jump hashing, power of two choices, weighted
  least request, bounded-load consistent hashing, and locality hashing.
- **Consensus and coordination.** Raft vote, prevote, log matching,
  commit index, read index, joint consensus, and leader transfer, plus
  Lamport and Ricart-Agrawala mutual exclusion, bully and ring election,
  epoch fencing, two-phase commit, and saga.
- **Conflict-free replicated data types.** Grow-only and PN counters,
  OR-set, G-set, 2P-set, last-writer-wins register and map, multi-value
  register, and delta propagation.
- **Caching and eviction.** LRU, LFU, 2Q, CLOCK, SIEVE, and ARC.
- **Rate limiting.** Token bucket, leaky bucket, GCRA, sliding window
  and sliding log, bucketed counters, hierarchical and distributed
  limiters.
- **Networking.** Congestion window control, Nagle, SACK, Go-Back-N,
  selective repeat, retransmission timeout with Karn's rule, fast
  retransmit, pacing, ECN, window scaling, the bandwidth-delay product,
  TCP state handling, silly window avoidance, flow hashing, and the
  Internet checksum.
- **Probabilistic and streaming structures.** Bloom and counting Bloom
  filters, cuckoo filters, count-min sketch, HyperLogLog, space-saving,
  Morris counters, and reservoir sampling with weights.
- **Data structures.** Fenwick trees, segment trees, prefix sums, tries,
  radix trees, BK-trees, skip lists, binary heaps, union-find, bitsets,
  ring buffers, sliding maxima, and monotonic stacks.
- **Graph and string algorithms.** Dijkstra, Prim, Kruskal, Bellman-Ford,
  Floyd-Warshall, Tarjan's strongly connected components, BFS, bipartite
  checking, connected components, transitive closure, topological sort,
  KMP, Rabin-Karp, Boyer-Moore, Aho-Corasick, the Z-algorithm, Manacher,
  Kadane, Levenshtein, quickselect, and Eulerian paths.
- **Numeric and coding.** Modular exponentiation and inverse, the
  Chinese Remainder Theorem, prime sieving, Miller-Rabin, binary GCD,
  Huffman and LZW, the Burrows-Wheeler and move-to-front transforms,
  Elias gamma, Gray code, Hamming codes, base32, varint, zigzag,
  run-length, Fletcher and CRC-32, Kahan summation, Welford's method,
  and IPv6 canonicalization.
- **Scheduling.** Stride, lottery, completely fair scheduling, earliest
  deadline first, rate-monotonic, multilevel feedback, and deficit round
  robin.

## Drills

A drill is a scripted scenario that asserts a single, quantitative claim
about one of these mechanisms and then checks that the claim still
holds. The drills live in `beacon/drills` and are surfaced through the
command line. They are the package's way of stating, in one sentence
each, what a piece of infrastructure actually buys you, with the numbers
attached.

```bash
python -m beacon.cli drills
python -m beacon.cli check
python -m beacon.cli summary
```

`drills` prints each claim and whether it holds, `check` reports whether
any drill is broken, and `summary` gives the count.

## Examples

The `examples` directory holds worked narratives, each a short "day in
the life" that walks one idea from a plausible question to a measured
answer, and often to an honest refusal when the intuitive answer turns
out to be wrong. They are run and checked as tests, so the numbers in
them cannot drift out of date.

## The voice

Two habits run through the whole package. The first is that every module
docstring makes a claim about why its design is the right one and then
states, in the same breath, what the design costs, because a technique
described only by its strengths is a technique you will misuse. The
second is honest measurement: where a first guess was refuted by a test,
the wrong guess stays written down next to the measured truth rather
than being quietly erased, because the correction is often more
instructive than the fact. Several modules carry a guess that a
benchmark overturned, kept on purpose.

## Testing

The suite covers every module.

```bash
python -m pytest tests/ -q
```

At the time of writing the package is a little over thirty thousand
lines of code counted strictly, meaning code alone with docstrings,
comments, and blank lines excluded, and the suite runs just under two
and a half thousand tests, all passing. Linting is clean under `ruff`.

```bash
python -m ruff check .
```

## Layout

```
beacon/          the modules, one idea each
beacon/drills/   scripted claims with numbers, and the CLI behind them
examples/        worked day-in-the-life narratives, run as tests
tests/           one test file per module
```

## License

This is a learning repository. Read it, run it, take the pieces that are
useful, and check the numbers for yourself.
