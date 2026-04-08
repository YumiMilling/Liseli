"""
Extract Cinyanja text from downloaded JW.org HTML files and fetch additional content.
Saves to corpus text file and inserts into SQLite database.
"""

import re
import sqlite3
import uuid
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "nyanja-zambian"
DB_PATH = BASE_DIR / "data" / "liseli_local.db"
OUTPUT_FILE = DATA_DIR / "jw-cinyanja-corpus.txt"


class JWTextExtractor(HTMLParser):
    """Extract prose text from JW.org HTML pages."""

    # Tags that contain text we want
    TEXT_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "td", "blockquote", "figcaption"}
    # Tags/classes to skip
    SKIP_CLASSES = {
        "articleNavLinks", "articleShareLinks", "articleFooterLinks",
        "articlePrintButton", "articleShareButton", "articleCitation",
        "jsAudioPlayer", "jsNav", "navPublications", "siteBanner",
        "footerLinks", "pageFooter", "siteFooter", "siteHeader",
        "jsScrollIndicator", "jsDisclaimer", "modalContainer",
        "jsRespImg", "lnkReported", "directoryBar",
    }

    def __init__(self):
        super().__init__()
        self.texts = []
        self._in_article = False
        self._in_text_tag = False
        self._skip_depth = 0
        self._current_text = ""
        self._in_script = False
        self._article_depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")

        # Skip scripts and styles
        if tag in ("script", "style", "noscript"):
            self._in_script = True
            return

        # Skip navigation and site-level footer only (NOT header inside article)
        if tag == "nav":
            self._skip_depth += 1
            return
        # Only skip footer at site level (has class with 'site' or 'page')
        if tag == "footer" and ("site" in cls.lower() or "page" in cls.lower()):
            self._skip_depth += 1
            return

        # Skip certain classes
        if any(sc in cls for sc in self.SKIP_CLASSES):
            self._skip_depth += 1
            return

        # Track article
        if tag == "article":
            self._in_article = True
            self._article_depth += 1

        # Capture text from text tags inside article
        if tag in self.TEXT_TAGS and self._in_article and self._skip_depth == 0:
            self._in_text_tag = True
            self._current_text = ""

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._in_script = False
            return

        if tag == "nav":
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "footer" and self._skip_depth > 0:
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if tag == "article":
            self._article_depth -= 1
            if self._article_depth <= 0:
                self._in_article = False

        if tag in self.TEXT_TAGS and self._in_text_tag:
            self._in_text_tag = False
            text = self._current_text.strip()
            text = re.sub(r'\s+', ' ', text)
            if text and len(text) >= 5:
                self.texts.append(text)
            self._current_text = ""

    def handle_data(self, data):
        if self._in_script or self._skip_depth > 0:
            return
        if self._in_text_tag:
            self._current_text += data


def extract_text_from_html(filepath: Path) -> list[str]:
    """Extract clean Cinyanja text lines from an HTML file."""
    try:
        html = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  Error reading {filepath.name}: {e}")
        return []

    # Fix IE conditional comments that break the parser
    html = re.sub(r'<!--\[if[^\]]*\]>.*?<!\[endif\]-->', '', html, flags=re.DOTALL)
    # Also handle unclosed base tags
    html = re.sub(r'<base\b[^>]*/?>(?!</base>)', lambda m: m.group(0) if m.group(0).endswith('/>') else m.group(0), html)

    parser = JWTextExtractor()
    try:
        parser.feed(html)
    except Exception as e:
        print(f"  Error parsing {filepath.name}: {e}")
        return []

    # If no article tag found, try fallback: extract from entire body
    if not parser.texts:
        parser2 = JWFallbackExtractor()
        try:
            parser2.feed(html)
        except Exception:
            pass
        return parser2.texts

    return parser.texts


class JWFallbackExtractor(HTMLParser):
    """Fallback extractor for pages without <article> tags - extracts from main/body."""

    TEXT_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}

    def __init__(self):
        super().__init__()
        self.texts = []
        self._in_main = False
        self._in_text_tag = False
        self._current_text = ""
        self._in_script = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")
        tag_id = attr_dict.get("id", "")

        if tag in ("script", "style", "noscript"):
            self._in_script = True
            return

        if tag == "nav" or tag == "footer":
            self._skip_depth += 1
            return

        if tag == "main" or (tag == "div" and tag_id == "content"):
            self._in_main = True

        if tag in self.TEXT_TAGS and self._in_main and self._skip_depth == 0:
            self._in_text_tag = True
            self._current_text = ""

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._in_script = False
            return
        if tag in ("nav", "footer"):
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag in self.TEXT_TAGS and self._in_text_tag:
            self._in_text_tag = False
            text = re.sub(r'\s+', ' ', self._current_text.strip())
            if text and len(text) >= 5:
                self.texts.append(text)
            self._current_text = ""

    def handle_data(self, data):
        if self._in_script or self._skip_depth > 0:
            return
        if self._in_text_tag:
            self._current_text += data


def clean_sentence(text: str) -> str:
    """Clean a sentence for corpus use."""
    # Remove reference markers like (a), (b), etc.
    text = re.sub(r'^\s*\([a-z]\)\s*', '', text)
    # Remove leading bullet markers
    text = re.sub(r'^\s*[•●◦▪]\s*', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Strip
    text = text.strip()
    return text


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences on period, question mark, exclamation."""
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for part in parts:
        part = clean_sentence(part)
        if part and len(part) >= 5:
            sentences.append(part)
    return sentences


def is_cinyanja_text(text: str) -> bool:
    """Basic check that text is likely Cinyanja, not English boilerplate."""
    # Skip pure English navigation text
    english_only = re.match(
        r'^(Share|Print|Back|Next|Previous|Home|Search|Menu|Close|Loading|'
        r'Copyright|Terms|Privacy|Contact|Download|Video|Watch|Play|More|'
        r'JW\.ORG|DOWNLOAD|OPTIONS|SHARE|Go|Log In|Sign Up)$',
        text, re.IGNORECASE
    )
    if english_only:
        return False

    # Skip if it's just a number or reference
    if re.match(r'^[\d\s:;,.\-]+$', text):
        return False

    # Skip very short content
    if len(text) < 5:
        return False

    # Skip if it looks like a scripture reference only
    if re.match(r'^[12]?\s*[A-Z][a-z]+\s+\d+:\d+', text) and len(text) < 30:
        return False

    return True


def main():
    print("=" * 60)
    print("EXTRACTING CINYANJA TEXT FROM JW.ORG HTML FILES")
    print("=" * 60)

    # Find all JW HTML files
    jw_files = sorted(DATA_DIR.glob("jw-cinyanja-*.html"))
    print(f"\nFound {len(jw_files)} JW HTML files")

    all_sentences = []
    file_stats = {}

    for filepath in jw_files:
        print(f"\n  Processing: {filepath.name}")
        raw_texts = extract_text_from_html(filepath)
        print(f"    Raw text blocks: {len(raw_texts)}")

        sentences = []
        for text in raw_texts:
            for sent in split_into_sentences(text):
                if is_cinyanja_text(sent):
                    sentences.append(sent)

        # Deduplicate within file
        seen = set()
        unique = []
        for s in sentences:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        file_stats[filepath.name] = len(unique)
        all_sentences.extend(unique)
        print(f"    Extracted sentences: {len(unique)}")

    # Global deduplication
    seen = set()
    unique_sentences = []
    for s in all_sentences:
        if s not in seen:
            seen.add(s)
            unique_sentences.append(s)

    print(f"\n{'=' * 60}")
    print(f"Total unique sentences: {len(unique_sentences)}")

    # Write corpus file
    print(f"\nWriting corpus to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for sent in unique_sentences:
            f.write(sent + "\n")

    # Count words
    word_count = sum(len(s.split()) for s in unique_sentences)
    print(f"Lines: {len(unique_sentences)}")
    print(f"Words: {word_count:,}")

    # Insert into database
    print(f"\nInserting into database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    inserted = 0
    skipped = 0
    for sent in unique_sentences:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO corpus (id, language, text, source, domain, quality, dialect) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "nyanja", sent, "jw.org", "religion", "verified", "nyanja-zm")
            )
            inserted += 1
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  Error: {e}")

    conn.commit()

    # Register data source
    try:
        conn.execute(
            "INSERT OR IGNORE INTO data_sources (id, name, url, source_type, languages, license, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "jw-org-cinyanja", "https://www.jw.org/nya/", "monolingual",
             "nyanja", "Fair use",
             f"Cinyanja (Zambian Nyanja) text from JW.org, {len(unique_sentences)} sentences")
        )
    except Exception:
        pass

    conn.commit()

    # Summary
    print(f"\n  Inserted: {inserted}")
    print(f"  Skipped/duplicate: {skipped}")

    # Show corpus stats
    print(f"\nCorpus stats for nyanja:")
    for r in conn.execute(
        "SELECT source, dialect, COUNT(*) FROM corpus WHERE language='nyanja' GROUP BY source, dialect ORDER BY COUNT(*) DESC"
    ):
        print(f"  {r[0]:20s} {r[1] or '':15s} {r[2]:>8,}")

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Corpus file: {OUTPUT_FILE}")
    print(f"  Total lines: {len(unique_sentences)}")
    print(f"  Total words: {word_count:,}")
    print(f"  Database:    {DB_PATH}")
    print(f"\nPer-file breakdown:")
    for name, count in sorted(file_stats.items()):
        print(f"  {name:50s} {count:>6}")


if __name__ == "__main__":
    main()
