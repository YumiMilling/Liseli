
---

## Tutor App — English Learning That Feeds Liseli

### The Insight

People don't want to "build a dataset." They want to learn English, pass exams, get jobs. An English tutor app gives them something they actually want — and every interaction produces data for Liseli.

**The learner thinks:** "I'm practicing English."
**The database sees:** "New verified translation pair. New pronunciation recording. New validation vote."

### Two Brands, One Database

| | **Liseli** | **Tutor App** |
|---|---|---|
| Framing | "Build Zambia's language data" | "Learn English for free" |
| Motivation | Patriotism, contribution, pride | Self-improvement, grades, jobs |
| Primary user | University students, teachers, diaspora | School kids (Gr 1-9), job seekers, parents |
| Data produced | Same sentences, translations, audio, validations |
| Backend | Supabase `sentences`, `translation_pairs`, `pronunciations`, `re_recordings` |

The tutor app is a **separate frontend** that reads from and writes to the same Liseli Supabase database. Different UI, different brand, same data layer.

### Exercise Types → Data Produced

#### 1. Vocabulary (produces: dictionary validation)
```
Show: Picture of a dog
Ask: "What is this in English?"
Student types: "dog"
→ Correct! 

Now ask: "What is 'dog' in Icibemba?"
Student types: "imbwa"
→ DATA: validates or creates translation pair (dog ↔ imbwa)
```

#### 2. Translate to English (produces: translation pairs)
```
Show: "Amenshi yawama"
Ask: "What does this mean in English?"
Student types: "The water is clean"
→ DATA: new EN translation for an existing Nyanja sentence
→ If it matches an existing verified translation: student scores points
→ If it's different: flagged for community validation
```

#### 3. Listen & Type (produces: ASR training data)
```
Play: Audio of "The children are going to school"
Ask: "Type what you heard"
Student types: "The children are going to school"
→ Correct! Tests English listening comprehension
→ DATA: validates the audio clip + transcription pair
```

#### 4. Read Aloud (produces: pronunciation data)
```
Show: "Good morning, how are you?"
Ask: "Read this aloud" → student records
→ DATA: English pronunciation with Zambian accent (valuable for ASR)
→ Also: re_recording linked to sentence_id

Show: "Mwabonwa, muli bwanji?"
Ask: "Read this in Icibemba" → student records  
→ DATA: Bemba pronunciation → pronunciations table
```

#### 5. Multiple Choice (produces: validation votes)
```
Show: "fever"
Ask: "Which is correct in Chitonga?"
A) umusunko  B) ulubuto  C) icitondo
Student picks A
→ DATA: validation vote on dictionary entry (weighted by student's accuracy history)
```

#### 6. Fill in the Blank (produces: grammar patterns)
```
Show: "I ___ going to school" (am/is/are)
Student picks: "am"
→ Tests English grammar

Show: "Nine ___ ku sukulu" (naya/ndeya/baya)
Student picks: "ndeya"
→ DATA: verb conjugation validation (1st person singular, present progressive, Bemba)
```

#### 7. Picture Description (produces: sentence-level translations)
```
Show: Photo of a market scene
Ask: "Describe this in English"
Student types: "A woman is selling tomatoes at the market"
Ask: "Now say the same thing in your language"
Student types: "Umwanakashi aleshitisha intomato ku musika"
→ DATA: natural, contextual parallel pair — not Bible/textbook language
```

#### 8. Story Completion (produces: natural language)
```
Show first part of a Storybooks Zambia story in target language
Ask: "What happens next? Write in English"
Student writes continuation
→ DATA: comprehension check + creative English writing
→ Also validates that student understood the source language text
```

### Difficulty Levels Map to Data Needs

| Level | English skill | Exercises | Data produced |
|---|---|---|---|
| **Beginner** (Gr 1-3) | Letters, basic words | Vocabulary, picture matching, read aloud single words | Word-level dictionary, pronunciation |
| **Elementary** (Gr 4-6) | Simple sentences | Translate phrases, fill blanks, listen & type | Phrase-level pairs, grammar patterns |
| **Intermediate** (Gr 7-9) | Paragraphs, grammar | Translate sentences, picture description, story | Sentence-level pairs, natural language |
| **Advanced** (secondary+) | Fluent reading/writing | Translate complex text, discuss, correct AI | High-quality corrections, nuanced translations |

### The Zambian Curriculum Alignment

MoE mandates local language instruction Grades 1-4, transition to English from Grade 5. The tutor app maps directly to this:

- **Gr 1-4:** Learn in your language, start basic English words → produces word-level data
- **Gr 5-7:** Transition to English → produces the most translation pairs (students actively translating between languages)  
- **Gr 8-9:** English fluency → produces sentence-level data, complex translations

### Data Quality From Learners

Learner data is noisy — they make mistakes. But this is actually useful:

**Correct answers** → validation of existing data (high confidence)
**Common wrong answers** → reveal systematic patterns ("Bemba speakers commonly confuse X with Y") → useful for building better teaching materials AND better translation models
**Unique correct answers** → new translations we didn't have

Quality control:
- Weight learner votes lower than expert contributors (trust_score = 0.3 vs 0.8)
- Require 5 learner votes to equal 2 expert votes
- Flag patterns: if 80% of Bemba-speaking learners give the same "wrong" answer, it might actually be a valid dialectal variant

### How It Feeds Liseli's Database

Every tutor interaction maps to existing Liseli tables:

```
Exercise completed
  → sentences table (if new English text produced)
  → translation_pairs table (if translation produced)
  → validation_votes table (if multiple choice / confirm)
  → pronunciations table (if read-aloud)
  → re_recordings table (if speak-in-your-language)
  → contributions table (user gets credit)
  → user_language_trust table (accuracy tracked)
```

New fields needed in existing tables:
```
contributions.context = 'tutor'  -- vs 'liseli' for direct contributors
sentences.source_id = 'tutor-app'
```

### Technical Architecture

```
┌─────────────┐     ┌─────────────┐
│  Liseli App │     │  Tutor App  │
│ (contribute)│     │   (learn)   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
        ┌──────┴──────┐
        │  Supabase   │
        │  (shared)   │
        │             │
        │ sentences   │
        │ translations│
        │ audio       │
        │ users       │
        └─────────────┘
```

Same database, same API, same auth. Two React frontends, deployed separately on Netlify.

### Naming

The tutor app needs a name that appeals to Zambian school kids and parents. Options:

- **Phunzira** ("learn" in Nyanja) — but only resonates with Nyanja speakers
- **Sambilila** ("learn" in Bemba) — same issue
- **Mwana Smart** — "smart child", code-switches like Zambians actually do
- **Liseli Learn** — keeps the brand but adds learning angle
- **Something in English** — "LearnZam", "ZamEnglish" — aspirational

Should NOT feel like another school assignment. Should feel like a game / social app.

### Revenue Angle

The tutor app could eventually be:
- **Free basic tier** (produces data = the real product)
- **Premium tier** (AI-powered explanations, personalized lessons, progress reports for parents) — pays for infrastructure
- **School/NGO licenses** (bulk access, teacher dashboards, MoE alignment reports)
- **Sponsor-funded** (telcos bundle it with data plans: "Free English lessons with your Airtel bundle")

The data produced is always open (CC BY-SA). The app experience can be monetized. This funds Liseli's infrastructure without compromising the open data mission.

