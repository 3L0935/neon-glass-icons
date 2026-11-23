#!/usr/bin/env python3
"""Trace extra glyphs (category / action icons) and merge them into glyphs.json.

Sources: sources/extra/ (rendered from Papirus symbolic SVGs, GPL) or, for third-party
app logos, the untracked local/extra/.
Reuses mask_of() and trace() from trace.py without running its main().
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
src = (HERE / "trace.py").read_text().rsplit("\nmain()", 1)[0]
ns = {"__file__": str(HERE / "trace.py"), "__name__": "trace_lib"}
exec(compile(src, "trace.py", "exec"), ns)

EXTRA = {  # glyph -> (source, mode, threshold)
    "tools":  ("tools.png", "alpha", 128),
    "paste":  ("paste.png", "alpha", 128),
    "lutris": ("lutris.png", "facets", 128),
}

glyphs = json.loads((ROOT / "glyphs.json").read_text())
for name, (f, mode, thr) in EXTRA.items():
    path = ROOT / "sources" / "extra" / f
    if not path.exists():
        path = ROOT / "local" / "extra" / f
    img = ns["Image"].open(path)
    m = ns["mask_of"](img, mode, thr)
    if not m.getbbox():
        print("EMPTY", name)
        continue
    glyphs[name] = ns["trace"](m, name)
    print("ok", name, glyphs[name]["bbox"])
(ROOT / "glyphs.json").write_text(json.dumps(glyphs))
