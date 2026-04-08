"""
Build local SQLite database for Liseli from scraped materials.
- Scrapes Storybooks Zambia (bilingual story texts)
- Imports into SQLite with schema matching Supabase
"""

import sqlite3
import ssl
import json
import uuid
import os
import re
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "liseli_local.db"
STORYBOOKS_DIR = BASE_DIR / "data" / "storybooks-zambia"

# Zambian languages on Storybooks Zambia
LANG_MAP = {
    "bem": "bemba",
    "ny": "nyanja",
    "toi": "tonga",
    "loz-zm": "lozi",
    "kqn": "kaonde",
    "lun": "lunda",
    "lue": "luvale",
}

# SSL context that skips verification (needed for some sites)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Liseli/1.0 (educational)"})
    with urlopen(req, context=ctx, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


class StoryPageParser(HTMLParser):
    """Extract bilingual text from a Storybooks Zambia story page."""

    def __init__(self):
        super().__init__()
        self.pages = []  # list of {"en": ..., "l2": ...}
        self._current_div_class = None
        self._in_h1 = False
        self._in_h3 = False
        self._capture = None  # "def", "l1", "l2", or None
        self._current_page = {}
        self._text_buf = ""
        self._div_depth = 0
        self._in_text_div = False

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")

        if tag == "div":
            div_id = attr_dict.get("id", "")
            if re.match(r"text\d+", div_id):
                self._in_text_div = True
                self._div_depth = 0
                if self._current_page.get("en") or self._current_page.get("l2"):
                    self.pages.append(self._current_page)
                self._current_page = {}
            if self._in_text_div:
                self._div_depth += 1

            # Detect l1/l2/def content divs
            # "def" = the page's primary language (the one in the URL)
            # "l1" = English
            # "l2" = Bemba (always Bemba as secondary, regardless of URL language)
            if "level" in cls and "-txt" in cls:
                if " def" in f" {cls} " or cls.endswith("def"):
                    self._capture = "def"
                    self._text_buf = ""
                elif " l1" in f" {cls} " or cls.endswith("l1"):
                    self._capture = "l1"
                    self._text_buf = ""
                elif " l2" in f" {cls} " or cls.endswith("l2"):
                    self._capture = "l2"
                    self._text_buf = ""

        if tag == "h1":
            self._in_h1 = True
        if tag == "h3" and self._capture:
            self._in_h3 = True
            self._text_buf = ""

        if tag == "span":
            if "l1" in cls.split():
                self._capture = "span_l1"
                self._text_buf = ""
            elif "l2" in cls.split():
                self._capture = "span_l2"
                self._text_buf = ""

    def handle_endtag(self, tag):
        if tag == "div" and self._in_text_div:
            self._div_depth -= 1
            if self._capture in ("l1", "l2", "def") and self._text_buf.strip():
                # "def" = target language, "l1" = English, "l2" = Bemba (secondary)
                if self._capture == "def":
                    key = "target"
                elif self._capture == "l1":
                    key = "en"
                else:
                    key = "bemba_secondary"
                self._current_page[key] = self._text_buf.strip()
                self._text_buf = ""
                self._capture = None

        if tag == "h3" and self._in_h3:
            self._in_h3 = False
            if self._capture and self._text_buf.strip():
                if self._capture == "def":
                    key = "target"
                elif self._capture == "l1":
                    key = "en"
                else:
                    key = "bemba_secondary"
                self._current_page[key] = self._text_buf.strip()

        if tag == "h1":
            self._in_h1 = False

        if tag == "span":
            if self._capture == "span_l1" and self._text_buf.strip():
                self._current_page["en_title"] = self._text_buf.strip()
                self._capture = None
            elif self._capture == "span_l2" and self._text_buf.strip():
                self._current_page["l2_title"] = self._text_buf.strip()
                self._capture = None

    def handle_data(self, data):
        if self._capture and (self._in_h3 or self._in_h1):
            self._text_buf += data
        elif self._capture in ("span_l1", "span_l2"):
            self._text_buf += data

    def finish(self):
        if self._current_page.get("en") or self._current_page.get("target"):
            self.pages.append(self._current_page)


def scrape_story(story_id: str, lang_code: str) -> list[dict]:
    """Scrape a single story page and return bilingual text pairs."""
    url = f"https://storybookszambia.net/stories/{lang_code}/{story_id}/"
    try:
        html = fetch(url)
    except Exception as e:
        print(f"    FETCH ERROR {story_id}/{lang_code}: {e}")
        return []

    parser = StoryPageParser()
    parser.feed(html)
    parser.finish()

    # Build pairs from pages
    # "target" = the language from the URL (def class)
    # "en" = English (l1 class)
    pairs = []
    for page in parser.pages:
        en = page.get("en", "").strip()
        target = page.get("target", "").strip()
        if en and target:
            pairs.append({"en": en, "l2": target})

    # Also check for title pair
    title_pages = [p for p in parser.pages if p.get("en_title") and p.get("l2_title")]
    if title_pages:
        tp = title_pages[0]
        pairs.insert(0, {"en": tp["en_title"], "l2": tp["l2_title"]})

    return pairs


def get_story_ids() -> list[str]:
    """Get all story IDs from the English stories page."""
    html = fetch("https://storybookszambia.net/stories/en/")
    return sorted(set(re.findall(r"/stories/en/(\d+)/", html)))


def classify_tier(text: str) -> str:
    words = text.split()
    if len(words) <= 2:
        return "word"
    elif len(words) <= 6:
        return "phrase"
    return "sentence"


def init_db(db_path: Path) -> sqlite3.Connection:
    """Create SQLite database with Liseli schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sentences (
            id TEXT PRIMARY KEY,
            english TEXT NOT NULL,
            tier TEXT NOT NULL CHECK (tier IN ('word', 'phrase', 'sentence')),
            domain TEXT NOT NULL DEFAULT 'education',
            concept_id TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'moe' CHECK (source IN ('moe', 'ai', 'community')),
            difficulty INTEGER NOT NULL DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS translations (
            id TEXT PRIMARY KEY,
            sentence_id TEXT NOT NULL REFERENCES sentences(id),
            language TEXT NOT NULL CHECK (language IN ('bemba','nyanja','tonga','lozi','kaonde','lunda','luvale')),
            text TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'moe',
            status TEXT NOT NULL DEFAULT 'verified',
            story_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(sentence_id, language, text)
        );

        CREATE TABLE IF NOT EXISTS source_materials (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            source_type TEXT NOT NULL,
            language TEXT,
            level TEXT,
            term TEXT,
            file_path TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_sentences_tier ON sentences(tier);
        CREATE INDEX IF NOT EXISTS idx_sentences_domain ON sentences(domain);
        CREATE INDEX IF NOT EXISTS idx_translations_sentence ON translations(sentence_id);
        CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language);
        CREATE INDEX IF NOT EXISTS idx_translations_status ON translations(status);
    """)
    conn.commit()
    return conn


def catalog_pdfs(conn: sqlite3.Connection):
    """Catalog downloaded MoE PDFs in the database."""
    pdf_dir = BASE_DIR / "data" / "moe-zambian-languages"
    if not pdf_dir.exists():
        print("No MoE PDF directory found, skipping catalog")
        return

    count = 0
    for pdf_file in sorted(pdf_dir.glob("*.pdf")):
        name = pdf_file.stem.upper()

        # Determine language
        lang = None
        for keyword, lang_id in {
            "ICIBEMBA": "bemba", "BEMBA": "bemba",
            "CINYANJA": "nyanja", "NYANJA": "nyanja",
            "CHITONGA": "tonga", "TONGA": "tonga",
            "SILOZI": "lozi", "LOZI": "lozi",
            "KIKAONDE": "kaonde", "KAONDE": "kaonde",
            "LUNDA": "lunda",
            "LUVALE": "luvale",
        }.items():
            if keyword in name:
                lang = lang_id
                break

        # Determine level
        level = None
        if "ECE" in name:
            level = "ECE"
        elif "GRADE-1" in name or "GRADE1" in name:
            level = "Grade 1"
        elif "FORM-1" in name or "FORM1" in name:
            level = "Form 1"

        # Determine term
        term = None
        term_match = re.search(r"TERM[- ]?(\d)", name)
        if term_match:
            term = f"Term {term_match.group(1)}"

        source_type = "literature" if "LITERATURE" in name or "LIT-IN" in name else "teaching_module"

        conn.execute("""
            INSERT OR IGNORE INTO source_materials (id, filename, source_type, language, level, term, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), pdf_file.name, source_type, lang, level, term,
            str(pdf_file.relative_to(BASE_DIR))
        ))
        count += 1

    conn.commit()
    print(f"  Cataloged {count} MoE PDFs")


def import_storybooks(conn: sqlite3.Connection):
    """Scrape Storybooks Zambia and import bilingual pairs."""
    print("\nScraping Storybooks Zambia...")
    story_ids = get_story_ids()
    print(f"  Found {len(story_ids)} stories")

    total_pairs = 0
    total_sentences = 0

    for lang_code, lang_name in LANG_MAP.items():
        print(f"\n  {lang_name} ({lang_code}):")
        lang_pairs = 0

        for story_id in story_ids:
            pairs = scrape_story(story_id, lang_code)
            if not pairs:
                continue

            for pair in pairs:
                en_text = pair["en"]
                l2_text = pair["l2"]
                tier = classify_tier(en_text)

                # Insert English sentence (deduplicate by text)
                existing = conn.execute(
                    "SELECT id FROM sentences WHERE english = ?", (en_text,)
                ).fetchone()

                if existing:
                    sentence_id = existing[0]
                else:
                    sentence_id = str(uuid.uuid4())
                    conn.execute("""
                        INSERT INTO sentences (id, english, tier, domain, concept_id, source)
                        VALUES (?, ?, ?, 'education', ?, 'moe')
                    """, (sentence_id, en_text, tier, f"storybook-{story_id}"))
                    total_sentences += 1

                # Insert translation
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO translations (id, sentence_id, language, text, source, status, story_id)
                        VALUES (?, ?, ?, ?, 'moe', 'verified', ?)
                    """, (str(uuid.uuid4()), sentence_id, lang_name, l2_text, story_id))
                    lang_pairs += 1
                except sqlite3.IntegrityError:
                    pass

            print(f"    Story {story_id}: {len(pairs)} pairs")

        conn.commit()
        total_pairs += lang_pairs
        print(f"  {lang_name} total: {lang_pairs} translation pairs")

    print(f"\n  TOTAL: {total_sentences} unique English sentences, {total_pairs} translations")

    # Save scraped text files too
    STORYBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for lang_code, lang_name in LANG_MAP.items():
        lang_dir = STORYBOOKS_DIR / f"{lang_code}-{lang_name}"
        lang_dir.mkdir(exist_ok=True)

        for story_id in story_ids:
            pairs = conn.execute("""
                SELECT s.english, t.text FROM translations t
                JOIN sentences s ON s.id = t.sentence_id
                WHERE t.story_id = ? AND t.language = ?
            """, (story_id, lang_name)).fetchall()

            if pairs:
                outfile = lang_dir / f"{story_id}.txt"
                with open(outfile, "w", encoding="utf-8") as f:
                    f.write(f"# Story ID: {story_id}\n")
                    f.write(f"# English <-> {lang_name} ({lang_code})\n")
                    f.write(f"# Source: https://storybookszambia.net/stories/{lang_code}/{story_id}/\n")
                    f.write(f"# License: CC-BY\n\n")
                    for en, l2 in pairs:
                        f.write(f"EN: {en}\n")
                        f.write(f"{lang_code}: {l2}\n\n")


def print_summary(conn: sqlite3.Connection):
    """Print database summary."""
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)

    total = conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0]
    print(f"\nTotal English sentences: {total}")

    print("\nBy tier:")
    for row in conn.execute("SELECT tier, COUNT(*) FROM sentences GROUP BY tier ORDER BY tier"):
        print(f"  {row[0]}: {row[1]}")

    print("\nTranslations by language:")
    for row in conn.execute("""
        SELECT language, COUNT(*), COUNT(*) FILTER (WHERE status='verified')
        FROM translations GROUP BY language ORDER BY language
    """):
        print(f"  {row[0]}: {row[1]} total ({row[2]} verified)")

    print("\nSource materials (MoE PDFs):")
    for row in conn.execute("""
        SELECT language, COUNT(*) FROM source_materials
        WHERE language IS NOT NULL GROUP BY language ORDER BY language
    """):
        print(f"  {row[0]}: {row[1]} files")

    print(f"\nDatabase: {DB_PATH}")
    print(f"Size: {DB_PATH.stat().st_size / 1024:.1f} KB")


def main():
    print("=" * 50)
    print("LISELI - Building Local Database")
    print("=" * 50)

    print(f"\nDatabase: {DB_PATH}")
    conn = init_db(DB_PATH)

    print("\n1. Cataloging MoE PDFs...")
    catalog_pdfs(conn)

    print("\n2. Scraping & importing Storybooks Zambia...")
    import_storybooks(conn)

    print_summary(conn)
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
