import re
import timeit
import time

class DummyParagraph:
    def __init__(self, text):
        self.text = text

paragraphs = [DummyParagraph(f"Paragraph {i}") for i in range(39)] + [DummyParagraph("Это наша ЦЕЛЬ.")]

def original_find_goal_index(paragraphs):
    for idx, paragraph in enumerate(paragraphs[:40]):
        if re.search(r"\bцель\b", paragraph.text, flags=re.IGNORECASE):
            return idx
    return None

_RE_GOAL = re.compile(r"\bцель\b", flags=re.IGNORECASE)

def optimized_find_goal_index(paragraphs):
    for idx, paragraph in enumerate(paragraphs[:40]):
        if _RE_GOAL.search(paragraph.text):
            return idx
    return None

if __name__ == "__main__":
    n = 10000
    # Warmup
    original_find_goal_index(paragraphs)
    optimized_find_goal_index(paragraphs)

    t1 = timeit.timeit(lambda: original_find_goal_index(paragraphs), number=n)
    t2 = timeit.timeit(lambda: optimized_find_goal_index(paragraphs), number=n)

    print(f"Original: {t1:.4f} seconds for {n} iterations")
    print(f"Optimized: {t2:.4f} seconds for {n} iterations")
    if t1 > 0:
        improvement = ((t1 - t2) / t1) * 100
        print(f"Improvement: {improvement:.2f}%")
