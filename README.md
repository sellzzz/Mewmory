# Mewmory · 喵忆

Local-first, model-independent, traceable long-term personal memory research.
本地优先、模型无关、可追溯的长期个人记忆系统实验。

**Kitten-01** explores a small loop from a fictional cat's perspective:
save raw experiences → summarize repeated associations → recall a few relevant
memories → trace original events. Runtime uses Python's standard library only;
there are no model calls, telemetry, credentials, or network requests.

第一阶段以虚构小猫 Pip 的视角理解主人与环境：保存原始经历、统计关联规律、
按线索召回少量记忆，并通过事件 ID 回查证据。它是可运行的工程基线，
还不是完整的个人记忆产品。

## Run / 运行

Requires Python 3.10+. From this repository directory, no installation is needed:

```sh
python -m mewmory --db data/kitten.db demo
python -m mewmory --db data/kitten.db rules
python -m mewmory --db data/kitten.db recall "can opening" --limit 3 --max-chars 1200
python -m mewmory --db data/kitten.db trace 1 2
python -m mewmory --db data/kitten.db events
python -m unittest discover -s tests -v
```

The demo adds six entirely fictional events. Run it once per fresh database;
repeating it appends duplicates and changes statistics. `--db` goes before the
subcommand. Optional installation: `python -m pip install .` enables `mewmory`.
Installation may download the build dependency setuptools; direct module use does not.

```sh
python -m mewmory --db data/kitten.db add --actor Mira --place kitchen --cue "can opening" --outcome food --text "Fictional Pip receives dinner."
```

`add` accepts an optional timezone-aware ISO 8601 `--occurred-at`; otherwise it
records the current UTC time. SQLite retains the full event text.

## Instinct experiment / 本能实验

Run five fully invented steps with a small needs-driven controller:

```sh
python -m mewmory --db :memory: simulate
python -m mewmory --db data/instinct.db simulate --name Kitten-01
python -m mewmory --db data/instinct.db rules
python -m mewmory --db data/instinct.db recall caregiver_scent --limit 1
python -m mewmory --db data/instinct.db trace 3 4
```

Use a fresh database for the example IDs above. Each invocation starts a new
synthetic kitten state and appends five events; it does not resume its body state.
`:memory:` discards events on exit. The built-in scenario produces:
`call → nuzzle → orient_to_food → orient_to_food → rest`.

需求强度（饥饿、寒冷、疲劳）乘以预设权重决定当前优先需求，再结合感官线索
选择有限动作。只有环境明确提供的反馈能改变状态；“闻到食物”本身不会消除饥饿。
每步保存状态、动作和反馈，反复出现的“照顾者气味伴随饥饿降低”可形成统计关联。
这些关联目前可召回，但尚未参与行为策略，也没有实现强化学习。

This is a deliberately hand-designed controller, not a validated neonatal cat
model. Its numbers are unitless assumptions, not physiological measurements or
care instructions. The public scenario is fictional. See [algorithm and research
boundaries](docs/INSTINCT.md).

## What the baseline means / 基线含义

- Rules group exact, explicitly supplied `(actor, place, cue)` labels and count
  outcomes. Labels are provided by the caller, not extracted by a language model.
- Two food events and one no-food event yield support 2, total 3, frequency 2/3.
  This is an observed frequency, **not calibrated confidence or causation**.
- Recall ranks overlapping lowercase words/CJK characters, preferring rules on
  ties. It returns at most `--limit` items within a serialized JSON character
  budget. Characters are **not tokens**; actual token savings need measurement
  with the chosen model's tokenizer. The trailing CLI newline is outside this budget.
- Recall includes up to three evidence IDs per rule. `rules` exposes all IDs;
  `trace` retrieves original events. Oversized items are skipped, never silently
  clipped. If nothing matches or fits, recall returns `[]`.

这些简单统计规则不代表神经科学上的真实猫记忆机制。当前没有证据表明它优于
向量检索；低上下文 Token 开销是研究目标，而非已经验证的性能结论。
This is not a neuroscientific model of feline memory and makes no claim of
superiority to vector retrieval. Benchmarking remains future work.

## Privacy / 隐私

Data stays in the selected local SQLite file, **unencrypted**. Protect that file,
its backups, and terminal output with appropriate device access controls. Local
storage is not a guarantee of confidentiality. Do not collect other people's
personal data without appropriate consent. No real chats or credentials belong
in this repository; examples are fictional. Database files, `.env`, common key
files and `data/` are ignored, but `.gitignore` cannot protect every filename or
already tracked file. Inspect staged changes before publishing.

数据库为本地明文；终端输出和备份也可能泄露内容。尚未实现逐事件删除、加密、
访问控制或备份擦除；删除整个数据库并不保证设备上的数据不可恢复。
Do not use this prototype as a production store for sensitive information.

## Roadmap

1. Reproducible benchmarks: held-out cues, recall relevance, evidence coverage,
   contradictory observations, measured tokens, latency and storage.
2. Compare keyword baseline with embeddings and full-history context under the
   same budgets; add optional model adapters only after measurement.
3. Rule revision, recency/forgetting, deletion/export and privacy controls.
4. Optional MCP integration with explicit access boundaries.

See [design](docs/DESIGN.md) and [contributing](CONTRIBUTING.md). MIT licensed.
