# Wordtally: an agent workflow experiment

Wordtally is a small Python word counter used to test a larger system: spec-driven development
with AI agents, independent audits, human-controlled PRs, executable evidence, and a dashboard
that measures the work. It is a pilot of the
[agentic workflow kit](https://github.com/Yusuprozimemet/agentic-workflow-kit).

The product is the test case. The workflow, its controls, and what they reveal are the experiment.

## Status and navigation

Paused after Day 5 on 2026-10-28; the product plan is delivered. The final notebook entry is
dated 2026-10-29. Further work requires a new plan and maintainer direction. Jev's E1 experiment
ended in **no-go**; it is not an active workflow agent or CI gate.

- [Working order](CLAUDE.md), [spec rules](specs/README.md), and [workflow guide](docs/workflow.md).
- [Live dashboard](https://yusuprozimemet.github.io/wordtally/).
- [Lab notebook](docs/lab-notebook.md): measurements, experiments, audits, and remaining gaps.
- [Product plan](plan.md), [workflow experiment plan](docs/workflow-improvement-plan.md), and
  [spec-drift improvement plan](docs/spec-drift-improvement.md). Plans describe proposals;
  the implementation and notebook establish what actually landed.

Blue means work or artifacts; purple means agents or review; green means automation or
measurement; amber means human decisions; red means failures or limitations.

## 1. The experiment as a whole

```mermaid
flowchart TD
    Goal["Test an agent development system"] --> Workflow["Spec-driven workflow<br/>Small PRs and merge stops"]
    Goal --> Agents["Separate implementation<br/>and independent review"]
    Goal --> Controls["Executable controls<br/>Tests, CI, invariants and hooks"]
    Workflow --> Pilot["Wordtally<br/>Small application as test case"]
    Agents --> Pilot
    Controls --> Pilot
    Pilot --> Records["Git, PRs, specs, Notes,<br/>break evidence and transcripts"]
    Records --> Observe["Dashboard and spec drift<br/>Progress, evidence, defects and cost"]
    Observe --> Findings["Findings and open items"]
    Findings --> Decision{"Maintainer decision"}
    Decision --> Improve["Improve rules, scripts or CI"]
    Improve --> Workflow
    Improve --> Controls
    Decision --> Pause["Pause or define another experiment"]
    class Goal,Workflow,Pilot,Records,Improve work
    class Agents,Findings review
    class Controls,Observe auto
    class Decision,Pause human
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

## 2. Agents, models, and authority

The main session is documented as Opus 5.5. Plan and spec auditors inherit their session model;
their definitions do not pin one. The implementer and defect rater have explicit model IDs.

```mermaid
flowchart TD
    Human["Maintainer<br/>Scope, departures, merges and continuation"] --> Main["Main session: Opus 5.5<br/>Specs, briefs, review, full checks,<br/>commits, PRs and closing records"]
    Main -->|"PRs and findings"| Human
    Main -->|"Phase review"| PA["Plan auditor: inherited model<br/>Plan, specs, code and hand-offs"]
    Main -->|"Day review"| SA["Spec auditor: inherited model<br/>Claims, checks and hold criteria"]
    PA -->|"Read-only findings"| Main
    SA -->|"Read-only findings"| Main
    Main -->|"One-track brief"| Impl["Implementer: Haiku 5.5<br/>claude-haiku-5-5"]
    Impl -->|"Code, tests and targeted results<br/>Never commits or pushes"| Main
    Main -->|"Blinded defect record"| Rater["Defect rater: Opus 5.5<br/>claude-opus-5-5"]
    Rater -->|"Independent labels"| Main
    Main -->|"After Day 5 close merges"| Final["Independent audits on Opus<br/>Security-ops, agentic engineering,<br/>and architecture: separate contexts"]
    Final -->|"Separate reports"| Human
    Guard["auditor-guard.py hooks<br/>Command and repository-change checks"] -.-> PA
    Guard -.-> SA
    Guard -.-> Final
    Human -.-> Limit["Open gap: owner-level agent credentials<br/>Human-only merging is an instruction"]
    class Main,Impl work
    class PA,SA,Rater,Final review
    class Guard auto
    class Human human
    class Limit risk
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

## 3. The development loop

Every PR uses the validation pipeline below. Tracks run sequentially from fresh `main`, following
`CLAUDE.md`; `specs/README.md` still contains a conflicting parallel-tracks sentence. The actual
phase order was Days **1, 3**, stop, then Days **2, 4, 5**, stop.

```mermaid
flowchart TD
    Start["Maintainer starts a day<br/>Fresh session: plan, specs, current code<br/>spec-drift.py reports next step"] --> First{"Phase starts?"}
    First -->|Yes| PA["Plan audit"]
    First -->|No| SA["Spec audit"]
    PA --> SA
    SA --> Findings{"Corrections needed?"}
    Findings -->|Yes| Spec["Spec-change PR<br/>Plan-change PR if goal changes"]
    Spec --> SP["PR pipeline and maintainer merge<br/>Fresh main and dashboard refresh"]
    SP --> Track["Next track from fresh main<br/>Track 0 first when needed"]
    Findings -->|No| Track
    Track --> Brief["Main session writes brief"]
    Brief --> Impl["Implementer writes code and tests"]
    Impl --> Review["Main session reviews<br/>Full checks and recorded intentional breaks"]
    Review --> TP["PR pipeline and maintainer merge<br/>Fresh main and dashboard refresh"]
    TP --> More{"More tracks?"}
    More -->|Yes| Track
    More -->|No| Close["Closing PR<br/>Verify on main; criteria and evidence<br/>Notes, notebook and token usage<br/>Blind defect relabel and decisions"]
    Close --> CP["PR pipeline and maintainer merge<br/>Fresh main and dashboard refresh"]
    CP --> End{"Phase ends?"}
    End -->|No| Wait["Report next step<br/>Wait for maintainer direction"]
    Wait --> Start
    End -->|Yes| Audit["Phase-end plan audit<br/>Day 5: three additional audits"]
    Audit --> Stop["Report and stop<br/>Maintainer decides further work"]
    class Start,Spec,Track,Brief,Impl,Close work
    class PA,SA,Review,Audit review
    class SP,TP,CP auto
    class First,Findings,More,End,Wait,Stop human
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

## 4. Local checks, CI, and human merge

CI passing does not authorize the agent to merge. Frozen word-rule tests cannot be edited as a
routine fix; an unmet criterion or required frozen-test change needs a recorded departure and
maintainer decision. There is no repository `/close-day` skill or single preflight script.

```mermaid
flowchart TD
    Change["Prepared changes"] --> Local["Local preflight<br/>Unit tests and expected count<br/>Naming, diff size, Markdown links<br/>Evidence and PR-description review"]
    Local --> Ready{"Pass?"}
    Ready -->|No| Fix["Correct changes or records"]
    Fix --> Local
    Ready -->|Yes| Open["Commit, push and open PR"]
    Open --> CI["GitHub Actions<br/>Unit tests; template; naming<br/>400-line default limit<br/>Frozen files and test-count invariants<br/>Track tests seen red<br/>Relevant tooling tests"]
    CI --> Result{"Applicable checks pass?"}
    Result -->|No| Fix
    Result -->|Yes| Human["Stop and wait<br/>Maintainer reviews and merges"]
    Human --> Main["Fresh main<br/>Refresh dashboard and report next step"]
    class Change,Open work
    class Local,CI,Main auto
    class Ready,Result,Human human
    class Fix risk
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

The size gate allows an explicit `Oversized:` reason. Service-wiring validation applies when
services exist. Tooling tests are selected by the files changed.

## 5. Evidence creation and historical replay

A passing test, a reproduced break, and evidence that covers every promise are different claims.
Closing PRs collect prior evidence; they should not first demonstrate that a criterion can fail.

```mermaid
flowchart TD
    Criterion["Checkable acceptance criterion"] --> Type{"new or hold?"}
    Type -->|new| New["Test fails on earlier code<br/>and passes after implementation"]
    New --> Seen["seen-red.py locally<br/>track-red.py in CI"]
    Type -->|hold| Hold["Check passes before and after"]
    Hold --> Break["break.py: intentionally break implementation<br/>Observe expected failure; restore bytes"]
    Break --> Record["Record actual broken: output<br/>and replay arguments"]
    Seen --> PR["Evidence in the PR that first runs the check"]
    Record --> PR
    PR --> Close["Closing PR collects evidence under criteria"]
    Close --> Checker["Explicit evidence.py run<br/>Historical scratch worktrees"]
    Checker --> Checks["Named-test presence at closing revision<br/>Execute Verify commands<br/>Replay breaks and compare reports"]
    Checks --> Report["evidence-checks.json<br/>Results, revisions and input hashes"]
    Report --> Dashboard["Dashboard validates applicability<br/>Current, stale, missing or invalid<br/>Passed, failed, error, not applicable"]
    Checks -.-> Limit["Replay does not establish<br/>complete behavioral coverage"]
    class Criterion,Type,New,Hold,Record,PR,Close,Report work
    class Seen,Break,Checker,Checks,Dashboard auto
    class Limit risk
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

Intentional breaks never merge. CI tests the checker; dashboard builds read its committed report
without replaying historical commands. A missing or stale report is not a current pass.

## 6. Dashboard data flow

The dashboard reports the workflow; it does not decide merges or override the sources of truth:
`plan.md` for goals, merged specs for promises, and code on `main` for actual behavior.

```mermaid
flowchart LR
    Git["Git history and merge snapshots"] --> Engine["spec-drift.py<br/>Measurements and workflow-state reconstruction"]
    GH["GitHub via gh<br/>PR metadata and workflow runs"] --> Engine
    Specs["Plan, specs, Notes and configuration"] --> Engine
    Transcripts["Local transcripts"] --> Tokens["token-usage.py"]
    Tokens --> TokenJSON["Committed token-usage.json"]
    TokenJSON --> Engine
    Evidence["Explicit evidence.py run"] --> EvidenceJSON["Committed evidence-checks.json"]
    EvidenceJSON --> Engine
    Trigger["Push to main or manual dispatch"] --> Action["Dashboard GitHub Actions"]
    Action --> Engine
    Engine --> Progress["Days, tracks, criteria and next step"]
    Engine --> Drift["Name coverage, gap and history"]
    Engine --> Quality["Defects, hand-off citations,<br/>verification and evidence checks"]
    Engine --> Cost["Token usage and work measurements"]
    Progress --> Build["Build dashboard HTML"]
    Drift --> Build
    Quality --> Build
    Cost --> Build
    Build --> Pages["GitHub Pages"]
    class Git,GH,Specs,Transcripts,TokenJSON,EvidenceJSON work
    class Engine,Tokens,Evidence,Trigger,Action,Progress,Drift,Quality,Cost,Build,Pages auto
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

## 7. What spec drift measures

Measurements use extracted names, not semantic understanding. Historical snapshots only use
names known at that point, so later specs do not move earlier measurements.

```mermaid
flowchart TD
    Snapshot["Each merge snapshot"] --> Spec["Code-like names from<br/>plan and spec backticks"]
    Snapshot --> Code["Scan permitted code files<br/>Exclude specs and excluded paths<br/>Apply comment filtering; retain paths"]
    Spec --> S["S: names currently in specs"]
    Code --> A["A: names in scanned code"]
    Code --> P["P: names in production paths"]
    S --> Coverage["All-code coverage: intersection of S and A / size of S"]
    A --> Coverage
    S --> Prod["Production coverage: intersection of S and P / size of S"]
    P --> Prod
    S --> Lists["Names absent from all code<br/>Names present only outside production<br/>Matching paths and categories"]
    Code --> Lists
    S --> Jaccard["Jaccard: intersection / union<br/>Within historically known vocabulary"]
    A --> Jaccard
    Spec --> Counts["Spec and code name-count vectors"]
    Code --> Counts
    Counts --> Gap["Gap angle between count vectors"]
    Counts --> Shuffle["Seeded shuffled-count reference<br/>Mean and 95% reference band"]
    Gap --> Compare["Inside, below or above reference band"]
    Shuffle --> Compare
    Snapshot --> History["Compare name presence across snapshots"]
    History --> Kept["Names kept: dropped from specs,<br/>still in scanned code"]
    History --> Retired["Names retired: currently in specs,<br/>absent from code but present earlier"]
    Compare -.-> Limit["Diagnostics, not correctness tests<br/>Path classification does not prove execution<br/>Name presence does not prove behavior"]
    Prod -.-> Limit
    class Snapshot,Spec,Code,S,A,P,Counts,History work
    class Coverage,Prod,Lists,Jaccard,Gap,Shuffle,Compare,Kept,Retired auto
    class Limit risk
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

## 8. How the workflow learns

```mermaid
flowchart TD
    Problem["Mistake, escape or audit finding"] --> Notes["Day Notes<br/>found: discovery point<br/>cause: category<br/>made: originating day"]
    Notes --> Blind["Blind independent defect relabel"]
    Blind --> Notebook["Record disagreement decisions<br/>Lab notebook and open items"]
    Notebook --> Decision{"Maintainer decision"}
    Decision --> Rule["Workflow instruction"]
    Decision --> Script["Deterministic script or CI gate"]
    Decision --> Experiment["Separately evaluated experiment"]
    Decision --> Open["Keep open explicitly"]
    Rule --> Risk["Instructions can be skipped"]
    Script --> Regression["Test the checker itself<br/>including intentional failures"]
    Regression --> Enforce["Repeatable enforcement"]
    Experiment --> E1["E1: evidence judgment<br/>Frozen cases and labels<br/>Jev versus Opus and baseline"]
    E1 --> Verdict["NO-GO<br/>Both models flagged all 12 real supports cases"]
    Verdict --> Halt["No Jev adoption or shadow-day continuation"]
    Notebook --> Remaining["Open controls include credentials,<br/>trusted check sources and frozen control plane"]
    Remaining --> Human["Paused: new plan required"]
    class Notes,Notebook,Rule work
    class Blind,Experiment,E1 review
    class Script,Regression,Enforce auto
    class Decision,Open,Human human
    class Problem,Risk,Verdict,Halt,Remaining risk
    classDef work fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    classDef review fill:#EDE9FE,stroke:#7C3AED,color:#4C1D95
    classDef auto fill:#DCFCE7,stroke:#16A34A,color:#14532D
    classDef human fill:#FEF3C7,stroke:#B45309,color:#78350F
    classDef risk fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
```

## Findings

- Every day's estimate held (3 pull requests each), and frozen word-rule tests were never edited.
- A lesson written only in Notes did not reach the next day: the same gap recurred on Days 4
  and 5. Behavior changed where a lesson became a rule or script.
- Seen-red evidence was skipped twice before a CI gate enforced it.
- Measurement tools need their own checks: spec evidence once counted as implementation;
  auditor hooks behaved differently across Claude Code clients.
- Human-only merging remains an instruction while the agent has the owner's admin credentials.
  The notebook records the remaining controls to address before more autonomy.

## Run the test application and checks

Wordtally uses Python 3.10+ and the standard library. It counts lines, words, and characters;
supports files or standard input; and adds top words, a built-in stopword filter, and JSON output.
A word is a run of ASCII letters, digits, and apostrophes. Stopwords affect only the top list.

```bash
python -m wordtally --help
python -m wordtally --top 3 example.txt
python -m unittest discover -s tests -t .
```

The measurement tools additionally need `numpy`, `gh` authenticated to GitHub, and Node for page
tests. Run the relevant tooling checks when changing the measurement system:

```bash
python scripts/test_spec_drift.py
python scripts/test_evidence.py
python scripts/spec-drift.py --out spec-drift.json
```
