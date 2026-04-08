# Liseli — Project Memory

## Mission: Why Teach AI Zambian Languages?

### The Exclusion Problem
AI is English-first. Zambian languages (Bemba, Nyanja, Tonga, Lozi, Kaonde, Lunda, Luvale) are not meaningfully represented in any AI model. The people who could benefit most — rural communities needing agricultural advice, patients describing symptoms, parents helping children — are locked out.

### Concrete Use Cases
- **Health:** A mother in Mongu describes symptoms in Lozi to an AI health assistant
- **Agriculture:** A farmer in Serenje asks in Bemba when to plant maize
- **Education:** A Grade 3 student in Solwezi gets reading help in Kaonde (MoE mandates local language instruction Grades 1-4)
- **Government:** Citizens interact with services in their language
- **Commerce:** Voice-based AI for market traders
- **Legal:** Understanding rights, contracts, disputes in your own language

### Why Zambians Must Do This Themselves
- No commercial incentive for tech companies (small market)
- No existing digital corpus to scrape (unlike Hindi, Arabic)
- Linguistic expertise is inherently local — only speakers know what's correct
- **"Only Zambians can build Zambia's AI"** is literally true, not just marketing

### Language Survival Stakes
Languages that don't exist digitally lose status. If AI speaks English but not Nyanja, it reinforces that Nyanja is "less modern." Putting Zambian languages in AI makes them languages of the future.

### Window of Opportunity
AI is being built now. Models get bigger, products get built, patterns get set — all without Zambian languages. If not represented in training data within the next few years, they risk permanent AI invisibility.

---

## One App, Not Seven

**Decision: One unified app for all 7 languages. No separate apps.**

### Why One App
1. **The gap IS the motivation.** Lozi at 3% next to Bemba at 12% is a call to arms. Separate apps hide this.
2. **National identity > tribal identity.** "Zambia's AI" unites. Seven apps fragment along ethnic lines — politically sensitive.
3. **Multilingual contributors.** Most Zambians speak 2-4 languages. One app lets them contribute to all naturally.
4. **Community critical mass.** Seven tiny communities die. One community of 500 survives.
5. **Cross-language data value.** Same sentence in all 7 languages = 7-way parallel corpus, exponentially more valuable for AI.

### Personalization Within One App
- On signup: select your languages → app defaults to those
- Language switcher always visible, one tap
- "Your languages" vs "All languages" views on leaderboards
- Notifications in context: "Tonga needs 12 more health translations to reach 50%"

### One Exception
Voice-based interface for low-literacy users might warrant a separate lightweight app (fundamentally different UX). Future decision, not day-one.

---

## Motivation Design: Five Layers

### Layer 1: Identity & Purpose (Why I Start)
- The most powerful lever — uniquely strong for Liseli
- Frame contribution as a national act: "You're one of 23 Lozi contributors building the first Lozi AI dataset in history"
- Show absence visibly — coverage gaps are the call to action
- Reflect impact: "before you" vs "after you" visualization

### Layer 2: Micro-Completion Loops (Why I Stay 5 Minutes)
- Show ONE sentence at a time, full-screen, swipeable (like Duolingo, not a spreadsheet)
- AI pre-seed means often just tapping "Correct" — near-zero effort
- "Just one more" mechanics: "Nice! 3 more words in this topic?"
- Session summary: "You translated 5 words in Health. Bemba health vocabulary is now 34% complete."
- Completion sounds/haptics on mobile

### Layer 3: Progress & Status (Why I Come Back Tomorrow)
- **Points as impact:** "47 verified translations = 47 concepts taught to AI" (not abstract numbers)
- **Streaks:** Visual indicator, streak freeze earnable through points, weekly streaks (forgiving for intermittent data)
- **Leaderboards:** Per-language, per-province, weekly reset + all-time, "rising" (fastest climbers)
- **Trust titles:** 0-10 "New contributor", 10-25 "Active contributor", 25-50 "Trusted translator", 50+ "Language elder" — higher trust = votes carry more weight = real power

### Layer 4: Social & Competitive (Why I Tell Friends)
- **Provincial competition:** Map of Zambia colored by contribution density, weekly provincial rankings
- **Language rivalry (positive framing):** "Bemba at 12%, Nyanja at 9%. Who gets to 20% first?" — collaborative within, competitive between
- **Social proof:** "247 people contributed today", live activity feed
- **WhatsApp virality:** Shareable image cards ("I've contributed 50 Tonga translations"), not just links. Zambia runs on WhatsApp.

### Layer 5: Tangible Rewards (Last 10%)
- **Free tier (now):** Badges, titles, leaderboard position, "Language Elder" status with real influence
- **Sponsored tier (later, after traction):** Airtime rewards (Airtel/MTN), monthly prize draws
- **Never pay per translation from day one.** Attracts spam, kills intrinsic motivation. Build community first.

---

## Key Design Principles

1. **One-tap contribution flow** — reduce friction to absolute zero
2. **Language coverage gaps visible everywhere** — the absence motivates
3. **AI pre-seed as engagement** — correcting a machine is satisfying and produces higher-value training data
4. **Discussions as community** — translation debates are engagement, not friction. Feature them.
5. **Offline-first** — pre-load sentences when online, sync when reconnected. Many users have intermittent data.
6. **WhatsApp shareability** — the only growth channel that matters in Zambia

---

## LLM Training Path

| Milestone | What You Can Build | Method |
|-----------|-------------------|--------|
| 5K verified pairs | RAG-based translation agent | No training — retrieval + Claude |
| 20K pairs | Fine-tuned small model | LoRA fine-tune on Llama/Phi/Mistral |
| 100K+ pairs | Solid bilingual model | Full fine-tune on 7B base |
| 500K+ pairs | Foundation for Zambian language model | Pre-training candidate |

### The Flywheel
Better model → better AI pre-seeds → contributors correct fewer errors → faster data growth → better model

### Claude's Role
- **Generates seed data** (AI pre-seed attempts for contributors to correct)
- **Distillation** (bulk-generate translations, use output to fine-tune smaller open model)
- **Evaluation** (filter and assess translation quality)
- Cannot extract weights or create models directly — it's an inference API

### Key Tools
- Hugging Face Transformers + PEFT/LoRA for fine-tuning
- Unsloth for optimized fine-tuning on single GPU
- OPUS/NLLB (Meta's open translation models) as potential base
- Masakhane (African NLP research community)

---

## Technical Architecture

- **Frontend:** React PWA (Vite + Tailwind), mobile-first
- **Backend:** Supabase (auth, Postgres, real-time for leaderboards)
- **Hosting:** Netlify (free tier, SPA redirects)
- **Offline:** IndexedDB queue via `idb`, sync when connected, PWA service worker
- **Data:** Open dataset, CC BY-SA, public API endpoints

### Three Modes
1. **Translate** — See English source with AI attempt. Confirm, edit, or replace.
2. **Validate** — Vote on others' translations: correct / almost / wrong. 3 correct = verified.
3. **Discuss** — Flagged translations open threads. Community resolves or documents dialect variation.

### Quality Pipeline
Translation → unverified → votes → 3 correct from different contributors → verified
Split votes → flagged → discussion → community resolution → verified or rejected
Rejected translations kept as negative training examples.

### Three Tiers of Content
- **T1 Words:** "maize", "school" — lowest effort, fastest contribution
- **T2 Phrases:** "bag of maize" — shows how words combine, noun classes
- **T3 Sentences:** "How much is a bag of maize?" — full morphology, word order

Cross-tier linking via concept_id — the relationship between tiers is where grammar emerges.

### Seed Data
Ministry of Education curriculum materials (Grades 1-4, all 7 languages) — government-approved, standardised orthography. Community builds on top; divergences flagged as dialect variation.

---

## Growth Model
1. **Seed & test:** 50-100 contributors, validate mechanics
2. **Word of mouth:** University language departments, WhatsApp, provincial pride
3. **Sponsored:** Prizes, airtime, institutional partnerships (only after traction)
4. **Dataset consumption:** API access, research partnerships, fine-tuning

## Ownership
- App: open source (AGPL)
- Translations: community-owned (CC BY-SA)
- Nobody locks up what the crowd built

---

## Brand Identity

### Name
**Liseli** = "light" in Lozi. Illuminating Zambian languages for the AI era.

### Positioning
Modern open-data project. National language infrastructure — not a startup, not a dated wiki. Think of it as Zambia's equivalent of Common Voice (Mozilla) or OpenStreetMap, but for language.

**Tagline:** "Zambia's Open Language Project"

**Trust statement:** Prominent ownership declaration on every page. CC BY-SA and AGPL are pride badges, not legal fine print. "This data belongs to Zambia. Nobody locks up what the crowd built."

### Visual Identity

**Aesthetic:** Dark UI, modern and premium. The polish of Duolingo + the clarity of Linear + the community feel of GitHub. This is a serious national project, not a toy.

- **Primary color:** Emerald green (`#059669`) — Zambian flag colour
- **Dark background:** Slate 900 (`#0f172a`) — premium, modern, easy on eyes
- **Typography:** Inter — clean sans-serif, readable at all sizes
- **Micro-animations:** Progress bars filling, numbers ticking up, cards swiping, coverage percentages animating
- **Zambia map:** Data visualization showing provinces lit by contribution density — not decorative clipart, but a live dashboard showing where contributions come from
- **CC BY-SA badge:** Styled and prominent, a mark of pride not a footnote
- **Open source:** Featured as a selling point — "Built by Zambians, owned by Zambians, open to all"

### What the UI Should NOT Be
- Not a spreadsheet of translations (academic/boring)
- Not a dated wiki interface (Wikipedia circa 2008)
- Not cluttered with options (mobile-first, one action at a time)
- Not English-heavy (UI should feel bilingual, language names in endonyms)

---

## Sponsor Strategy

### Two Audiences, One Project

**To contributors:** "You're building something historic. The first dataset of its kind. Your language, preserved and empowered."

**To sponsors:** "Fund the infrastructure for Zambian language AI. Measurable impact, brand association with national digital inclusion."

### Why Sponsors Would Care

| Sector | Interest | Use Case |
|--------|----------|----------|
| **Telcos** (Airtel, MTN, Zamtel) | Voice AI, customer service in local languages | Chatbots that speak Bemba, IVR systems in Tonga |
| **Government** (Smart Zambia, MoE) | Digital inclusion, e-government | Government services accessible in all 7 languages |
| **Banks** (Zanaco, FNB, Stanbic) | Financial inclusion, mobile banking | Banking chatbots in local languages |
| **Research/NGOs** (UNICEF, USAID, British Council) | Language preservation, education | AI-powered learning tools |

### Value Proposition for Sponsors
- Logo placement on app and dataset
- Early API access to translation models
- PR: "Powering Zambian language AI"
- Named dataset releases ("The Airtel Zambian Language Corpus v1")
- Impact metrics: translations funded, languages covered, contributors supported

### Sponsor Tiers

| Tier | Contribution | Recognition |
|------|-------------|-------------|
| **Community Partner** | In-kind (airtime, prizes, hosting) | Logo on sponsors page, social media mentions |
| **Training Sponsor** | Fund model training compute | Logo on app, named model release, API preview |
| **Founding Sponsor** | Major funding, multi-year commitment | Co-branding, advisory role, permanent recognition |

### Non-Negotiable Rule
**Never compromise community ownership for sponsorship.** Data stays CC BY-SA. Code stays AGPL. No exclusive access deals. No data lock-in. Sponsors fund the project; the crowd owns the output.

---

## User Personas

### 1. Mwila — The Linguistics Student (21, UNZA, Lusaka)
- **Languages:** Bemba (mother tongue), Nyanja (town), English (academic)
- **Device:** Mid-range Android, always on WhatsApp, intermittent WiFi at campus
- **Motivation:** Needs thesis material, wants her name on something published, peer validation
- **Behaviour:** Does 10-20 translations in one sitting between classes, shares progress with classmates
- **What she needs from Liseli:** Quick sign-up (Google), visible contribution count, shareable stats card, her name credited on the dataset
- **Risk:** Loses interest after the novelty wears off — needs streaks or academic incentive to retain
- **Sign-up trigger:** Lecturer mentions it in class, or classmate shares WhatsApp achievement card
- **Trust level:** Starts as contributor, can become trusted translator quickly with volume

### 2. Mr. Banda — The Posted Teacher (34, Grade 2, Southern Province)
- **Languages:** Nyanja (home), learning Tonga (for students), English (professional)
- **Device:** Older Android, buys data bundles weekly, uses phone mostly for WhatsApp and calling
- **Motivation:** Needs to teach in Tonga but doesn't speak it well — the cross-language feature is genuinely useful for lesson prep
- **Behaviour:** Uses the app as a reference tool first, contributes translations when he feels confident
- **What he needs from Liseli:** Cross-language dictionary, offline access, simple UI with big text, validation of Tonga entries so he knows they're correct
- **Risk:** Won't contribute if the flow is complex or data-heavy — he's paying per MB
- **Sign-up trigger:** Shared by another teacher on a WhatsApp group, or recommended at a CPD workshop
- **Trust level:** Reliable validator for Nyanja, cautious contributor for Tonga

### 3. Chanda — The Diaspora Developer (28, Cape Town)
- **Languages:** Bemba (childhood), English (daily), Nyanja (some)
- **Device:** iPhone, fast internet, uses GitHub
- **Motivation:** Misses home, wants to contribute to Zambia without moving back, understands the tech value
- **Behaviour:** Contributes in bursts — 50 translations on a Sunday afternoon. Also looks at the codebase, might submit PRs.
- **What he needs from Liseli:** Open source credibility (GitHub, AGPL), clean API, visible data quality metrics, a way to contribute code not just translations
- **Risk:** Will leave if the project looks amateur or the data is full of junk
- **Sign-up trigger:** Finds the GitHub repo through African NLP communities (Masakhane, etc.)
- **Trust level:** High for Bemba, can review code and data quality

### 4. Ba Mutale — The Retired Teacher (55, Kasama)
- **Languages:** Deep Bemba (including rural dialects), English (limited)
- **Device:** Basic smartphone, struggles with small text, son helps him with apps
- **Motivation:** Worried that young people are losing Bemba, wants to preserve it
- **Behaviour:** Would validate 5-10 entries per day if the flow is simple. His contributions are gold — dialect knowledge no student has.
- **What he needs from Liseli:** Large text, minimal options per screen, Bemba UI labels where possible, voice input eventually
- **Risk:** Will abandon the app if he can't figure out sign-up or navigation alone
- **Sign-up trigger:** Son or grandchild sets it up for him
- **Trust level:** Should be "Language Elder" fast — his validations carry more weight than a student's

### 5. Bwalya — The NGO Officer (38, UNICEF, Lusaka)
- **Languages:** Bemba, Nyanja, English (professional)
- **Device:** Good Android, office laptop, strong internet
- **Motivation:** Works on "digital inclusion" but it's all reports and workshops — wants to DO something real
- **Behaviour:** Champions Liseli internally, connects it to funding. Contributes moderately but her real value is institutional credibility and network.
- **What she needs from Liseli:** Impact metrics she can put in a report ("Liseli has X translations by Y contributors"), professional presentation, data export for research
- **Risk:** Wants to "partner" and slow things down with institutional process
- **Sign-up trigger:** Sees it at a digital inclusion conference or through ZAMAI network
- **Trust level:** Moderate contributor, high value as ambassador and connector

### 6. Mumba — The Frustrated Civil Servant (42, MoE, Ndola)
- **Languages:** Bemba, Nyanja, some Lamba
- **Device:** Android, government data plan
- **Motivation:** Knows the education system is failing at local language instruction. Sees Liseli as what the ministry should have built. Quiet contribution — doesn't want visibility from employer.
- **Behaviour:** Validates MoE-sourced content for accuracy, contributes during lunch breaks
- **What he needs from Liseli:** Anonymity option (handle not real name), ability to validate specific domains (education), see that the data is actually being used
- **Risk:** May push for government involvement which could politicize the project
- **Sign-up trigger:** Hears about it through education WhatsApp groups
- **Trust level:** High validator for education content specifically

### 7. Tembo — The Language Champion (30, Monze)
- **Languages:** Tonga (fierce pride), English, some Nyanja
- **Device:** Android, decent data
- **Motivation:** Identity. Tonga is underrepresented everywhere — in government, media, technology. Liseli's coverage chart showing Tonga behind Bemba lights a fire in him.
- **Behaviour:** Recruits every Tonga speaker he knows. Posts about it on Facebook. Competitive — checks the leaderboard daily. Will do 100 translations to push Tonga past Bemba.
- **What he needs from Liseli:** Provincial/language leaderboards, visible competition ("Tonga vs Bemba"), community pride metrics, ability to recruit and track his network's contributions
- **Risk:** Quality suffers when he's chasing quantity. May submit rushed translations to boost numbers.
- **Sign-up trigger:** Sees a post about it on Zambian Facebook/WhatsApp, notices Tonga is low
- **Trust level:** High volume but needs cross-validation — flag if accuracy drops while speed increases

### 8. The Troll
- **Who:** Bad actor — bored teenager, political saboteur, or spam bot
- **Behaviour:** Submits "asdf", offensive content, deliberately wrong translations, or automated garbage
- **Design against:**
  - Rate limiting (max translations per hour)
  - Cross-validation (3 independent votes needed)
  - Anomaly detection (flag contributors whose validations consistently disagree with consensus)
  - New accounts can only validate high-confidence entries, not translate freely
  - Report button on every translation
  - Shadow ban (they see their contributions but nobody else does)
  - IP/device fingerprinting for repeat offenders

### Sign-up Flow (for all personas)
- **Barrier:** As low as possible
- **Options:** Phone number (SMS OTP) or Google sign-in — these cover 95% of Zambian smartphone users
- **Profile creation:** Handle (not real name required), languages spoken, province — three fields, one screen
- **Browse first:** Anyone can explore the data without signing up. Sign-up prompt appears only when they try to contribute.
- **Progressive profile:** Start minimal, earn badges and trust level through contributions

### Growth Path
1. **Seed:** 50-100 university contributors (Mwila × 50), validate mechanics and data quality
2. **WhatsApp word-of-mouth:** Shareable achievement cards, "I contributed 50 Tonga translations" images
3. **Provincial pride:** "Eastern Province leads! Northern Province closing the gap!" — Tembo recruits his whole town
4. **Institutional adoption:** Bwalya brings UNICEF/MoE interest, adds credibility
5. **General public:** Once the app works and has visible traction, open to everyone
6. **Diaspora:** Chanda tells the Masakhane Slack channel, developer community picks it up
7. **Elders:** Ba Mutale's son sets it up for him, his contributions become the gold standard
