# Liseli

**Zambia's Open Language Project**

**Zambia's Open Language Project**

**Liseli** ("light" in Lozi) is Zambia's open language project. We're building the dataset that will teach technology to understand Zambian languages — **Bemba, Nyanja, Tonga, Lozi, Kaonde, Lunda, Luvale**, and more to come.

If you speak a Zambian language, you can contribute. Translate a word, validate a phrase — every contribution counts.

---

## Why This Exists

AI speaks English. It doesn't speak Bemba, Nyanja, or Tonga. The 20 million Zambians who use these languages daily are locked out of AI tools that could transform health, agriculture, education, commerce, and government in Zambia.

No tech company will fix this. The market is too small, the languages too niche, and the linguistic expertise too local. **This is infrastructure that Zambians have to build ourselves.**

Languages that don't exist digitally lose status. If AI speaks English but not Nyanja, it reinforces that Nyanja is "less modern." Putting Zambian languages in AI is an act of preservation — making them languages of the future, not relics of the past.

Liseli crowdsources translations, validates them through community consensus, and produces open datasets that belong to Zambia. The data is CC BY-SA — free, open, owned by the community that built it.

## The Data

| Language | Parallel Pairs | Corpus | Words |
|----------|---------------|--------|-------|
| Nyanja (Chinyanja) | 57,733 | 79,096 | ~1.7M |
| Bemba (Icibemba) | 31,785 | 40,104 | ~755K |
| Tonga (Chitonga) | 31,751 | 39,897 | ~746K |
| Lozi (Silozi) | 31,803 | 43,931 | ~805K |
| Luvale | 31,777 | 39,535 | ~830K |
| Lunda (Chilunda) | 31,804 | 37,979 | ~691K |
| Kaonde (Kikaonde) | 8,888 | 18,228 | ~347K |

**Sources:** Storybooks Zambia (CC-BY), Bible translations, MoE teaching modules, USAID Let's Read, ZambeziVoice, FLORES-200, and community contributions.

## How It Works

1. **Translate** — See an English word or sentence. Translate it into your language.
2. **Validate** — Review others' translations. Vote: correct, almost, or wrong.
3. **Discuss** — When votes are split, the community debates and resolves.
4. **Build AI** — Every verified translation becomes training data for Zambian language AI.

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Data:** SQLite (local), Supabase (production)
- **Deployment:** Netlify
- **Data pipeline:** Python scripts for scraping, extraction, and alignment

## Getting Started

```bash
# Clone and install
git clone https://github.com/YumiMilling/Liseli.git
cd Liseli
npm install

# Run dev server
npm run dev
```

The app runs with pre-loaded data from `public/data/`. To rebuild the database from source materials, see `scripts/`.

## Data Pipeline

```bash
# Build local SQLite database from Storybooks Zambia
python scripts/build_local_db.py

# Extract text from MoE PDFs
python scripts/extract_pdf_text.py

# Align Bible translations (requires downloaded Bible files)
python scripts/align_bibles.py

# Extract statistical dictionaries
python scripts/extract_dictionary.py

# Generate cross-language pairs
python scripts/build_crosslang.py

# Export to JSON for frontend
python scripts/export_to_json.py
```

## Ownership

- **Code:** AGPL-3.0 — open source, always
- **Data:** CC BY-SA 4.0 — community-owned, open, free forever
- **Nobody locks up what the crowd built**

## Contributing

We welcome contributions from:
- **Zambian language speakers** — translate, validate, and discuss
- **Developers** — improve the platform
- **Linguists** — help with data quality and language structure
- **Researchers** — use the data, publish findings, share back

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Code: [AGPL-3.0](LICENSE)
Data: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
