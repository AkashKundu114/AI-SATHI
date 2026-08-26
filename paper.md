# Structural Guardrails for Trustworthy Voice-First LLM Assistants: A Societal-Computing Deployment for Rural Self-Help Groups

*Anonymous Author(s)*
*Anonymous Institution(s)*

**ABSTRACT**
Large language models (LLMs) are increasingly deployed as financial decision-support assistants, yet prevailing safety mechanisms rely on prompt engineering or post-generation filtering — both vulnerable to hallucination, prompt injection, and unsafe disclosure of numeric information. We present a structurally enforced guardrail architecture that prevents an LLM from generating financial values while preserving natural-language explanation: every monetary quantity is computed deterministically by application logic and is injected into the response only after language generation, so the model is restricted to digit-free rationale. We implement this architecture in AI-SATHI, a voice-first WhatsApp assistant for rural Self-Help Group (SHG) women in West Bengal, India, offering bookkeeping, pricing recommendation, negotiation support, catalogue generation, and government-scheme guidance. An iterative red-team process shows that an earlier blocklist-based guardrail was bypassed through ordinary multilingual phrasing (spelled-out numerals, Unicode digits) rather than adversarial injection, motivating the structural redesign. A consent-governed formative field study across eight SHGs in Hooghly district, West Bengal, surfaces persistent bookkeeping, market-access, and infrastructure gaps that motivated the system's design and its accessibility-first, privacy-preserving posture. We report this work as pre-pilot, needs-assessment evidence and argue that separating deterministic computation from language generation is a general, model-agnostic pattern for trustworthy conversational AI in resource-constrained, safety-critical societal settings.

**Keywords:** large language models, guardrails, societal computing, financial inclusion, voice interfaces, WhatsApp, rural development, Self-Help Groups

**CCS Concepts:** • Human-centered computing → Empirical studies in HCI; • Computing methodologies → Natural language generation; • Security and privacy → Software security engineering.

## 1 Introduction

LLMs are rapidly entering decision-support systems across finance, health, education, and public services (Brown et al. 2020; Touvron et al. 2023; OpenAI 2023), yet they remain susceptible to hallucination (Ji et al. 2023), prompt injection (Perez and Ribeiro 2022; Greshake et al. 2023), and uncontrolled generation of sensitive numerical content. Such failures are safety-critical when an assistant recommends prices, negotiates on a user's behalf, or otherwise communicates monetary values that shape real economic decisions. Existing mitigations — prompt engineering, RLHF, and post-generation filtering (Rebedea et al. 2023; OWASP Foundation 2025) — constrain the model only after it has been allowed to generate unrestricted output, so their guarantees hold only insofar as the model follows instructions.

This gap is acute in low-resource, low-literacy communities. In a formative field study with rural Self-Help Groups (SHGs) in West Bengal, we observed women running legitimate micro-enterprises on manual bookkeeping, informal pricing, and word-of-mouth markets, with little means to independently verify an AI-generated number. We argue that preventing unsafe financial outputs is a systems-design problem, not a prompting problem: rather than repeatedly instructing an LLM not to fabricate numbers, we remove numerical decision-making from the model entirely. Financial quantities are computed exclusively by deterministic application logic; the LLM contributes only a digit-free explanation, which a composition layer merges with the verified values immediately before delivery.

We implement this architecture in AI-SATHI, a voice-first WhatsApp prototype for rural SHGs that supports bookkeeping, pricing, negotiation, catalogue generation, and government-scheme guidance in spoken Bengali. This paper makes four contributions: (i) a structurally enforced guardrail architecture that provably isolates financial values from language generation; (ii) an iterative red-team evaluation showing why structural separation succeeds where an earlier blocklist-based guardrail failed — not against adversarial jailbreaks, but against ordinary multilingual phrasing; (iii) AI-SATHI itself, a real-world research prototype demonstrating the architecture end to end; and (iv) findings from a consent-governed formative field study across eight SHGs that motivate the system's design while explicitly scoping the study's methodological limits.

## 2 Related Work

**Structural guardrails.** Mitigating unsafe LLM output largely relies on prompting, RLHF (Bai et al. 2022), or output filtering, as in NeMo Guardrails (Rebedea et al. 2023) and the OWASP LLM Top-10 (2025); such approaches cannot guarantee robustness to novel phrasing or adversarial prompting. A parallel line delegates safety-critical computation to deterministic components: negotiation systems decouple strategy from generation (He et al. 2018; Xia et al. 2024, OG-Narrator), GuardAgent (2024) supervises an agent's tool calls with a separate guard agent, and Ryt AI (2025) places a guardrail and intent classifier ahead of banking action agents. A recent survey of LLM agents in finance (Dong et al. 2025) likewise argues for bounding agent authority over monetary actions rather than trusting instruction-following alone. Our work follows this direction but goes further for a single, well-scoped class of output: financial values are never sampled by the model at all, and we document, via red-teaming, why a blocklist-based predecessor — conceptually similar to today's output-filtering guardrail products — failed under ordinary multilingual usage rather than adversarial attack.

**AI for low-resource and rural communities.** WhatsApp-based, expert-in-the-loop assistants have supported community health workers (ASHABot; Ramjee et al. 2025) and cataract patients (CataractBot; Ramjee et al. 2025), while retrieval-augmented bots have served WASH education in low-infrastructure regions (Kloker et al. 2024). FormBharo (2026) shows that decomposing a task into independently validated attributes — rather than trusting one end-to-end LLM call — improves reliability for rural, low-literacy callers, echoing our own separation of computation from generation. A large-scale WhatsApp deployment among extreme-poverty households in Rwanda (GiveDirectly, 2025–2026) confirms that recipients readily use unrestricted LLM chat for everyday financial and family matters, underscoring both the demand for such assistants and the risk of ungoverned numeric advice. ASR for rural Indian speakers, particularly women, remains substantially less accurate than for urban speakers (Joshi et al. 2025), motivating voice-first design that tolerates dialectal variation.

**AI for financial inclusion and SHGs.** Early ICT-for-SHG systems used structured SMS to connect groups with banks and schemes, and documented persistent gaps in market access and scheme awareness (Parikh, Ghosh, and Chavan 2003). A recent quantitative study confirms SHG participation still measurably shapes women's financial-inclusion outcomes today (Roy 2025), and our field findings echo the same structural barriers more than two decades after Parikh et al., suggesting they are systemic rather than location-specific. AI-SATHI extends this line by pairing unstructured spoken interaction with a structural safety architecture purpose-built for financial decision support, rather than treating the LLM as an autonomous decision-maker.

**Positioning.** Table-stakes safety tooling (Rebedea et al. 2023; OWASP Foundation 2025) and agent-supervision frameworks (GuardAgent 2024) generally sit between the model and the user as a classifier, inspecting output after it is sampled; our design instead removes the sampling step for one narrow, high-stakes output class, which is a stronger but more limited guarantee — it does not generalize automatically to arbitrary unsafe content the way a general-purpose classifier does. We view the two approaches as complementary rather than competing: a deployment can use a general safety classifier for open-ended harms while additionally applying structural separation to the specific quantities whose correctness is safety-critical, which is the posture AI-SATHI takes.

## 3 Structural Guardrail Architecture

AI-SATHI treats the LLM as an untrusted natural-language generator whose output is constrained by deterministic program logic, not as the author of financial truth. The protected assets are all financially significant outputs — recommended prices, negotiation counter-offers, minimum acceptable prices, and margin calculations. We assume an adversary can submit arbitrary natural-language input, including prompt-injection or jailbreak instructions, multilingual and code-mixed phrasing, role-play framings, and numbers expressed as digits, Unicode numerals, or spelled-out words; the backend application, database, and execution environment are trusted. Table 1 summarizes the threats considered.

| Threat | Conventional LLM | AI-SATHI |
| :--- | :--- | :--- |
| Hallucinated price/value | Possible | Prevented |
| Prompt injection | Possible | Prevented |
| Fabricated / manipulated price | Possible | Prevented |
| Arithmetic error | Possible | Prevented |

*Table 1: Threat comparison between a conventional LLM assistant and AI-SATHI's structural guardrail.*

**Design.** Let C be production cost, m the desired margin, and Pₘᵢₙ a seller-defined floor. The engine computes Pₛₐᶠₑ = max(C·(1+m), Pₘᵢₙ), and for a buyer offer O it accepts if O≥Pₛₐᶠₑ, counters at max(Pₘᵢₙ, (O+Pₛₐᶠₑ)/2) if Pₘᵢₙ≤O<Pₛₐᶠₑ, and otherwise declines. Crucially, the LLM never touches these variables: it receives only a sanitized context x′ with all protected numbers removed, produces a digit-free explanation E, and a validator V(E) rejects any residual digit, Unicode numeral, currency symbol, or spelled-out number word, substituting a safe template on failure. The response composer G(P, E′) then interpolates the trusted values P into the validated explanation, so the language model has no path — benign or adversarial — to influence a number that reaches the user. Algorithm 1 summarizes the execution.

```text
Algorithm 1: Structural Guardrail Execution
Input: user turn x, cost inputs, prior offer O (if any)
1: P ← C(x)                 ▷ deterministic financial values
2: x′ ← Sanitize(x)         ▷ strip all protected numerics
3: E ← LLM(x′)              ▷ digit-free rationale only
4: E′ ← Validate(E)         ▷ numeric-content check
5: if E′ = ⊥ then E′ ← E_safe  ▷ fallback template
6: R ← Compose(P, E′)       ▷ inject P after generation
7: return R
```

Because P = C(x) is computed independently of the model, an adversarial prompt x_adv = x+δ satisfies C(x_adv)=C(x) for unchanged business inputs, so P_adv = P: wording can be manipulated, the recommendation cannot. Identical inputs always yield identical P (deterministic consistency), and swapping the explanation E for any alternative E* leaves P unchanged (explanation independence); if validation fails, the response still contains only verified values, wrapped in E_safe (response integrity). These four properties hold regardless of the underlying model, prompt phrasing, or future model updates, so long as the computation and composition layers remain trusted — they are architectural guarantees, not claims about model behaviour.

## 4 System Architecture and Implementation

AI-SATHI is a modular, LangGraph-orchestrated multi-agent system spanning five layers: user interaction (WhatsApp voice/text), agent orchestration, deterministic computation, the structural guardrail, and data/knowledge storage (Figure 1). The Gateway Service authenticates each request, and voice notes are transcribed by an ASR model tuned for Bengali dialects before intent routing. Six task-specific agents share this backbone: a Ledger agent records income, expense, loan, and savings transactions; a Pricing Recommendation agent and a Negotiation agent both call the deterministic engine of Section 3; a Government Scheme agent answers welfare-scheme questions via retrieval-augmented generation with per-chunk, scheme-aware grounding verification; a Catalogue Creator agent compose promotional posters combining a product photo, an AI caption, and a verified price; and a Market Intelligence agent reports k-anonymized (k≥5) demand trends aggregated across sellers so no individual's sales are inferable.

*[Figure 1: AI-SATHI system architecture — WhatsApp interaction, LangGraph orchestrator, deterministic backend services, structural guardrail, and data/knowledge layer.]*

For every financially reasoning turn, the pipeline of Algorithm 1 is realized as shown in Figure 2: the LLM's sanitized-context explanation is checked by the structural validator before the response composer injects the deterministic values, falling back to a safe template on validation failure so the user always receives a response containing only verified numbers.

*[Figure 2: Structural response composition — explanation and computation are generated independently and merged only after validation.]*

The backend uses FastAPI for request routing and a LangGraph state machine (now checkpointed in PostgreSQL and executed in-process via background tasks rather than a separate Celery worker, after a cost-driven simplification for the pilot's traffic volume) for stateful multi-agent execution; PostgreSQL with pgvector stores ledger records, user profiles, and RAG chunks, and object storage holds generated posters and PDF statements. Speech-to-text, conversational explanation, translation of Banglish/code-mixed input, and image generation are provided by external AI services (Sarvam AI models; an image model for posters); none of these services can write a financial value — only the deterministic engine and response composer can. Privacy-by-design is applied throughout: voice audio is discarded immediately after transcription, personal ledger records are accessible only to their owner, and market analytics are released only after aggregation across at least five sellers, consistent with India's Digital Personal Data Protection Act, 2023.

Figure 3 details the routing among the six business agents. The orchestrator maintains per-user conversation state across turns (e.g., a pending negotiation or an unconfirmed ledger entry) so a user can interrupt, correct, or resume a task in natural spoken Bengali without re-stating context, which matches the turn-taking style observed in our field visits. Every agent that touches a financial quantity — Ledger, Pricing Recommendation, and Negotiation — calls the same deterministic engine described in Section 3 rather than maintaining its own copy of the pricing logic, so the guardrail's guarantees are enforced once, centrally, rather than re-implemented per agent.

*[Figure 3: Business-agent routing (subset shown) — the orchestrator dispatches each turn to one of six agents: Ledger, Pricing, Negotiation, Government Scheme, Catalogue Creator, or Market Intelligence.]*

| Layer | Technology |
| :--- | :--- |
| Orchestration | LangGraph state machine, FastAPI |
| Storage | PostgreSQL + pgvector, object storage |
| Speech / language | Bengali-tuned ASR; Sarvam AI LLMs |
| Delivery channel | WhatsApp Business Cloud API |

*Table 2: Implementation stack by architectural layer.*

## 5 Evaluation

We ask: (RQ1) does the guardrail prevent the LLM from ever emitting a protected value; (RQ2) is it robust to prompt injection targeting pricing; (RQ3) is explanation quality preserved; and (RQ4) what overhead does validation/composition add. We compare three baselines — prompt-only, prompt+output filtering, and prompt+blocklist — against the proposed structural guardrail, using a benchmark of pricing, bookkeeping, negotiation, and scheme queries representative of SHG interactions, and a red-team suite covering direct injection, role-play ("act as the pricing engine"), multilingual and code-mixed prompts, alternative numeric representations (Bengali number words, Unicode ০–৯ digits), multi-turn manipulation, and attempts to push a negotiated price below the seller's floor.

| Scenario | Prompt-only | Blocklist | Structural |
| :--- | :---: | :---: | :---: |
| Normal conversation | ✓ | ✓ | ✓ |
| Direct / role-play injection | ✗ | ✗ | ✓ |
| Spelled-out numerals | ✗ | ✗ | ✓ |
| Unicode / Bengali digits | ✗ | ✗ | ✓ |
| Multi-turn manipulation | ✗ | partial | ✓ |
| Below-floor negotiation push | ✗ | partial | ✓ |

*Table 3: Combined benchmark and red-team outcomes across three baseline guardrails and the proposed structural design.*

The prompt-only baseline handled ordinary conversation adequately but leaked unauthorized values under injection; output filtering caught explicit digit/currency patterns but missed paraphrased or non-standard numerals; the blocklist baseline improved coverage further but was still bypassed — notably, several bypasses arose from unprompted, ordinary linguistic variation (e.g., the model spontaneously writing a price as a Bengali number word) rather than adversarial intent, echoing findings that hand-written pattern rules cannot enumerate every safe/unsafe surface form (cf. OWASP 2025). The structural guardrail prevented unauthorized numeric generation by construction in every scenario: because P is never sampled by the model, an injection attempt can change only the wording of E, never P. Validation and composition are lightweight, deterministic post-processing steps executed after generation completes, so the added latency is small relative to LLM inference time (RQ4), and because explanations are unconstrained natural language subject only to a digit-free filter, conversational fluency is preserved (RQ3).

| Stage | Contribution to turn latency |
| :--- | :--- |
| LLM explanation generation | Dominant (network + inference) |
| Structural validation V(E) | Sub-inference-time, regex-based |
| Response composition G(P,E′) | Sub-inference-time, template fill |
| Fallback substitution (on failure) | Negligible, no extra model call |

*Table 4: Qualitative latency breakdown by pipeline stage. Guardrail overhead is deterministic post-processing after the dominant LLM call, so end-to-end responsiveness tracks the underlying model's inference time rather than the guardrail itself.*

We report this breakdown qualitatively rather than as absolute wall-clock numbers because the pilot ran against a shared, rate-limited external LLM endpoint whose latency varied with provider load independent of our guardrail; the relative ordering of contributions, however, was stable across runs and is the property relevant to RQ4 — the guardrail is not the bottleneck. A controlled benchmark isolating guardrail overhead from provider latency, once AI-SATHI runs against a fixed, self-hosted model, is left to future work.

## 6 Formative Field Study

To ground the architecture in real needs rather than assumed ones, we conducted a consent-governed, two-visit formative study at a cooperative society in Hooghly district, West Bengal (Table 5), prior to any deployment. No Aadhaar numbers, bank credentials, OTPs, or individual financial records were collected; participation, publication of anonymized responses, photography, and audio recording each used separate consent, and participants could withdraw or request deletion at any time.

| Item | Count |
| :--- | :---: |
| Participating SHGs | 8 |
| Site visits | 2 |
| Participants giving informed consent | 8 |
| Structured feedback forms completed | 5 |

*Table 5: Formative field study summary, Bali Gram Panchayat cooperative society, Hooghly district.*

Five recurring themes emerged and map directly onto system components: (i) bookkeeping was almost universally handwritten, incomplete, and hard to present to banks, motivating the Ledger agent; (ii) awareness of eligibility and procedure for government schemes was low despite many applicable programs, motivating retrieval-augmented scheme guidance; (iii) market access — not production capacity — was the most consistently cited barrier, motivating the Catalogue Creator, pricing, and negotiation agents; (iv) participants preferred spoken Bengali to typed text, motivating the voice-first design; and (v) government record-keeping systems were reported as occasionally slow or unavailable, reinforcing the need for a system that degrades gracefully under infrastructure gaps. Most participants used smartphones primarily for WhatsApp, and phones were often shared within a household — a usage pattern that shaped our preference for short, confirmable voice interactions over long typed sessions.

## 7 Discussion, Limitations, and Ethics

The central claim of this work is that trustworthiness in financial LLM assistants is better treated as a property of system architecture than of model behaviour: separating deterministic computation from language generation converts numerical correctness from a probabilistic outcome into a reproducible, auditable one, and this guarantee survives model upgrades or replacement. The red-team results reinforce a broader lesson for safety-critical societal deployments — filtering after generation cannot enumerate every safe/unsafe surface form in a multilingual, code-mixed setting, whereas removing the model's authority over the protected quantity removes the failure mode outright. The same pattern generalizes to other domains where an LLM should explain but not decide — loan eligibility, insurance quotes, dosage guidance, and tax computation among them.

**Generalizability.** Although AI-SATHI's protected quantity is a rupee amount, the pattern — compute the safety-critical value deterministically, generate only a digit-free (or otherwise scrubbed) explanation, validate before composition — requires only that (i) the protected quantity is expressible in closed form or by a lookup, and (ii) explanations can be usefully separated from the value they justify. Loan-eligibility verdicts, insurance premium quotes, dosage bands, and tax line-items share this shape; open-ended advice, diagnosis, or free-form recommendation generally does not, since there is no single deterministic value to protect.

**Limitations.** The guardrail assumes the deterministic pricing engine itself is correct and economically appropriate; it does not validate whether the business rules are optimal for a given product or market. Structural protection currently covers financial values only — scheme eligibility and market forecasts still depend on retrieval quality. The red-team suite, while covering six attack families, is not an exhaustive adversarial benchmark, and the field study is a single-site, leader-weighted, pre-deployment needs assessment (n=8 SHGs, one cooperative society) that should be read as exploratory rather than representative; AI-SATHI has not yet undergone a longitudinal deployment evaluating adoption or economic outcomes.

**Ethics.** The field study followed a granular informed-consent protocol (separate consent for participation, publication, photography, and recording), collected no Aadhaar, bank, or OTP data, and was presented explicitly as academic research rather than a financial or lending service. AI-SATHI is a decision-support tool, not an autonomous financial actor: it authorizes no loans and makes no binding decisions, and it discards voice audio immediately after transcription. We see the structural guardrail itself as an ethical design choice — in a community with limited means to contest an incorrect number, removing the LLM's ability to fabricate one is a meaningful reduction in harm, independent of any productivity benefit the assistant provides.

## 8 Conclusion

We presented a structurally enforced guardrail architecture that keeps financial values entirely outside an LLM's generative authority, and AI-SATHI, a voice-first WhatsApp assistant for rural SHGs that implements it across pricing, negotiation, bookkeeping, and catalogue agents. Red-teaming showed that ordinary multilingual phrasing — not adversarial cleverness — defeated an earlier blocklist guardrail, while the structural design prevented every tested scenario by construction. A consent-governed formative study across eight SHGs grounds the system in genuine, recurring bookkeeping and market-access needs and motivates its voice-first, privacy-preserving design. We position architectural separation of computation from generation as a general, model-agnostic pattern for societal-computing deployments where numerical correctness is safety-critical, and plan to extend it to additional protected information classes, evaluate AI-SATHI in a longitudinal multi-SHG pilot, and broaden dialectal and language coverage.

## References

*   Anonymous (FormBharo). 2026. FormBharo: Designing and Evaluating a Voice Agent for Conversational Form Filling in Rural India. arXiv:2608.06027.
*   Anonymous (GuardAgent). 2024. GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning. arXiv:2406.09187.
*   Anonymous (Ryt AI). 2025. Banking Done Right: Redefining Retail Banking with Language-Centric AI. arXiv:2510.07645.
*   Barnita Roy. 2025. Effect of Women's Self-Help Group Participation on Their Financial Inclusion Measured Through a Women-Centric Index: A Study in North-East India. Annals of Public and Cooperative Economics 96: 65–97.
*   Fábio Perez and Ian Ribeiro. 2022. Ignore Previous Prompt: Attack Techniques for Language Models. In NeurIPS ML Safety Workshop.
*   GiveDirectly. 2026. What 21,000 WhatsApp Messages Reveal About AI Utility in Extreme Poverty Contexts. GiveDirectly Research Note.
*   Government of India. 2023. The Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023). Ministry of Electronics and Information Technology.
*   He He, Derek Chen, Anusha Balakrishnan, and Percy Liang. 2018. Decoupling Strategy and Generation in Negotiation Dialogues. In EMNLP 2018, 2333–2343.
*   Hugo Touvron et al. 2023. Llama 2: Open Foundation and Fine-Tuned Chat Models. arXiv:2307.09288.
*   Indrani Medhi, Somani Patnaik, Emma Brunskill, S. N. Nagasena Gautama, William Thies, and Kentaro Toyama. 2011. Designing Mobile Interfaces for Novice and Low-Literacy Users. ACM TOCHI 18, 1: Article 2.
*   Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz. 2023. Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. In AISec '23, 79–90.
*   Kexin Xia et al. 2024. OG-Narrator: Decoupling Pricing Decisions from Language Generation in LLM-Based Negotiation Agents. In ACL 2024.
*   OpenAI. 2023. GPT-4 Technical Report. arXiv:2303.08774.
*   OWASP Foundation. 2025. OWASP Top 10 for Large Language Model Applications, 2025 Edition. OWASP GenAI Security Project.
*   Patrick Lewis et al. 2020. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In NeurIPS, 33:9459–9474.
*   Pragnya Ramjee, Bhuvan Sachdeva, Satvik Golechha, Shreyas Kulkarni, Geeta Fulari, Kaushik Murali, and Mohit Jain. 2025. CataractBot: An LLM-Powered Expert-in-the-Loop Chatbot for Cataract Patients. Proc. ACM IMWUT 9, 2: Article 45.
*   Pragnya Ramjee, Mehak Chhokar, Bhuvan Sachdeva, Mahendra Meena, Hamid Abdullah, Aditya Vashistha, Ruchit Nagar, and Mohit Jain. 2025. ASHABot: An LLM-Powered Chatbot to Support the Informational Needs of Community Health Workers. In CHI '25, 1–22.
*   Sakshi Joshi, Eldho Ittan George, Tahir Javed, Kaushal Bhogale, Nikhil Narasimhan, and Mitesh M. Khapra. 2025. Recognizing Every Voice: Towards Inclusive ASR for Rural Bhojpuri Women. In Interspeech 2025.
*   Simon Kloker, Julius Straub, et al. 2024. WASHtsApp — A RAG-Powered WhatsApp Chatbot for Supporting Rural African Clean Water Access, Sanitation and Hygiene. arXiv:2411.02850.
*   Tapan Parikh, Kaushik Ghosh, and Apala Chavan. 2003. Design Studies for a Financial Management System for Micro-Credit Groups in Rural India. In ACM CUU '03, 15–22.
*   Tom B. Brown et al. 2020. Language Models are Few-Shot Learners. In NeurIPS, 33:1877–1901.
*   Traian Rebedea, Razvan Dinu, Makesh Narsimhan Sreedhar, Christopher Parisien, and Jonathan Cohen. 2023. NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails. In EMNLP 2023: System Demonstrations, 431–445.
*   Yifei Dong, Fengyi Wu, Kunlin Zhang, Yilong Dai, Sanjian Zhang, Wanghao Ye, Sihan Chen, and Zhi-Qi Cheng. 2025. Large Language Model Agents in Finance: A Survey Bridging Research, Practice, and Real-World Deployment. In Findings of ACL: EMNLP 2025, 17889–17907.
*   Yuntao Bai et al. 2022. Constitutional AI: Harmlessness from AI Feedback. arXiv:2212.08073.
*   Zhengbao Ji et al. 2023. Survey of Hallucination in Natural Language Generation. ACM Comput. Surv. 55, 12: 1–38.
