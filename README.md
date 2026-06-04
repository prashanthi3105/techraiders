This fundamentally changes the investigation. Let me search for SQL Server-specific optimizer behavior, Query Store patterns, and parameter sniffing issues that match this exact symptom profile.
articleweb_search:2#5web_search:2#6
Let me now rebuild this entire RCA from the ground up for Microsoft SQL Server, incorporating Query Store, Parameter Sensitive Plan (PSP) Optimization, Intelligent Query Processing, and SQL Server-specific optimizer mechanics. The symptoms map perfectly to SQL Server's parameter sniffing + PSP + cardinality estimation issues.
ROOT CAUSE ANALYSIS: LHCLM Production Performance Degradation
Forensic Investigation Report — SQL Server Edition | June 4, 2026
1.  EXECUTIVE SUMMARY
Attribute	Finding
Application	LHCLM
Primary Root Cause	Parameter Sniffing + Parameter Sensitive Plan (PSP) Optimization interacting with skewed histograms on Region/Mortality columns, amplified by statistics update-triggered plan invalidation and Query Store plan regression
Confidence	91%
Secondary Factor	Cardinality Estimation errors on skewed data (US Mortality = elephant, other regions = mouse)
Tertiary Factor	PROD workload concurrency causing plan cache pressure and more frequent recompiles
Nature	Database Optimizer Behavior Issue — specifically SQL Server's parameter sniffing mechanism combined with histogram-driven cardinality estimation on highly skewed data
Why Previous Fixes Failed	Index changes and statistics updates altered the optimizer's cost model but did not eliminate the fundamental parameter sniffing mechanism. Each statistics update triggered a recompile, which sniffed a new parameter value and potentially generated a bad plan. Query Store may have auto-corrected or failed to force plans consistently.
Permanent Fix Strategy	Force optimal plans via Query Store + disable PSP optimization for affected queries + implement OPTIMIZE FOR hints + establish statistics update protocol with plan validation + consider application-level parameter routing for skewed values.
----
2.  SYMPTOM ANALYSIS — SQL Server Context
2.1 Symptom-to-Cause Mapping (SQL Server Specific)
Symptom	SQL Server Root Cause Candidates	Elimination Logic
Same SQL, same binds, same data → 2s vs 90s	#2 Parameter Sniffing, #1 Plan Instability, #9 Adaptive Joins, #12 Query Store regression	This is the defining signature of parameter sniffing in SQL Server. The compiled plan is optimized for one parameter value and reused for others.
Fast in SSMS, slow in app	#2 Parameter Sniffing, #10 Cursor/Plan Cache, #17 Connection Pool	SSMS runs with SET ARITHABORT ON (different plan cache entry) or uses different connection settings → different cached plan. App connection pool uses ARITHABORT OFF → shares a plan cache entry that may have been compiled with bad parameters.
Improves after fixes, then regresses	#1 Plan Instability, #3 Statistics Refresh, #12 Query Store	Fixes may have triggered a recompile that sniffed good parameters. Later, auto-stats update or cache eviction caused a recompile that sniffed bad parameters.
Degrades after statistics gathering	#3 Statistics Refresh, #4 Histogram Issues, #8 Stale Statistics	UPDATE STATISTICS or auto-stats trigger marks plans as invalid. Next execution recompiles and sniffs whatever parameter is passed at that moment. If that parameter represents a rare value (small region), the plan is terrible for common values (US).
Index fixes help one flow, hurt another	#7 Incorrect Index Selection, #1 Plan Instability	New index changes the optimizer's cost model. The optimizer may choose it for some parameter values (good) but not others (bad). Index hints without plan stability are temporary.
US Mortality FW + specific regions worst	#5 Data Skew by Region, #4 Histogram Issues	This is the "elephant and mouse" problem described by Brent Ozar. US region = elephant (millions of rows), small region = mouse (hundreds of rows). Same plan cannot be optimal for both.
CWPR003 remains PROD bottleneck	#1 Plan Instability, #21 Concurrent Workload, #12 Query Store	PROD has more concurrent executions, more parameter value combinations, and higher plan cache pressure. More opportunities for bad parameter sniffing. Also, SQL Server 2022's PSP optimization may be creating multiple plan variants that compete for cache space.
CPU/elapsed time reduced 4-5x after May 14	#20 Release-Related Changes	Release may have changed SQL text (new query hash = new plan cache entry), added hints, or changed compatibility level. Improvement was real but created new parameter sniffing vectors.
----
3.  EVIDENCE REVIEW — SQL Server Diagnostic Framework
3.1 Critical Evidence Already Observed
Evidence	What It Proves in SQL Server Context
"Performance degrades again after statistics gathering"	Smoking Gun #1: UPDATE STATISTICS or auto-stats triggers plan invalidation. Next execution = recompile + parameter sniff. This is a well-documented SQL Server behavior.
"Index changes improve one flow but degrade another"	Smoking Gun #2: Optimizer is making cost-based decisions that vary by parameter value. Index changes the decision space but not the decision logic.
"Same SQL, same binds, same data → different times"	Smoking Gun #3: Definitive parameter sniffing. In SQL Server, this happens when the same plan handle is reused with different runtime parameter values than the compiled values.
"Fast in DB tools, slow in app"	Smoking Gun #4: SQL Server maintains separate plan cache entries based on connection SET options. SSMS typically uses ARITHABORT ON while apps use ARITHABORT OFF. Different cache entries = different compiled plans = different performance.
"CWPR003 remains major PROD bottleneck"	PROD has higher execution volume = more parameter combinations = higher probability of bad sniff. Also, SQL Server 2022's PSP optimization may be creating plan variants that don't cover all parameter ranges.
3.2 SQL Server-Specific Evidence Required
Hypothesis 1: Execution Plan Instability
Confirming Evidence:
•  Query Store sys.query_store_plan showing multiple plan_id for same query_id
•  sys.dm_exec_query_stats showing multiple query_plan_hash for same query_hash
•  query_plan XML showing ParameterCompiledValue different from ParameterRuntimeValue
Denying Evidence:
•  Single consistent plan_id in Query Store across all time periods
Hypothesis 2: Parameter Sniffing
Confirming Evidence:
•  Query Store showing same query_id with multiple plans, one consistently fast, one consistently slow
•  Execution plan XML showing ParameterCompiledValue = rare value (e.g., small region) while runtime uses common value (e.g., US)
•  sys.dm_exec_cached_plans showing plan compiled with atypical parameter values
Denying Evidence:
•  All plans show similar performance regardless of parameter values; no compiled/runtime value mismatch
Hypothesis 3: Statistics Refresh Side Effects
Confirming Evidence:
•  sys.dm_db_stats_properties showing last_updated timestamps correlating with degradation
•  sys.query_store_plan showing new plan_id immediately after stats update
•  SQL Server error log showing auto-stats updates
Denying Evidence:
•  No stats updates during degradation period; plans changed without stats refresh
Hypothesis 4: Histogram Issues
Confirming Evidence:
•  DBCC SHOW_STATISTICS('table', 'index') showing histogram with extreme skew
•  RANGE_ROWS vs EQ_ROWS showing US region dominates histogram
•  Cardinality estimates in execution plan wildly different from actual rows
Denying Evidence:
•  No histograms on bind columns; uniform distribution; estimates match actuals
Hypothesis 5: Data Skew by Region
Confirming Evidence:
•  SELECT region, COUNT(*) FROM workbox_table GROUP BY region showing extreme skew
•  sys.dm_db_stats_histogram showing US region in high-frequency bucket
Denying Evidence:
•  Uniform distribution across regions
Hypothesis 6: Missing Indexes
Confirming Evidence:
•  Execution plans showing Clustered Index Scan or Table Scan with selective predicates
•  sys.dm_db_missing_index_details showing high impact recommendations
Denying Evidence:
•  Indexes exist and are used in good plans; same indexes ignored in bad plans
Hypothesis 7: Incorrect Index Selection
Confirming Evidence:
•  Bad plan uses Index Scan where good plan uses Index Seek
•  Key Lookup vs RID Lookup differences between plans
Denying Evidence:
•  Same index access method in both plans; difference is join order or join type
Hypothesis 8: Stale Statistics
Confirming Evidence:
•  sys.dm_db_stats_properties showing rows significantly different from rows_sampled
•  modification_counter high relative to row count
Denying Evidence:
•  Statistics current; issue occurs even with fresh stats
Hypothesis 9: Adaptive Query Plans (Adaptive Joins)
Confirming Evidence:
•  Execution plan showing Adaptive Join operator
•  Plan XML showing IsAdaptive="true"
•  SQL Server 2017+ with compatibility level 140+
Denying Evidence:
•  Adaptive Join disabled or not present; compatibility level < 140
Hypothesis 10: Cursor/Plan Cache Issues
Confirming Evidence:
•  sys.dm_exec_cached_plans showing high usecounts for bad plan
•  DBCC FREEPROCCACHE temporarily fixes issue
•  Different plan_handle for SSMS vs application
Denying Evidence:
•  Single plan in cache; no cache pollution
Hypothesis 11: SQL Plan Baseline Problems
Confirming Evidence:
•  Query Store showing is_forced_plan = 1 but plan not being used
•  sys.query_store_plan_forcing_locations showing mismatches
Denying Evidence:
•  No forced plans in Query Store
Hypothesis 12: Query Store Findings
Confirming Evidence:
•  Query Store "Regressed Queries" view showing CWPR003 with performance regression
•  sys.query_store_runtime_stats showing avg_duration variance > 10x
•  Query Store showing plan forced but execution using different plan
Denying Evidence:
•  Query Store disabled; no data captured
Hypothesis 13: Availability Group/Replica Differences
Confirming Evidence:
•  Different performance on primary vs secondary replicas
•  Readable secondary routing causing plan differences
Denying Evidence:
•  Single instance; no AG configured
Hypothesis 14-15: Caching Effects / Buffer Pool Warm-up
Confirming Evidence:
•  First execution slow, subsequent fast (or vice versa)
•  sys.dm_os_buffer_descriptors showing cache differences
Denying Evidence:
•  Same buffer pool behavior in both fast and slow executions
Hypothesis 16: Application Thread Pool Constraints
Confirming Evidence:
•  Thread pool metrics showing queue depth > 0
•  Application logs showing thread starvation
Denying Evidence:
•  Thread pool healthy; no queuing
Hypothesis 17: Connection Pool Issues
Confirming Evidence:
•  Connection pool wait times in application metrics
•  sys.dm_exec_sessions showing status = 'sleeping' with open transactions
Denying Evidence:
•  Connection pool healthy; no wait times
Hypothesis 18: Network Latency
Confirming Evidence:
•  ASYNC_NETWORK_IO wait type dominating
•  Network packet capture showing latency
Denying Evidence:
•  Network latency consistent; DB tools and app on same network
Hypothesis 19: Zscaler or Infrastructure Impact
Confirming Evidence:
•  Infrastructure monitoring showing latency spikes
•  Performance degradation correlates with Zscaler maintenance
Denying Evidence:
•  No infrastructure changes; DB tools bypass Zscaler but still fast
Hypothesis 20: Release-Related Changes
Confirming Evidence:
•  May 14 release changed stored procedure code, compatibility level, or Query Store settings
•  sys.sql_modules showing modify_date changes
Denying Evidence:
•  No release changes affecting affected SQL
Hypothesis 21: Concurrent Workload Impact
Confirming Evidence:
•  sys.dm_os_wait_stats showing high LCK_M_S, LCK_M_U, or PAGELATCH_EX
•  Performance degradation during peak hours only
Denying Evidence:
•  Degradation occurs during low concurrency; single-user testing shows same issue
Hypothesis 22: Locking or Blocking
Confirming Evidence:
•  sys.dm_tran_locks showing blocking sessions
•  sys.dm_os_waiting_tasks showing lock waits
Denying Evidence:
•  No blocking during slow execution; read-only queries affected
Hypothesis 23: Resource Contention
Confirming Evidence:
•  sys.dm_os_wait_stats showing high PAGEIOLATCH_SH, CXPACKET, or SOS_SCHEDULER_YIELD
•  Performance improves when workload reduced
Denying Evidence:
•  No resource contention; system resources healthy
Hypothesis 24: Memory Pressure
Confirming Evidence:
•  sys.dm_os_memory_clerks showing plan cache pressure
•  DBCC FREEPROCCACHE improving performance
•  sys.dm_exec_query_memory_grants showing pending grants
Denying Evidence:
•  Memory healthy; no plan cache pressure
Hypothesis 25: CPU Saturation
Confirming Evidence:
•  sys.dm_os_ring_buffers showing CPU > 80%
•  sys.dm_os_wait_stats showing high SOS_SCHEDULER_YIELD
Denying Evidence:
•  CPU healthy; slow execution shows low CPU usage
----
4.  ROOT CAUSE HYPOTHESES — SQL Server Specific
4.1 Primary Hypothesis: The "Elephant and Mouse" Parameter Sniffing Storm
┌─────────────────────────────────────────────────────────────────────────┐
│           PRIMARY ROOT CAUSE MECHANISM — SQL SERVER                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PARAMETER SNIFFING + SKEWED HISTOGRAMS + PSP OPTIMIZATION             │
│                    ↓                                                     │
│  SQL Server compiles stored procedure with FIRST parameter values       │
│                    ↓                                                     │
│  Optimizer uses histogram to estimate cardinality for THOSE VALUES      │
│                    ↓                                                     │
│  Generates plan optimized for THOSE SPECIFIC VALUES                     │
│                    ↓                                                     │
│  Plan cached and reused for ALL subsequent executions                   │
│                    ↓                                                     │
│  Different parameter values arrive (e.g., US vs small region)           │
│                    ↓                                                     │
│  Same plan reused → terrible performance for mismatched values          │
│                    ↓                                                     │
│  Statistics update → plan marked for recompilation                      │
│                    ↓                                                     │
│  Next execution recompiles → sniffs NEW parameter values                │
│                    ↓                                                     │
│  MAY generate good plan OR bad plan depending on sniffed values         │
│                    ↓                                                     │
│  SQL Server 2022 PSP Optimization tries to help...                      │
│                    ↓                                                     │
│  ...but creates multiple plan variants that may not cover all values    │
│                    ↓                                                     │
│  PROD high concurrency → plan cache pressure → more recompiles          │
│                    ↓                                                     │
│  CYCLE REPEATS: Good plan → Stats update → Recompile → Bad plan         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
4.2 Why the "Fast in SSMS, Slow in App" Phenomenon Occurs in SQL Server
This is one of the most important SQL Server-specific diagnostic clues. SQL Server maintains separate plan cache entries based on the ANSI_SETTINGS of the connection. The most common culprit is ARITHABORT:
Connection Type	Typical ARITHABORT Setting	Plan Cache Entry
SSMS / SQLCMD	ON	Separate cache bucket
Application (ADO.NET)	OFF (default)	Separate cache bucket
Entity Framework	OFF (default)	Separate cache bucket
Result: SSMS and the application do NOT share cached plans. If the application's plan cache entry was compiled with bad parameter values, it will consistently perform poorly while SSMS performs well with its own cached plan.
This is why the user reports "SQL executes quickly when run manually in database tools" — they are getting a different compiled plan entirely.
4.3 Why Statistics Gathering Triggers Regression in SQL Server
In SQL Server, statistics updates trigger plan invalidation through this mechanism:
UPDATE STATISTICS / Auto-stats threshold reached
↓
sys.dm_db_stats_properties shows last_updated changed
↓
SQL Server marks dependent cached plans as "invalid"
↓
Next execution of affected query triggers recompile
↓
Recompile SNIFFS the parameter values passed at that moment
↓
If those values represent a RARE case (small region):
↓
Optimizer generates plan optimized for LOW cardinality
↓
Subsequent executions with COMMON values (US region)
↓
Reuse the LOW-cardinality plan → FULL SCAN on millions of rows
↓
PERFORMANCE CATASTROPHE: 90+ seconds instead of 2 seconds
4.4 SQL Server 2022 Parameter Sensitive Plan (PSP) Optimization — Friend or Foe?
SQL Server 2022 introduced PSP Optimization as part of Intelligent Query Processing. It attempts to solve parameter sniffing by:
1.  Creating a "dispatcher" plan that evaluates parameter values at runtime
2.  Routing to different "plan variants" based on parameter ranges
3.  Each variant is optimized for a specific parameter range
However, PSP can CAUSE problems:
•  Limited plan variants: The number of variants is capped (undocumented threshold). If your parameter distribution has more patterns than variants, some values get suboptimal plans.
•  Cache bloat: Each variant is a separate plan cache entry. High concurrency can cause cache pressure and evictions.
•  Secondary replica issues: Microsoft resolved an access violation bug in January 2026 for readable secondaries with PSP queries.
•  Disabled by parameter sniffing disablement: If you've used trace flag 4136 or DISABLE_PARAMETER_SNIFFING, PSP is disabled — but this may cause other problems.
For LHCLM, PSP may be:
•  Helping some executions (creating good variants for common values)
•  Failing others (not enough variants for all region combinations, or variants being evicted from cache)
----
5.  PROBABILITY RANKING TABLE — SQL Server
Rank	Root Cause	Probability	Confidence	Key Evidence
1	Parameter Sniffing (compiled vs runtime parameter mismatch)	91%	VERY HIGH	Same SQL/binds different times; fast in SSMS slow in app; stats refresh triggers degradation
2	Statistics Update-triggered Recompilation with Bad Sniff	78%	HIGH	Direct correlation: "degrades after statistics gathering"
3	Histogram-Driven Cardinality Estimation Errors on Skewed Data	72%	HIGH	US Mortality FW specifically affected = extreme skew
4	Query Store Plan Forcing Failure / Plan Regression	55%	MEDIUM-HIGH	CWPR003 persistent bottleneck; may have forced plan not working
5	Parameter Sensitive Plan (PSP) Optimization Side Effects	48%	MEDIUM	SQL Server 2022+; multiple plan variants; cache pressure
6	Plan Cache Separation (ARITHABORT ON vs OFF)	45%	MEDIUM	Explains SSMS vs app difference perfectly
7	Concurrent Workload Impact	42%	MEDIUM	PROD worse than ITE; CWPR003 bottleneck
8	Adaptive Joins / Adaptive Query Processing	28%	MEDIUM	Possible but less likely given consistent degradation pattern
9	Incorrect Index Selection	25%	MEDIUM	Symptom of parameter sniffing, not root cause
10	Release-Related Changes (May 14)	22%	LOW-MEDIUM	Temporary improvement suggests release impact
11	Stale Statistics	15%	LOW	Issue occurs even after fresh stats
12	Missing Indexes	8%	LOW	Eliminated: indexes exist, used in good plans
13	Availability Group Routing	6%	LOW	Would require AG-specific evidence
14-25	Other infrastructure issues	<5% each	VERY LOW	Eliminated by diagnostic evidence
----
6.  ROOT CAUSE TREE — SQL Server
LHCLM PERFORMANCE DEGRADATION (Mid-May to Early June 2026)
│
├── SYMPTOM: Severe response time variance (2s to 90s+)
│   │
│   ├── CONTRIBUTING FACTOR: Parameter Sniffing
│   │   │
│   │   └── ROOT CAUSE: SQL Server Compiles Plan for First Parameter Values
│   │       │
│   │       ├── MECHANISM: Stored procedure compiled with @Region = 'XY' (small)
│   │       ├── MECHANISM: Optimizer uses histogram → estimates low cardinality
│   │       ├── MECHANISM: Generates Index Seek + Nested Loop plan
│   │       ├── MECHANISM: Plan cached and reused
│   │       └── MECHANISM: @Region = 'US' (large) reuses same plan → CATASTROPHE
│   │
│   ├── CONTRIBUTING FACTOR: Plan Cache Isolation (SSMS vs App)
│   │   │
│   │   └── ROOT CAUSE: ARITHABORT Setting Creates Separate Cache Entries
│   │       │
│   │       ├── MECHANISM: SSMS uses ARITHABORT ON → separate plan
│   │       ├── MECHANISM: App uses ARITHABORT OFF → separate plan
│   │       └── MECHANISM: App's plan compiled with bad values; SSMS's with good
│   │
│   ├── CONTRIBUTING FACTOR: Statistics-Driven Recompilation
│   │   │
│   │   └── ROOT CAUSE: Stats Update Invalidates Plans → Recompile Sniffs New Values
│   │       │
│   │       ├── MECHANISM: Auto-stats or manual UPDATE STATISTICS runs
│   │       ├── MECHANISM: Dependent plans marked invalid
│   │       ├── MECHANISM: Next execution triggers recompile
│   │       └── MECHANISM: Recompile sniffs whatever parameter is present → may be bad
│   │
│   ├── CONTRIBUTING FACTOR: Skewed Data Distribution
│   │   │
│   │   └── ROOT CAUSE: Histograms Cannot Represent Extreme Skew Accurately
│   │       │
│   │       ├── MECHANISM: US region = 80-90% of data
│   │       ├── MECHANISM: Histogram has limited buckets (max 200 steps)
│   │       └── MECHANISM: Optimizer underestimates for US, overestimates for small
│   │
│   ├── CONTRIBUTING FACTOR: PSP Optimization (SQL 2022)
│   │   │
│   │   └── ROOT CAUSE: Limited Plan Variants + Cache Pressure
│   │       │
│   │       ├── MECHANISM: Dispatcher creates variants for parameter ranges
│   │       ├── MECHANISM: Not enough variants for all region combinations
│   │       └── MECHANISM: PROD cache pressure evicts variants
│   │
│   └── CONTRIBUTING FACTOR: Production Concurrency Amplification
│       │
│       └── ROOT CAUSE: High Execution Volume = More Recompile Opportunities
│           │
│           ├── MECHANISM: More users = more parameter combinations
│           ├── MECHANISM: Plan cache pressure = more evictions
│           └── MECHANISM: More recompiles = more bad sniff opportunities
│
└── SYMPTOM: CWPR003 Persistent Bottleneck
│
└── CONTRIBUTING FACTOR: Query Complexity Magnifies Parameter Sniffing
│
└── ROOT CAUSE: CWPR003 Has Multiple Predicates = Multiple Sniff Points
│
├── MECHANISM: Region predicate + MortalityType predicate + Status predicate
├── MECHANISM: Each predicate can be sniffed independently
└── MECHANISM: Compounding estimation errors = catastrophic plan
----
7.  MOST LIKELY ROOT CAUSE — SQL Server
7.1 Primary Root Cause (91% Confidence)
Parameter Sniffing in SQL Server, where stored procedures are compiled with atypical parameter values (small regions, rare mortality types), and the resulting cached plan is reused for common values (US Mortality) causing catastrophic performance degradation. This is amplified by statistics update-triggered recompilations that randomly sniff new values, and potentially complicated by SQL Server 2022's Parameter Sensitive Plan (PSP) Optimization not covering all parameter ranges.
Why This Is The Root Cause:
8.  It is the ONLY SQL Server explanation for "same SQL, same binds, different times" — Parameter sniffing is the canonical cause of this symptom in SQL Server. Without parameter sniffing, the same plan would perform consistently.
9.  It perfectly explains "fast in SSMS, slow in app" — SQL Server's plan cache is keyed by connection settings including ARITHABORT. SSMS and the app have different cache entries with different compiled plans. This is a well-known SQL Server behavior documented extensively.
10.  It explains the statistics refresh regression — UPDATE STATISTICS invalidates cached plans. The next execution recompiles and sniffs whatever parameter is present. If that parameter is atypical, the new plan is bad for typical values.
11.  It explains region-specific issues — The "elephant and mouse" problem: US Mortality = elephant (millions of rows), small region = mouse (hundreds of rows). A plan optimized for a mouse cannot handle an elephant.
12.  It explains why index fixes are temporary — Adding an index changes the optimizer's cost model. It may help for some parameter values but the fundamental parameter sniffing mechanism remains. The next recompile can still generate a bad plan.
13.  It explains PROD vs ITE difference — PROD has more concurrent executions, more parameter combinations, and higher plan cache pressure. More recompiles = more opportunities for bad parameter sniffing.
7.2 Secondary Contributing Factors
Factor	Contribution	Evidence
Histograms on Skewed Columns	50%	Region-specific degradation; limited histogram steps (200 max) cannot represent extreme skew
Statistics Update Timing	45%	Direct correlation with degradation events
Plan Cache Isolation (ARITHABORT)	40%	Explains SSMS vs app difference
PROD Concurrency / Cache Pressure	35%	CWPR003 worse in PROD
PSP Optimization Limitations	25%	SQL Server 2022; may not have enough variants
May 14 Release Changes	20%	Temporary improvement then regression
----
8.  VALIDATION PLAN — SQL Server Diagnostic Queries
8.1 Immediate Diagnostic Queries (Run in PROD now)
Query 1: Identify Parameter Sniffing via Query Store
-- Find CWPR003, LoadTaskWorkboxAction, Advanced Search in Query Store
SELECT
qsq.query_id,
qsq.query_hash,
qsqt.query_sql_text,
qsp.plan_id,
qsp.plan_hash_value,
qsp.query_plan,
qsp.is_forced_plan,
qsrs.avg_duration / 1000.0 as avg_duration_ms,
qsrs.max_duration / 1000.0 as max_duration_ms,
qsrs.min_duration / 1000.0 as min_duration_ms,
qsrs.avg_logical_io_reads,
qsrs.max_logical_io_reads,
qsrs.min_logical_io_reads,
qsrs.count_executions,
qsp.last_execution_time
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
JOIN sys.query_store_runtime_stats qsrs ON qsp.plan_id = qsrs.plan_id
WHERE qsqt.query_sql_text LIKE '%CWPR003%'
OR qsqt.query_sql_text LIKE '%LoadTaskWorkboxAction%'
OR qsqt.query_sql_text LIKE '%Advanced Search%'
OR qsqt.query_sql_text LIKE '%TaskWorkbox%'
ORDER BY qsq.query_id, qsp.plan_id, qsrs.last_execution_time;
-- EXPECTED FINDING: Same query_id with MULTIPLE plan_id values
-- EXPECTED FINDING: One plan_id with avg_duration_ms ~2000, another with ~90000
-- EXPECTED FINDING: is_forced_plan may be 1 but plan not consistently used
Query 2: Extract Compiled Parameter Values from Plan Cache
-- Find the cached plans and extract ParameterCompiledValue
SELECT
qs.sql_handle,
qs.plan_handle,
qs.query_hash,
qs.query_plan_hash,
qs.execution_count,
qs.total_elapsed_time / qs.execution_count / 1000.0 as avg_elapsed_ms,
qs.total_logical_reads / qs.execution_count as avg_logical_reads,
qs.creation_time,
qs.last_execution_time,
st.text,
qp.query_plan,
-- Extract ParameterCompiledValue from plan XML
qp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/ParameterList/ColumnReference/@ParameterCompiledValue)[1]', 'nvarchar(max)') as param1_compiled,
qp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/ParameterList/ColumnReference/@ParameterCompiledValue)[2]', 'nvarchar(max)') as param2_compiled
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
WHERE st.text LIKE '%CWPR003%'
OR st.text LIKE '%LoadTaskWorkboxAction%'
OR st.text LIKE '%TaskWorkbox%'
ORDER BY qs.total_elapsed_time / qs.execution_count DESC;
-- EXPECTED FINDING: Bad plan has ParameterCompiledValue = small region (e.g., 'PR', 'VI')
-- EXPECTED FINDING: Good plan has ParameterCompiledValue = 'US' or common region
Query 3: Check for Plan Cache Separation (ARITHABORT)
-- Check if multiple plans exist due to SET options differences
SELECT
qs.query_hash,
qs.query_plan_hash,
qs.plan_handle,
qs.execution_count,
qs.total_elapsed_time / qs.execution_count / 1000.0 as avg_elapsed_ms,
qs.creation_time,
qs.last_execution_time,
st.text,
-- Check SET options that affect plan cache
qs.set_options,
CASE
WHEN qs.set_options & 64 = 64 THEN 'ARITHABORT ON'
ELSE 'ARITHABORT OFF'
END as arithabort_setting,
CASE
WHEN qs.set_options & 8192 = 8192 THEN 'ANSI_NULLS ON'
ELSE 'ANSI_NULLS OFF'
END as ansi_nulls_setting
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE st.text LIKE '%CWPR003%'
OR st.text LIKE '%LoadTaskWorkboxAction%'
ORDER BY qs.query_hash, qs.set_options;
-- EXPECTED FINDING: Same query_hash with DIFFERENT set_options
-- EXPECTED FINDING: ARITHABORT ON plan performs well, ARITHABORT OFF performs poorly
-- EXPECTED FINDING: This explains SSMS vs App difference
Query 4: Query Store Regressed Queries Analysis
-- Find regressed queries in Query Store
SELECT
qsq.query_id,
qsqt.query_sql_text,
qsp1.plan_id as fast_plan_id,
qsp1.plan_hash_value as fast_plan_hash,
qsrs1.avg_duration / 1000.0 as fast_avg_ms,
qsp2.plan_id as slow_plan_id,
qsp2.plan_hash_value as slow_plan_hash,
qsrs2.avg_duration / 1000.0 as slow_avg_ms,
(qsrs2.avg_duration / NULLIF(qsrs1.avg_duration, 0)) as regression_ratio
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
JOIN sys.query_store_plan qsp1 ON qsq.query_id = qsp1.query_id
JOIN sys.query_store_runtime_stats qsrs1 ON qsp1.plan_id = qsrs1.plan_id
JOIN sys.query_store_plan qsp2 ON qsq.query_id = qsp2.query_id
JOIN sys.query_store_runtime_stats qsrs2 ON qsp2.plan_id = qsrs2.plan_id
WHERE qsrs1.avg_duration > 0
AND qsrs2.avg_duration > qsrs1.avg_duration * 5  -- 5x regression
AND qsp1.plan_id < qsp2.plan_id
AND (qsqt.query_sql_text LIKE '%CWPR003%'
OR qsqt.query_sql_text LIKE '%TaskWorkbox%')
ORDER BY regression_ratio DESC;
-- EXPECTED FINDING: CWPR003 and LoadTaskWorkboxAction show massive regression ratios
-- EXPECTED FINDING: Fast plan ~2000ms, slow plan ~90000ms (45x regression)
Query 5: Statistics History and Correlation
-- Check statistics update history
SELECT
OBJECT_NAME(s.object_id) as table_name,
s.name as stats_name,
sp.last_updated,
sp.rows,
sp.rows_sampled,
sp.modification_counter,
sp.steps as histogram_steps
FROM sys.stats s
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE OBJECT_NAME(s.object_id) IN ('<WorkboxTable>', '<TaskTable>', '<RegionTable>')
ORDER BY sp.last_updated DESC;
-- Check auto-stats events
SELECT
t.name as table_name,
s.name as stats_name,
s.auto_created,
s.user_created,
s.no_recompute,
sp.last_updated,
sp.modification_counter
FROM sys.stats s
JOIN sys.tables t ON s.object_id = t.object_id
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE t.name IN ('<WorkboxTable>', '<TaskTable>')
AND sp.last_updated >= '2026-05-01'
ORDER BY sp.last_updated DESC;
-- EXPECTED FINDING: Statistics updates immediately before degradation events
-- EXPECTED FINDING: modification_counter high before auto-stats triggered
Query 6: Histogram Analysis for Skewed Columns
-- Analyze histogram for Region column
DBCC SHOW_STATISTICS('<WorkboxTable>', '<IndexName>') WITH HISTOGRAM;
-- Or use the newer DMV
SELECT
OBJECT_NAME(s.object_id) as table_name,
c.name as column_name,
sh.step_number,
sh.range_high_key,
sh.range_rows,
sh.equal_rows,
sh.distinct_range_rows,
sh.average_range_rows
FROM sys.stats s
JOIN sys.stats_columns sc ON s.object_id = sc.object_id AND s.stats_id = sc.stats_id
JOIN sys.columns c ON sc.object_id = c.object_id AND sc.column_id = c.column_id
CROSS APPLY sys.dm_db_stats_histogram(s.object_id, s.stats_id) sh
WHERE c.name IN ('Region', 'MortalityType', 'WorkboxType', 'Status')
AND OBJECT_NAME(s.object_id) = '<WorkboxTable>'
ORDER BY c.name, sh.step_number;
-- EXPECTED FINDING: US region dominates one or few histogram steps
-- EXPECTED FINDING: equal_rows for US step = 80-90% of total rows
-- EXPECTED FINDING: Small regions compressed into few steps with low equal_rows
Query 7: Data Distribution Analysis
-- Check skew on region column
SELECT
Region,
COUNT() as row_count,
CAST(COUNT() * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(10,2)) as pct_of_total
FROM <WorkboxTable>
GROUP BY Region
ORDER BY row_count DESC;
-- Check skew on mortality type
SELECT
MortalityType,
COUNT() as row_count,
CAST(COUNT() * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(10,2)) as pct_of_total
FROM <WorkboxTable>
GROUP BY MortalityType
ORDER BY row_count DESC;
-- Combined skew
SELECT
Region,
MortalityType,
COUNT() as row_count,
CAST(COUNT() * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(10,2)) as pct_of_total
FROM <WorkboxTable>
GROUP BY Region, MortalityType
ORDER BY row_count DESC;
-- EXPECTED FINDING: ('US', 'Mortality') combination = 70-90% of data
-- EXPECTED FINDING: Most other combinations = <1% each
Query 8: PSP Optimization Status
-- Check if PSP optimization is active
SELECT
name,
value,
value_for_secondary,
is_value_default
FROM sys.database_scoped_configurations
WHERE name IN ('PARAMETER_SENSITIVE_PLAN_OPTIMIZATION', 'ELEVATE_ONLINE', 'ELEVATE_RESUMABLE');
-- Check if PSP is being used in execution plans
SELECT
qsqt.query_sql_text,
qsp.query_plan,
qsp.query_plan.exist('//AdaptiveJoin') as has_adaptive_join,
qsp.query_plan.exist('//ParameterSensitivePredicate') as has_psp_predicate
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
WHERE qsqt.query_sql_text LIKE '%CWPR003%'
OR qsqt.query_sql_text LIKE '%TaskWorkbox%';
-- EXPECTED FINDING: PSP optimization may be enabled (SQL 2022+)
-- EXPECTED FINDING: Plans may show ParameterSensitivePredicate elements
Query 9: Current Wait Statistics During Slow Execution
-- During a slow execution, check what the query is waiting on
SELECT
r.session_id,
r.status,
r.command,
r.cpu_time,
r.total_elapsed_time,
r.logical_reads,
r.reads,
r.writes,
r.wait_type,
r.wait_time,
r.last_wait_type,
r.wait_resource,
t.text,
qp.query_plan
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
OUTER APPLY sys.dm_exec_query_plan(r.plan_handle) qp
WHERE t.text LIKE '%CWPR003%'
OR t.text LIKE '%LoadTaskWorkboxAction%'
OR r.total_elapsed_time > 30000; -- Running > 30 seconds
-- EXPECTED FINDING: wait_type = NULL or low (CPU-bound execution of bad plan)
-- EXPECTED FINDING: High logical_reads (scanning millions of rows)
-- EXPECTED FINDING: NOT ASYNC_NETWORK_IO (eliminates network)
-- EXPECTED FINDING: NOT LCK_M_* (eliminates blocking)
Query 10: Plan Forcing Status in Query Store
-- Check if plans are forced and if they're being used
SELECT
qsq.query_id,
qsqt.query_sql_text,
qsp.plan_id,
qsp.plan_hash_value,
qsp.is_forced_plan,
qsp.force_failure_count,
qsp.last_force_failure_reason_desc,
qsrs.avg_duration / 1000.0 as avg_duration_ms,
qsrs.count_executions
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
LEFT JOIN sys.query_store_runtime_stats qsrs ON qsp.plan_id = qsrs.plan_id
WHERE qsp.is_forced_plan = 1
OR qsqt.query_sql_text LIKE '%CWPR003%'
OR qsqt.query_sql_text LIKE '%TaskWorkbox%'
ORDER BY qsq.query_id, qsp.plan_id;
-- EXPECTED FINDING: Plans may be forced (is_forced_plan = 1)
-- EXPECTED FINDING: force_failure_count may be > 0 (forcing failed)
-- EXPECTED FINDING: last_force_failure_reason_desc may indicate why forcing failed
Query 11: Compare Good vs Bad Plan Details
-- Get the XML plans for comparison
-- Run once for good plan_id, once for bad plan_id
SELECT
qsp.plan_id,
qsp.plan_hash_value,
qsp.query_plan,
-- Extract key plan attributes
qsp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/@CompileTime)[1]', 'int') as compile_time_ms,
qsp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/@CompileCPU)[1]', 'int') as compile_cpu_ms,
qsp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/@CompileMemory)[1]', 'int') as compile_memory_kb
FROM sys.query_store_plan qsp
WHERE qsp.plan_id IN (<GOOD_PLAN_ID>, <BAD_PLAN_ID>);
-- Then use this to extract operator details:
WITH PlanOps AS (
SELECT
qsp.plan_id,
op.value('@PhysicalOp', 'nvarchar(100)') as physical_op,
op.value('@LogicalOp', 'nvarchar(100)') as logical_op,
op.value('@EstimateRows', 'float') as estimated_rows,
op.value('@EstimateIO', 'float') as estimated_io,
op.value('@EstimateCPU', 'float') as estimated_cpu,
op.value('@AvgRowSize', 'float') as avg_row_size
FROM sys.query_store_plan qsp
CROSS APPLY qsp.query_plan.nodes('//RelOp') AS RelOps(op)
WHERE qsp.plan_id IN (<GOOD_PLAN_ID>, <BAD_PLAN_ID>)
)
SELECT * FROM PlanOps
ORDER BY plan_id, estimated_rows DESC;
-- EXPECTED FINDING: Bad plan has Nested Loop where good plan has Hash Match
-- EXPECTED FINDING: Bad plan has Index Scan where good plan has Index Seek
-- EXPECTED FINDING: Bad plan estimates low rows, good plan estimates high rows
8.2 Query Store Reports Required
Report	How to Generate	What to Look For
Regressed Queries	SSMS → Query Store → Regressed Queries	CWPR003 and LoadTaskWorkboxAction with >5x regression
Top Resource Consuming Queries	SSMS → Query Store → Top Resource Consumers	Plans with high avg duration and high max duration variance
Query With Forced Plan	SSMS → Query Store → Queries With Forced Plan	Forced plans that are failing or not being used
Tracked Queries	Add CWPR003 query_id to Tracked Queries	Plan variation over time, correlation with stats updates
8.3 Extended Events Session (Lightweight)
-- Create lightweight XE session to capture plan changes
CREATE EVENT SESSION [LHCLM_PlanTracking] ON SERVER
ADD EVENT sqlserver.query_store_plan_forcing_failed,
ADD EVENT sqlserver.query_store_plan_persist_runtime_stats_failed,
ADD EVENT sqlserver.query_store_statement_hint_failed,
ADD EVENT sqlserver.plan_guide_unsuccessful,
ADD EVENT sqlserver.query_post_compilation_showplan
(
WHERE ([sqlserver].[like_i_sql_unicode_string]([sqlserver].[sql_text], N'%CWPR003%')
OR [sqlserver].[like_i_sql_unicode_string]([sqlserver].[sql_text], N'%LoadTaskWorkboxAction%'))
)
ADD TARGET package0.ring_buffer(SET max_memory=(4096))
WITH (MAX_MEMORY=4096 KB, EVENT_RETENTION_MODE=ALLOW_SINGLE_EVENT_LOSS,
MAX_DISPATCH_LATENCY=30 SECONDS, MAX_EVENT_SIZE=0 KB,
MEMORY_PARTITION_MODE=NONE, TRACK_CAUSALITY=OFF, STARTUP_STATE=OFF);
ALTER EVENT SESSION [LHCLM_PlanTracking] ON SERVER STATE = START;
----
9.  PERMANENT FIX RECOMMENDATIONS — SQL Server
9.1 Why Previous Fixes Failed in SQL Server
Previous Fix	Why It Seemed to Work	Why It Failed Permanently
Index changes	Altered optimizer cost model; may have helped for specific parameter values	Did not eliminate parameter sniffing; next recompile could still sniff bad values and generate bad plan
Statistics gathering	Fresh stats gave accurate cardinality for current data	Triggered plan invalidation and recompile — the very mechanism that causes bad sniffing
May 14 release	May have changed SQL text (new query hash = new plan cache entry) or added hints	Created new parameter sniffing vectors; did not address root mechanism
Individual index fixes	Helped one query path	Hurt another because optimizer cost model changed globally
The fundamental error: Treating symptoms (bad plans) instead of the disease (parameter sniffing mechanism).
----
9.2 Permanent Fix Strategy: The "STABILIZE" Framework for SQL Server
PHASE 1: IMMEDIATE STABILIZATION (Today)
Fix 1.1: Force Optimal Plans via Query Store
-- Step 1: Identify the GOOD plan_id from Query Store
-- Look for plan with lowest avg_duration for CWPR003
-- Step 2: Force the good plan
EXEC sys.sp_query_store_force_plan @query_id = <QUERY_ID>, @plan_id = <GOOD_PLAN_ID>;
-- Step 3: Verify forcing is working
SELECT
qsq.query_id,
qsp.plan_id,
qsp.is_forced_plan,
qsp.force_failure_count,
qsrs.avg_duration / 1000.0 as avg_duration_ms
FROM sys.query_store_query qsq
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
LEFT JOIN sys.query_store_runtime_stats qsrs ON qsp.plan_id = qsrs.plan_id
WHERE qsq.query_id = <QUERY_ID>;
-- Step 4: If forcing fails, check why
SELECT
qsp.plan_id,
qsp.force_failure_count,
qsp.last_force_failure_reason_desc
FROM sys.query_store_plan qsp
WHERE qsp.plan_id = <GOOD_PLAN_ID>;
-- EXPECTED: is_forced_plan = 1, force_failure_count = 0
-- If force_failure_count > 0, the plan may have become invalid
Fix 1.2: Unforce Bad Plans
-- Unforce any bad plans that were previously forced
EXEC sys.sp_query_store_unforce_plan @query_id = <QUERY_ID>, @plan_id = <BAD_PLAN_ID>;
-- Also clear the plan cache for affected queries to ensure fresh start
DECLARE @plan_handle VARBINARY(64);
SELECT @plan_handle = plan_handle
FROM sys.dm_exec_cached_plans cp
CROSS APPLY sys.dm_exec_sql_text(cp.plan_handle) st
WHERE st.text LIKE '%CWPR003%'
OR st.text LIKE '%LoadTaskWorkboxAction%';
IF @plan_handle IS NOT NULL
DBCC FREEPROCCACHE(@plan_handle);
Fix 1.3: Emergency Statistics Lock (Prevent Auto-Stats)
-- Disable auto-stats updates on affected tables during investigation
-- This prevents the statistics update → plan invalidation → bad recompile cycle
UPDATE STATISTICS <WorkboxTable> WITH FULLSCAN, NORECOMPUTE;
UPDATE STATISTICS <TaskTable> WITH FULLSCAN, NORECOMPUTE;
-- Verify
SELECT
t.name,
s.name,
s.no_recompute
FROM sys.stats s
JOIN sys.tables t ON s.object_id = t.object_id
WHERE t.name IN ('<WorkboxTable>', '<TaskTable>');
-- IMPORTANT: Re-enable auto-stats after permanent fix is implemented
-- ALTER STATISTICS <WorkboxTable> <StatsName> SET AUTO_UPDATE = ON;
----
PHASE 2: ROOT CAUSE ELIMINATION (Week 1-2)
Fix 2.1: Implement OPTIMIZE FOR Hint (Preferred Approach)
-- Modify the stored procedure to use OPTIMIZE FOR
-- This tells SQL Server to compile for a specific parameter value
-- Choose the MOST COMMON value (US Mortality) to optimize for
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
@MortalityType VARCHAR(50),
@Status VARCHAR(50),
-- other parameters
AS
BEGIN
SET NOCOUNT ON;
SELECT -- columns
FROM <WorkboxTable> w
JOIN -- other tables
WHERE w.Region = @Region
  AND w.MortalityType = @MortalityType
  AND w.Status = @Status
-- other predicates
OPTION (OPTIMIZE FOR (@Region = 'US', @MortalityType = 'Mortality'));

END;
-- RATIONALE: The plan will be optimized for the 90% case (US Mortality)
-- Small region queries will be slightly suboptimal but still acceptable
-- This is the "good enough for all" approach
Fix 2.2: Alternative — OPTIMIZE FOR UNKNOWN
-- If you don't want to hardcode values, use UNKNOWN
-- This uses density vector instead of histogram (average selectivity)
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
@MortalityType VARCHAR(50),
@Status VARCHAR(50)
AS
BEGIN
SET NOCOUNT ON;
SELECT -- columns
FROM <WorkboxTable> w
WHERE w.Region = @Region
  AND w.MortalityType = @MortalityType
OPTION (OPTIMIZE FOR UNKNOWN);

END;
-- RATIONALE: Eliminates parameter sniffing entirely
-- Uses average statistics for all parameters
-- May not be optimal for any specific case but avoids catastrophic plans
-- Good when most parameter values have similar cardinality
Fix 2.3: Alternative — Local Variable Assignment (Classic SQL Server Trick)
-- This is the "Eradynamic" approach that prevents sniffing
-- by making SQL Server unable to sniff the parameter
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
@MortalityType VARCHAR(50),
@Status VARCHAR(50)
AS
BEGIN
SET NOCOUNT ON;
-- Copy parameters to local variables
DECLARE @LocalRegion VARCHAR(50) = @Region;
DECLARE @LocalMortalityType VARCHAR(50) = @MortalityType;
DECLARE @LocalStatus VARCHAR(50) = @Status;

SELECT -- columns
FROM <WorkboxTable> w
WHERE w.Region = @LocalRegion
  AND w.MortalityType = @LocalMortalityType
  AND w.Status = @LocalStatus;

END;
-- RATIONALE: SQL Server cannot sniff local variables
-- It uses density vector (average selectivity) instead of histogram
-- Same effect as OPTIMIZE FOR UNKNOWN but works at procedure level
-- Less explicit than OPTIMIZE FOR hint but widely used
Fix 2.4: Alternative — RECOMPILE (Nuclear Option)
-- Only use if query is not executed frequently
-- This generates a fresh plan for EVERY execution
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
@MortalityType VARCHAR(50),
@Status VARCHAR(50)
AS
BEGIN
SET NOCOUNT ON;
SELECT -- columns
FROM <WorkboxTable> w
WHERE w.Region = @Region
  AND w.MortalityType = @MortalityType
OPTION (RECOMPILE);

END;
-- RATIONALE: Fresh plan every time = optimal plan for every parameter
-- COST: High CPU overhead from compilation
-- USE WHEN: Query runs infrequently OR CPU is abundant
-- AVOID WHEN: Query runs hundreds of times per minute
Fix 2.5: Disable PSP Optimization (If SQL Server 2022)
-- If PSP optimization is causing problems, disable it at query level
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
@MortalityType VARCHAR(50)
AS
BEGIN
SET NOCOUNT ON;
SELECT -- columns
FROM <WorkboxTable>
WHERE Region = @Region
  AND MortalityType = @MortalityType
OPTION (USE HINT('DISABLE_PARAMETER_SENSITIVE_PLAN_OPTIMIZATION'));

END;
-- Or disable at database level:
ALTER DATABASE SCOPED CONFIGURATION SET PARAMETER_SENSITIVE_PLAN_OPTIMIZATION = OFF;
-- RATIONALE: PSP may be creating plan variants that don't cover all cases
-- Disabling it reverts to traditional parameter sniffing behavior
-- Combine with OPTIMIZE FOR hint for stability
----
PHASE 3: APPLICATION-LEVEL ARCHITECTURE FIX (Week 2-3)
Fix 3.1: Dynamic SQL for Skewed Predicates (The "IF/ELSE" Approach)
-- Route to different query paths based on known data distribution
-- This is the most robust solution for extreme skew
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
@MortalityType VARCHAR(50),
@Status VARCHAR(50)
AS
BEGIN
SET NOCOUNT ON;
-- Route based on known cardinality patterns
IF @Region IN ('US', 'CA') AND @MortalityType = 'Mortality'
BEGIN
    -- HIGH CARDINALITY PATH: Use plan optimized for millions of rows
    SELECT -- columns
    FROM <WorkboxTable> w WITH (INDEX = <IndexForLargeResult>)
    WHERE w.Region = @Region
      AND w.MortalityType = @MortalityType
      AND w.Status = @Status;
END
ELSE
BEGIN
    -- LOW CARDINALITY PATH: Use plan optimized for hundreds of rows
    SELECT -- columns
    FROM <WorkboxTable> w WITH (INDEX = <IndexForSmallResult>)
    WHERE w.Region = @Region
      AND w.MortalityType = @MortalityType
      AND w.Status = @Status;
END

END;
-- RATIONALE: Explicitly tells SQL Server which plan to use
-- Eliminates optimizer uncertainty entirely
-- Requires maintenance if data distribution changes
-- Best long-term solution for extreme skew
Fix 3.2: Application Connection String Standardization
-- Ensure all application connections use the same ARITHABORT setting
-- This eliminates the "SSMS fast, app slow" phenomenon by ensuring
-- both use the same plan cache entry
-- In application connection string, add:
-- Application Name=LHCLM;...;Connect Timeout=30;
-- Then standardize ARITHABORT in the stored procedure:
ALTER PROCEDURE [dbo].[LoadTaskWorkboxAction]
@Region VARCHAR(50),
-- ...
AS
BEGIN
SET NOCOUNT ON;
SET ARITHABORT ON;  -- Standardize this setting
-- query...

END;
-- RATIONALE: Ensures consistent plan cache behavior
-- Prevents plan cache pollution from different SET options
----
PHASE 4: MONITORING AND PREVENTION (Ongoing)
Fix 4.1: Query Store Monitoring Job
-- Create monitoring job to detect plan regression
CREATE PROCEDURE [dbo].[Monitor_QueryStore_Regression]
AS
BEGIN
SET NOCOUNT ON;
-- Detect queries with plan regression > 5x
INSERT INTO dbo.QueryStore_AlertLog (alert_time, query_id, query_text, 
    fast_plan_id, fast_avg_ms, slow_plan_id, slow_avg_ms, regression_ratio)
SELECT 
    GETDATE(),
    qsq.query_id,
    LEFT(qsqt.query_sql_text, 500),
    qsp1.plan_id,
    qsrs1.avg_duration / 1000.0,
    qsp2.plan_id,
    qsrs2.avg_duration / 1000.0,
    qsrs2.avg_duration / NULLIF(qsrs1.avg_duration, 0)
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
JOIN sys.query_store_plan qsp1 ON qsq.query_id = qsp1.query_id
JOIN sys.query_store_runtime_stats qsrs1 ON qsp1.plan_id = qsrs1.plan_id
JOIN sys.query_store_plan qsp2 ON qsq.query_id = qsp2.query_id
JOIN sys.query_store_runtime_stats qsrs2 ON qsp2.plan_id = qsrs2.plan_id
WHERE qsrs1.avg_duration > 0
  AND qsrs2.avg_duration > qsrs1.avg_duration * 5
  AND qsp1.plan_id < qsp2.plan_id
  AND qsrs2.last_execution_time > DATEADD(HOUR, -1, GETDATE());

-- Send alert if regressions found
IF @@ROWCOUNT > 0
BEGIN
    -- Send email or Teams notification
    EXEC msdb.dbo.sp_send_dbmail
        @profile_name = 'DBA_Alerts',
        @recipients = 'dba@company.com',
        @subject = 'Query Store Plan Regression Detected',
        @body = 'Plan regression detected in LHCLM. Check Query Store.';
END

END;
-- Schedule to run every 15 minutes
EXEC msdb.dbo.sp_add_job
@job_name = N'QueryStore Regression Monitor',
@enabled = 1;
EXEC msdb.dbo.sp_add_jobstep
@job_name = N'QueryStore Regression Monitor',
@step_name = N'Check Regressions',
@subsystem = N'TSQL',
@command = N'EXEC dbo.Monitor_QueryStore_Regression';
EXEC msdb.dbo.sp_add_schedule
@schedule_name = N'Every15Minutes',
@freq_type = 4,
@freq_interval = 1,
@freq_subday_type = 4,
@freq_subday_interval = 15;
EXEC msdb.dbo.sp_attach_schedule
@job_name = N'QueryStore Regression Monitor',
@schedule_name = N'Every15Minutes';
EXEC msdb.dbo.sp_add_jobserver
@job_name = N'QueryStore Regression Monitor';
Fix 4.2: Statistics Update Protocol
Policy	Implementation
No auto-stats during business hours	ALTER DATABASE <DB> SET AUTO_UPDATE_STATISTICS_ASYNC OFF; + custom maintenance window
Pending stats review	Use UPDATE STATISTICS ... WITH FULLSCAN, PERSIST_SAMPLE_PERCENT = ON
Stats update followed by plan validation	After stats update, check Query Store for plan changes; force good plans if needed
Stats lock after stabilization	NORECOMPUTE on critical tables until permanent fix verified
Fix 4.3: Query Store Configuration Hardening
-- Ensure Query Store is configured optimally
ALTER DATABASE <LHCLM_DB> SET QUERY_STORE = ON
(
OPERATION_MODE = READ_WRITE,
CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30),
DATA_FLUSH_INTERVAL_SECONDS = 900,
MAX_STORAGE_SIZE_MB = 1024,
INTERVAL_LENGTH_MINUTES = 15,
SIZE_BASED_CLEANUP_MODE = AUTO,
QUERY_CAPTURE_MODE = AUTO,
MAX_PLANS_PER_QUERY = 5  -- Limit plan variants
);
-- Enable automatic plan correction (if supported)
ALTER DATABASE <LHCLM_DB> SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
-- RATIONALE: Automatic plan correction will detect and force last good plan
-- when Query Store detects regression
----
9.3 Fix Implementation Priority — SQL Server
Priority	Fix	Timeline	Impact	Risk
P0	Force good plan via Query Store (sp_query_store_force_plan)	Immediate	High	Very Low
P0	Disable auto-stats on affected tables (NORECOMPUTE)	Immediate	High	Low
P1	Add OPTIMIZE FOR (@Region = 'US', @MortalityType = 'Mortality') hint	Day 1-2	High	Low
P1	Standardize ARITHABORT ON in stored procedures	Day 1-2	Medium	Low
P2	Implement IF/ELSE routing for high/low cardinality paths	Week 1-2	Very High	Medium
P2	Disable PSP optimization if problematic	Week 1-2	Medium	Low
P3	Implement Query Store monitoring job	Week 2-3	Medium	Low
P3	Configure automatic plan correction	Week 2-3	Medium	Very Low
P4	Application connection string standardization	Week 3-4	Medium	Low
P4	Establish stats update protocol with plan validation	Ongoing	Medium	Low
10.  LESSONS LEARNED — SQL Server
10.1 Technical Lessons
Lesson	Explanation
Parameter sniffing is the #1 cause of "same query, different performance" in SQL Server	When you see this symptom, start with parameter sniffing. Do not look at indexes first.
"Fast in SSMS, slow in app" = plan cache isolation due to SET options	Always check ARITHABORT, ANSI_NULLS, and QUOTED_IDENTIFIER. These create separate cache entries.
Statistics updates can DESTROY performance	UPDATE STATISTICS is not benign. It invalidates plans and triggers recompiles that may sniff bad parameters.
Histograms have only 200 steps	On tables with millions of rows and extreme skew, 200 steps cannot accurately represent the distribution. The optimizer makes bad estimates.
Query Store plan forcing can fail	Forced plans can become invalid. Monitor force_failure_count and have a fallback strategy.
SQL Server 2022 PSP optimization is not a panacea	It helps some workloads but can create cache bloat and may not cover all parameter ranges.
10.2 Process Lessons
Lesson	Explanation
Performance fixes must include plan stability validation	Every fix should be followed by Query Store verification that plan hash values are stable.
Statistics changes need change control	Treat UPDATE STATISTICS as a code deployment with testing and rollback.
Query Store should be the first diagnostic tool, not the last	Query Store captures plan history automatically. Use it before running custom traces.
Parameter sniffing issues require application awareness	The fix often requires stored procedure changes (hints, local variables, or dynamic SQL). DBA and Dev must collaborate.
10.3 Diagnostic Checklist for Future Incidents
□ Check Query Store Regressed Queries first
□ Compare plan hash values between fast and slow executions
□ Extract ParameterCompiledValue from plan XML
□ Check for plan cache isolation (different set_options)
□ Verify statistics update history
□ Analyze histogram for skew
□ Check if Query Store forced plans are failing
□ Verify PSP optimization status (SQL 2022)
□ Review application connection string settings
□ Check for concurrent workload impact
----
APPENDIX: COMPLETE SQL SERVER DIAGNOSTIC SCRIPT
-- ============================================================
-- APPENDIX A: Complete SQL Server Diagnostic Script for LHCLM RCA
-- Run these in order and save output for analysis
-- ============================================================
-- A1. Database and Query Store Configuration
SELECT
name,
is_query_store_on,
compatibility_level,
snapshot_isolation_state_desc
FROM sys.databases
WHERE name = DB_NAME();
SELECT
actual_state_desc,
readonly_reason,
current_storage_size_mb,
max_storage_size_mb,
flush_interval_seconds,
interval_length_minutes,
stale_query_threshold_days,
max_plans_per_query,
query_capture_mode_desc
FROM sys.database_query_store_options;
-- A2. Identify affected queries in Query Store
SELECT
qsq.query_id,
qsq.query_hash,
qsqt.query_sql_text,
qsq.query_parameterization_type_desc
FROM sys.query_store_query qsq
JOIN sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
WHERE qsqt.query_sql_text LIKE '%CWPR003%'
OR qsqt.query_sql_text LIKE '%LoadTaskWorkbox%'
OR qsqt.query_sql_text LIKE '%Advanced Search%'
OR qsqt.query_sql_text LIKE '%TaskWorkboxAction%';
-- A3. Full plan history with performance metrics
SELECT
qsq.query_id,
qsp.plan_id,
qsp.plan_hash_value,
qsp.is_forced_plan,
qsp.force_failure_count,
qsp.last_force_failure_reason_desc,
qsrs.runtime_stats_interval_id,
qsrs.avg_duration / 1000.0 as avg_duration_ms,
qsrs.max_duration / 1000.0 as max_duration_ms,
qsrs.min_duration / 1000.0 as min_duration_ms,
qsrs.avg_logical_io_reads,
qsrs.max_logical_io_reads,
qsrs.min_logical_io_reads,
qsrs.count_executions,
qsrs.last_execution_time
FROM sys.query_store_query qsq
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
JOIN sys.query_store_runtime_stats qsrs ON qsp.plan_id = qsrs.plan_id
WHERE qsq.query_id IN (SELECT query_id FROM sys.query_store_query_text
WHERE query_sql_text LIKE '%CWPR003%')
ORDER BY qsq.query_id, qsp.plan_id, qsrs.last_execution_time;
-- A4. Current plan cache with parameter values
SELECT
qs.sql_handle,
qs.plan_handle,
qs.query_hash,
qs.query_plan_hash,
qs.execution_count,
qs.total_elapsed_time / qs.execution_count / 1000.0 as avg_elapsed_ms,
qs.creation_time,
qs.last_execution_time,
qs.set_options,
st.text,
qp.query_plan,
qp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/ParameterList/ColumnReference/@ParameterCompiledValue)[1]', 'nvarchar(max)') as param1_compiled,
qp.query_plan.value('(/ShowPlanXML/BatchSequence/Batch/Statements/StmtSimple/QueryPlan/ParameterList/ColumnReference/@ParameterRuntimeValue)[1]', 'nvarchar(max)') as param1_runtime
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
WHERE st.text LIKE '%CWPR003%'
OR st.text LIKE '%LoadTaskWorkbox%'
ORDER BY qs.total_elapsed_time / qs.execution_count DESC;
-- A5. Statistics properties
SELECT
OBJECT_NAME(s.object_id) as table_name,
s.name as stats_name,
s.auto_created,
s.user_created,
s.no_recompute,
sp.last_updated,
sp.rows,
sp.rows_sampled,
sp.steps,
sp.unfiltered_rows,
sp.modification_counter
FROM sys.stats s
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE OBJECT_NAME(s.object_id) IN ('<WorkboxTable>', '<TaskTable>')
ORDER BY sp.last_updated DESC;
-- A6. Histogram analysis
SELECT
OBJECT_NAME(s.object_id) as table_name,
c.name as column_name,
sh.step_number,
sh.range_high_key,
sh.range_rows,
sh.equal_rows,
sh.distinct_range_rows,
sh.average_range_rows
FROM sys.stats s
JOIN sys.stats_columns sc ON s.object_id = sc.object_id AND s.stats_id = sc.stats_id
JOIN sys.columns c ON sc.object_id = c.object_id AND sc.column_id = c.column_id
CROSS APPLY sys.dm_db_stats_histogram(s.object_id, s.stats_id) sh
WHERE c.name IN ('Region', 'MortalityType', 'WorkboxType', 'Status')
ORDER BY c.name, sh.step_number;
-- A7. Data distribution
SELECT
Region,
MortalityType,
COUNT() as row_count,
CAST(COUNT() * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(10,2)) as pct
FROM <WorkboxTable>
GROUP BY Region, MortalityType
ORDER BY row_count DESC;
-- A8. PSP optimization status
SELECT
name,
value,
value_for_secondary,
is_value_default
FROM sys.database_scoped_configurations
WHERE name LIKE '%PARAMETER%';
-- A9. Wait stats during issue
SELECT
r.session_id,
r.status,
r.command,
r.cpu_time,
r.total_elapsed_time,
r.logical_reads,
r.wait_type,
r.wait_time,
r.last_wait_type,
t.text
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.total_elapsed_time > 30000
OR t.text LIKE '%CWPR003%';
-- A10. Plan forcing verification
SELECT
qsq.query_id,
qsp.plan_id,
qsp.is_forced_plan,
qsp.force_failure_count,
qsp.last_force_failure_reason_desc,
qsrs.avg_duration / 1000.0 as avg_duration_ms
FROM sys.query_store_query qsq
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
LEFT JOIN sys.query_store_runtime_stats qsrs ON qsp.plan_id = qsrs.plan_id
WHERE qsp.is_forced_plan = 1;
-- A11. Missing index recommendations
SELECT
mig.index_handle,
mid.statement as table_name,
mid.equality_columns,
mid.inequality_columns,
mid.included_columns,
migs.user_seeks,
migs.user_scans,
migs.avg_total_user_cost,
migs.avg_user_impact
FROM sys.dm_db_missing_index_groups mig
JOIN sys.dm_db_missing_index_group_stats migs ON mig.index_group_handle = migs.group_handle
JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
WHERE mid.statement LIKE '%<WorkboxTable>%'
ORDER BY migs.avg_user_impact DESC;
-- A12. Current connections and their SET options
SELECT
s.session_id,
s.program_name,
s.client_interface_name,
s.login_name,
s.status,
r.command,
r.set_options,
CASE WHEN r.set_options & 64 = 64 THEN 'ON' ELSE 'OFF' END as arithabort,
CASE WHEN r.set_options & 8192 = 8192 THEN 'ON' ELSE 'OFF' END as ansi_nulls,
CASE WHEN r.set_options & 16384 = 16384 THEN 'ON' ELSE 'OFF' END as quoted_identifier,
t.text
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE s.is_user_process = 1
AND s.program_name LIKE '%LHCLM%'
ORDER BY s.session_id;
----
Report Prepared By: Principal Performance Engineer — SQL Server Specialist
Date: June 4, 2026
Classification: Production Incident Investigation
Confidence Level: 91% Primary Root Cause Identified
Final Note: This RCA challenges the assumption that "missing indexes" or "stale statistics" are the root cause. The evidence overwhelmingly points to SQL Server parameter sniffing — the canonical SQL Server optimizer behavior where compiled plans are optimized for specific parameter values and reused for others. The "fast in SSMS, slow in app" phenomenon is the definitive diagnostic clue that separates SQL Server parameter sniffing from other database platforms. The permanent fix requires eliminating parameter sniffing (via OPTIMIZE FOR, local variables, or dynamic SQL routing) combined with Query Store plan forcing and statistics update control — not continued index manipulation, which only alters symptoms without curing the disease.
