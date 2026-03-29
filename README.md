
You are an expert Jira Story Enhancement Agent. I have 4,000+ historical tickets, 700-800 documents (DOCX, XLSX, PNG, JPG), Confluence specs, and code repository access - all connected via PAT tokens in my .env.

YOUR ENHANCEMENT MISSION:

When I give you a story requirement, you MUST:

1. INTELLIGENT SOURCE DISCOVERY
   - Search my 4,000 Jira tickets for similar stories (last 12 months, same project/component)
   - Query Confluence for technical specs matching keywords from my requirement
   - Scan my 700-800 documents (prioritize: DOCX requirements, XLSX test cases, PNG/JPG mockups/diagrams)
   - Check code repository for relevant files (if implementation story)

2. RELEVANCE SCORING (Do this automatically)
   - Rank found items 0-100 based on: keyword match + date recency + author relevance + file type priority
   - Only include items scoring >70 in final story
   - For large docs (>50 pages), extract only relevant sections using headings

3. STORY ENRICHMENT RULES
   Summary: Max 60 chars, start with verb, include component name if clear
   
   Description must have these 5 sections:
   h2. Objective (1 sentence, what success looks like)
   h2. Business Context (from DOCX requirements docs - summarize in 2 sentences, link source)
   h2. Technical Context (from Confluence + code analysis - current state, constraints)
   h2. Acceptance Criteria (3-5 items, each testable with "verify/measure/confirm")
   h2. Related Sources (bullet list: Jira tickets, Confluence pages, documents with paths)

4. SMART ATTACHMENT SUGGESTIONS
   After analyzing sources, explicitly tell me:
   "SUGGESTED ATTACHMENTS:" 
   - [filename] from [source] - [reason relevant]
   - [filename] from [source] - [reason relevant]
   
   Categories to suggest:
   - Requirements docs (DOCX) - if business rules unclear
   - Architecture diagrams (PNG/JPG) - if technical complexity high  
   - Test cases (XLSX) - if acceptance criteria need validation
   - UI mockups (PNG/JPG) - if user-facing feature
   - Similar story examples - from Jira history

5. FIELD INTELLIGENCE
   - Component: Most frequent from similar tickets
   - Labels: [auto-created] + patterns from similar tickets + inferred from keywords
   - Story Points: Median of last 5 similar tickets (round to Fibonacci: 1,2,3,5,8,13)
   - Priority: Blocker (prod down), High (user-impacting), Medium (planned), Low (nice-to-have)
   - Epic Link: Auto-detect from requirement doc hierarchy or similar tickets

6. CONFIDENCE & VALIDATION
   Rate 0-100. If <75, list what's missing and ask me.
   Check: No duplicate ticket exists (title similarity >80% = warn me)

OUTPUT FORMAT:
ANALYSIS: [What sources found, relevance scores]
DRAFT STORY: [Full Jira structure]
SUGGESTED ATTACHMENTS: [List with reasons]
CONFIDENCE: [X]/100
ACTION: [Create / Needs clarification / Blocked]

Use my PAT tokens from .env for all API calls. Process large documents in chunks. Prioritize recent sources (2024-2025).
qqqqqqqq

const userMessage = `
[THE_PROMPT_ABOVE]

Now create story for: "${requirement}"
Local files: ${attachedFiles}
Project: ${projectKey}
`;









Om Shanti
D Knawledge gef
2 Induidual IM → Poc for cattical roodules
F7
3 Areas that we are strong & gagk
6
* Release process...
@ Prod support (pre/post) / Incidents
* user/ process spacitic for 3 ARms
* velocity maintanance
8 capability matsta
9) Risk mitigation - pan
Action plan
@ Team Readiness.
→ Aceuto logs (all em
3) Trace back all production issuese
RCA + Resolution
14) SP-TI+ JIRA Stories o module
B mention that automation opic can be talen by S.R. TIm
B SDET Shadowing test cases
12 wohat sergey do? → check be declass what we know de dost knaco.
Keep Thought, Word & Deed in Harmony.
Mode
&
7
Y
U
H
N


You are a senior Java developer and architect.

I will provide a Jira ticket in JSON format.

Perform the following:

1. Summarize the requirement
2. Identify impacted modules in a Spring Boot application
3. Provide Low-Level Design (LLD)
4. Suggest exact code changes (file-level)
5. Highlight risks and edge cases
6. Generate unit and integration test cases
7. Create a PR description

Ensure the solution is production-grade and scalable.

Jira JSON:
[PASTE HERE]

Got it—you don’t want a generic leadership pitch. You want something practical, grounded, and aligned to your actual setup:
	•	Adam = 1:1 Scrum Master replacement (Sergei)
	•	You = own technical + delivery readiness
	•	Team = India + Riga + Swiss representative
	•	Goal = Show control, not theory

Let’s build exactly that.

⸻

✅ 1. Readiness Matrix (Realistic & Actionable)

This is what leadership actually looks for—clarity on “who is ready for what”

⸻

Claims Readiness Matrix

Area	Current Readiness	Owner(s)	Backup	Gaps	Action Plan	Target Date
Core Claims Flow	✅ High (80–90%)	India Team + You	Senior Engineer	Edge cases	Reverse KT	2 weeks
TA / Payment Cycles	⚠️ Medium (60–70%)	You + Swiss Rep	QA SME	Quarterly scenarios	Focused KT + walkthrough	Before next cycle
Release Handling	⚠️ Medium	You	Adam (process)	Dependency on past vendor flow	Define release checklist	2 weeks
Jira Delivery	✅ High	All Engineers	—	None	Continue	Stable
PR Reviews	✅ High	Internal Team	Senior Engg	None	Continue	Stable
Production Support	⚠️ Medium	Senior Engg + You	Riga Team	Limited exposure	Shadow + runbook	3 weeks
Vendor Dependency	⚠️ Reducing	You	Swiss Rep	Historical knowledge	Document + escalate model	Ongoing


⸻

👉 How to position this:

“We have clear visibility of readiness by area. Core development is strong. Critical flows like TA/Payment are being prioritized for closure before transition.”

⸻

✅ 2. Risk Mitigation Plan (Focused & Real)

No theory—only what can go wrong + what you will do

⸻

Top Risks & Mitigation

⸻

🔴 Risk 1: Loss of Critical Knowledge (Sergei Dependency)

Impact: High
Reality: Some historical + edge-case knowledge still external

Mitigation:
	•	Reverse KT sessions (mandatory for all critical areas)
	•	Swiss representative as functional anchor
	•	Record all KT sessions + document scenarios
	•	Create “Known Issues & Edge Cases” repository

👉 Position:

“We are converting individual knowledge into team-accessible assets.”

⸻

🟠 Risk 2: TA / Payment Cycle Failure

Impact: Very High
Reality: Complex, periodic, not frequently executed

Mitigation:
	•	Dedicated KT only for TA/Payment (not generic KT)
	•	Dry run / simulation before actual cycle
	•	QA + Swiss Rep validation
	•	Checklist-based execution

👉 Position:

“We are treating TA/Payment as a separate critical track, not part of general KT.”

⸻

🟠 Risk 3: Velocity Drop Post Transition

Impact: Medium

Mitigation:
	•	Adam ensures sprint discipline (same as Sergei)
	•	No change in team structure → only role replacement
	•	Work already being delivered internally
	•	Prioritize known work over new complexity initially

👉 Position:

“Since delivery is already internal, impact is expected to be minimal.”

⸻

🟡 Risk 4: Resource Dependency / Leaves

Impact: Medium

Mitigation:
	•	Primary + Secondary owner for each module
	•	Riga team as backup capacity
	•	No single point of failure
	•	Planned leave tracking

👉 Position:

“We are distributing ownership to eliminate dependency risks.”

⸻

🟡 Risk 5: Production / Support Issues

Impact: Medium

Mitigation:
	•	Runbooks creation (step-by-step fixes)
	•	Shadow support sessions
	•	Swiss Rep + QA support during initial phase

👉 Position:

“We are transitioning support with structured runbooks, not ad-hoc handling.”

⸻

✅ 3. Operating Model (Simple & Realistic)

No fancy layers—just reality:

⸻

Post-Transition Model
	•	You → Technical + Release Owner
	•	Adam → Scrum Master (same as Sergei role)
	•	India Team → Core delivery
	•	Riga Team → Backup + extended capacity
	•	Swiss Rep → Functional SME

⸻

👉 Position clearly:

“This is not a new model. It is continuity with strengthened internal ownership.”

⸻

✅ 4. Final Positioning Statement (Use This in Call/Email)

Say this confidently:

“From a delivery standpoint, there is no major structural change—Adam is a direct replacement for Sergei.
The difference is that technical ownership is now internal, and we have strengthened it with additional resources in Riga and a Swiss functional representative.

We have identified key risk areas like TA/Payment cycles and production support, and we are addressing them through focused KT, reverse KT, and documentation.

Overall, core development and delivery are already stable, and remaining gaps are clearly tracked with mitigation plans.”

⸻

🎯 Why This Will Work

This approach shows:

✔ You understand real risks (not generic)
✔ You have clear ownership
✔ You are not overcomplicating
✔ You are in control of transition

⸻

If you want, next step I can help you with:
	•	Convert this into a 1-slide summary (very powerful)
	•	Or exact answers for Boris/German style grilling questions (they will go deep)

