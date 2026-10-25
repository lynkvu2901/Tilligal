

L-MARS: Legal Multi-Agent System with Agentic Search
and Citation-Faithfulness Audit
## Boqin Yuan
## 1
## Ziqi Wang
## 2
## Abstract
Large language models are increasingly deployed
for legal question answering, where evaluations
typically focus on multiple-choice accuracy. This
measure overlooks a common failure:  whether
the citation source attached to an answer exists
and supports the rule the system attributes to it.
We  present  L-MARS,  an  open  multi-agent  le-
gal QA system with agentic search and judge-
driven  evidence  checks,  and  audit  it  claim  by
claim against its cited source. Each atomic claim
is labelled with a six-class taxonomy and scored
with strict-ALCE under cross-provider judging,
where the answerer and verifier come from differ-
ent model families. On a stratified 100-question
Bar Exam audit, retrieval barely moves accuracy,
yet the multi-turn judge loop lifts strict citation
## F
## 1
from0.13(naive RAG) to0.25and cuts the
no-citation rate from34%to13%.  We further
introduce  Faith-Search,  a  post-draft  step  that
re-verifies and repairs unreachable citations;  it
drops the unreachable rate below1%but does
not improveF
## 1
over the multi-turn loop, so we
report it as a targeted reachability intervention
rather than a faithfulness breakthrough.   A 50-
question  LegalSearchQA  case  study  confirms
the  picture:   retrieve-then-draft  pipelines  satu-
rate near0.75citationF
## 1
, while a single-agent
web-search baseline collapses to0.22under ex-
ternal  audit.   We  release  code  and  prompts  at
§L-MARSand  the  LegalSearchQA  dataset  at
LegalSearchQA.
## 1
University  of  California,  San  Diego,  USA
## 2
University  of
Southern  California,  USA.  Correspondence  to:   Boqin  Yuan
## <b4yuan@ucsd.edu>.
Proceedings of the AI4Law Workshop at the43
rd
## International
Conference on Machine Learning, Seoul, South Korea.  PMLR
306, 2026. Copyright 2026 by the author(s).
## 1. Introduction
Large  language  models  (LLMs)  such  as  GPT  (OpenAI,
2026),  Claude  (Anthropic,  2025),  and  Gemini  (Google
DeepMind, 2025) are increasingly applied to legal tasks
including  case  law  retrieval  (Locke  et  al.,  2022),  statu-
tory interpretation, and automated legal assistance (Rinc
## ́
on-
Riveros et al., 2021). Direct use can produce hallucinations
(Ji et al., 2023; Xu et al., 2025): the model states incorrect
legal facts with high confidence.  In legal contexts these
errors carry real-world risk. Wrong citations and outdated
statutes can undermine credibility and mislead decisions.
Domain-specific fine-tuning (Chalkidis et al., 2020) can help
but requires frequent retraining as laws change. Retrieval-
Augmented Generation (RAG) (Lewis et al., 2020) avoids
retraining by fetching relevant documents at inference time,
but its effectiveness depends on retrieval quality.  Recent
work has shown that on legal benchmarks centered on rule
application, standard retrieval pipelines can have little effect
on downstream QA accuracy. On Bar Exam QA, even the
best traditional retriever improves GPT-4o-mini accuracy
by only 0.5 percentage points over zero-shot (Zheng et al.,
## 2025).
We present L-MARS, a multi-agent legal QA system de-
signed for answer generation with auditable evidence.  L-
MARS combines online search (Serper (Serper, 2024), with
Tavily (Tavily, 2024) as a fallback backend), offline retrieval
using BM25 over local documents, and case law retrieval
through the CourtListener API (Free Law Project, 2024).
Unlike naive retrieve-and-generate pipelines, L-MARS uses
a multi-agent system that decomposes queries into struc-
tured search intents, executes targeted retrieval, filters ev-
idence through a Judge Agent, and synthesizes grounded
answers.
L-MARS supports a fast single-pass path and an iterative
judge-driven path.  The single-pass path decomposes the
query,  retrieves  and  filters  evidence,  and  synthesizes  a
grounded answer.  The iterative path repeats search, ver-
ification, and refinement until the evidence is sufficient or
the retrieval budget is exhausted.
Answer accuracy alone is an incomplete measure of legal-
QA quality.  A system that picks the correct answer letter
## 1
arXiv:2509.00761v4  [cs.AI]  15 Jul 2026

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Figure 1.  L-MARS system.  Simple Mode runs Query, Search, and Summary agents once over web, local BM25, and CourtListener
retrieval. Multi-Turn Mode adds a Judge Agent that checks evidence sufficiency and sendsinsufficientcases back for re-search,
up toMturns. The dashed Faith-Search block is the post-draft URL-repair extension evaluated as L-MARS-FS (Section 6); panel (b)
without it is L-MARS-MT.
while citing fabricated authorities creates false trust in ev-
idence that does not survive verification.  Prior audits of
closed commercial assistants (Magesh et al., 2025; Dahl
et al., 2024) report 17–33% hallucinated citations despite
retrieval, but to our knowledge no equivalent measurement
exists for open multi-agent legal-QA systems, where each
agent in the loop can introduce a fabricated reference.
The central observation that drives this paper is that legal
QA should not treat citations as decorative explanations at-
tached to an otherwise self-contained answer. We therefore
evaluate systems at the level a legal user would inspect them:
whether each answer claim is backed by a reachable source
that actually supports it. This framing turns retrieval from
a question of marginal accuracy gains into a question of
evidentiary accountability, and explains why the systems
we evaluate improve citation support far more than they
improve answer accuracy. We audit L-MARS Multi-Turn
against three baselines in Section 6, surface a previously
hidden failure mode in its cited URLs, and study a post-draft
URL-repair extension as one targeted intervention.
We focus on three contributions, in the order an AI4Law
reader  is  most  likely  to  care  about  them.   First,  we  au-
dit  citation  faithfulness  for  an  open  multi-agent  legal-
QA system, a setting that, to our knowledge, prior work
has  not  measured  directly.    The  audit  uses  a  six-class
claim taxonomy and strict-ALCE precision-recall adapted
for  unreachable  citations.   We  use  cross-provider  judg-
ing  across  three  model  families:gpt-5.4-minias
the answerer,gemini-2.5-flashas the verifier, and
claude-haiku-4-5as the third-family cross-evaluator.
The  multi-turn  judge  loop  in  L-MARS  raises  strict cita-
tionF
## 1
from0.131(naive RAG) to0.254, a paired gain
whose 95% bootstrap CI excludes zero.  Second,  we de-
sign Faith-Search as one targeted intervention with a null
## F
## 1
effect on this benchmark: a post-draft URL-repair step
the verifier triggers when a claim’s cite is flagged unreach-
able. Faith-Search drops the unreachable-citation rate from
2.4% to 0.9% and reachesF
## 1
= 0.287on Bar Exam, but
the matched-budgetF
## 1
gain over the multi-turn loop is not
statistically distinguishable from zero onn  =  100.   We
therefore report Faith-Search as a reachability intervention,
not a general faithfulness improvement; an ablation shows
URL replacement is the necessary active component while
the failure-type-aware router contributes no measurable ben-
efit. Third, we release the system that this audit is run on,
L-MARS, a multi-agent legal-QA system that combines
structured query decomposition, agentic web search, judge-
driven evidence checks, and cited-answer synthesis, together
with a 50-question LegalSearchQA case study for time-
sensitive legal questions. The case study supplies external
validity for time-sensitive legal search beyond the Bar Exam
## 2

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
audit’s reasoning-focused regime. All prompts, evaluation
scripts, and raw outputs are released for reproducibility.
## 2. Related Work
Agentic RAG and search systems.Retrieval-augmented
generation grounds model output in external evidence to
reduce hallucination (Lewis et al., 2020); interleaving rea-
soning with retrieval (Yao et al., 2023; Khattab et al., 2023)
improves factual grounding further. Multi-agent frameworks
(Wu et al., 2023; LangChain, 2024) enable role specializa-
tion and iterative critique,  and recent agentic-RAG vari-
ants combine planning, verification, and retrieval for long-
horizon tasks (Singh et al., 2025; Shinn et al., 2023). On the
search side, Search-o1 (Li et al., 2025a) and WebThinker
(Li et al., 2025b) integrate agentic search into reasoning
models; OpenAI’s Deep Research (OpenAI, 2025a) exposes
a production-grade web-scale research loop.   These sys-
tems sit alongside reasoning models (OpenAI, 2024; 2025b;
Qwen Team, 2024; DeepSeek-AI, 2025) that scale delibera-
tion at test time through chain-of-thought prompting (Wei et
al., 2023), self-consistency (Wang et al., 2022), and verifier-
based calibration (Kadavath et al., 2022). L-MARS inherits
the search-and-judge design pattern from Search-o1 and the
agent-orchestration pattern from AutoGen and LangGraph,
instantiated for the legal domain; our distinct contribution
is the citation-faithfulness audit applied to this class of sys-
tem, which prior work has not measured in the open agentic
setting.
Legal AI and benchmarks.    Legal AI evaluation spans
benchmarks for reasoning (Guha et al., 2023), multi-task
NLU  (Chalkidis  et  al.,  2022),  Chinese  legal  knowledge
(Fei et al., 2023), and pretraining data (Henderson et al.,
2022).  More recent work targets retrieval and reasoning
specifically:  Bar Exam QA (Zheng et al., 2025) captures
realistic legal RAG settings where standard retrieval fails,
and LEXam (Fan et al., 2025) benchmarks multi-step le-
gal reasoning across languages.  Katz et al. (2024) report
that GPT-4 zero-shot passes the multistate bar exam, pro-
viding the multiple-choice methodology we adopt. Zhang
et al. (2025) document that LLMs fail to track the tem-
poral validity of legal authorities (for example, whether a
precedent has been overruled), reinforcing the case for ex-
plicit retrieval on time-sensitive legal questions. On the sys-
tems side, ChatLaw (Cui et al., 2024) explores multi-agent
approaches for legal tasks, and Steenhuis (2025) applies
ensemble LLM classifiers to civil legal intake and refer-
ral, illustrating the deployment regime in which a retrieval-
grounded answer assistant would sit.  Many LegalBench
(Guha et al., 2023) subtasks are now saturated (GPT-4o-mini
reaches 100% onruleqa), limiting their discriminative
value for knowledge-intensive legal QA.
Legal hallucination and citation evaluation.    Dahl et al.
(2024) document 58–88% hallucination rates from vanilla
LLMs on case-law tasks. Magesh et al. (2025) audit Lexis+
AI, Westlaw AI, and Practical Law’s Ask AI assistant and
find 17–33% hallucinated citations despite commercial re-
trieval, with failure modes concentrated in source identity
rather than reasoning errors. Bohnet et al. (2022) formalize
Attributed QA, and Gao et al. (2023) introduce ALCE’s
strict citation precision and recall, which we adopt verbatim.
Wallat et al. (2025) separate correctness from faithfulness
in RAG attributions.  Selective-classification frameworks
(Geifman et al., 2017; Kirichenko et al., 2025) provide stan-
dard abstention metrics. Our citation-faithfulness analysis
(Section 6) extends these tools to open multi-agent legal
QA, a setting prior work has not directly audited.
## 3. Methodology
## 3.1. Problem Formulation
Given a user queryqand optional clarificationsU, the sys-
tem maintains an evidence setDand iterates between ex-
pandingD(issuing new search queries) and synthesizing a
cited answerawith a reasoning chainRthat interleaves rea-
soning steps with retrieved evidence. A Judge Agent emits
a sufficiency decisions ∈ {SUFFICIENT, INSUFFICIENT}
and refinement notesEthat guide the next query state; the
loop terminates whens  =  SUFFICIENTor afterMitera-
tions.
3.2. System and Agents
L-MARS  is  implemented  inLangGraph(LangChain,
2024) with structured output validation and tool use. State
transitions are deterministic and type-checked, so an answer
trace is reproducible from the same query and a fixed seed.
The system has four agents:
Query Agent.Parses the user’s question into a structured
query containing intent, jurisdiction, date scope, and one or
more search subqueries. Each subquery is annotated with a
confidence and a triggering rationale.
Search Agent.    Executes tool calls to the retrieval back-
ends  and  returns  a  list  of  normalizedSearchResult
objects (title, URL, snippet, optional full content, source
type).  The agent dispatches across web search (Serper),
local BM25, and case-law retrieval (CourtListener) and ap-
plies a deduplication and provenance check before returning
results to shared state.
Judge Agent.    Performs an explicit evidence-sufficiency
checklist withT  = 0: factual support, jurisdiction match,
temporal specificity, and contradiction analysis. The agent
returns SUFFICIENT when the evidence answers each check-
## 3

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
list item or INSUFFICIENT together with structured refine-
ment notes used to seed the next iteration’s query state.
Summary Agent.Composes the final cited answer. Each
atomic factual claim is paired with an inline citation that
names the cited URL and snippet, so the answer is verifiable
against retrieved evidence.
## 3.3. Agentic Search
Online search.    We adopt an agentic retrieval policy in-
spired by Search-o1 (Li et al., 2025a): targeted web queries
are interleaved with stepwise reasoning rather than issued in
a single problem-oriented fetch. The Search Agent triggers
retrieval when the Judge Agent flags a knowledge gap or
the Query Agent predicts that external evidence will reduce
uncertainty. Two modes are available: a fast basic search
that parses organic results into the normalized schema, and
an enhanced search that fetches page contents and PDFs and
applies snippet-anchored extraction (token-levelF
## 1
overlap,
2.5k-character window) to preserve local evidence while
discarding boilerplate.
Local BM25.    We maintain a local retrieval index over
user-provided documents. Markdown files are segmented
into overlapping 500-character windows with 100-character
stride and indexed with BM25 (Robertson et al., 2009). New
files added to the input directory are picked up on the next
query.
CourtListener.The CourtListener Legal Search API pro-
vides access to U.S. judicial opinions, oral arguments, and
dockets. When enabled, the Search Agent queries by party
name, citation, docket number, or keyword and normalizes
the API response into the sameSearchResultschema
as the other backends.
## 3.4. Operating Modes
Simple Mode.    A single forward pass with minimal la-
tency: Query Agent→Search Agent→Summary Agent.
No Judge Agent, no re-search loop. We use Simple Mode
for the LegalSearchQA case study and the Bar Exam accu-
racy headline.
Multi-Turn Mode.    Adds a Judge Agent and an iterative
search-judge-refine loop.  The Query Agent may propose
clarifying follow-ups (user responses, when available, are
folded into the query state).  Each iteration generates tar-
geted search queries, runs enhanced search (top-3 with con-
tent), and invokes the Judge to decide sufficiency.  If the
Judge returns INSUFFICIENT the refinement notes are folded
into the next query state and the loop repeats, up to a fixed
maximum ofMturns. Multi-Turn Mode is the configuration
audited for citation faithfulness in Section 6.
## 4. Experiments
4.1. Tasks and Datasets
LegalSearchQA (case study).    LegalSearchQA is a 50-
question multiple-choice case study for time-sensitive le-
gal  questions,  designed  to  test  external  validity  of  the
systems beyond the Bar Exam audit’s reasoning-focused
regime rather than to serve as a benchmark. Questions span
## Tax, Corporate & Financial Regulation, Labor & Employ-
ment, Immigration, Technology & Privacy, and Criminal,
Drug  &  State  Law.   Each  item  was  authored  and  cross-
referenced against the source most directly relevant to it
during March 2026:  predominantly primary government
and judicial sources (e.g., IRS.gov, USCIS.gov, SEC.gov,
the Federal Register, the Congressional Research Service,
Supreme Court opinions;≈ 70%of items), with a minority
of authoritative secondary sources (e.g., established law-
firm publications, regulatory trackers;≈  30%).  Correct
answers require 2024–2026 legal or regulatory information.
Bar Exam QA.We also evaluate on the 594-question His-
torical MBE subset of Bar Exam QA (Zheng et al., 2025),
covering Contracts, Torts, Constitutional Law, Evidence,
Real  Property,  and  Criminal  Law.   This  benchmark  em-
phasizes rule application over current information access:
Zheng et al. (2025) report that their best retriever improves
GPT-4o-mini accuracy by only 0.5 points over zero-shot.
4.2. Baselines and Conditions
The LegalSearchQA case study and the Bar Exam citation-
faithfulness  audit  usegpt-5.4-mini.   Two  auxiliary
analyses usegpt-4o-mini: the full Bar Exam accuracy
comparison,  which  follows  the  prior  benchmark  setting,
and the LegalSearchQA per-domain diagnostic in the ap-
pendix.  LegalSearchQA compares zero-shot, naive RAG,
GPT-5.4-mini  with  nativewebsearch,  L-MARS-MT,
and L-MARS-FS. All agents use T  = 0.
## 4.3. Implementation
For LegalSearchQA we evaluated all 50 questions under
each condition.  For Bar Exam QA we evaluated the full
594 questions under zero-shot and L-MARS, and we tested
both Serper and Tavily retrieval backends.  CourtListener
was disabled because neither benchmark requires specific
case citations.
## 5. Results
5.1. Case Study: LegalSearchQA
Table  1  evaluates  the  LegalSearchQA  case  study  with
gpt-5.4-miniand the same citation verifier used in the
Bar Exam audit.  We read this case study as external va-
## 4

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Table 1.  LegalSearchQA case study,n = 50time-sensitive multiple-choice questions,gpt-5.4-mini×gemini-2.5-flash.
Reported as external validity for time-sensitive legal search, not as a benchmark-grade comparison. Brackets are 95% bootstrap CIs (B =
10K, clustered by question, seed = 42).
Conditionn    AccP
strict
## F
## 1
strictUnreach %    No-cite %
Zero-Shot50    0.840 [.74,.94]    0.000 [.00,.00]    0.000 [.00,.00]0.0100.0
Naive RAG50    0.900 [.80,.98]    0.749 [.66,.83]    0.747 [.66,.83]0.00.5
GPT-5.4-mini + websearch    50    0.900 [.80,.98]    0.227 [.12,.33]    0.223 [.12,.33]1.23.6
## L-MARS-MT50    0.920 [.84,.98]    0.736 [.65,.82]    0.722 [.63,.80]2.73.8
## L-MARS-FS50    0.920 [.84,.98]    0.775 [.69,.85]    0.767 [.68,.85]0.02.2
Figure 2. Two evaluation settings. Left: on the retrieval-dependent LegalSearchQA case study every retrieve-then-draft pipeline saturates
accuracy at 90–92% while retrieval-blind Zero-Shot drops to 84%.  Right:  on reasoning-focused Bar Exam QA, retrieval provides
negligible accuracy improvement over Zero-Shot regardless of the search backend. Accuracy is therefore an insensitive metric on Bar
Exam; the multi-turn judge loop’s effect on citation faithfulness, audited in Section 6 under this retrieval budget and verifier, is the signal
of interest.
lidity for time-sensitive legal search, not as a benchmark-
grade comparison; withn = 50it sizes confidence intervals
rather than power-runs hypothesis tests. Two patterns stand
out.  Accuracy saturates once retrieval is available:  every
retrieval-equipped system reaches 90–92% and the CIs over-
lap. Citation faithfulness, in contrast, is sensitive to how the
retrieved evidence is surfaced. Explicit retrieve-then-draft
pipelines (Naive RAG, L-MARS-MT, L-MARS-FS) reach
strict citationF
## 1
between0.72and0.77, with overlapping
CIs across the three; the single-agent nativewebsearch
baseline drops toF
## 1
= 0.223under external audit because
most of its inline citations point to URLs whose externally-
fetched content does not entail the claim. The case study is
consistent with the Bar Exam picture in Section 6.3: when
retrieve-then-draft already keeps unreachable citations near
zero, the post-draft URL-repair step in Faith-Search has lit-
tle headroom, and the FS-over-MT gain is small. The older
gpt-4o-miniper-domain run is reported in Section D as
a domain-dependence diagnostic only.
5.2. Bar Exam QA
Table 2 reports the full 594-question Bar Exam accuracy
comparison and Figure 2 contrasts it side-by-side with the
LegalSearchQA accuracy from Table 1. L-MARS provides
a negligible 0.7-point gain with Serper and a slight 0.8-point
Table 2. Accuracy on Bar Exam QA (594 questions). All condi-
tions use GPT-4o-mini.
ConditionAcc. (%)Correct
Zero-Shot55.2328/594
L-MARS (Serper)55.9332/594
L-MARS (Tavily)54.4323/594
Prior work (Zheng et al., 2025):
GPT-4o-mini49.7–
+ best retriever50.2–
degradation with Tavily, consistent with Bar Exam ques-
tions testing rule application more than current information
access. On this benchmark, raw answer accuracy is there-
fore a poor discriminator;  the signal we audit instead is
citation faithfulness in Section 6. Per-subject error patterns,
LegalSearchQA misses, and retrieval-depth ablations are in
## Section D.
- Citation-Faithfulness Analysis
Section 5 shows that retrieval barely changes Bar Exam an-
swer accuracy. The right question on this dataset is therefore
not whether the system gets the letter right, but whether the
evidence it cites exists and supports the claim it is used to
justify. This section audits that question directly. We label
## 5

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
every atomic claim in each answer against its cited source
with a six-class taxonomy, report strict-ALCE precision and
recall under cross-provider judging, and add a stress test
against a blinded human pass on a stratified slice. Tables 3
and 4 report the headline numbers; the rest of the section
interprets them, runs ablations on the post-draft URL-repair
step, and bounds the conclusions that survive the human
stress test.
## 6.1. Setup
We sample a stratifiedn = 100subset of Bar Exam (seed =
42) and run four conditions ongpt-5.4-mini: zero-shot
(no  retrieval),  naive  RAG  (single  search  query  before
the draft), L-MARS-MT (the multi-turn judge loop,≤ 3
retrievals), and L-MARS-FS, an extension of L-MARS-MT
that adds a post-draft URL-repair step. All retrieval calls use
Serper as the web search backend. For each atomic claim
in the answer we run a citation verifier that issues one of
six   labels   (supported,partiallysupported,
unsupported,citationunreachable,
nocitation,verifiererror)  and  we  compute
strict-ALCE precisionP
strict
= S/(S +P +U +X), recall
## R
strict
= S/T, and their harmonic mean, whereS,P,U,X
are  counts  ofsupported,partiallysupported,
unsupported,citationunreachableandTis
total claims.verifiererrorcounts were zero across
all four conditions, so the corresponding column is omitted
from  Table  4  for  compactness.   Unreachable  URLs  are
scored as failures (not abstentions), so a fabricated citation
cannot game the metric.
Cross-provider   judging.    The   answering   model   is
gpt-5.4-mini(OpenAI)  and  the  citation  verifier  is
gemini-2.5-flash(Google), different model family
and different training data. The verifier reads only the cited
source (canonical host plus path-prefix match, snippet fall-
back at token Jaccard≥ 0.5); it does not fall back to the rest
of the retrieved pool.  We additionally re-label a stratified
n = 57slice withclaude-haiku-4-5as a third-family
judge (Section 6.5). A blinded human verification pass on
ann = 65slice (Section C) falls below our pre-registered
κ≥ 0.55release gate on the full slice; we use it as a stress
test for the verifier rather than as validation of the labels.
What survives the human stress test.    Three observa-
tions  bound  the  conclusions  we  draw.   First,  the  stress
test  confirms  that  the  LLM  verifier  and  the  human  an-
notator agree most on the entailment buckets (supported,
partially supported, unsupported), withκrising to0.518
on  then   =   35claims  where  neither  side  labeled
citationunreachable.   Second,  the  disagreement
concentrates on URL reachability, a label that depends on
fetch-time network state shared by neither pass; this is a
property of point-in-time auditing rather than of the entail-
ment judgment.  Third, every comparison in this paper is
therefore a relative comparison of systems under the same
fixed verifier and audit window. We do not claim absolute
citation-label correctness, and the∆F
## 1
values between L-
MARS variants and the baselines are the quantities we ask
the reader to trust.
6.2. The Multi-Turn Loop Lifts Citation F
## 1
Table 3 reports the main result.  Naive single-pass RAG
reaches strict citationF
## 1
= 0.131.  Adding the multi-turn
judge loop (L-MARS-MT) raises this to0.254,  a paired
## ∆F
## 1
= +0.123with 95% bootstrap CI[+0.056, +0.191]
that excludes zero. The judge loop helps in two coordinated
ways visible in Table 4:  the supported-claim count more
than doubles (64→147 across∼  600claims),  and the
no-citation rate falls from 34% to 13% because the loop con-
tinues searching when the first query returns weak evidence.
The unreachable-citation rate is naturally low on this clean
trace:1.2%for naive RAG and2.4%for L-MARS-MT.
Both sit well below the17–33%band that Magesh et al.
(2025)  report  for  closed  commercial  assistants.   An  ex-
plicit retrieve-then-draft pipeline therefore already keeps
fabricated-citation rates low, provided the search backend
itself returns valid results.
6.3.Faith-Search: A Targeted Reachability Intervention
L-MARS Faith-Search (L-MARS-FS) extends L-MARS-
MT with two pieces: an atomic-claim verifier that scopes
strictly to the cited source, and a URL-repair action that,
when a claim’s cite is flagged unreachable, replaces the dead
cite with a newly-retrieved URL whose snippet still supports
the claim. The pipeline reorganizes search so that the bulk of
retrieval happens after the first draft, in response to verifier
flags.  With a budget of≤ 3total retrievals matched to L-
MARS-MT, L-MARS-FS reachesF
## 1
= 0.287(Table 3),
a paired∆F
## 1
= +0.033over L-MARS-MT with 95% CI
[−0.048, +0.113] that overlaps zero.
We therefore describe Faith-Search as a targeted reacha-
bility intervention, not as a general faithfulness improve-
ment.   The  unreachable  rate  drops  from2.4%to0.9%,
which  is  the  one  outcome  the  URL-repair  action  is  de-
signed to produce.  One side effect is visible in Table 4:
L-MARS-FS shows a36.6% nocitationrate, up from
13.2%for  L-MARS-MT.  The  mechanism  is  built  into
the  repair  branch:   when  URL  repair  cannot  find  a  re-
placement source whose snippet still supports the claim,
Faith-Search drops the citation rather than keep a broken
one,  which tradescitationunreachablemass for
nocitationmass and cancels much of the F1 gain that
the unreachable drop would otherwise have produced. The
strict-F
## 1
gain over the multi-turn loop is not statistically
## 6

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Table 3.  Bar Exam citation audit,n = 100,gpt-5.4-mini×gemini-2.5-flash.  Brackets are 95% bootstrap CIs (B = 10K,
clustered by question, seed = 42).
ConditionAcc    P
strict
## R
strict
## F
## 1
strictUnreach %avg retr
Zero-Shot0.740 [.65,.82]0.000 [.00,.00]0.000 [.00,.00]0.000 [.00,.00]1.10
Naive RAG0.710 [.62,.80]0.165 [.11,.23]0.109 [.07,.15]0.131 [.09,.18]1.21
## L-MARS-MT0.760 [.67,.84]0.273 [.22,.33]0.237 [.19,.29]0.254 [.21,.31]2.42.66
## L-MARS-FS0.690 [.60,.78]0.370 [.29,.45]0.234 [.18,.30]0.287 [.22,.35]0.91.72
Table 4.  Per-condition claim taxonomy (counts; percentages in parentheses).  Bold cells highlight dominant failure modes for each
condition.
## Conditionclaimssupportedpartialunsupportedunreachablenocitation
Zero-Shot6460 (0.0%)0 (0.0%)0 (0.0%)7 (1.1%)639 (98.9%)
Naive RAG58964 (10.9%)13 (2.2%)303 (51.4%)7 (1.2%)202 (34.3%)
## L-MARS-MT621147 (23.7%)40 (6.4%)336 (54.1%)15 (2.4%)82 (13.2%)
## L-MARS-FS576135 (23.4%)15 (2.6%)210 (36.5%)5 (0.9%)211 (36.6%)
distinguishable from zero onn  =  100,  because once L-
MARS-MT already selects evidence whose host and snippet
match the cited URL, post-draft URL replacement cannot
create support that the underlying retrieval did not surface.
Put plainly: URL repair fixes broken citations; it does not
invent supporting evidence where none was retrieved. This
motivates testing the intervention in regimes where the base
system has many unreachable citations to begin with (com-
mercial legal assistants,  single-pass agents with light re-
trieval, the GPT-5.4-mini nativewebsearchbaseline on
LegalSearchQA), and we report its present-data behavior as
an honest null result on the F1-over-MT comparison.
6.4. Ablations: What Inside Faith-Search Is Doing the
## Work?
Two ablations isolate which piece of Faith-Search matters,
holding the retrieval budget fixed at≤ 3 calls.
A1a  –  remove  the  failure-type-aware  router.    Faith-
Search picks specialized re-query strategies based on the
verifier’s failure type (authoritative-domain bias for fabri-
cated URLs, date constraints for stale ones, gap-targeted
reformulation for unsupported ones). A1a replaces this with
a single generic claim-text re-query.  Result:F
## 1
## = 0.286
versus the full Faith-Search at0.287; the unreachable rate
is even lower (0.5%). The router contributes nothing mea-
surable; the simple re-query suffices.
A1b  –  disable  URL  replacement  inside  Faith-Search.
The verifier still flags unreachable citations, but the system
does not substitute a working URL: flagged claims are sim-
ply marked as failed. Result:F
## 1
collapses to0.170and the
unreachable rate climbs back to2.3%. Without replacement,
the verifier only counts failures and never fixes them.
Within Faith-Search and at this retrieval budget, URL re-
placement is the necessary component: removing it (A1b)
dropsF
## 1
by0.117and reverts the unreachable rate from
0.9%to2.3%. The failure-type-aware router is dispensable:
A1a, a single generic re-query, is statistically indistinguish-
able from the full Faith-Search atF
## 1
## = 0.286versus0.287.
Faith-Search itself does not improve significantly over L-
MARS-MT on this benchmark (∆F
## 1
= +0.033with CI
overlapping zero),  so the ablations describe the internal
mechanism  of  Faith-Search,  and  the  multi-turn  baseline
remains the stronger choice at this retrieval budget.
6.5. Cross-Evaluator Robustness
Because the citation verifier is itself an LLM, we re-label
a stratifiedn  =  57Case-3 slice (claims whose cite was
located  in  the  retrieved  set,  so  the  judge  issued  an  NLI
call) withclaude-haiku-4-5as a third-family judge.
3-class Cohen’sκbetween Gemini and Claude-Haiku is
0.683; strict-binaryκis0.661. Both clear the 0.55 release-
gate threshold.  Most disagreements stay within adjacent
labels (supported↔partial, partial↔unsupported) and few
cross the taxonomy more than one step. Two LLM judges
from different families assigning consistent entailment la-
bels is consistent with the labels carrying real signal, al-
though it stops short of validation against non-LLM ground
truth.  A blinded human verification pass on ann  =  65
slice falls below the pre-registered gate and is reported in
Section C as a stress test.
## 6.6. What This Audit Does Not Fix
The  audit  measures  and  partially  addresses  one  failure
mode:  source-identity errors visible as unreachable cita-
tions. It does not move the largernocitation(37% for
L-MARS-FS) andunsupported(36%) buckets. Pushing
absoluteF
## 1
above0.5on Bar Exam will require separate
work on cite-density-rewarding prompts and on stronger
## 7

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
entailment-time retrieval. We discuss these and other limits
in Section 7.
## 7. Conclusion
We presented a citation-faithfulness audit of an open multi-
agent legal-QA system, the audited system itself (L-MARS),
and  a  50-question  LegalSearchQA  case  study  for  time-
sensitive legal questions.  The Bar Exam audit shows that
the multi-turn judge loop in L-MARS raises strict citation
## F
## 1
from0.131(naive RAG) to0.254, a gain whose 95%
bootstrap CI excludes zero, mainly by recovering supported
citations and cutting the no-citation rate from 34% to 13%.
A post-draft URL-repair extension, Faith-Search, addresses
a narrower failure mode: it drops unreachable citations from
2.4% to 0.9% and reachesF
## 1
=  0.287, but its matched-
budgetF
## 1
lift over the multi-turn loop is not statistically
distinguishable from zero onn = 100. We therefore report
Faith-Search as a targeted reachability intervention rather
than as a general faithfulness improvement; ablations show
that URL replacement is the necessary component while the
failure-type-aware router contributes no measurable benefit.
On the LegalSearchQA case study, every retrieve-then-draft
pipeline saturates accuracy and citationF
## 1
, while a single-
agent native web-search baseline collapses on externally
auditable citations.
Implications for legal AI.Accuracy alone is a misleading
metric on Bar Exam: every retrieval setting we tested pro-
duces roughly the same letter-grade answer, and a system
judged on accuracy alone looks fine even when its evidence
is broken. At the claim level, on the audited traces and un-
der the verifier we use, the multi-agent search loop roughly
doubles how often the cited source actually supports the
claim,  although the absolute level of citation support re-
mains modest. Three implications follow. First, legal QA
assistants warrant evaluation on supportability of evidence
as well as on whether the final letter is correct, because an
accuracy-only evaluation hides citation breakage. Second,
in this setting multi-agent retrieval helps supportability more
than it helps raw accuracy, so the value of agentic search
in law on these tasks lies primarily in producing answers
whose evidence a legal user can verify line by line. Third,
the audit itself is fragile: citation reachability drifts across
fetch environments and time, so any production system that
depends on URL-level verification needs an explicit policy
for handling that drift. We demonstrate improved citation
support in this setup; we do not claim a general solution to
legal faithfulness.
Limitations.LegalSearchQA is small (50 items) and time-
sensitive.  The Bar Exam audit uses a stratifiedn = 100
subset and a single backbone family (gpt-5.4-mini);
the citation verifier is itself an LLM, so the cross-provider
and human checks should be read as triangulation evidence
and stop short of non-LLM ground truth. The human stress
test, in particular, prevents us from claiming absolute cor-
rectness of any individual citation label,  but it does not
undercut the relative comparisons across systems under the
same fixed verifier and audit window, which are the quan-
tities the paper reports.   The audit measures one failure
mode (citation source identity); the largerunsupported
(36–54%) andnocitation(13–37%) buckets are not
addressed by Faith-Search and dominate the residual error
mass.   Pushing absoluteF
## 1
above 0.5 will require sepa-
rate work on cite-density-rewarding prompts and stronger
entailment-time retrieval.
## References
OpenAI.   (2026).GPT-5   System   Card.arXiv   preprint
arXiv:2601.03267.  Available  athttps://openai.com/
index/gpt-5-system-card/.
## Anthropic. (2025). System Card: Claude Opus 4 & Claude Sonnet
- Technical report, Anthropic, May 2025. Available athttps:
## //www.anthropic.com/claude-4-system-card.
Google   DeepMind.   (2025).Gemini   3   Pro   Model   Card.
Technical   report,    Google   DeepMind,    December   2025.
## Availableathttps://storage.googleapis.
com/deepmind-media/Model-Cards/
Gemini-3-Pro-Model-Card.pdf.
## Rinc
## ́
on-Riveros, Daniel A., Sergio M. Salazar-Molina, William A.
Pinto-C
## ́
aceres, Sindy P. Amaya, and Juan M. Calderon. (2021).
Automation System Based on NLP for Legal Clinic Assistance.
IFAC-PapersOnLine.
Ji, Ziwei, Nayeon Lee, Jason Fries, Tao Yu, and Pascale Fung.
(2023). Survey of Hallucination in Natural Language Genera-
tion. ACM Computing Surveys, 55(12):1–38.
## Chalkidis, Ilias, Manos Fergadiotis, Prodromos Malakasiotis, Niko-
laos Aletras, and Ion Androutsopoulos. (2020). LEGAL-BERT:
The  Muppets  straight  out  of  Law  School.    arXiv  preprint
arXiv:2010.02559.
## Lewis, Patrick, Ethan Perez, Aleksandra Piktus, Fabio Petroni,
## Vladimir Karpukhin,  Naman Goyal,  Heinrich K
## ̈
uttler,  Mike
## Lewis, Wen-tau Yih, Tim Rockt
## ̈
aschel, Sebastian Riedel, and
Douwe Kiela. (2020).   Retrieval-Augmented Generation for
Knowledge-Intensive NLP Tasks. In NeurIPS.
Serper. (2024). Serper: Google Search API.https://serper.
dev/. Accessed: 2025-08-21.
Tavily. (2024). Tavily Search API. https://tavily.com/.
Free Law Project. (2024).  CourtListener API.https://www.
courtlistener.com/api/rest/v4/search/.
## Khattab, Omar, Keshav Santhanam, Xiang Lisa Li, David Hall,
Percy  Liang,  Christopher  Potts,  and  Matei  Zaharia.  (2023).
Demonstrate-Search-Predict:   Composing  retrieval  and  lan-
guage models for knowledge-intensive NLP.   arXiv preprint
arXiv:2212.14024.
## 8

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Wu, Qianfan, Gagan Bansal, Jingfeng Zhang, et al. (2023). Auto-
Gen: Enabling Next-Gen LLM Applications via Multi-Agent
Conversation. arXiv preprint arXiv:2308.08155.
LangChain. (2024). LangGraph: State-Driven Multi-Agent Work-
flows for LLM Applications.https://www.langchain.
com/langgraph.
## Li, Xiaoxi, Guanting Dong, Jiajie Jin, Yuyao Zhang, Yujia Zhou,
Yutao Zhu, Peitian Zhang, and Zhicheng Dou. (2025a). Search-
o1: Agentic Search-Enhanced Large Reasoning Models. arXiv
preprint arXiv:2501.05366.
## Li, Xiaoxi, Jiajie Jin, Guanting Dong, Hongjin Qian, Yutao Zhu,
Yongkang Wu, Ji-Rong Wen, and Zhicheng Dou. (2025b). Web-
Thinker:  Empowering  Large  Reasoning  Models  with  Deep
Research Capability. arXiv preprint arXiv:2504.21776.
OpenAI.(2025a).IntroducingDeepRe-
search.https://openai.com/index/
introducing-deep-research/.
OpenAI.  (2024).OpenAI  o1  System  Card.arXiv  preprint
arXiv:2412.16720.
OpenAI.(2025b).OpenAIo3ando4-miniSys-
temCard.https://openai.com/index/
o3-o4-mini-system-card/.
## Wei, Jason, Xuezhi Wang, Dale Schuurmans, Maarten Bosma,
Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou. (2023).
Chain-of-Thought Prompting Elicits Reasoning in Large Lan-
guage Models. arXiv preprint arXiv:2201.11903.
Wang, Xuezhi, Jason Wei, Dale Schuurmans, et al. (2022). Self-
Consistency  Improves  Chain-of-Thought Reasoning  in Lan-
guage Models. arXiv preprint arXiv:2203.11171.
Qwen Team. (2024).  QwQ: Reflect Deeply on the Boundaries
of the Unknown.https://qwenlm.github.io/blog/
qwq-32b-preview/.
DeepSeek-AI. (2025).  DeepSeek-R1:  Incentivizing Reasoning
Capability in LLMs via Reinforcement Learning. arXiv preprint
arXiv:2501.12948.
## Chalkidis,  Ilias,  Manos  Fergadiotis,  Prodromos  Malakasiotis,
Spyridon Spanakis, and Nikolaos Aletras. (2022). LexGLUE:
A Benchmark Dataset for Legal Language Understanding in
English. In ACL, pp. 4310–4330.
Henderson,  Peter,  Massimiliano  S.  Krass,  Lucy  Zheng,  et  al.
(2022).   Pile  of  Law:  Learning  Responsible  Data  Filtering
from the Law and a 256GB Open-Source Legal Dataset. arXiv
preprint arXiv:2207.00220.
Guha, Neel, Julian Nyarko, Daniel E. Ho, et al. (2023).  Legal-
Bench: A Collaboratively Built Benchmark for Measuring Le-
gal Reasoning in LLMs. arXiv preprint arXiv:2308.11462.
Robertson, Stephen and Hugo Zaragoza. (2009). The Probabilistic
Relevance Framework: BM25 and Beyond.  Foundations and
Trends in Information Retrieval, 3(4):333–389.
Locke,  Daniel and Guido Zuccon. (2022).   Case law retrieval:
problems, methods, challenges and evaluations in the last 20
years. arXiv preprint arXiv:2202.07209.
Xu, Ziwei, Sanjay Jain, and Mohan Kankanhalli. (2025). Halluci-
nation is Inevitable: An Innate Limitation of Large Language
Models. arXiv preprint arXiv:2401.11817.
## Zheng, Lucia, Neel Guha, Javokhir Arifov, Sarah Zhang, Michal
Skreta, Christopher D. Manning, Peter Henderson, and Daniel E.
Ho. (2025). A Reasoning-Focused Legal Retrieval Benchmark.
In CSLAW ’25, pp. 169–193. ACM.
## Fan,  Yu,  Jingwei Ni,  Jakob Merane,  Etienne Salimbeni,  Yang
## Tian,  Yoan Hermstr
## ̈
uwer,  Yinya Huang,  Mubashara Akhtar,
## Florian Geering, Oliver Dreyer, Daniel Brunner, Markus Leip-
pold, Mrinmaya Sachan, Alexander Stremitzer, Christoph En-
gel, Elliott Ash, and Joel Niklaus. (2025).   LEXam:  Bench-
marking Legal Reasoning on 340 Law Exams. arXiv preprint
arXiv:2505.12864.
## Yao,  Shunyu,  Jeffrey  Zhao,  Dian  Yu,  Nan Du,  Izhak Shafran,
Karthik Narasimhan, and Yuan Cao. (2023). ReAct: Synergiz-
ing Reasoning and Acting in Language Models. arXiv preprint
arXiv:2210.03629.
Singh, Aditi, Abul Ehtesham, Saket Kumar, and Tala Talaei Khoei.
(2025).  Agentic Retrieval-Augmented Generation: A Survey
on Agentic RAG. arXiv preprint arXiv:2501.09136.
Kadavath, Saurav, Tom Conerly, Amanda Askell, et al. (2022).
Language Models (Mostly) Know What They Know.  arXiv
preprint arXiv:2207.05221.
## Shinn,   Noah,   Federico  Cassano,   Edward  Berman,   Ashwin
Gopinath, Karthik Narasimhan, and Shunyu Yao. (2023). Re-
flexion: Language Agents with Verbal Reinforcement Learning.
arXiv preprint arXiv:2303.11366.
## Fei, Zhiwei, Xiaoyu Shen, Dawei Zhu, Fengzhe Zhou, Zhuo Han,
Songyang Zhang, Kai Chen, Zongwen Shen, and Jidong Ge.
(2023). LawBench: Benchmarking Legal Knowledge of Large
Language Models. arXiv preprint arXiv:2309.16289.
## Cui, Jiaxi, Munan Ning, Zongjian Li, Bohua Chen, Yang Yan, Hao
Li, Bin Ling, Yonghong Tian, and Li Yuan. (2024). ChatLaw:
A Multi-Agent Collaborative Legal Assistant with Knowledge
Graph Enhanced Mixture-of-Experts Large Language Model.
arXiv preprint arXiv:2306.16092.
## Magesh,   Varun,   Faiz   Surani,   Matthew   Dahl,   Mirac   Suz-
gun,  Christopher  D.  Manning,  and  Daniel  E.  Ho.  (2025).
Hallucination-Free?  Assessing the Reliability of Leading AI
Legal Research Tools.   Journal of Empirical Legal Studies,
22(2):216–242. DOI: 10.1111/jels.12413.
Dahl, Matthew, Varun Magesh, Mirac Suzgun, and Daniel E. Ho.
(2024). Large Legal Fictions: Profiling Legal Hallucinations in
Large Language Models. Journal of Legal Analysis, 16(1):64–
- DOI: 10.1093/jla/laae003.
## Bohnet, Bernd, Vinh Q. Tran, Pat Verga, Roee Aharoni, Daniel An-
dor, Livio Baldini Soares, Jacob Eisenstein, Kuzman Ganchev,
Jonathan Herzig, Kai Hui, et al. (2022).  Attributed Question
Answering: Evaluation and Modeling for Attributed Large Lan-
guage Models. arXiv preprint arXiv:2212.08037.
Gao, Tianyu, Howard Yen, Jiatong Yu, and Danqi Chen. (2023).
Enabling Large Language Models to Generate Text with Cita-
tions. In EMNLP.
## 9

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Wallat, Jonas, Maria Heuss, Maarten de Rijke, and Avishek Anand.
(2025). Correctness is not Faithfulness in Retrieval Augmented
Generation Attributions.   In Proceedings of the ACM SIGIR
International Conference on the Theory of Information Retrieval
(ICTIR), pp. 22–32. DOI: 10.1145/3731120.3744592.
Geifman, Yonatan and Ran El-Yaniv. (2017). Selective Classifica-
tion for Deep Neural Networks. In NeurIPS.
Kirichenko,  Polina,  Mark  Ibrahim,  Kamalika  Chaudhuri,  and
Samuel J. Bell. (2025). AbstentionBench: Reasoning LLMs Fail
on Unanswerable Questions. arXiv preprint arXiv:2506.09038.
## Katz,  Daniel  Martin,  Michael  James  Bommarito,  Shang  Gao,
and Pablo Arredondo. (2024).   GPT-4 passes the bar exam.
Philosophical Transactions of the Royal Society A, 382(2270):
- DOI: 10.1098/rsta.2023.0254.
Steenhuis, Quinten. (2025). That’s So FETCH: Fashioning Ensem-
ble Techniques for LLM Classification in Civil Legal Intake and
Referral. In Legal Knowledge and Information Systems (JURIX
2025), Frontiers in Artificial Intelligence and Applications, vol.
416, pp. 192–203. DOI: 10.3233/FAIA251588.
Zhang, Li, Jaromir Savelka, and Kevin Ashley. (2025). Do LLMs
Truly “Understand” when a Precedent Is Overruled?  In Legal
Knowledge and Information Systems (JURIX 2025), Frontiers in
Artificial Intelligence and Applications, vol. 416, pp. 239–250.
## DOI: 10.3233/FAIA251592.
## 10

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
## A. Agent Instructions
## Query Agent
The Query Agent is a stateless pass-through that wraps the user
query into a structured QueryGeneration dataclass:
## @dataclass
class QueryGeneration:
query: str
query_type: str = "web_search"
priority: str = "high"
class QueryAgent:
def build_query(self, user_query: str) -> QueryGeneration:
return QueryGeneration(query=user_query.strip())
## Summary Agent
You are a bar exam expert. A user will provide retrieved legal
sources and a multiple-choice question. Use the retrieved sources
together with your legal knowledge to select the single best
answer.
## Rules:
- Your response MUST start with exactly one letter on the first
line: A, B, C, or D.
- Follow with a concise 1-2 sentence rationale citing the
controlling legal rule.
- Bar exam questions test specific exceptions and nuances; do
not just apply the most common general rule if the specific
facts call for an exception.
Response format:
[Letter]
[Brief rationale]
The user message is structured as:
## Retrieved Evidence:
<concatenated search results with source, title, content>
## Question:
<full MCQ with answer choices A-D>
## Judge Agent
You are a legal research quality judge for US bar exam questions.
You will receive a bar exam multiple-choice question and a list of
retrieved search result snippets. Your job is to decide whether
the retrieved evidence is sufficient to reliably answer the
question.
"Sufficient" means: at least one result contains specific legal
rules, statutes, case holdings, or doctrinal exceptions that
directly address the core legal issue tested by the question;
not just a restatement of the facts.
If the evidence is NOT sufficient, provide a better search query
that targets primary legal sources (specific rule names, statute
citations, or doctrine names) rather than generic question text.
Respond with valid JSON only, no markdown fences:
{"sufficient": true_or_false,
"reason": "one sentence",
"next_query": "refined query (omit if sufficient)"}
## 11

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Pre-filtering: before LLM evaluation, results matching any of
these patterns are deterministically removed at zero cost:
HTTP error, 403/404, Connection error, Request timed out,
JavaScript is disabled, No search results found.
VerifyAgent (citation-faithfulness)
DECOMPOSE: You decompose a legal answer into atomic factual
claims. Skip rhetorical sentences, conclusions, and pure
restatements of the question. Each atomic claim is a single,
self-contained factual assertion that can be independently
checked against a source.
ENTAIL (per claim): You are an NLI-style judge for a single
legal claim against ONLY its cited source. Return one of:
supported            -- the cited source NLI-entails the claim
partially_supported  -- a subset of predicates is entailed
unsupported          -- the cite is reachable but does not entail
citation_unreachable -- the cite is absent from the retrieved
pool, fabricated, or dead at external fetch
no_citation          -- the claim is made without a cite
verifier_error       -- judge failed to produce a label
Strict scoping: match the cited source by canonical-host plus
path-prefix, with a snippet-Jaccard >= 0.5 fallback. Do not
silently rescue a fabricated URL with adjacent retrieved evidence.
B. Case Study: Post-Training Knowledge Gap
Two representative items from LegalSearchQA where zero-shot and chain-of-thought both fail from stale parametric
knowledge, while L-MARS retrieves the current information.
Q1 (lsqa001): Executive Order 14110 status
Question: What is the current status of Executive Order 14110,
the Biden administration’s executive order on AI safety signed
in October 2023?
A. It remains in full effect and is being actively enforced
B. It was revoked by President Trump on January 20, 2025
C. It was partially amended but key provisions remain
D. It expired automatically after 12 months
## Correct Answer: B
Zero-Shot selected A. The model’s parametric knowledge has EO
14110 as an active, enforceable order; the January 2025
revocation post-dates training data.
Chain-of-Thought selected A. The model reasons step-by-step from
stale knowledge: it recalls that EO 14110 was signed in October
2023, notes that executive orders do not expire automatically,
and concludes it must still be in effect. The reasoning is
internally consistent but factually wrong.
L-MARS selected B. Retrieved sources included whitehouse.gov and
Federal Register entries confirming revocation via EO 14148 on
## January 20, 2025.
## 12

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
Q2 (lsqa002): 2025 standard deduction
Question: For tax year 2025, what is the standard deduction for
a single filer under age 65, after the One Big Beautiful Bill
Act amendments?
## A. $14,600    B. $15,000    C. $15,350    D. $15,750
## Correct Answer: D
Zero-Shot selected C ($15,350): the model recalls an intermediate
figure from pre-OBBBA IRS projections but lacks knowledge of the
legislative amendment.
Chain-of-Thought selected C ($15,350): step-by-step reasoning
reinforces the wrong figure -- the model recalls the 2024 standard
deduction ($14,600), applies an estimated inflation adjustment,
and arrives at $15,350. The reasoning is plausible but anchored
in stale data.
L-MARS selected D ($15,750): retrieved current IRS sources
confirming the One Big Beautiful Bill Act raised the 2025
standard deduction to $15,750 for single filers.
Both items illustrate the same failure mode: the model’s parametric knowledge is confidently wrong about post-training
developments. Chain-of-thought amplifies the failure: by encouraging step-by-step reasoning from stale premises, CoT
produces internally coherent but factually incorrect justifications.  L-MARS resolves both cases by retrieving current
authoritative sources (whitehouse.gov, IRS.gov) and grounding the answer in retrieved evidence rather than parametric
memory.
## C. Human Verification Audit
We collected a blinded human audit on a stratifiedn = 65subset (5 claims per (condition×label) cell, seed= 42, drawn
across all four conditions). The annotator saw only the claim, the cited URL, and the cited snippet, with no indication of
which system produced the claim or which label the Gemini judge had assigned. A Claude Opus 4.7 agent with a web-fetch
utility opened each cited URL and surfaced potentially relevant passages. The human annotator then read the surfaced text
alongside the snippet, applied the four-label rubric released with the code, and entered the final label.
## Claude’sprovisionallabels(sliceannotatedclaude.csv)andthefinalhumanlabels
(sliceannotatedhumanfinal.csv)  are  both  released  so  the  override  trail  is  auditable;   allκvalues  re-
ported in the paper are computed against the human-final CSV. The strict-binary κ between the human-final labels and the
Gemini judge is0.458on the fulln = 65slice, below our pre-registered 0.55 release gate; the 3-classκis0.219. Restricted
to then = 35claims where neither side labeledcitationunreachable, bothκvalues rise to0.518, within the
moderate-agreement band.
The disagreement concentrates oncitationunreachable: of 20 URLs the Gemini judge reached at audit time, 15
were unreachable when the human refetched them; of 15 URLs the human reached, 10 returned content the Gemini judge
had earlier labeled unreachable. Three plausible causes contribute to this divergence: the two passes ran in different fetch
environments (different user-agents, different proxy paths, no shared cache), the verifier and the human applied slightly
different operational tests for absent from retrieved pool versus dead at external fetch, and URL reachability itself drifts
between inference time and audit time. The result shows that anchoring an audit trail to a single point-in-time reachability
check is brittle by construction. Because the pass uses one annotator and Claude-assisted source retrieval, we use it as a
stress test for the verifier.
## D. Supplementary Analyses
Error analysis (LegalSearchQA).L-MARS missed two questions. Q27 asked about H-1B weighted-selection details, a
procedural rule about wage-level assignment; the retrieved results did not surface the specific Federal Register provision.
Q44 asked for the exact effective date of T+1 settlement; search results discussed the policy broadly but missed the precise
## 13

L-MARS: Legal Multi-Agent System with Citation-Faithfulness Audit
date. Both errors share a pattern: the correct answer requires a specific fact buried in a longer document, and snippet-level
retrieval missed the critical sentence.  The chain-of-thought baseline degrades to 30.0% on this set because the model
recalls outdated dollar amounts from prior tax years and builds multi-step justifications around them; this is the canonical
confident-confabulation failure mode in any domain where facts change faster than model training cycles.
Per-domain breakdown (LegalSearchQA, GPT-4o-mini reference).    On the earlier GPT-4o-mini reference run, the
largest retrieval-driven gain appears in Tax / Corporate & Financial Regulation (+61.5pp) and Technology & Privacy
(+44.4pp); the smallest appears in Criminal, Drug & State Law (+12.5pp), where many items concern well-publicized
events likely covered by pretraining news.  This pattern shows that the dataset’s retrieval-dependence is concentrated in
fast-moving regulatory domains.
Retrieval-depth ablation (Bar Exam).    On a 50-question subsample of Bar Exam QA, single-query web retrieval at
varying depths gave:k = 1snippet→66.0% accuracy,k = 5andk = 10both 62.0%. Additional snippets add noise on
reasoning-focused questions. A basic vs. enhanced deep-search comparison atk = 5produced 64.0% for both, but deep
search incurred 40× higher latency (30.4 s vs. 0.75 s).
## 14