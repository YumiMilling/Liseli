#!/bin/bash
# Scrape Storybooks Zambia - bilingual story texts (English + Zambian languages)
# Source: https://storybookszambia.net/ (CC-BY licensed)

BASE_URL="https://storybookszambia.net"
OUTPUT_DIR="$(dirname "$0")/../data/storybooks-zambia"
mkdir -p "$OUTPUT_DIR"

# All story IDs (40 stories)
STORY_IDS=$(curl -sk "$BASE_URL/stories/en/" | grep -oE '/stories/en/[0-9]+/' | sed 's|/stories/en/||;s|/||' | sort -u)

# Zambian language codes and names
declare -A LANGS
LANGS[bem]="Bemba"
LANGS[ny]="Nyanja"
LANGS[toi]="Tonga"
LANGS[loz-zm]="Lozi"
LANGS[kqn]="Kaonde"
LANGS[lun]="Lunda"
LANGS[lue]="Luvale"
LANGS[tum]="Tumbuka"

echo "Found stories: $(echo "$STORY_IDS" | wc -w)"
echo "Languages: ${!LANGS[@]}"
echo "---"

for lang_code in "${!LANGS[@]}"; do
    lang_name="${LANGS[$lang_code]}"
    lang_dir="$OUTPUT_DIR/$lang_code-$lang_name"
    mkdir -p "$lang_dir"

    echo "Scraping $lang_name ($lang_code)..."

    for story_id in $STORY_IDS; do
        url="$BASE_URL/stories/$lang_code/$story_id/"
        html=$(curl -sk "$url" 2>/dev/null)

        if [ -z "$html" ]; then
            echo "  SKIP $story_id (no response)"
            continue
        fi

        # Extract title from <title> tag
        title=$(echo "$html" | grep -oE '<title>[^<]+</title>' | sed 's/<[^>]*>//g' | sed 's/ - Storybooks Zambia//')

        # Extract English text (l1 class) - each page is in h3 tags within l1 divs
        english_texts=$(echo "$html" | grep -A2 'level.-txt l1' | grep '<h3>' | sed 's/<[^>]*>//g;s/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')

        # Extract target language text (l2 class)
        target_texts=$(echo "$html" | grep -A2 'level.-txt l2' | grep '<h3>' | sed 's/<[^>]*>//g;s/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')

        # Also get the title translations
        en_title=$(echo "$html" | grep 'class="l1"' | head -1 | sed 's/<[^>]*>//g;s/^[[:space:]]*//;s/[[:space:]]*$//')
        target_title=$(echo "$html" | grep 'class="l2"' | head -1 | sed 's/<[^>]*>//g;s/^[[:space:]]*//;s/[[:space:]]*$//')

        if [ -z "$target_texts" ]; then
            echo "  SKIP $story_id (no target text)"
            continue
        fi

        # Write bilingual file
        outfile="$lang_dir/${story_id}.txt"
        {
            echo "# Story: $title"
            echo "# ID: $story_id"
            echo "# English <-> $lang_name ($lang_code)"
            echo "# Source: $url"
            echo "# License: CC-BY"
            echo ""
            echo "## Title"
            echo "EN: $en_title"
            echo "$lang_code: $target_title"
            echo ""
            echo "## Text"

            # Pair up sentences
            paste <(echo "$english_texts") <(echo "$target_texts") | while IFS=$'\t' read -r en tgt; do
                if [ -n "$en" ] && [ -n "$tgt" ]; then
                    echo "EN: $en"
                    echo "$lang_code: $tgt"
                    echo ""
                fi
            done
        } > "$outfile"

        echo "  OK $story_id: $title"
    done

    echo "  Done: $(ls "$lang_dir"/*.txt 2>/dev/null | wc -l) stories"
    echo ""
done

# Also save English originals for reference
en_dir="$OUTPUT_DIR/en-English"
mkdir -p "$en_dir"
echo "Scraping English originals..."
for story_id in $STORY_IDS; do
    url="$BASE_URL/stories/en/$story_id/"
    html=$(curl -sk "$url" 2>/dev/null)
    title=$(echo "$html" | grep -oE '<title>[^<]+</title>' | sed 's/<[^>]*>//g' | sed 's/ - Storybooks Zambia//')
    texts=$(echo "$html" | grep -A2 'level.-txt def' | grep '<h3>' | sed 's/<[^>]*>//g;s/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')

    {
        echo "# Story: $title"
        echo "# ID: $story_id"
        echo "# Language: English"
        echo "# Source: $url"
        echo "# License: CC-BY"
        echo ""
        echo "$texts"
    } > "$en_dir/${story_id}.txt"

    echo "  OK $story_id: $title"
done

echo ""
echo "=== DONE ==="
echo "Output: $OUTPUT_DIR"
ls -d "$OUTPUT_DIR"/*/
