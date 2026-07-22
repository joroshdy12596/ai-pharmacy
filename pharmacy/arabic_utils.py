import re

_TASHKEEL_AND_TATWEEL = re.compile(r'[ً-ْٰـ]')
_ALEF_FORMS = re.compile(r'[إأآٱ]')  # إ أ آ ٱ
_YAA_FORMS = re.compile(r'[ى]')  # ى (alef maksura) -> ي
_WHITESPACE = re.compile(r'\s+')


def normalize_text(text):
    """
    Normalize Arabic/English product names for fuzzy matching:
    strips diacritics/tatweel, unifies common alternate letter forms
    (different alef shapes, alef maksura, hamza-on-waw/yaa, taa marbuta),
    and collapses whitespace/case so typos in common Arabic spelling
    variants don't prevent a match.
    """
    if not text:
        return ''
    text = text.strip()
    text = _TASHKEEL_AND_TATWEEL.sub('', text)
    text = _ALEF_FORMS.sub('ا', text)  # -> ا
    text = _YAA_FORMS.sub('ي', text)  # -> ي
    text = text.replace('ة', 'ه')  # ة -> ه
    text = text.replace('ؤ', 'و')  # ؤ -> و
    text = text.replace('ئ', 'ي')  # ئ -> ي
    text = _WHITESPACE.sub(' ', text).strip()
    return text.lower()
