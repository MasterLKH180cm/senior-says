# Development Execution Contract

> Delivery-first、resource-adaptive、review-required、review-aware。目標是交付最小且安全的可合併增量，而不是累積流程、文件、測試或代理活動。

## 0. 核心原則與優先序

依下列優先序處理衝突：

1. 資料安全、資安邊界、法規要求與 repository 強制政策。
2. 使用者明確指定的目標、範圍與驗收條件。
3. 本文件的預設流程。

硬性規則：

- 嚴格禁止 over-engineering、無關 refactor、重複掃描、重複測試與形式化文件膨脹。
- 不得宣稱未執行的 test、review、audit、skill、CI、approval 或 merge 已完成。
- 任何 production-code diff 在 commit／push 前都必須完成一次 final code review、一次 code smell／bad smell review，以及 focused security review；三者可在同一 consolidated pass 中完成，但不得被測試、CI 或 reviewer approval 取代。
- 以 working code、可驗證 evidence、可 rollback 與可 review 為完成標準；文件與流程本身不是進度。
- 任務開始時先確認：`Goal`、`Context`、`Constraints`、`Done when`、`Non-goals`。可安全推斷時直接推斷；只有無法安全決定且會影響 correctness、security 或 public contract 時才詢問。

## 1. 不可妥協的安全規則

### Git 與使用者資料

- 不得直接在 `dev`、`staging` 或 `main` 開發。
- 使用語意清楚且短生命週期的 `feat/*`、`fix/*`、`hotfix/*` 或 `refactor/*` branch。
- PR target 預設為 `dev`，除非 repository policy、issue 或使用者另有指定。
- 禁止 `git reset --hard`、`git clean`、`stash drop`、覆蓋未知變更、刪除未知檔案與自動 merge。
- 無法判斷的 local change 視為使用者既有工作並原樣保留。
- 只有存在平行工作、無關 local changes、branch 衝突或 repository policy 時才建立 worktree；不要為形式建立 worktree。
- 每個 increment 必須可獨立 review、validate、merge 與 rollback，預期一個工作日內 ready for review。

### Secrets、local artifacts 與 migrations

- 不得輸出、stage、commit 或 push `.env`、token、credential、secret、audit artifact、local checklist 或臨時產物。
- 不得修改既有 migration；只能依 repository ordering 新增下一個 migration。
- migration 變更必須驗證 ordering、upgrade path 與 repository 規定的 migration tests；downgrade 依 repository policy。
- 不得為了通過測試改寫 migration history 或加入 test-only production behavior。

### Merge

只有使用者明確要求，且 CI、required approvals、branch policy 與 blocking feedback 全部滿足時才可 merge。

## 2. Contract／Compliance 不得成為預設工作流

Contract、ADR、OpenSpec、compliance memo、policy 文件與 governance record 都不是每個 high-risk 任務的預設產物。

### 只有符合下列任一 trigger 才建立或修改治理文件

- issue、PR、repository policy、法規控制或指定 owner 明確要求。
- 本次 diff 實際改變 public API、shared schema、cross-service contract、trust boundary、authorization semantics、audit identity、deployment contract 或 production control，且既有 authoritative document 會因此失真。
- merge 或 deployment 的正式 gate 明確要求該 evidence。
- 已確認既有 authoritative document 與實作不一致，且本 PR 的 acceptance criteria 包含修正。

未符合 trigger 時：

- 不建立新 contract／compliance 文件。
- 不因「可能需要」而撰寫 ADR、design memo、matrix 或長篇證明。
- PR body、issue comment 或既有文件中的最小修正足夠時，不新增平行文件。
- 不把 internal skill、audit 流程、OpenSpec 或本機 checklist 名稱寫入 PR。

### 決策與等待分類

將阻塞狀態明確分類：

- `READY`：可安全實作。
- `BLOCKED_DECISION`：未決定事項直接決定 security、behavior 或 public contract；不得猜測。
- `BLOCKED_EXTERNAL_APPROVAL`：實作或文件已完成，只等待 reviewer、compliance owner、CI 或 operator。
- `BLOCKED_ENVIRONMENT`：必要環境、credential、service 或 fixture 不可用。

處理原則：

- 只凍結受影響的 increment，不凍結整個 issue。
- approval 預設是 merge／deploy gate，不是本機分析與獨立實作的 gate；repository policy 明確相反時除外。
- `BLOCKED_DECISION` 時，只可實作不依賴該決策的 invariant、backward-compatible、additive、disabled 或 flag-off 部分。
- `BLOCKED_EXTERNAL_APPROVAL` 時，凍結該 branch scope，記錄 owner 與 exact blocker，然後切換到下一個獨立 increment；不得停下等待或反覆催促。
- 不得以 feature flag 或 compatibility layer 掩蓋不安全、不可部署或無法 rollback 的修改。

需要 decision request 時，內容限制為：

1. 待決定的一句話。
2. 可行選項與差異。
3. 建議選項及理由。
4. 被阻塞的 exact scope。
5. owner／required approver。
6. 已有 evidence 或連結。

除非正式政策要求，不擴寫成完整 contract 或 compliance memo。

## 3. Adaptive Resource Governor 與程序生命週期

硬體資源應用來縮短 wall-clock time。系統仍流暢且工作彼此獨立時，不要預先降載；只有觀察到持續資源壓力、衝突或不穩定時才逐步節流。

### 正常模式（預設）

- 預設可使用主代理加最多 `2` 個 subagents；多 repository、明確 read-heavy discovery 或獨立 validation workstreams 可使用 `3` 個。只有預期節省時間明顯、ownership 清楚且系統保持流暢時，才暫時增加至 `4` 個。
- 禁止 nested subagents。write-enabled subagents 不得修改相同 files、contract、migration chain 或核心邏輯。
- 預設可同時執行最多 `3` 組 local commands；短時間、低負載且互不依賴的 commands 可暫時增加至 `4` 組。
- 最多可同時執行 `2` 組 heavy workloads，但必須彼此獨立、沒有相同 port／database／worktree／fixture 衝突，且具有足夠記憶體餘裕。不得同時啟動第 `3` 組 heavy workload。
- Heavy workload 包含 full test suite、全 repo typecheck、build、coverage、browser／E2E、Docker compose、dev server 或大量 code generation。
- 兩個同為高記憶體或高 CPU 的 Node／browser workloads 可以並行，但必須先判斷收益是否高於 contention；若啟動後系統仍流暢，不必僅因規則而中止。
- 正常模式下可使用 test runner 的預設 workers，不設固定 `50% CPU` 或 `2 workers` 上限。若同時執行兩個 CPU-heavy workloads，優先讓每組使用約 `50–70%` logical CPUs，避免 worker oversubscription。
- dev server、Docker service、browser、test database 或其他 long-lived process 若會在相鄰 phases 重用，可維持運作，不必為了形式化 phase boundary 反覆關閉與重啟；但必須登記 PID／用途並在不再需要時清理。
- 優先把 exploration、test discovery、log triage、PR inspection 與 review 交給 read-only subagent；implementation 只有 ownership 清楚時才平行。

### 動態降載條件

不得只因 CPU 短暫達到 100%、風扇轉快、單一 command 較慢或一個 process 使用大量資源就立即降載。只有出現持續且會影響工作或系統穩定性的訊號時才切換節流模式，例如：

- UI、terminal 或 shell input latency 反覆明顯增加。
- 可用記憶體長時間低於約 `15%`、pagefile／swap 持續成長，或出現 OOM。
- CPU 長時間高於約 `90%` 且 commands 沒有實質進展。
- thermal throttling、test runner crash、browser crash、Node heap exhaustion 或反覆 process spawn failure。
- 同時工作因 port、database、fixture、cache、lock 或 filesystem contention 互相干擾。

出現壓力時，依下列順序逐步處理，不直接退回全 serial：

1. 暫停或排隊最低優先的 heavy workload，將 heavy concurrency 從 `2` 降為 `1`。
2. 暫停新增 subagent；已接近完成且仍有價值的 read-only subagent 可繼續。
3. 將 test／build workers 限制為約 `60–75%` logical CPUs；只有壓力持續、runner 不穩定或記憶體不足時才改為 serial。
4. 暫停 coverage、profiling、非必要 E2E、dev server 或 background service。
5. 清理已完成、失去用途、hang 或 ownership 已確認的 agent-owned processes。

當 UI 恢復流暢、記憶體餘裕恢復、paging 停止且 commands 正常前進時，可逐步恢復正常模式；不得讓一次暫時降載永久限制後續工作。

### 命令與程序規則

- 任務開始時建立空的 agent-owned process registry；不要為了建立 baseline 掃描或管理全機程序。只登記本次任務實際啟動的 process。
- 優先重用目前 shell；不得為每個 command 開新的 CMD、PowerShell、terminal 或 Node runtime。
- automation 中禁止無界限 watch mode。不得使用 `gh pr checks --watch` 或無界限 polling。互動式 UI 驗證、短期 dev server 或明確有終止條件的 watch process 可以使用，但必須登記 PID 並在驗證完成後停止。
- 所有可能長時間執行的 command 必須有 timeout、明確終止條件或可追蹤 PID。
- 啟動 long-lived process 時，立即記錄：PID、parent PID、command、purpose、working directory、start time。
- 短命令優先前景執行並等待結束；需要 `Start-Process` 時使用 `-PassThru` 取得 process object／PID。
- 在 logical checkpoint 清理不再需要的 agent-owned processes。仍會在下一個相鄰 phase 重用的 process 可保留，不必為了清理數量而反覆重啟。
- 先嘗試 graceful shutdown；Windows 上可依 PID 使用 `Stop-Process` 並確認退出。若已知 parent PID 的 child tree 殘留，再使用 `taskkill /PID <pid> /T`；`/F` 只能作為最後手段。
- 嚴禁依 image name 全域終止 `node.exe`、`powershell.exe`、`pwsh.exe`、`cmd.exe` 或 terminal，避免殺死使用者與其他任務的程序。
- 不得終止未由本次任務啟動、ownership 不明或 PID 未驗證的程序。
- 完成前驗證 process registry 已清空；若無法清理，必須回報 exact PID、command、原因與安全的人工處理方式，不得假裝完成。

### 輸出與 context 控制

- 不把完整 build log、test log、stack trace 或重複 command output 灌入主執行緒。
- 只保留 command、exit status、關鍵 failure excerpt、changed files、finding 與 decision。
- subagent 只回傳摘要與 evidence，不回傳冗長逐步日誌。

## 4. GitHub PR Review Inbox：強制檢查點

不得只在使用者提醒後才讀 PR comments。

### Session 開始

1. 執行一次 `gh pr status`，只用於辨識目前 branch PR、本人 authored PR 與 review-requested queue；不得因此擴大當前任務。
2. 若目前 branch、issue 或使用者提供的連結已有 PR，開始修改前一次取得：
   - PR number／URL／head SHA／`updatedAt`
   - review decision、reviews、general comments
   - inline review comments 與 unresolved review threads
   - required CI checks
3. 將所有 feedback 分成 `blocking`、`non-blocking`、`question`、`follow-up`。
4. 未分類現有 feedback 前，不開始新的 in-scope implementation。

可使用：

- `gh pr view --json number,url,headRefOid,updatedAt,reviewDecision,comments,reviews,statusCheckRollup`
- `gh api graphql` 讀取 `reviewThreads { isResolved comments { ... } }`，或使用 GitHub REST review-comments endpoint。
- `gh pr checks --required`；不得使用 `--watch`。

### 必要重新檢查點

對有既存 PR 的任務，在下列時點讀取一次最新狀態：

- 開始修改前。
- push／更新 PR 前。
- push 後或 final report 前；若兩者相鄰且 `updatedAt`／head SHA 未變，同一次查詢即可同時滿足。
- 長任務進入下一個 increment 前。

保存本次 session 的 last-seen `updatedAt`、comment IDs 與 thread IDs；沒有變化就不得重複處理。禁止背景 polling、固定間隔刷新或等待 reviewer。

若出現新 blocking feedback：

- 先批次處理本輪全部 in-scope blockers，再做無關工作。
- 執行受影響的 targeted validation。
- 預設建立一個 logical follow-up commit。
- 以 evidence 回覆 comments；未驗證前不得 resolve thread 或宣稱完成。

## 5. 執行深度與 Skill Budget

依實際行為變更分類，不以檔名判斷。

### Fast

文件、copy、style、test-only、mechanical rename，或不影響 API、auth、permission、database、config 與 shared behavior 的局部修改。

- focused read、最小修改、1 個 targeted check、人工 diff review。
- 預設不使用 specialist skill 或 subagent。

### Standard

一般 production behavior、局部 API、frontend state／interaction、一般 bug fix。

- regression test 或 verification-first。
- 1–3 個 targeted validation commands。
- 最終 diff 一次 code review，加人工 focused security check。
- subagent 只有符合 Resource Governor 且可獨立時才使用。

### High-risk

authentication、authorization、session、tenant／site／patient isolation、PHI、signing、audit identity、public API／shared schema、migration、secret、deployment、parser／protocol、attacker-controlled input、filesystem／network privilege、concurrency／retry／idempotency、irreversible workflow 或 shared core。

- 增加與實際風險直接相關的 contract、auth、migration、integration 與 focused security evidence。
- High-risk 不自動要求新增治理文件、full repository audit、full suite 或所有 skills。
- 若 trust boundary 未改變，使用 focused manual security review 即可；若改變，只選一套最適用的 security skill。

### Skill 使用

- `$i-have-adhd` 可用於 scope 與節奏控制。
- `$TDD` 只用於有價值的 behavior regression；無法提供有效 red state 時改用 verification-first。
- `$code-review` 在 final candidate diff 執行一次：Standard、High-risk，以及包含 production code 的 Fast path 都必須執行；skill 不可用時使用等價人工 review。純文件、copy、style-only、test-only 或 mechanical change 可使用人工 diff review。
- code smell／bad smell review 不是可選 specialist skill，而是所有 code-changing increments 的必要 final review 面向；只列實際 finding、修正與 deferred 項目，不輸出逐項通過清單。
- `$spectra-audit` 只用於 scope／contract 不清、跨 repository、重大 trust boundary 或確認的 spec drift；不得因 High-risk 標籤自動執行。
- `$spectra-apply` 只在已有適用 checklist 且本 increment 必須依其實作時執行。
- security skills 預設互斥，只選一套；不得重複 full audit。
- frontend、React、UX、GSAP 或其他 domain skill 只在 production diff 實際涉及該領域時使用，預設一套。
- 同一 skill 每個 increment 預設最多一次；只有 scope、contract 或 trust boundary 實質改變才可重跑。

## 6. 執行流程

### Gate A — Preflight

一次完成：

- repository、branch、`git status`、staged／unstaged／untracked changes。
- repository instructions、linked issue／PR、現有 checklist。
- PR Review Inbox。
- agent-owned process baseline。
- entire issue 與 current increment 的 acceptance criteria、non-goals、dependency。
- branch／worktree suitability。

若 increment 無法在一個工作日內 ready for review，先拆分；不得建立大型 divergent branch。

### Gate B — Focused scope lock

只閱讀直接相關的 production code、callers／consumers、tests、contract 與必要 config；除非 evidence 要求，不做 full repository scan。

在修改前輸出並鎖定：

- current increment。
- affected files／call path／data flow。
- risk class。
- contract／compliance artifact trigger：`Yes` 或 `No`，以及理由。
- 最小測試計畫。
- resource plan：subagents、heavy commands、long-lived processes。
- 明確 deferred／follow-up。

Checklist 只有 scope 必須預先反映時才更新一次；否則到 final commit 後再更新。Checklist 不得進入 Git diff。

### Gate C — Implement

- 只做 acceptance criteria 所需的最小 production change。
- behavior change／bug fix：優先建立有價值的 regression；red state 成本過高或不可靠時記錄理由並使用 verification-first。
- 不加入 speculative abstraction、無必要 fallback、broad formatting、無關 cleanup 或 test-only production path。
- 未啟用功能使用安全的 additive／disabled／flag-off／compatibility isolation，並記錄 activation 與 cleanup follow-up。
- 每完成一個 bounded phase，立即清理不再需要的 process。

### Gate D — Validation Budget

測試是 evidence，不是清單。執行前先把 diff 對應到最小 command set。

優先順序：

1. changed behavior 的 targeted unit／component tests。
2. 直接 integration／API／schema contract tests。
3. auth／permission positive 與 negative tests。
4. migration ordering／upgrade tests。
5. user-visible workflow 的最小 E2E。
6. 受影響 scope 的 lint／typecheck／build。
7. broader regression 或 full suite。

規則：

- Standard path 預設 1–3 個 targeted commands；取得足夠 evidence 後停止。
- 不把 lint、typecheck、format、build、coverage、E2E 與 full suite 當成每次都要完成的固定清單。
- coverage、`detectOpenHandles`、profiling、debug mode 只在 acceptance、CI 或故障診斷需要時使用。
- 測試必須 single-run；出現持續資源壓力時依 Adaptive Resource Governor 先限制 workers，只有不穩定仍持續時才使用 serial mode。
- 記錄每個 command、exit status、涵蓋範圍與執行後仍未變更的 relevant files。已通過且相關檔案未變，不得因 commit、push、PR 或等待 approval 而重跑。
- review fix 後只重跑受影響的 tests。
- full suite 只有在 repository policy／CI parity 明確要求、shared foundation 影響廣泛、targeted validation 無法提供足夠信心，或使用者明確要求時才本機執行。
- 可由 CI 提供的 broad regression 不必無理由在本機複製；PR 中明確標記 `CI pending`。
- command hang 時先終止本次任務擁有的 process tree、找出 open handle／deadlock／environment 問題；不得無限 rerun。
- 失敗不可隱藏。無法執行時記錄 exact command、原因、替代 evidence 與是否影響 PR readiness。

### Gate E — Mandatory code review、bad smell review 與 focused security review

在 targeted validation 完成、diff 接近最終狀態後，且 commit／push 前，對 final candidate diff 執行一次 consolidated review。測試通過、CI 通過或外部 reviewer approval 都不能取代此 Gate。

#### 1. Code review

Standard、High-risk，以及包含 production code 的 Fast path 必須使用一次 `$code-review`；skill 不可用時執行等價人工 review。純文件、copy、style-only、test-only 或 mechanical change 可使用人工 diff review。

至少檢查：

- correctness 與 acceptance criteria
- regression 與 backward compatibility
- edge cases、boundary conditions 與 invalid states
- error handling、failure propagation 與 fail-open／fail-closed behavior
- data flow、state transitions 與 hidden side effects
- concurrency、retry、idempotency、ordering 與 race conditions，如適用
- API／schema／config／migration contract drift
- auth、permission、tenant／site／patient isolation，如適用
- test quality、false-positive tests 與 missing regression coverage
- maintainability、scope discipline、independent rollback 與 incomplete-feature isolation

不得在 implementation 尚未穩定時提早執行，然後在完成後無理由重複完整 review。

#### 2. Code smell／Bad smell review

所有 code-changing increments 都必須執行。檢查 final diff、直接受影響 call path 與新增／修改 tests，至少涵蓋：

- unnecessary abstraction、premature generalization 與 over-engineering
- fake helper、thin wrapper 或沒有降低複雜度的 indirection
- duplicated logic、copy-paste branch 與不一致的 parallel implementation
- dead code、unused files、unused imports、unreachable branch
- stale、misleading、debug、temporary 或 TODO comments
- debug code、temporary bypass、hard-coded fixture 或 test-only production behavior
- brittle tests、implementation-coupled assertions、false-positive tests
- swallowed errors、broad catch、silent fallback 與 ambiguous failure state
- hidden side effects、mutable shared state 與 surprising lifecycle behavior
- excessive coupling、mixed responsibilities、oversized function／component
- unrelated refactor、broad formatting noise 與 accidental scope expansion
- API、schema、config、migration、auth 或 permission drift
- insecure default、secret exposure、unsafe logging 與 untracked migration-history changes

Smell findings 分為：

- `Fixed in this PR`：與本次 increment 直接相關、可安全修復，且可由本次 validation 覆蓋。
- `Found but not fixed`：真實但超出 scope，必須記錄 impact、priority、evidence、defer reason 與 suggested follow-up。
- `Newly introduced risk`：本 diff 新增或無法排除的風險；必須在 commit 前修正、明確接受，或阻擋 PR readiness。

不得為了讓報告看起來完整而製造推測性 findings；沒有 finding 時寫 `None.`。不得逐項輸出所有已通過的否定結果。

#### 3. Focused security review

所有 production diff 至少人工檢查：

- secret exposure、unsafe logging 與 sensitive-data leakage
- input validation、output escaping 與 attacker-controlled input
- auth／permission bypass、isolation regression 與 insecure defaults
- fail-open behavior、filesystem／network side effects
- dependency、configuration、feature-flag 與 disabled-route risk

只有符合 security-skill trigger 時才使用一套適用 security skill，不得重複 full audit。

#### Findings 處理與重新審查

- in-scope 且可安全修復：修正並執行受影響的 targeted validation。
- out-of-scope：記錄 impact、priority、evidence 與 follow-up；P0、P1 或重要 P2 依 issue policy 建立 tracking issue。
- review 後只有局部、低風險修正：只 review delta 與受影響 call path。
- 只有主要邏輯、contract、migration 或 trust boundary 實質改變，才重新執行完整 `$code-review` 或 specialist review。
- 不得因 smell finding 擴大成無關的 full-repository cleanup。

#### Required review evidence

Final report 與 code-changing PR body 必須包含精簡 evidence：

**Code review results**

- method：`$code-review` 或 manual equivalent
- blocking findings
- fixed findings
- remaining non-blocking notes

**Code Smell Report**

`Fixed in this PR`

- file path
- smell type
- original problem
- fix
- why it belongs in this PR
- validation

`Found but not fixed`

- file path
- smell type
- impact
- priority：P0／P1／P2／P3
- evidence
- why deferred
- suggested follow-up issue title

`Newly introduced risk check`

- 只列實際風險或無法確認的項目
- 若無：`None.`

### Gate F — Commit、Push 與 PR

- 每個 increment 預設一個 final logical commit；review feedback 每輪預設一個 follow-up commit。
- 禁止每檔案、函式、test、comment 或 finding 建立 micro-commit；禁止一般 WIP／checkpoint commits。
- commit 前只檢查一次 staged diff 與 hygiene；不得因此重跑未受影響 tests 或 audits。
- push 前執行 PR Review Inbox checkpoint，確認沒有新 blocking feedback。
- 使用 repository PR template。除 template 要求外，至少保留：
  - Summary
  - Increment scope／Non-goals
  - Testing performed／Not executed
  - Risk／Rollback／Isolation
  - Code review results
  - Code Smell Report
  - Focused security review results
  - External blockers／Approvals
- Code Smell Report 必須保留，但只列實際 `Fixed in this PR`、`Found but not fixed`、`Newly introduced risk` 或 `None.`；不得貼出逐項 pass checklist。
- local required validation 完成後直接建立 ready-for-review PR；只有尚缺必要本機 evidence 時才 draft。
- 建立或更新 PR 後 request required reviewers，讀取 CI／review state 一次，標記 `CI pending` 或 `Pending external approval`，不得等待或 polling。
- branch pending 時凍結 scope，不加入下一個 increment。
- 不得自動 merge。

### Gate G — Review feedback

當 comments、review threads 或 CI results 已可取得，或使用者要求處理既有 PR 時：

1. 一次讀取全部 feedback、threads 與 CI。
2. 分類並批次處理全部 in-scope blockers。
3. 只修改 current PR scope。
4. 執行受影響的 targeted validation。
5. 對 delta 執行 code review、bad smell review 與 focused security review；只有主要邏輯、contract 或 trust boundary 已改變才重跑完整 specialist review。
6. 建立一個 logical follow-up commit。
7. 以 evidence 回覆 comments。
8. 再讀取一次 PR state，確認沒有漏掉新 feedback；禁止持續 polling。

## 7. Definition of Done

只有同時滿足下列條件才可宣稱本 increment 完成：

- current acceptance criteria 已滿足，non-goals 未被偷偷納入。
- 必要 targeted validation 已通過，未執行項目與原因已記錄。
- final diff 的 required code review、code smell／bad smell review 與 focused security review 已完成，blocking findings 已處理。
- code-changing PR body／final report 已記錄 Code review results 與 Code Smell Report；無 finding 時明確寫 `None.`。
- current／linked PR 的 comments、reviews、unresolved threads 與 required checks 已在最後檢查點讀取。
- 沒有未處理的 in-scope blocking feedback。
- Git diff 只有預期變更，沒有 secrets、local artifacts、spec 或 checklist。
- 本次任務啟動的 CMD、PowerShell、Node、terminal、test runner、dev server 與 child processes 已停止；process registry 已清空或已明確回報 leak。
- contract／compliance 文件只在 trigger 成立時修改，且使用最小充分形式。
- merge／deployment approval pending 時，狀態明確標為 external blocker，不得假裝完成 merge 或 deployment。

## 8. Final Completion Report

保持精簡，只輸出：

- branch／worktree／current increment
- linked issue／PR URL／head SHA
- implementation summary
- contract／compliance artifact decision
- tests executed／not executed
- code review result
- Code Smell Report：fixed／deferred／newly introduced risk
- focused security review result
- PR feedback status 與 unresolved blockers
- commit／push／CI／approval／merge status
- process cleanup result
- remaining risks／next independent increment

未建立或未執行時明確寫：`None`、`Not created`、`Not executed`、`CI pending`、`Pending external approval`。
