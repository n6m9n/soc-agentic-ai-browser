"""Auto-detect form fields on a page — inputs, selects, checkboxes, radios, files,
textareas — including inside iframes.

Uses one JS pass per frame to collect field descriptors robustly (labels via
`<label for>`, aria-label, placeholder, or name; selectors prefer #id then [name]).
"""
from app.core.schemas import FormField

_JS_COLLECT = r"""
() => {
  const SKIP = ['hidden','submit','button','reset','image'];
  const out = [];
  const seen = new Set();
  const radioGroups = {};
  for (const el of document.querySelectorAll('input, select, textarea')) {
    const tag = el.tagName.toLowerCase();
    const type = (el.type || '').toLowerCase();
    if (tag === 'input' && SKIP.includes(type)) continue;

    let selector = '';
    if (el.id) selector = '#' + CSS.escape(el.id);
    else if (el.name) selector = tag + '[name="' + el.name + '"]';
    else continue;

    // label resolution
    let label = '';
    if (el.id) {
      const l = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
      if (l) label = l.innerText.trim();
    }
    if (!label) label = el.getAttribute('aria-label') || el.placeholder || el.name || '';

    let kind = tag === 'textarea' ? 'textarea'
             : tag === 'select' ? 'select'
             : (type || 'text');

    let options = [];
    if (tag === 'select') options = [...el.options].map(o => o.value || o.text).filter(Boolean);

    if (kind === 'radio') {
      // collapse a radio group to one field, collecting its option values
      const key = el.name || selector;
      if (radioGroups[key]) { radioGroups[key].options.push(el.value); continue; }
      radioGroups[key] = { label, selector: (tag + '[name="' + el.name + '"]'),
                           kind, options: [el.value] };
      out.push(radioGroups[key]);
      continue;
    }
    if (seen.has(selector)) continue;
    seen.add(selector);
    out.push({ label, selector, kind, options });
  }
  return out;
}
"""


def _detect_in(frame, in_iframe: bool) -> list[FormField]:
    raw = frame.evaluate(_JS_COLLECT)
    return [
        FormField(label=f["label"], selector=f["selector"], kind=f["kind"],
                  options=f.get("options", []), in_iframe=in_iframe)
        for f in raw
    ]


def detect_fields(page, include_iframes: bool = True) -> list[FormField]:
    fields = _detect_in(page, in_iframe=False)
    if include_iframes:
        for frame in page.frames:
            if frame is page.main_frame:
                continue
            try:
                fields.extend(_detect_in(frame, in_iframe=True))
            except Exception:  # noqa: BLE001 - cross-origin/detached frames are skippable
                continue
    return fields
