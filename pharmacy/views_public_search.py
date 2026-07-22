from django.shortcuts import render
from rapidfuzz import fuzz, process

from .models import Medicine
from .arabic_utils import normalize_text

# Below this fuzzy-match score (0-100), a result is considered too weak to
# be useful and is hidden - avoids showing unrelated products for garbled input.
MIN_MATCH_SCORE = 55
MAX_RESULTS = 25


def public_medicine_search(request):
    """
    Public, no-login-required page where customers can check whether a
    product exists in stock. Tolerant of typos and common Arabic spelling
    variants (different alef/yaa forms, taa marbuta, stray diacritics) via
    normalization + fuzzy string matching - no external AI service call,
    so it's free, instant, and works offline.
    """
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        normalized_query = normalize_text(query)
        medicines = list(
            Medicine.objects.filter(is_active=True).values('id', 'name', 'stock', 'category')
        )
        choices = {m['id']: normalize_text(m['name']) for m in medicines}
        matches = process.extract(
            normalized_query,
            choices,
            scorer=fuzz.WRatio,
            limit=MAX_RESULTS,
        )

        by_id = {m['id']: m for m in medicines}
        for _matched_text, score, medicine_id in matches:
            if score < MIN_MATCH_SCORE:
                continue
            medicine = by_id[medicine_id]
            results.append({
                'name': medicine['name'],
                'in_stock': medicine['stock'] > 0,
                'category': medicine['category'],
                'score': round(score),
            })

    return render(request, 'pharmacy/public/search.html', {
        'query': query,
        'results': results,
        'searched': bool(query),
    })
