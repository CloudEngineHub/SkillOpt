# ReflACT Ablation Study 启动计划

最终可复现实验配置已单独固化在 `configs/ablation_study/`：
`matrix.yaml` 记录公共 overrides、benchmark splits、消融变量、token/output caps 和无效 run 规则；
`launch_commands.sh` 记录正确启动命令；`validation.md` 记录监控和填表检查。

当前新增实验目标有两类：

```text
1. 新增 train.batch_size 消融：8 / 24 / 40 / 56 / full，gradient.minibatch_size 固定为 8。
2. 在现有 ablation table 方法不变的前提下，补齐 LiveMathBench、ALFWorld 和 DocVQA。
```

已完成的 SearchQA / SpreadsheetBench 结果不重复跑，除非缺 batch-size 新表所需的点。`train.batch_size=40` 是默认 setting，优先复用已有 default run；LiveMathBench / ALFWorld 还没有 default 结果，因此需要先跑 default。

## 2026-05-06 Harness 冲分实验清单

目标：把 harness 分数跑高，而不是继续扩大无关 ablation 矩阵。当前只考虑
SearchQA、SpreadsheetBench、LiveMathBench、DocVQA 10%；不跑 ALFWorld harness。

状态规则：

```text
[ ] = 还没起，另一台机器可以接着跑。
[x] = 已经起过、正在跑、或已经完成，不要重复起。
```

通用 harness 固定参数：

```text
model.teacher_backend=openai_chat
model.teacher=gpt-5.5
model.teacher_azure_openai_endpoint=https://oaidr21.openai.azure.com/
model.teacher_azure_openai_auth_mode=azure_cli
model.reasoning_effort=medium
model.student_backend=codex_exec for the Codex rows
model.student=gpt-5.5
model.codex_exec_use_sdk=auto
model.codex_exec_sandbox=workspace-write
model.codex_exec_approval_policy=never
model.codex_exec_reasoning_effort=medium
model.codex_trace_to_teacher=true
train.num_epochs=4
train.train_size=0
train.accumulation=1
gradient.minibatch_size=8
gradient.merge_batch_size=8
gradient.analyst_workers=16
gradient.use_deep_reflect=false
optimizer.lr_control_mode=fixed
optimizer.skill_update_mode=patch
optimizer.use_slow_update=true
optimizer.slow_update_samples=20
optimizer.use_meta_skill=true
optimizer.use_meta_reflect=false
evaluation.use_gate=true
evaluation.eval_test=true
env.split_mode=split_dir
```

当前已经在跑或已经有结果的参考实验，不要重复起：

| Status | 通俗名字 | Table row | 说明 |
| --- | --- | --- | --- |
| [x] | SearchQA 从默认 skill 训练 Codex | `HARNESS-BESTSETTING-searchqa-codex` | fresh-machine completed, test `0.8800` |
| [x] | LiveMath 从默认 skill 训练 Codex | `HARNESS-BESTSETTING-livemathematicianbench-codex` | fresh-machine completed, test `0.7600` |
| [x] | LiveMath 从默认 skill 训练 Claude | `HARNESS-BESTSETTING-livemathematicianbench-claude` | fresh-machine completed, test `0.3040` |
| [x] | DocVQA10 从默认 skill 训练 Codex | `HARNESS-BESTSETTING-docvqa10pct-codex` | fresh-machine completed, test `0.7032` |
| [x] | DocVQA10 从默认 skill 训练 Claude | `HARNESS-BESTSETTING-docvqa10pct-claude` | fresh-machine completed after image fix, test `0.5802` |
| [x] | SearchQA 从默认 skill 训练 Claude | `HARNESS-BESTSETTING-searchqa-claude` | fresh-machine running |
| [x] | Spreadsheet 从默认 skill 训练 Codex | `HARNESS-BESTSETTING-spreadsheetbench-codex` | fresh-machine running |
| [x] | Spreadsheet 从默认 skill 训练 Claude | `HARNESS-BESTSETTING-spreadsheetbench-claude` | fresh-machine running |
| [x] | SearchQA 最好 skill 迁移 Codex | `HARNESS-BESTSKILL-searchqa-codex` | completed, test `0.8714` |
| [x] | LiveMath 最好 skill 迁移 Codex | `HARNESS-BESTSKILL-livemathematicianbench-codex` | completed, test `0.8240` |
| [x] | DocVQA10 最好 skill 迁移 Codex | `HARNESS-BESTSKILL-docvqa10pct-codex` | completed, test `0.7032` |
| [x] | Spreadsheet 最好 skill 迁移 Codex | `HARNESS-BESTSKILL-spreadsheetbench-codex-multifix` | running on this machine |
| [x] | 四个 Claude 最好 skill fixed rerun | `HARNESS-BESTSKILL-*-claude*` | running on this machine; wait for fixed summaries |

Harness 冲分分三步：

```text
Step 1: Codex 先搜 no-harness 里最可能高分的 setting。
Step 2: Claude Code 完整复制 Step 1 的 18 个 setting，用来比较两个 harness backend。
Step 3: Codex 再补齐 no-harness 里剩余可调参数。
```

全程固定：

```text
optimizer.use_slow_update=true
optimizer.use_meta_skill=true
env.split_mode=split_dir
不调 split ratio；所有 harness 都用当前固定 harness split。
不跑 meta-only、slow-only、no-meta、no-slow 这类模块关闭实验。
所有 score-pushing run 都必须用 benchmark-level 唯一 best skill 初始化；不要用 setting-specific best_skill，也不要从默认初始 skill 训练。
SpreadsheetBench 所有 score-pushing run 都必须保持 env.mode=multi, env.workers=4, env.data_root=data/spreadsheetbench/files。
```

Step 1: Codex 高概率搜索，共 18 个。原则是从 `docs/ablation_paper_tables.html` 的 2:1:7 split 下所有消融实验中，为每个 benchmark 选 test 最好的一个 benchmark-level `best_skill.md`，再把不同参数设置迁移到 harness。每个 benchmark 只允许一个 source skill；参数 sweep 只改变参数，不改变 source skill。不选 split-ratio setting。

2026-05-06 note: the successful 2026-05-05 Codex harness rows used
`model.codex_exec_use_sdk=auto` and actually executed through `codex_sdk`.
The first local Codex Step 1 attempts were stopped and their outputs deleted
because `codex_exec` hit student-side Codex service 429s under high concurrency.
The 2026-05-06 08:04-08:26 UTC reruns were also stopped because they used
setting-specific source skills instead of one benchmark-level source skill per
benchmark. They are not valid results. Rerun these rows with SDK/auto auth
restored, low local concurrency, and the canonical source skills below.

Canonical benchmark-level source skills:
SearchQA: `docs/harness_source_skills/searchqa_best_skill.md` from `outputs/ablation_20260502_040604_unique48/optimizer.lr_scheduler-searchqa-constant/best_skill.md`, test `0.8729`.
SpreadsheetBench: `docs/harness_source_skills/spreadsheetbench_best_skill.md` from `outputs/ablation_20260502_040604_unique48/optimizer.lr_scheduler-spreadsheetbench-constant/best_skill.md`, test `0.8071`.
LiveMathBench: `docs/harness_source_skills/livemathematicianbench_best_skill.md` from `outputs/ablation_livemath_alfworld_clean_20260503_155155_run/LR-livemathematicianbench-8/best_skill.md`, test `0.6694`.
DocVQA: `docs/harness_source_skills/docvqa_best_skill.md` from `outputs/ablation_docvqa_20260503_160225_run/BATCH-docvqa-full/best_skill.md`, test `0.9049`.

| Status | 通俗名字 | 建议 Run ID | Benchmark | Backend | Skill init | Split / data | 需要改的参数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [ ] | SearchQA skill + constant scheduler | `HARNESS-Codex-SearchQA-sched-constant` | SearchQA | `codex_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | `data/searchqa/splits` | Pending valid rerun; 2026-05-06 setting-specific run stopped; Azure MI Codex wrapper, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | SearchQA skill + linear scheduler | `HARNESS-Codex-SearchQA-sched-linear` | SearchQA | `codex_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | `data/searchqa/splits` | Pending valid rerun; `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | SearchQA skill + full batch | `HARNESS-Codex-SearchQA-batch-full` | SearchQA | `codex_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | `data/searchqa/splits` | Pending valid rerun; `train.batch_size=400`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | SearchQA skill + LR=8 | `HARNESS-Codex-SearchQA-lr8` | SearchQA | `codex_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | `data/searchqa/splits` | Pending valid rerun; `optimizer.learning_rate=8`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Spreadsheet skill + constant scheduler | `HARNESS-Codex-Spreadsheet-sched-constant-multi` | SpreadsheetBench | `codex_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `data/spreadsheetbench`, data root `data/spreadsheetbench/files` | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=2`, `train.batch_size=40`, `env.mode=multi`, `env.workers=4` |
| [ ] | Spreadsheet skill + LR=4 | `HARNESS-Codex-Spreadsheet-lr4-multi` | SpreadsheetBench | `codex_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `data/spreadsheetbench`, data root `data/spreadsheetbench/files` | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1`, `train.batch_size=40`, `env.mode=multi`, `env.workers=4` |
| [ ] | Spreadsheet skill + LR=16 | `HARNESS-Codex-Spreadsheet-lr16-multi` | SpreadsheetBench | `codex_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `data/spreadsheetbench`, data root `data/spreadsheetbench/files` | `optimizer.learning_rate=16`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1`, `train.batch_size=40`, `env.mode=multi`, `env.workers=4` |
| [ ] | Spreadsheet skill + minibatch=16 | `HARNESS-Codex-Spreadsheet-minibatch16-multi` | SpreadsheetBench | `codex_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `data/spreadsheetbench`, data root `data/spreadsheetbench/files` | `train.batch_size=40`, `gradient.minibatch_size=16`, `env.mode=multi`, `env.workers=4` |
| [ ] | LiveMath skill + LR=8 | `HARNESS-Codex-LiveMath-lr8` | LiveMathBench | `codex_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | `data/livemathbench/splits` | Pending valid rerun; teacher oaidr9 MI, Codex student MI wrapper, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | LiveMath skill + LR=16 | `HARNESS-Codex-LiveMath-lr16` | LiveMathBench | `codex_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | `data/livemathbench/splits` | Pending valid rerun; `optimizer.learning_rate=16`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | LiveMath skill + slow10 | `HARNESS-Codex-LiveMath-slow10` | LiveMathBench | `codex_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | `data/livemathbench/splits` | Pending valid rerun; `optimizer.slow_update_samples=10`, teacher oaidr9 MI, Codex student MI wrapper |
| [ ] | LiveMath skill + linear scheduler | `HARNESS-Codex-LiveMath-sched-linear` | LiveMathBench | `codex_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | `data/livemathbench/splits` | Pending valid rerun; `optimizer.lr_scheduler=linear`, teacher oaidr9 MI, Codex student MI wrapper |
| [ ] | LiveMath skill + minibatch=4 | `HARNESS-Codex-LiveMath-minibatch4` | LiveMathBench | `codex_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | `data/livemathbench/splits` | Pending valid rerun; `gradient.minibatch_size=4`, teacher oaidr9 MI, Codex student MI wrapper |
| [ ] | DocVQA10 skill + full batch | `HARNESS-Codex-DocVQA10-batch-full` | DocVQA 10% | `codex_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | `data/harness_splits/docvqa_zisu_first10pct` | Pending valid rerun; `train.batch_size=107`, teacher oaidr9 MI, absolute Codex wrapper |
| [ ] | DocVQA10 skill + LR=16 | `HARNESS-Codex-DocVQA10-lr16` | DocVQA 10% | `codex_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | `data/harness_splits/docvqa_zisu_first10pct` | Pending valid rerun; `optimizer.learning_rate=16`, teacher oaidr9 MI, absolute Codex wrapper |
| [ ] | DocVQA10 skill + LR=8 | `HARNESS-Codex-DocVQA10-lr8` | DocVQA 10% | `codex_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | `data/harness_splits/docvqa_zisu_first10pct` | Pending valid rerun; `optimizer.learning_rate=8`, teacher oaidr9 MI, absolute Codex wrapper |
| [ ] | DocVQA10 skill + minibatch=32 | `HARNESS-Codex-DocVQA10-minibatch32` | DocVQA 10% | `codex_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | `data/harness_splits/docvqa_zisu_first10pct` | Pending valid rerun; `gradient.minibatch_size=32`, teacher oaidr9 MI, absolute Codex wrapper |
| [ ] | DocVQA10 skill + student batch=24 | `HARNESS-Codex-DocVQA10-batch24` | DocVQA 10% | `codex_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | `data/harness_splits/docvqa_zisu_first10pct` | Pending valid rerun; `train.batch_size=24`, teacher oaidr9 MI, absolute Codex wrapper |

Step 2: Claude Code 镜像实验，共 18 个。Claude Code 现在没有搜完；目前只是 fixed best-skill / best-setting 相关 run 在跑或部分完成。为了公平比较 harness backend，Claude Step 2 应完整复制 Codex Step 1 的 18 个 setting，而不是只复制每个 benchmark 的 top 1。每个 benchmark 也只允许一个 benchmark-level source skill。每个 run 单独打勾，不能用一个勾概括一组。Claude Step 2 默认用 `env.workers=2`, `env.exec_timeout=1020`（17 分钟）；不要再把 `workers=4` 当默认稳定设置。

| Status | 通俗名字 | 建议 Run ID | Benchmark | Backend | Skill init | 必须保持 |
| --- | --- | --- | --- | --- | --- | --- |
| [ ] | Claude SearchQA skill + constant scheduler | `HARNESS-Claude-SearchQA-sched-constant` | SearchQA | `claude_code_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | Pending valid rerun; prior setting-specific run stopped; `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude SearchQA skill + linear scheduler | `HARNESS-Claude-SearchQA-sched-linear` | SearchQA | `claude_code_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | Pending valid rerun; `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude SearchQA skill + full batch | `HARNESS-Claude-SearchQA-batch-full` | SearchQA | `claude_code_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | Pending valid rerun; `train.batch_size=400`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude SearchQA skill + LR=8 | `HARNESS-Claude-SearchQA-lr8` | SearchQA | `claude_code_exec` | `docs/harness_source_skills/searchqa_best_skill.md` | Pending valid rerun; `optimizer.learning_rate=8`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude Spreadsheet skill + constant scheduler | `HARNESS-Claude-Spreadsheet-sched-constant-multi` | SpreadsheetBench | `claude_code_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `env.mode=multi`, `env.workers=4`, `env.data_root=data/spreadsheetbench/files` |
| [ ] | Claude Spreadsheet skill + LR=4 | `HARNESS-Claude-Spreadsheet-lr4-multi` | SpreadsheetBench | `claude_code_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `env.mode=multi`, `env.workers=4`, `env.data_root=data/spreadsheetbench/files` |
| [ ] | Claude Spreadsheet skill + LR=16 | `HARNESS-Claude-Spreadsheet-lr16-multi` | SpreadsheetBench | `claude_code_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `env.mode=multi`, `env.workers=4`, `env.data_root=data/spreadsheetbench/files` |
| [ ] | Claude Spreadsheet skill + minibatch=16 | `HARNESS-Claude-Spreadsheet-minibatch16-multi` | SpreadsheetBench | `claude_code_exec` | `docs/harness_source_skills/spreadsheetbench_best_skill.md` | `env.mode=multi`, `env.workers=4`, `env.data_root=data/spreadsheetbench/files` |
| [ ] | Claude LiveMath skill + LR=8 | `HARNESS-Claude-LiveMath-lr8` | LiveMathBench | `claude_code_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | Pending valid rerun; `optimizer.learning_rate=8`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude LiveMath skill + LR=16 | `HARNESS-Claude-LiveMath-lr16` | LiveMathBench | `claude_code_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | Pending valid rerun; `optimizer.learning_rate=16`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude LiveMath skill + slow10 | `HARNESS-Claude-LiveMath-slow10` | LiveMathBench | `claude_code_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | Pending valid rerun; `optimizer.slow_update_samples=10`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude LiveMath skill + linear scheduler | `HARNESS-Claude-LiveMath-sched-linear` | LiveMathBench | `claude_code_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | Pending valid rerun; `optimizer.lr_scheduler=linear`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude LiveMath skill + minibatch=4 | `HARNESS-Claude-LiveMath-minibatch4` | LiveMathBench | `claude_code_exec` | `docs/harness_source_skills/livemathematicianbench_best_skill.md` | Pending valid rerun; `gradient.minibatch_size=4`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude DocVQA10 skill + full batch | `HARNESS-Claude-DocVQA10-batch-full` | DocVQA 10% | `claude_code_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | Pending valid rerun; `train.batch_size=107`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude DocVQA10 skill + LR=16 | `HARNESS-Claude-DocVQA10-lr16` | DocVQA 10% | `claude_code_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | Pending valid rerun; `optimizer.learning_rate=16`, `env.workers=2`, `env.exec_timeout=1020` |
| [ ] | Claude DocVQA10 skill + LR=8 | `HARNESS-Claude-DocVQA10-lr8` | DocVQA 10% | `claude_code_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | 确认 image attachment fix 生效 |
| [ ] | Claude DocVQA10 skill + minibatch=32 | `HARNESS-Claude-DocVQA10-minibatch32` | DocVQA 10% | `claude_code_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | 确认 image attachment fix 生效 |
| [ ] | Claude DocVQA10 skill + student batch=24 | `HARNESS-Claude-DocVQA10-batch24` | DocVQA 10% | `claude_code_exec` | `docs/harness_source_skills/docvqa_best_skill.md` | 确认 image attachment fix 生效 |

Step 3: Codex 补齐剩余可调参数。这个阶段是计划内的后续补齐，不一次性全起；通常在 Step 1 初步结果后按 benchmark 展开。搜索空间来自 no-harness ablation 中所有仍允许调的参数；排除 split ratio 和模块关闭实验。每个 run 单独打勾；启动前必须设置 `env.skill_init` 指向该 benchmark 的 canonical best skill，不能用 setting-specific skill，也不能用默认初始 skill。

| Status | 建议 Run ID | Benchmark | 参数 | 必须保持 |
| --- | --- | --- | --- | --- |
| [ ] | `HARNESS-Codex-SearchQA-batch8` | SearchQA | `train.batch_size=8` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-batch24` | SearchQA | `train.batch_size=24` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-batch56` | SearchQA | `train.batch_size=56` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-Spreadsheet-batch8-multi` | SpreadsheetBench | `train.batch_size=8` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-batch24-multi` | SpreadsheetBench | `train.batch_size=24` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-batch56-multi` | SpreadsheetBench | `train.batch_size=56` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-batch-full-multi` | SpreadsheetBench | `train.batch_size=80` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-LiveMath-batch8` | LiveMathBench | `train.batch_size=8` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-batch24` | LiveMathBench | `train.batch_size=24` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-batch56` | LiveMathBench | `train.batch_size=56` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-batch-full` | LiveMathBench | `train.batch_size=35` | 对应 no-harness best_skill; current 2:1:7 train size |
| [ ] | `HARNESS-Codex-DocVQA10-batch8` | DocVQA 10% | `train.batch_size=8` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-batch56` | DocVQA 10% | `train.batch_size=56` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-minibatch1` | SearchQA | `gradient.minibatch_size=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-minibatch2` | SearchQA | `gradient.minibatch_size=2` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-minibatch4` | SearchQA | `gradient.minibatch_size=4` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-minibatch16` | SearchQA | `gradient.minibatch_size=16` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-minibatch32` | SearchQA | `gradient.minibatch_size=32` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-Spreadsheet-minibatch1-multi` | SpreadsheetBench | `gradient.minibatch_size=1` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-minibatch2-multi` | SpreadsheetBench | `gradient.minibatch_size=2` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-minibatch4-multi` | SpreadsheetBench | `gradient.minibatch_size=4` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-minibatch32-multi` | SpreadsheetBench | `gradient.minibatch_size=32` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-LiveMath-minibatch1` | LiveMathBench | `gradient.minibatch_size=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-minibatch2` | LiveMathBench | `gradient.minibatch_size=2` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-minibatch16` | LiveMathBench | `gradient.minibatch_size=16` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-minibatch32` | LiveMathBench | `gradient.minibatch_size=32` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-minibatch1` | DocVQA 10% | `gradient.minibatch_size=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-minibatch2` | DocVQA 10% | `gradient.minibatch_size=2` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-minibatch4` | DocVQA 10% | `gradient.minibatch_size=4` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-minibatch16` | DocVQA 10% | `gradient.minibatch_size=16` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-lr1` | SearchQA | `optimizer.learning_rate=1`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-lr2` | SearchQA | `optimizer.learning_rate=2`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-lr4` | SearchQA | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-lr16` | SearchQA | `optimizer.learning_rate=16`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-Spreadsheet-lr1-multi` | SpreadsheetBench | `optimizer.learning_rate=1`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-lr2-multi` | SpreadsheetBench | `optimizer.learning_rate=2`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-lr8-multi` | SpreadsheetBench | `optimizer.learning_rate=8`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-LiveMath-lr1` | LiveMathBench | `optimizer.learning_rate=1`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-lr2` | LiveMathBench | `optimizer.learning_rate=2`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-lr4` | LiveMathBench | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-lr1` | DocVQA 10% | `optimizer.learning_rate=1`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-lr2` | DocVQA 10% | `optimizer.learning_rate=2`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-lr4` | DocVQA 10% | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=1` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-Spreadsheet-sched-linear-multi` | SpreadsheetBench | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=linear`, `optimizer.min_learning_rate=2` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-LiveMath-sched-constant` | LiveMathBench | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=2` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-sched-constant` | DocVQA 10% | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=constant`, `optimizer.min_learning_rate=2` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-sched-linear` | DocVQA 10% | `optimizer.learning_rate=4`, `optimizer.lr_scheduler=linear`, `optimizer.min_learning_rate=2` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-slow5` | SearchQA | `optimizer.slow_update_samples=5` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-slow10` | SearchQA | `optimizer.slow_update_samples=10` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-slow40` | SearchQA | `optimizer.slow_update_samples=40` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-Spreadsheet-slow5-multi` | SpreadsheetBench | `optimizer.slow_update_samples=5` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-slow10-multi` | SpreadsheetBench | `optimizer.slow_update_samples=10` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-slow40-multi` | SpreadsheetBench | `optimizer.slow_update_samples=40` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-LiveMath-slow5` | LiveMathBench | `optimizer.slow_update_samples=5` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-slow40` | LiveMathBench | `optimizer.slow_update_samples=40` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-slow5` | DocVQA 10% | `optimizer.slow_update_samples=5` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-slow10` | DocVQA 10% | `optimizer.slow_update_samples=10` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-slow40` | DocVQA 10% | `optimizer.slow_update_samples=40` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-policy-changed` | SearchQA | `optimizer.longitudinal_pair_policy=changed` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-SearchQA-policy-unchanged` | SearchQA | `optimizer.longitudinal_pair_policy=unchanged` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-Spreadsheet-policy-changed-multi` | SpreadsheetBench | `optimizer.longitudinal_pair_policy=changed` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-Spreadsheet-policy-unchanged-multi` | SpreadsheetBench | `optimizer.longitudinal_pair_policy=unchanged` | 对应 no-harness best_skill; `env.mode=multi` |
| [ ] | `HARNESS-Codex-LiveMath-policy-changed` | LiveMathBench | `optimizer.longitudinal_pair_policy=changed` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-LiveMath-policy-unchanged` | LiveMathBench | `optimizer.longitudinal_pair_policy=unchanged` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-policy-changed` | DocVQA 10% | `optimizer.longitudinal_pair_policy=changed` | 对应 no-harness best_skill |
| [ ] | `HARNESS-Codex-DocVQA10-policy-unchanged` | DocVQA 10% | `optimizer.longitudinal_pair_policy=unchanged` | 对应 no-harness best_skill |

Step 3 展开数量：共 66 个 Codex 实验。计数规则是：排除 Step 1 已经覆盖的值，排除现有 default/best-skill/best-setting 已覆盖的默认值，排除 split ratio 和模块关闭组合。

| 参数组 | SearchQA | SpreadsheetBench | LiveMathBench | DocVQA10 | 小计 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `train.batch_size` | 3 | 4 | 4 | 2 | 13 |
| `gradient.minibatch_size` | 5 | 4 | 4 | 4 | 17 |
| `optimizer.learning_rate` | 4 | 3 | 3 | 3 | 13 |
| `optimizer.lr_scheduler` | 0 | 1 | 1 | 2 | 4 |
| `optimizer.slow_update_samples` | 3 | 3 | 2 | 3 | 11 |
| `optimizer.longitudinal_pair_policy` | 2 | 2 | 2 | 2 | 8 |
| **Total** | **17** | **17** | **16** | **15** | **66** |

数量上限：

```text
Codex Step 1：18 个。
Claude Step 2：18 个，完整复制 Codex Step 1 的 setting。
Codex Step 3：66 个，补齐剩余允许参数。
当前完整计划总量：102 个新实验。
实际启动原则：每轮最多 1-4 个，高负载时不要继续加。
```

明确不跑：

```text
1. 不跑 ALFWorld harness。
2. 不在本机重复 fresh-machine best-setting from-scratch。
3. 不一次性启动 8 个 harness best-setting。
4. 不在 Claude fixed rerun 完成前做 Claude Step 2 镜像实验。
5. Claude Step 2 只复制 Codex Step 1 的 18 个 setting；Step 3 不默认镜像到 Claude。
6. 不跑 `optimizer.use_slow_update/use_meta_skill` 的 off/on 模块关闭组合。
```

## 0. 启动前强制检查

每次启动新一批实验前必须满足：

| 检查项 | 必须满足 |
| --- | --- |
| Python | 使用 `/home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python` |
| 代码语法 | `py_compile` 覆盖 launcher、train、LiveMathBench dataloader、ALFWorld dataloader/adapter |
| Harness | 普通 ablation 使用 `model.teacher_backend=openai_chat` 且 `model.student_backend=openai_chat`；本节 harness 冲分使用 `model.teacher_backend=openai_chat` 且 `model.student_backend=codex_exec/claude_code_exec` |
| 模型 | teacher/student 默认均为 `gpt-5.5` |
| Azure | 当前 harness 冲分 endpoint 使用 `https://oaidr21.openai.azure.com/` |
| Auth | teacher/student 默认均使用 `azure_cli` |
| API version | teacher/student 默认均为 `2024-12-01-preview` |
| Reasoning | `model.reasoning_effort=medium`，teacher 和 student 都必须生效 |
| Split | 所有 benchmark 都使用固定 `env.split_mode=split_dir` |
| Train size | `train.train_size=0`，由 split 自动推断 |
| Batch 逻辑 | `steps_per_epoch = ceil(train_size / (train.batch_size * train.accumulation))` |
| Rollout 并发 | 本轮 active benchmark 的 rollout 不允许使用裸 `as_completed`; 必须使用 `wait(..., FIRST_COMPLETED)` + started-at timeout，避免最后一个 future 卡死 |
| LLM timeout | `chat_student` / `chat_student_messages` 必须向 SDK 传入显式 timeout，不能只依赖外层 future timeout |
| Gate/Test | `evaluation.use_gate=true`，`evaluation.eval_test=true` |
| 输出目录 | 每个 run 的 `env.out_root` 唯一；错误目录不复用 |

启动后立刻检查每个 run 的 `config.json` 和 log 前 50 行，确认模型、split、reasoning、train size、batch size、消融参数都正确。

## 1. 固定默认 Setting

除当前消融变量外，所有实验固定：

| 参数 | 默认值 |
| --- | --- |
| `model.teacher_backend` | `openai_chat` |
| `model.student_backend` | `openai_chat` |
| `model.teacher` | `gpt-5.5` |
| `model.student` | `gpt-5.5` |
| `model.teacher_azure_openai_endpoint` | `https://t2vgoaigpt4o3.openai.azure.com/` |
| `model.student_azure_openai_endpoint` | `https://t2vgoaigpt4o3.openai.azure.com/` |
| `model.teacher_azure_openai_api_version` | `2024-12-01-preview` |
| `model.student_azure_openai_api_version` | `2024-12-01-preview` |
| `model.teacher_azure_openai_auth_mode` | `azure_cli` |
| `model.student_azure_openai_auth_mode` | `azure_cli` |
| `model.reasoning_effort` | `medium` |
| `train.num_epochs` | `4` |
| `train.train_size` | `0` |
| `train.batch_size` | `40` |
| `train.accumulation` | `1` |
| `train.seed` | `42` |
| `gradient.minibatch_size` | `8` |
| `gradient.merge_batch_size` | `8` |
| `gradient.analyst_workers` | `16` |
| `gradient.use_deep_reflect` | `false` |
| `optimizer.learning_rate` | `4` |
| `optimizer.min_learning_rate` | `2` |
| `optimizer.lr_scheduler` | `cosine` |
| `optimizer.skill_update_mode` | `patch` |
| `optimizer.use_slow_update` | `true` |
| `optimizer.slow_update_samples` | `20` |
| `optimizer.use_meta_skill` | `true` |
| `optimizer.use_meta_reflect` | `false` |
| `evaluation.use_gate` | `true` |
| `evaluation.eval_test` | `true` |

Benchmark 固定项：

| Benchmark | Config | Default split | Train | Val | Test | Student rollout |
| --- | --- | --- | ---: | ---: | ---: | --- |
| SearchQA | `configs/searchqa/default.yaml` | `data/ablation_splits/searchqa/2-1-7_seed42` | 400 | 200 | 1400 | `chat_student` |
| SpreadsheetBench | `configs/spreadsheetbench/default.yaml` | `data/ablation_splits/spreadsheetbench/2-1-7_seed42` | 80 | 40 | 280 | `codegen_agent.py -> get_student_client()` |
| LiveMathBench | `configs/livemathematicianbench/default.yaml` | `data/ablation_splits/livemathematicianbench/2-1-7_seed42` | 35 | 18 | 124 | `chat_student` |
| ALFWorld | `configs/alfworld/default.yaml` | `data/ablation_splits/alfworld/2-1-7_seed42` | 39 | 18 | 134 | `chat_student` |
| DocVQA | `configs/docvqa/default.yaml` | `/home/azureuser/zisu/SkillReflection/data/docvqa/splits` | 1070 | 535 | 3744 | `chat_student_messages` |

ALFWorld 必须设置：

```bash
export ALFWORLD_DATA=/home/azureuser/.cache/alfworld
```

## 2. 已验证的数据和 loader 行为

LiveMathBench 使用固定 JSON split，训练时每个 batch 内仍按 seed shuffle choices。已验证 batch 切分：

| `train.batch_size` | Train size | Steps/epoch | Batch sizes |
| ---: | ---: | ---: | --- |
| 8 | 35 | 5 | `8 + 8 + 8 + 8 + 3` |
| 24 | 35 | 2 | `24 + 11` |
| 40 | 35 | 1 | `35` |
| 56 | 35 | 1 | `35` |
| full | 35 | 1 | `35` |

ALFWorld 使用固定 `gamefile` split，39 个 train gamefile 从本地 `/home/azureuser/.cache/alfworld/json_2.1.1/train` 中固定抽样，val/test 分别来自 `valid_seen` / `valid_unseen`。已验证本地 gamefile 全部存在，并做过单环境 `reset()` smoke。

| `train.batch_size` | Train size | Steps/epoch | Batch sizes |
| ---: | ---: | ---: | --- |
| 8 | 39 | 5 | `8 + 8 + 8 + 8 + 7` |
| 24 | 39 | 2 | `24 + 15` |
| 40 | 39 | 1 | `39` |
| 56 | 39 | 1 | `39` |
| full | 39 | 1 | `39` |

新增 benchmark 的 `env.split_dir` 多比例数据已补齐：

| Benchmark | Split | Train | Val | Test | 说明 |
| --- | --- | ---: | ---: | ---: | --- |
| LiveMathBench | `1shot_seed42` | 1 | 1 | 175 | 从同一 177-item 候选池生成 |
| LiveMathBench | `1-1-8_seed42` | 18 | 18 | 141 | 从同一 177-item 候选池生成 |
| LiveMathBench | `2-1-7_seed42` | 35 | 18 | 124 | 按 `scripts/prepare_ablation_splits.py` 同一整数规则生成 |
| LiveMathBench | `4-1-5_seed42` | 71 | 18 | 88 | 从同一 177-item 候选池生成 |
| ALFWorld | `1shot_seed42` | 1 | 1 | 134 | domain-preserving fixed gamefiles |
| ALFWorld | `1-1-8_seed42` | 18 | 18 | 134 | train 只来自 official train，val/test 保持 valid_seen/valid_unseen |
| ALFWorld | `2-1-7_seed42` | 39 | 18 | 134 | 已验证 fixed split |
| ALFWorld | `4-1-5_seed42` | 82 | 18 | 103 | train 只来自 `train_pool_80`，test 从 valid_unseen 固定抽样 |
| DocVQA | `1shot_seed42` | 1 | 1 | 5347 | 从同一 5349-item 候选池生成 |
| DocVQA | `1-1-8_seed42` | 535 | 535 | 4279 | 按 `scripts/prepare_ablation_splits.py` 同一整数规则生成 |
| DocVQA | zisu `splits` | 1070 | 535 | 3744 | 直接使用 `/home/azureuser/zisu/SkillReflection/data/docvqa/splits`；旧 `2-1-7_seed42` 是同一 5349 样本池的重新划分，不再作为最终 2:1:7 |
| DocVQA | `4-1-5_seed42` | 2140 | 535 | 2674 | 按 `scripts/prepare_ablation_splits.py` 同一整数规则生成 |

DocVQA 图片目录不复制，使用 symlink：

```text
data/docvqa_images -> /home/azureuser/zisu/SkillReflection/data/docvqa_images
```

2026-05-05 DocVQA 数据修正：

```text
使用路径：/home/azureuser/zisu/SkillReflection/data/docvqa/splits
数量：train=1070, val=535, test=3744, total=5349
CSV 字段：question, answer, topic, questionId, docId, image_path, ...
图片：所有抽查和全量 image_path 均可通过 data/docvqa_images symlink 解析
对比：旧 data/ablation_splits/docvqa/2-1-7_seed42 与 zisu split 的 5349 questionId 集合完全相同，但 train/val/test 分配不同。
结论：所有 DocVQA 2:1:7 结果需要按 zisu split 重跑；旧 DocVQA 表格结果仅作历史参考。
建议新 run_root：outputs/ablation_docvqa_zisu10pct_20260505_run，避免旧 outputs/ablation_docvqa_20260503_160225_run 的 summary.json 被 launcher 跳过。
```

## 3. 新跑实验清单

### 3.1 LiveMathBench / ALFWorld / DocVQA 补齐现有 ablation table

对 LiveMathBench、ALFWorld 和 DocVQA 新跑下面这些组；默认点会被复用，不重复跑同一设置：

| 组 | Values | 每 benchmark 新 run 数 |
| --- | --- | ---: |
| `default` | 默认 `gpt-5.5/gpt-5.5` setting | 1 |
| `env.split_dir` | `1shot / 1-1-8 / 4-1-5`，跳过默认 `2-1-7` | 3 |
| `gradient.minibatch_size` | `1 / 2 / 4 / 16 / 32`，跳过默认 `8` | 5 |
| `optimizer.learning_rate` | `1 / 2 / 4 / 8 / 16`，本组固定 `lr_scheduler=constant min_learning_rate=1` | 5 |
| `optimizer.lr_scheduler` | `constant / linear`，跳过默认 `cosine` | 2 |
| `optimizer.slow_update_samples` | `5 / 10 / 40`，跳过默认 `20` | 3 |
| `optimizer.use_slow_update` / `optimizer.use_meta_skill` | `true,false` / `false,true` / `false,false`，跳过默认 `true,true` | 3 |
| `model.student` | `gpt-5.4-pro / gpt-5.4-mini`，跳过默认 `gpt-5.5` | 2 |

合计：每个新增 benchmark 24 个现有表补齐 run；三个 benchmark 共 72 个。

### 3.2 新增 `train.batch_size` ablation

对五个 benchmark 都补 batch-size 表：

```text
train.batch_size = 8 / 24 / 40 / 56 / full
gradient.minibatch_size = 8
```

`train.batch_size=40` 是默认点：

| Benchmark | full 展开值 | 默认 40 来源 | 需要新跑 batch 点 |
| --- | ---: | --- | --- |
| SearchQA | 400 | 复用已有 default | `8 / 24 / 56 / full` |
| SpreadsheetBench | 80 | 复用已有 default | `8 / 24 / 56 / full` |
| LiveMathBench | 35 | 复用本轮新增 default | `8 / 24 / 56 / full` |
| ALFWorld | 39 | 复用本轮新增 default | `8 / 24 / 56 / full` |
| DocVQA | 1070 | 复用本轮新增 default | `8 / 24 / 56 / full` |

新增 batch-size run 数：五个 benchmark 共 20 个。

### 3.3 本轮总新增 run 数

| 实验块 | SearchQA | SpreadsheetBench | LiveMathBench | ALFWorld | DocVQA | 新增合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 补齐现有 table | 0 | 0 | 24 | 24 | 24 | 72 |
| 新增 batch-size table | 4 | 4 | 4 | 4 | 4 | 20 |
| 合计 | 4 | 4 | 28 | 28 | 28 | 92 |

### 3.4 新增 longitudinal comparison example policy ablation

这个实验只改变 slow update 和 meta skill 看到的 comparison examples，不改 prompt、不改模型、不改 rollout、不改优化主流程。默认 `mixed` 复用原版随机 20 条。

| Policy | Comparison examples | Top-up 规则 |
| --- | --- | --- |
| `mixed` | 原版随机样本，可能包含 `10/01/00/11` | 不额外补样本 |
| `changed` | 只保留 `10/01`，即 improved/regressed | 不满 20 时继续从 train split 扫描补满，扫完整个 train split 为止 |
| `unchanged` | 只保留 `00/11`，即 persistent_fail/stable_success | 不强求 20 条，不补样本 |

本轮先跑除 ALFWorld 外四个 benchmark：

```text
SearchQA / SpreadsheetBench / LiveMathBench / DocVQA
```

新增 run 数：`4 benchmarks x 2 policies = 8`。

### 3.5 新增 learning-rate-control baseline

这个实验只在除 ALFWorld 外四个 benchmark 上跑：

```text
SearchQA / SpreadsheetBench / LiveMathBench / DocVQA
```

两类 baseline：

| Run | 设置 | 说明 |
| --- | --- | --- |
| `autonomous` | `optimizer.lr_control_mode=autonomous` | 保留 edit/patch 框架，但每个 step 由 teacher 根据当前证据自主输出一个整数 LR；prompt 不给默认 LR、候选 LR 或历史 LR 先验；每步写 `lr_decision.json`，全局写 `lr_history.jsonl` |
| `full-rewrite` | `optimizer.lr_control_mode=none` + `optimizer.skill_update_mode=full_rewrite_minibatch` | 去掉 LR/edit budget/select/apply-edit；每个 minibatch 直接生成完整 skill candidate，aggregate/merge 直接合成最终 candidate skill |

新增 run 数：`4 benchmarks x 2 baselines = 8`。

实现落点：

| 功能 | 文件 |
| --- | --- |
| autonomous LR 决策 | `reflact/optimizer/lr_autonomous.py` |
| LR control config | `configs/_base_/default.yaml`, `reflact/config.py`, `scripts/train.py` |
| full-rewrite-minibatch mode | `reflact/optimizer/update_modes.py`, `reflact/gradient/reflect.py`, `reflact/gradient/aggregate.py`, `reflact/engine/trainer.py` |
| autonomous LR prompt | `reflact/prompts/lr_autonomous.md` |
| full-rewrite analyst prompts | `reflact/prompts/analyst_error_full_rewrite.md`, `reflact/prompts/analyst_success_full_rewrite.md` |
| full-rewrite merge prompts | `reflact/prompts/merge_failure_full_rewrite.md`, `reflact/prompts/merge_success_full_rewrite.md`, `reflact/prompts/merge_final_full_rewrite.md` |

验证记录：

```text
py_compile passed for train, config, trainer, reflect, aggregate, update_modes, lr_autonomous, env base.
SearchQA smoke autonomous passed: wrote steps/step_0001/lr_decision.json and lr_history.jsonl.
SearchQA smoke full-rewrite passed: wrote steps/step_0001/full_rewrite_result.json and candidate_skill.md.
Formal LRCTRL config alignment vs default: ALL OK.
```

正式 run root：

```text
outputs/ablation_lrctrl_20260504_run
```

正式启动后必须检查：

```text
autonomous: lr_decision.json count increases with steps; lr_history.jsonl exists.
full-rewrite: full_rewrite_result.json count increases with steps; edit_budget in step_record is null.
all: config.json differs from default only in lr_control_mode / skill_update_mode / out_root.
```

2026-05-05 minimal-prompt full-rewrite rerun:

```text
Motivation:
The original full-rewrite prompts were highly guided: expert rewriter framing,
failure corrections as high priority, preservation of strongest guidance, and
explicit generalizable behavioral guidance. To test a less scaffolded rewrite
baseline, the original full-rewrite prompt files were replaced in-place with
summary-style prompts.

Changed prompt files:
- reflact/prompts/analyst_error_full_rewrite.md
- reflact/prompts/analyst_success_full_rewrite.md
- reflact/prompts/merge_failure_full_rewrite.md
- reflact/prompts/merge_success_full_rewrite.md
- reflact/prompts/merge_final_full_rewrite.md

The replacement prompts keep the same JSON schema and still require complete
replacement skill documents, but only ask the model to summarize lessons or
combine complete skill candidates. They keep the no-task-specific-answer rule.

Runs started manually, not via matrix launcher:
run_root=outputs/rerun_lrctrl_fullrewrite_minimalprompt_20260505_run

LRCTRL-searchqa-full-rewrite-minimalprompt
  pid=281937
  config=configs/searchqa/default.yaml
  split=data/ablation_splits/searchqa/2-1-7_seed42
  verified train/val/test=400/200/1400
  overrides: optimizer.lr_control_mode=none, optimizer.skill_update_mode=full_rewrite_minibatch

LRCTRL-spreadsheetbench-full-rewrite-minimalprompt
  pid=281938
  config=configs/spreadsheetbench/default.yaml
  split=data/ablation_splits/spreadsheetbench/2-1-7_seed42
  verified train/val/test=80/40/280
  overrides: optimizer.lr_control_mode=none, optimizer.skill_update_mode=full_rewrite_minibatch

Table status rows were added in docs/ablation_paper_tables.md; metrics remain
blank until summary.json is produced.

2026-05-05 14:48 UTC update:

The code-assembled final merge user prompt also had hardcoded priority wording:
`Group 1 (failure-driven, HIGH priority)` and `Group 2 (success-driven, lower priority)`.
For `full_rewrite_minibatch` only, this was changed in `reflact/gradient/aggregate.py`
to neutral source labels: `Group 1 (from failed trajectories)` and
`Group 2 (from successful trajectories)`. Ordinary patch-mode merging keeps the
existing failure-priority prompt.

The earlier two `minimalprompt` processes were stopped before `summary.json`.
The replacement runs use a fresh root:

run_root=outputs/rerun_lrctrl_fullrewrite_minimalprompt_neutralmerge_20260505_run

LRCTRL-searchqa-full-rewrite-minimalprompt-neutralmerge
  pid=438572
  config=configs/searchqa/default.yaml
  split=data/ablation_splits/searchqa/2-1-7_seed42
  verified train/val/test=400/200/1400
  overrides: optimizer.lr_control_mode=none, optimizer.skill_update_mode=full_rewrite_minibatch

LRCTRL-spreadsheetbench-full-rewrite-minimalprompt-neutralmerge
  pid=438573
  config=configs/spreadsheetbench/default.yaml
  split=data/ablation_splits/spreadsheetbench/2-1-7_seed42
  verified train/val/test=80/40/280
  overrides: optimizer.lr_control_mode=none, optimizer.skill_update_mode=full_rewrite_minibatch
```

### 3.6 当前 active experiments snapshot

2026-05-04 18:00 UTC 左右，当前不跑 ALFWorld，active 训练进程保持 24 个，无重复 out_root。

DocVQA 旧矩阵剩余 8 个：

```text
SLOWN-docvqa-5
SLOWN-docvqa-10
SLOWN-docvqa-40
MOD-docvqa-slow-only
MOD-docvqa-meta-only
MOD-docvqa-none
SMODEL-docvqa-5.4
SMODEL-docvqa-5.4-mini
```

Longitudinal comparison-example policy 8 个：

```text
LONGPAIR-searchqa-changed
LONGPAIR-searchqa-unchanged
LONGPAIR-spreadsheetbench-changed
LONGPAIR-spreadsheetbench-unchanged
LONGPAIR-livemathematicianbench-changed
LONGPAIR-livemathematicianbench-unchanged
LONGPAIR-docvqa-changed
LONGPAIR-docvqa-unchanged
```

Learning-rate-control baseline 8 个：

```text
LRCTRL-searchqa-autonomous
LRCTRL-searchqa-full-rewrite
LRCTRL-spreadsheetbench-autonomous
LRCTRL-spreadsheetbench-full-rewrite
LRCTRL-livemathematicianbench-autonomous
LRCTRL-livemathematicianbench-full-rewrite
LRCTRL-docvqa-autonomous
LRCTRL-docvqa-full-rewrite
```

DocVQA skill-none eval 另有一个 eval-only 进程在跑，不计入 24 个 train：

```text
outputs/ablation_docvqa_20260503_160225_run/skill-none-model.student-docvqa-5.5
```

旧的 0-byte partial 已归档：

```text
outputs/ablation_docvqa_20260503_160225_run/archive_skill_none_docvqa_empty_20260504_175635
```

### 3.7 2026-05-05 handoff snapshot

2026-05-05 08:26 UTC 手动检查状态如下。本节覆盖上一节的过期 active snapshot；上一节只作为历史记录保留。

当前没有 `run_ablation_matrix.py` launcher、`rerun_unfinished_no_prior` helper 或自动监控脚本在跑。只保留已经直接启动的 `scripts/train.py` 实验进程。由于 ALFWorld 会派生本地环境 worker，进程行数会被放大；统计时必须按唯一 `env.out_root`/run id 计数。

当前 active setting 共 19 个：

```text
DEFAULT-alfworld-5.5
SPLIT-alfworld-1shot
SPLIT-alfworld-1-1-8
SPLIT-alfworld-4-1-5
BATCH-alfworld-8
BATCH-alfworld-24
BATCH-alfworld-56
BATCH-alfworld-full
MBS-alfworld-1
MBS-alfworld-2
MBS-alfworld-4
MBS-alfworld-16
MBS-alfworld-32
LR-alfworld-1
LR-alfworld-2
LR-alfworld-4
LONGPAIR-spreadsheetbench-changed
LRCTRL-docvqa-full-rewrite
LRCTRL-spreadsheetbench-autonomous
```

当前尚未启动、建议交给新机器补跑的 setting 共 17 个：

```text
LR-alfworld-8
LR-alfworld-16
SCHED-alfworld-constant
SCHED-alfworld-linear
SLOWN-alfworld-5
SLOWN-alfworld-10
SLOWN-alfworld-40
MOD-alfworld-slow-only
MOD-alfworld-meta-only
MOD-alfworld-none
SMODEL-alfworld-5.4
SMODEL-alfworld-5.4-mini
LONGPAIR-alfworld-changed
LONGPAIR-alfworld-unchanged
LRCTRL-alfworld-autonomous
LRCTRL-alfworld-full-rewrite
LRCTRL-docvqa-autonomous
```

No-prior autonomous LR rerun 状态：

```text
done: LRCTRL-searchqa-autonomous
done: LRCTRL-livemathematicianbench-autonomous
active: LRCTRL-spreadsheetbench-autonomous
not started: LRCTRL-docvqa-autonomous
```

健康状态：

```text
true 429 check: none found in active logs
Traceback/OOM/Killed check: none found in active logs
memory: about 617 GiB available, train RSS about 20 GiB
known non-fatal issue: SpreadsheetBench active runs have task-level TIMEOUT rows during rollout; these are benchmark item timeouts, not API 429.
```

继续手动监控时用这个唯一 run-id 统计，不要用裸进程行数：

```bash
/home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python - <<'PY'
import os, re, subprocess, collections
out = subprocess.check_output(["ps", "-eo", "pid,ppid,lstart,cmd"], text=True, errors="replace")
by = collections.defaultdict(list)
root_by = {}
for line in out.splitlines()[1:]:
    if "scripts/train.py" not in line or "python - <<" in line or "ps -eo" in line:
        continue
    m = re.search(r"env\.out_root=([^\s]+)", line)
    if not m:
        continue
    root = m.group(1)
    run_id = os.path.basename(root.rstrip("/"))
    by[run_id].append(line.split(None, 1)[0])
    root_by[run_id] = root
print(f"unique_active_settings={len(by)} process_rows={sum(len(v) for v in by.values())}")
for run_id in sorted(by):
    print(f"{run_id}\trows={len(by[run_id])}\troot={root_by[run_id]}")
PY
```

真实 429 检查必须用错误文本，不要把 ALFWorld progress bar 的 `429/494` 误判为 rate limit：

```bash
rg -n "Error code: 429|too_many_requests|Too Many Requests|Rate limit|rate_limit" \
  outputs/ablation_alfworld_nonray_20260505_run/logs \
  outputs/ablation_longpair_20260504_run/logs/LONGPAIR-spreadsheetbench-changed.log \
  outputs/ablation_lrctrl_20260504_run/logs/LRCTRL-docvqa-full-rewrite.log \
  outputs/ablation_lrctrl_autonomous_noprior_20260505_031612_run/logs/LRCTRL-spreadsheetbench-autonomous.rerun_20260505_0800.log \
  2>/dev/null || true
```

### 3.8 Fresh-machine handoff

新机器目标：不要重复当前 19 个 active setting；只补跑 17 个 not-started setting。若新机器和当前机器共享同一磁盘，必须使用新的 run root，避免与当前 active writer 混写。推荐：

```text
ALFWorld remaining root:
outputs/ablation_alfworld_nonray_newmachine_20260505_run

DocVQA no-prior autonomous root:
outputs/ablation_lrctrl_autonomous_noprior_newmachine_20260505_run
```

环境准备：

```bash
git clone <repo-url> SkillReflection
cd SkillReflection
git checkout ablation

conda create -n reflact python=3.11 -y
conda activate reflact
python -m pip install -U pip
python -m pip install openai pyyaml openpyxl numpy gymnasium ray regex tqdm alfworld textworld

az login
az account show

export ALFWORLD_DATA=/home/azureuser/.cache/alfworld
test -d "$ALFWORLD_DATA/json_2.1.1/train"
[ -L data/docvqa_images ] || [ -d data/docvqa_images ]
```

如果 DocVQA 图片目录不在仓库内，按机器实际路径建立 symlink：

```bash
ln -s /path/to/docvqa_images data/docvqa_images
```

启动前验证：

```bash
PY=$(which python)
$PY -m py_compile \
  scripts/train.py \
  scripts/run_ablation_matrix.py \
  reflact/envs/alfworld/rollout.py \
  reflact/envs/docvqa/rollout.py \
  reflact/engine/trainer.py \
  reflact/model/azure_openai.py

$PY - <<'PY'
from reflact.envs.alfworld.dataloader import load_alfworld_splits
s = load_alfworld_splits("data/ablation_splits/alfworld/2-1-7_seed42")
print(len(s["train"]), len(s["val"]), len(s["test"]))
PY
```

只生成 ALFWorld 剩余 16 个 direct train 命令。注意：`run_ablation_matrix.py` 原始 dry-run 会枚举整个 ALFWorld matrix，显示 `num_experiments=32` 是正常的，但这 32 个不能全跑；其中 16 个已经在当前机器 active，只能启动 filtered list 里的 16 个 remaining run。

```bash
PY=$(which python)
$PY scripts/run_ablation_matrix.py \
  --groups default split batch mbs lr sched slown mod smodel longpair lrctrl \
  --bench alfworld \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_alfworld_nonray_newmachine_20260505_run \
  > /tmp/alfworld_all_32_commands.txt

$PY - <<'PY'
from pathlib import Path

remaining = {
    "LR-alfworld-8",
    "LR-alfworld-16",
    "SCHED-alfworld-constant",
    "SCHED-alfworld-linear",
    "SLOWN-alfworld-5",
    "SLOWN-alfworld-10",
    "SLOWN-alfworld-40",
    "MOD-alfworld-slow-only",
    "MOD-alfworld-meta-only",
    "MOD-alfworld-none",
    "SMODEL-alfworld-5.4",
    "SMODEL-alfworld-5.4-mini",
    "LONGPAIR-alfworld-changed",
    "LONGPAIR-alfworld-unchanged",
    "LRCTRL-alfworld-autonomous",
    "LRCTRL-alfworld-full-rewrite",
}

lines = Path("/tmp/alfworld_all_32_commands.txt").read_text().splitlines()
out = []
current = None
for line in lines:
    if line.startswith("# "):
        current = line[2:].strip()
        continue
    if current in remaining and "scripts/train.py" in line:
        out.append(f"# {current}")
        out.append(line)
        current = None

missing = remaining - {out[i][2:] for i in range(0, len(out), 2)}
if missing:
    raise SystemExit(f"missing commands: {sorted(missing)}")
Path("/tmp/alfworld_remaining_16_commands.txt").write_text("\n".join(out) + "\n")
print("remaining_alfworld_commands", len(out) // 2)
PY
```

只允许启动 `/tmp/alfworld_remaining_16_commands.txt` 里的这些 header 后面的命令，逐个用 `setsid ... > logs/<run_id>.log 2>&1 &` 手动启动：

```text
LR-alfworld-8
LR-alfworld-16
SCHED-alfworld-constant
SCHED-alfworld-linear
SLOWN-alfworld-5
SLOWN-alfworld-10
SLOWN-alfworld-40
MOD-alfworld-slow-only
MOD-alfworld-meta-only
MOD-alfworld-none
SMODEL-alfworld-5.4
SMODEL-alfworld-5.4-mini
LONGPAIR-alfworld-changed
LONGPAIR-alfworld-unchanged
LRCTRL-alfworld-autonomous
LRCTRL-alfworld-full-rewrite
```

生成 DocVQA no-prior autonomous direct train 命令，同样不加 `--execute`，只启动 `LRCTRL-docvqa-autonomous`，不要启动 full-rewrite：

```bash
PY=$(which python)
$PY scripts/run_ablation_matrix.py \
  --groups lrctrl \
  --bench docvqa \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_lrctrl_autonomous_noprior_newmachine_20260505_run \
  > /tmp/docvqa_lrctrl_noprior_command.txt
```

建议新机器第一批不要超过 16 个 direct train；如果 15-30 分钟内无真实 429、无 OOM、日志持续增长，再补到 20-24。不要把 helper/launcher 留在后台自动补位；本轮按手动观察、手动起进程执行。

## 4. 启动命令

当前恢复第一轮节奏：总并发约 24 个 train。具体做法是拆成 3 个 matrix launcher，每个 `--max-parallel 8`。不要给每个 launcher 设 24，否则会超过总并发预期。

如果刚修完 runner 或刚接入新 benchmark，可以先用 `--max-parallel 1` 做短 smoke；确认没有重复 out_root、tail-sample hang、配置错误后，再切到下面的 24-way 运行方式。

### 4.1 当前 24-way 启动方式

```bash
export ALFWORLD_DATA=/home/azureuser/.cache/alfworld

setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups default split batch mbs lr sched slown mod smodel \
  --bench docvqa \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_docvqa_20260503_160225_run \
  --max-parallel 8 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_docvqa_20260503_160225_run/launcher_parallel8.log 2>&1 &

setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups default split batch mbs lr sched slown mod smodel \
  --bench livemathematicianbench alfworld \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run \
  --max-parallel 8 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run/launcher_parallel8.log 2>&1 &

setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups batch \
  --bench searchqa spreadsheetbench \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_batch_searchqa_spreadsheet_20260503_153902_run \
  --max-parallel 8 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_batch_searchqa_spreadsheet_20260503_153902_run/launcher_parallel8.log 2>&1 &
```

### 4.2 Longitudinal comparison example policy 启动方式

ALFWorld 暂停不跑；其余四个 benchmark 用独立 run root，避免污染旧矩阵：

```bash
setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups longpair \
  --bench searchqa spreadsheetbench livemathematicianbench docvqa \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_longpair_20260504_run \
  --max-parallel 8 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_longpair_20260504_run/launcher_longpair_parallel8.log 2>&1 &
```

### 4.3 Learning-rate-control baseline 启动方式

ALFWorld 暂停不跑；其余四个 benchmark 用独立 run root：

```bash
setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups lrctrl \
  --bench searchqa spreadsheetbench livemathematicianbench docvqa \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_lrctrl_20260504_run \
  --max-parallel 8 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_lrctrl_20260504_run/launcher_lrctrl_parallel8.log 2>&1 &
```

注意：`run_ablation_matrix.py` 会在启动时跳过当时 active 的 run，但不会管理先前 orphan train 的生命周期。重启 launcher 前后必须检查 `env.out_root` 是否重复；如果有两个进程写同一目录，立刻杀掉重复进程、删除污染目录、让 launcher 干净重启该 run。

### 4.4 实时监控命令

进程数和重复输出目录检查：

```bash
/home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python - <<'PY'
import subprocess, re, collections
try:
    raw = subprocess.check_output(["pgrep", "-af", "scripts/train.py"], text=True)
except subprocess.CalledProcessError:
    raw = ""
roots = []
for line in raw.splitlines():
    m = re.search(r"env\.out_root=([^\s]+)", line)
    if m:
        roots.append(m.group(1))
ctr = collections.Counter(roots)
print("train_count", len(roots))
print("duplicate_roots", [r for r, c in ctr.items() if c > 1])
for root in sorted(roots):
    print(root.rsplit("/", 1)[-1])
PY
```

launcher 和错误日志检查：

```bash
for f in \
  outputs/ablation_docvqa_20260503_160225_run/launcher_parallel8.log \
  outputs/ablation_livemath_alfworld_clean_20260503_155155_run/launcher_parallel8.log \
  outputs/ablation_batch_searchqa_spreadsheet_20260503_153902_run/launcher_parallel8.log
do
  echo "### $f"
  tail -80 "$f" 2>/dev/null || true
done

rg -n "Traceback|ERROR|Error code|AuthenticationError|BadRequest|RateLimit|content_filter|Killed|rc=|\\[FAIL\\]|\\[RETRY\\]" \
  outputs/ablation_docvqa_20260503_160225_run/logs \
  outputs/ablation_livemath_alfworld_clean_20260503_155155_run/logs \
  outputs/ablation_batch_searchqa_spreadsheet_20260503_153902_run/logs \
  -g '*.log' | tail -120 || true
```

结果行数进度检查：

```bash
/home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python - <<'PY'
from pathlib import Path
roots = [
    Path("outputs/ablation_docvqa_20260503_160225_run"),
    Path("outputs/ablation_livemath_alfworld_clean_20260503_155155_run"),
    Path("outputs/ablation_batch_searchqa_spreadsheet_20260503_153902_run"),
]
for root in roots:
    print("\\n##", root.name)
    for run in sorted([p for p in root.iterdir() if p.is_dir() and p.name != "logs"]):
        summary = run / "summary.json"
        if summary.exists():
            print("DONE", run.name)
            continue
        files = sorted(run.rglob("results.jsonl"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
        if not files:
            print("NO_RESULTS", run.name)
            continue
        f = files[-1]
        print("RUN", run.name, sum(1 for _ in f.open()), f.relative_to(run))
PY
```

DocVQA 是多模态 benchmark，`2-1-7` 默认 test 有 3744 个样本、selection 有 535 个样本；完整 28-run 矩阵成本显著高于 SearchQA/SpreadsheetBench。高并发时必须持续看 rate limit、content filter、重复 out_root 和尾样本 timeout。

## 5. 已完成的本地验证

当前本地验证状态：

| 项 | 状态 |
| --- | --- |
| `py_compile` | 已通过：launcher、train、OpenAI wrapper、LiveMathBench dataloader/adapter、ALFWorld dataloader/adapter/rollout、DocVQA adapter/rollout |
| Tail-sample hang audit | 已通过：SearchQA、SpreadsheetBench、LiveMathBench、ALFWorld、DocVQA rollout active paths 均移除裸 `as_completed` |
| LiveMathBench split | 已加载：train=35 val=18 test=124 |
| ALFWorld split | 已加载：train=39 val=18 test=134 |
| ALFWorld gamefile | 39+18+134 个本地路径全部存在 |
| ALFWorld env smoke | 已通过：单环境 build/reset，reset 后 gamefile 与 fixed split item 一致 |
| ALFWorld reflect `None` fields | 已修复：trajectory 的 `action/env_feedback/reasoning/cmd/obs/content` 先归一为空字符串再截断；修复前 ALFWorld run 不可填表 |
| ALFWorld slow-update `None` fields | 已修复：`reflact/optimizer/slow_update.py` 读取 comparison trajectory 时同样归一 `None`；修复前失败 run 已删除并用同一 matrix launcher 重挂 |
| LiveMathBench token cap | 已修复：旧 768/512 cap 导致 GPT-5.x hidden reasoning 吃完预算，results 中大量空 response；已提到 16384 并通过 8 条 smoke（empty=0, `<answer>`=8/8, acc=0.625） |
| ALFWorld token cap | 已修复：旧 512 cap 下 conversation 存在空 `model_response/no_action`；已提到 2048，旧 512-token run 已归档并重启 |
| ALFWorld empty action fallback | 已修复：`rollout.py` 对 empty response / missing `<action>` 统一 fallback 到 `<action>look</action>`；所有修复前启动的 ALFWorld active run 已归档，不能填表 |
| Launcher dry-run | 已验证：LiveMathBench/ALFWorld clean matrix 56 个；DocVQA matrix 28 个；SearchQA/SpreadsheetBench batch-size 8 个 |

2026-05-04 token-cap restart:

```bash
export ALFWORLD_DATA=/home/azureuser/.cache/alfworld
setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups default split batch mbs lr sched slown mod smodel \
  --bench livemathematicianbench alfworld \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run \
  --max-parallel 8 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run/launcher_parallel8_tokenfix_20260504_0223.log 2>&1 &
```

Token-cap restart monitor checks:

```text
LiveMath old evidence: DEFAULT baseline test 124 rows, 115 empty response, only 9 answer tags.
LiveMath 4096 smoke: 8 rows, 5 empty response, not enough.
LiveMath 16384 smoke: 8 rows, 0 empty response, 8 answer tags, acc=0.625.
New run first check: LiveMath DEFAULT/SPLIT selection baseline 38 rows total, empty=0, answer_tag=38/38.
New ALFWorld first check: SPLIT-alfworld-1shot first conversation 29 steps, empty_resp=0, no_action=0.
Archives:
- outputs/ablation_livemath_alfworld_clean_20260503_155155_run/archive_livemath_token768_20260504_022258/
- outputs/ablation_livemath_alfworld_clean_20260503_155155_run/archive_alfworld_token512_20260504_021417/
```

2026-05-04 parallelism top-up:

```text
SearchQA/SpreadsheetBench batch-size matrix completed, freeing 8 slots. DocVQA launcher remains at 8 active train processes. A second LiveMath/ALFWorld launcher was started with --max-parallel 16 on the same run_root; run_ablation_matrix active_run_ids() skips existing active out_roots and only starts pending runs. This brought total active train processes back to 24 with no duplicate out_root.
```

```bash
export ALFWORLD_DATA=/home/azureuser/.cache/alfworld
setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups default split batch mbs lr sched slown mod smodel \
  --bench livemathematicianbench alfworld \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run \
  --max-parallel 16 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run/launcher_parallel16_tokenfix_topup_20260504_0240.log 2>&1 &
```

Top-up verification:

```text
train_count=24
duplicate_roots=[]
newly started: BATCH-livemathematicianbench-{8,24,56,full}, BATCH-alfworld-{8,24,56,full}
```

2026-05-04 ALFWorld empty-action fallback restart:

```text
发现 DEFAULT-alfworld-5.5 和 BATCH-alfworld-8 中各有 1 条 empty model_response/no_action。为了不混用旧代码，已停掉并归档所有修复前启动的 ALFWorld active run：
- DEFAULT-alfworld-5.5
- SPLIT-alfworld-1shot
- SPLIT-alfworld-1-1-8
- SPLIT-alfworld-4-1-5
- BATCH-alfworld-8
- BATCH-alfworld-24
- BATCH-alfworld-56
- BATCH-alfworld-full

归档目录：
- outputs/ablation_livemath_alfworld_clean_20260503_155155_run/archive_alfworld_empty_action_20260504_025311/
- outputs/ablation_livemath_alfworld_clean_20260503_155155_run/archive_alfworld_prefallback_20260504_025402/

launcher 已记录这些 run 为 rc=-6 retry；后续 retry 使用修复后的 `reflact/envs/alfworld/rollout.py`。当前 24 并发已满，ALFWorld default/split/batch retry 会在槽位释放后启动。当前 active ALFWorld 是修复后启动的 MBS-alfworld-{1,2,4}。
```

2026-05-04 ALFWorld OOM/concurrency adjustment:

```text
在 24 总并发下，ALFWorld 多个 run 同时进入 Ray/ALFWorld env 初始化和 slow-update rollout，触发 Ray OOM prevention：
memory 约 823GB / 866GB (0.950+) 超过 Ray 默认 0.95 阈值，导致 worker 被杀。

受影响并归档的 partial run：
- MBS-alfworld-{1,2,4,16,32}
- LR-alfworld-{2,4,8,16}
- SCHED-alfworld-{constant,linear}
- SLOWN-alfworld-{5,10,40}

归档目录：
- outputs/ablation_livemath_alfworld_clean_20260503_155155_run/archive_alfworld_oom_partial_20260504_050517/

已停掉 LiveMath/ALFWorld 两个 launcher：
- launcher_parallel8_tokenfix_20260504_0223.log 对应进程
- launcher_parallel16_tokenfix_topup_20260504_0240.log 对应进程

当前只保留已跑较久的 `LR-alfworld-1` 继续，DocVQA launcher 不动，LiveMath 已启动进程继续。后续 ALFWorld 必须低并发补跑，建议 `--bench alfworld --max-parallel 1` 或最多 2；不要再把 ALFWorld 混入 24 总并发。
```

2026-05-04 ALFWorld serial retry launcher:

```bash
export ALFWORLD_DATA=/home/azureuser/.cache/alfworld
setsid /home/azureuser/workspace-gzy/miniconda3/envs/reflact/bin/python \
  scripts/run_ablation_matrix.py \
  --groups default split batch mbs lr sched slown mod smodel \
  --bench alfworld \
  --run-root /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run \
  --max-parallel 1 \
  --execute \
  > /home/azureuser/workspace-gzy/SkillReflection/outputs/ablation_livemath_alfworld_clean_20260503_155155_run/launcher_alfworld_serial_20260504_1258.log 2>&1 &
```

```text
launcher_pid=9322
first started: DEFAULT-alfworld-5.5
valid existing ALFWorld result before serial retry: LR-alfworld-1
reason: previous high-concurrency ALFWorld runs hit Ray OOM; serial retry avoids mixing ALFWorld into 24-way total concurrency.
```

2026-05-04 ALFWorld serial retry paused:

```text
DEFAULT-alfworld-5.5 启动 Ray 后，系统内存 available 从约 19GiB 降到约 6GiB，Ray 同时报 `/tmp/ray` spill 风险。为避免影响正在跑的 DocVQA/LiveMath，已停掉串行 ALFWorld launcher 和 DEFAULT-alfworld-5.5 train 进程。

归档目录：
- outputs/ablation_livemath_alfworld_clean_20260503_155155_run/archive_alfworld_serial_lowmem_20260504_1300/

后续重启条件：DocVQA/LiveMath 当前队列进一步释放资源后，再用同一串行命令重启 ALFWorld；不要在 available memory 只有十几 GiB 时启动 ALFWorld。
```

2026-05-04 current monitor and GPU-memory clarification:

```text
当前 SkillReflection active train processes=12，无重复 env.out_root：
- LR-docvqa-16
- MOD-docvqa-meta-only
- MOD-docvqa-none
- MOD-docvqa-slow-only
- SCHED-docvqa-constant
- SCHED-docvqa-linear
- SLOWN-docvqa-10
- SLOWN-docvqa-40
- SLOWN-docvqa-5
- SMODEL-docvqa-5.4
- SMODEL-docvqa-5.4-mini
- SMODEL-livemathematicianbench-5.4

最新完成并已填表：
- LR-docvqa-8: best_sel=0.9047, base=0.8675, best_test=0.9017, delta=+0.0342, tokens=279012493

SkillReflection ALFWorld 当前没有在跑。当前有效 ALFWorld summary 只有：
- LR-alfworld-1

nvidia-smi 显示 GPU 显存被 ray::ServeReplica:*GroundingDINOModel / DA3Model 占用，但这些进程 cwd 是：
/home/azureuser/workspace-gzy/zyf/gca-skill

这不是本仓库 /home/azureuser/workspace-gzy/SkillReflection 的 ALFWorld ablation。

另有 unrelated ALFWorld jobs 在：
/home/azureuser/zisu/skill_distill

这些不是本轮 SkillReflection ablation 输出，不能混进本表。
```

## 6. 不纳入本轮的内容

本轮不启动以下实验：

| 项 | 原因 |
| --- | --- |
| 已完成 default 点的重复 run | 复用 default 结果，避免同一设置重复计费 |
| `train.batch_size=40` 重复 run | 复用 default 结果，避免同一设置重复计费 |
| `model.student=gpt-5.5` student-model 重复 run | 复用 default 结果 |
| `gradient.minibatch_size=8` 重复 run | 复用 default 结果 |
| `optimizer.lr_scheduler=cosine` 重复 run | 复用 default 结果 |
| `optimizer.slow_update_samples=20` 重复 run | 复用 default 结果 |
| `use_slow_update=true,use_meta_skill=true` 重复 run | 复用 default 结果 |
