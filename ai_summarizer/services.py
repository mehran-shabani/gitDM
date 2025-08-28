from clinical_refs.models import ClinicalReference

TOPIC_KEYWORDS = {
    'diabetes': ['diabetes','hba1c','metformin','insulin','sglt2','glp-1'],
}

def link_references(summary_text, topic_hint='diabetes'):
    qs = ClinicalReference.objects.filter(topic__icontains=topic_hint)
    selected = []
    text_lower = summary_text.lower()
    for ref in qs[:20]:
        score = 0
        for kw in TOPIC_KEYWORDS.get(topic_hint, []):
            if kw in text_lower:
                score += 1
        if score:
            selected.append(ref)
    return selected[:3]
