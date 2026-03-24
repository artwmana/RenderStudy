import timeit
import sys
from unittest.mock import MagicMock

class MockModule(MagicMock):
    __path__ = []

sys.modules["docx"] = MockModule()
sys.modules["docx.shared"] = MagicMock()
sys.modules["docx.oxml"] = MagicMock()
sys.modules["docx.enum"] = MockModule()
sys.modules["docx.enum.text"] = MagicMock()
sys.modules["docx.enum.style"] = MagicMock()
sys.modules["docx.enum.section"] = MagicMock()
sys.modules["docx.enum.table"] = MagicMock()
sys.modules["docx.oxml.ns"] = MagicMock()
sys.modules["docx.oxml.xmlchemy"] = MagicMock()
sys.modules["markdown_it"] = MockModule()
sys.modules["mdit_py_plugins"] = MockModule()
sys.modules["mdit_py_plugins.front_matter"] = MagicMock()
sys.modules["mdit_py_plugins.texmath"] = MagicMock()
sys.modules["mdit_py_plugins.container"] = MagicMock()
sys.modules["yaml"] = MagicMock()

import src.RenderStudy.docx_formatter as df

class MockStyle:
    def __init__(self, name):
        self.name = name

class MockParagraph:
    def __init__(self, text, style_name):
        self.text = text
        self.style = MockStyle(style_name)

p = MockParagraph("Heading text", "Heading 1")

def run_detect():
    df._detect_heading_level(p, p.text)
    df._is_heading_candidate(p, p.text)

if __name__ == "__main__":
    t = timeit.timeit("run_detect()", setup="from __main__ import run_detect", number=100000)
    print(f"Time taken for 100000 iterations: {t:.4f} seconds")
