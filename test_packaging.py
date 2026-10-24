"""Bản cài từ PyPI phải có MỌI module agent import lúc chạy."""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def _py_modules():
    with open(os.path.join(HERE, "pyproject.toml"), encoding="utf-8") as f:
        text = f.read()
    block = re.search(r"py-modules\s*=\s*\[(.*?)\]", text, re.S).group(1)
    return set(re.findall(r'"([A-Za-z0-9_]+)"', block))


def test_every_flop_module_is_packaged():
    shipped = _py_modules()
    needed = {"agent_cron", "token_manager"} | {
        os.path.basename(p)[:-3] for p in glob.glob(os.path.join(HERE, "flop_*.py"))}
    assert needed - shipped == set(), f"thiếu trong py-modules: {sorted(needed - shipped)}"
    assert shipped - needed == set(), f"py-modules trỏ tới file không tồn tại: {sorted(shipped - needed)}"


def test_text_files_are_opened_as_utf8():
    # State/sổ cái chứa tiếng Việt: open() không nêu encoding dùng mã locale (cp1252 trên
    # Windows) -> ghi lỗi 'charmap' và sổ cái bị coi là rỗng.
    import ast
    bad = []
    for mod in sorted(_py_modules()):
        path = os.path.join(HERE, f"{mod}.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), path)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"):
                continue
            mode = node.args[1] if len(node.args) > 1 else next(
                (k.value for k in node.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and "b" in str(mode.value):
                continue
            if not any(k.arg == "encoding" for k in node.keywords):
                bad.append(f"{mod}.py:{node.lineno}")
    assert bad == [], f"open() văn bản thiếu encoding: {bad}"
