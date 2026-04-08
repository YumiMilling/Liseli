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

## Day-One Users

### Primary: University Students
- **Who:** Language/linguistics students at UNZA, CBU, Mulungushi, Chalimbana
- **Why them:** Have linguistic knowledge, phone/data access, academic motivation, social networks
- **Hook:** "Contribute to your thesis. Build your language's AI dataset. Get credited."
- **Activation:** Partner with language departments, offer as coursework/extra credit, campus ambassadors

### Secondary: MoE Teachers
- **Who:** Teachers using the 2025 local language curriculum (Grades 1-4)
- **Why them:** Already working with the content, understand the languages deeply, motivated by professional relevance
- **Hook:** "The translations you verify become teaching tools. Help build AI that teaches in your language."

### Growth Path
1. **Seed:** 50-100 university contributors, validate mechanics and data quality
2. **WhatsApp word-of-mouth:** Shareable achievement cards, "I contributed 50 Tonga translations" images
3. **Provincial pride:** "Eastern Province leads! Northern Province closing the gap!" — friendly competition
4. **General public:** Once the app works and has visible traction, open to everyone
5. **Diaspora:** Zambians abroad miss their languages — emotional hook for contributions
