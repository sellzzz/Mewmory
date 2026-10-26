# Kitten-01 design

## Scope and data flow

Caller-authored structured event → SQLite append → on-demand aggregation →
keyword-ranked bounded JSON → original event lookup.

The optional [instinct controller](INSTINCT.md) also generates explicitly
synthetic events from needs, sensed cues and environment feedback. Its fixed
policy operates independently of retrieved memory; policy learning is future work.

The event table holds an integer ID, UTC timestamp, actor, place, cue, outcome,
and raw text. IDs are local to one database. No external model or service is
required. Parameterized SQL keeps event text separate from executable queries.
Nonempty labels and timezone-aware supplied dates are validated before writes.

## Abstraction and provenance

For each exact actor/place/cue tuple, count each outcome; emit outcomes with
support >= 2 by default. The denominator includes every event in that tuple,
including conflicting outcomes below the support threshold. Full source ID
lists are derived from raw events, so no stale materialized rules need syncing.
All conclusions are associations in supplied labels, not causal explanations.
Missing observations, biased input and label synonyms can distort frequencies.

Recall tokenizes Latin words and individual CJK characters, counts unique query
overlaps, orders by score then rule preference then first evidence ID. It caps
items and JSON characters; a bounded excerpt of evidence IDs keeps provenance
from growing without bound. Full evidence is available in `rules`; `trace`
fails explicitly on unknown IDs. Events already represented by selected evidence
IDs are suppressed. Related events may still appear when evidence was truncated.

## Limits and tradeoffs

This is a tiny-data baseline. Rules and recall scan the full database in memory:
bounded output context does not mean bounded compute or storage. No embeddings,
semantic similarity, automatic label extraction, decay, encryption, concurrent
write orchestration, deduplication or event-level deletion is implemented.
Character budgets are portable but cannot enforce model-specific token budgets.
Repeated demo imports intentionally append; demo validation avoids malformed
input partial imports but is not an atomic bulk-write guarantee on disk failure.
No empirical claim about real feline cognition is made.

## Evaluation plan (not yet measured)

Construct fictional training episodes and separate held-out cue queries with
expected evidence IDs. Include paraphrases, novel cues, conflicting outcomes,
changed routines and long event text. Freeze data splits before evaluation.
Compare full history, this keyword baseline, and an embedding baseline using
identical datasets and output budgets. Report relevance/recall at k, source-ID
accuracy and coverage, contradictions retained, abstention, tokenizer-specific
input tokens, latency and database size. Any model-assisted evaluation must
record model/version and keep raw data local unless explicitly opted in.

Unit tests establish implementation behavior, not scientific validity or
retrieval superiority. Future model and MCP adapters should consume bounded
recall output without gaining default access to the entire event store.
