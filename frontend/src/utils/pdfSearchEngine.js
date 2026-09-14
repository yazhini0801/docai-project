export function normalizeForSearch(text) {
    return String(text || "")
        .replace(/\s+/g, " ")
        .replace(/[^\w\s]/g, "")
        .toLowerCase()
        .trim();
}

function getSearchCandidates(citationText) {
    const cleanText = String(citationText || "").replace(/\s+/g, " ").trim();

    const sentences = cleanText
        .split(/(?<=[.!?])\s+/)
        .map((sentence) => normalizeForSearch(sentence))
        .filter((sentence) => sentence.length > 30);

    const fullTarget = normalizeForSearch(cleanText);

    return [
        ...sentences,
        fullTarget.slice(0, 300),
        fullTarget.split(" ").slice(0, 18).join(" "),
        fullTarget.split(" ").slice(0, 12).join(" "),
        fullTarget.split(" ").slice(0, 8).join(" "),
    ].filter(Boolean);
}

export function findCitationRange(items, citationText) {
    if (!items || !citationText) return null;

    let fullText = "";
    const itemRanges = [];

    items.forEach((item, index) => {
        const normalized = normalizeForSearch(item.str);

        if (!normalized) return;

        const start = fullText.length;
        fullText += normalized + " ";
        const end = fullText.length;

        itemRanges.push({
            index,
            start,
            end,
        });
    });

    const candidates = getSearchCandidates(citationText);

    for (const target of candidates) {
        const targetStart = fullText.indexOf(target);

        if (targetStart !== -1) {
            const targetEnd = targetStart + target.length;

            return convertCharacterRangeToItemRange(
                itemRanges,
                targetStart,
                targetEnd
            );
        }
    }

    return null;
}

function convertCharacterRangeToItemRange(itemRanges, startChar, endChar) {
    const matched = itemRanges.filter((item) => {
        return item.end >= startChar && item.start <= endChar;
    });

    if (!matched.length) return null;

    return {
        start: matched[0].index,
        end: matched[matched.length - 1].index,
    };
}