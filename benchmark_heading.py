import timeit
import re
from unittest.mock import MagicMock

# Current implementation
def _detect_heading_level_old(paragraph, text: str) -> int | None:
    clean = text.strip()
    if not clean:
        return None
    style_name = getattr(getattr(paragraph, "style", None), "name", "") or ""
    heading_match = re.match(r"Heading\s+([1-6])", style_name, flags=re.IGNORECASE)
    if heading_match:
        return int(heading_match.group(1))
    return None

# Optimized implementation
_RE_HEADING_STYLE = re.compile(r"Heading\s+([1-6])", flags=re.IGNORECASE)
def _detect_heading_level_new(paragraph, text: str) -> int | None:
    clean = text.strip()
    if not clean:
        return None
    style_name = getattr(getattr(paragraph, "style", None), "name", "") or ""
    heading_match = _RE_HEADING_STYLE.match(style_name)
    if heading_match:
        return int(heading_match.group(1))
    return None

def run_benchmark():
    class Para:
        def __init__(self, style_name):
            class Style:
                def __init__(self, name):
                    self.name = name
            self.style = Style(style_name)

    p1 = Para("Heading 1")
    p2 = Para("Normal")
    p3 = Para("heading 2")

    globals_dict = globals()
    globals_dict.update({'p1': p1, 'p2': p2, 'p3': p3})

    time_old = timeit.timeit('_detect_heading_level_old(p1, "Title"); _detect_heading_level_old(p2, "Text"); _detect_heading_level_old(p3, "Subtitle")', globals=globals_dict, number=100000)
    time_new = timeit.timeit('_detect_heading_level_new(p1, "Title"); _detect_heading_level_new(p2, "Text"); _detect_heading_level_new(p3, "Subtitle")', globals=globals_dict, number=100000)

    print(f"Old time: {time_old:.4f}s")
    print(f"New time: {time_new:.4f}s")
    print(f"Improvement: {((time_old - time_new) / time_old) * 100:.2f}%")

if __name__ == "__main__":
    run_benchmark()
