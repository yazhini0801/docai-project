export function normalizeText(text) {
    return text
        .replace(/\s+/g, " ")
        .replace(/[^\w\s]/g, "")
        .toLowerCase()
        .trim();
}

export function findCitationRange(items, citation) {
    if (!items || !citation) return null;

    const target = normalizeText(citation);

    const texts = items.map((item) => normalizeText(item.str));

    for (let start = 0; start < texts.length; start++) {
        let combined = "";

        for (
            let end = start;
            end < texts.length && end < start + 60;
            end++
        ) {
            combined = `${combined} ${texts[end]}`.trim();

            const normalized = normalizeText(combined);

            if (
                normalized.includes(target) ||
                target.includes(normalized)
            ) {
                return {
                    start,
                    end,
                };
            }

            if (normalized.length > target.length + 100) {
                break;
            }
        }
    }

    return null;
}

export function highlightRange(container, range) {
    if (!container || !range) return;

    const spans = container.querySelectorAll("span");

    spans.forEach((span) => {
        span.style.background = "";
        span.style.borderRadius = "";
        span.style.padding = "";
    });

    for (
        let i = range.start;
        i <= range.end && i < spans.length;
        i++
    ) {
        spans[i].style.background = "rgba(255,235,59,.6)";
        spans[i].style.borderRadius = "3px";
        spans[i].style.padding = "1px 2px";
    }

    if (spans[range.start]) {
        spans[range.start].scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    }
}