import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from codexify.engine import CodexifyEngine  # noqa: E402


def test_classify_manual_files_without_discovery(tmp_path):
    engine = CodexifyEngine()

    swift_file = tmp_path / "Foo.swift"
    text_file = tmp_path / "notes.txt"
    swift_file.write_text("class Foo {}", encoding="utf-8")
    text_file.write_text("notes", encoding="utf-8")

    engine.state.all_discovered_files = set()
    engine.state.include_files = set()
    engine.state.other_files = {str(swift_file), str(text_file)}

    engine.set_active_formats({".swift"})

    assert str(swift_file) in engine.state.include_files
    assert str(text_file) in engine.state.other_files


def test_remove_files_records_original_buckets(tmp_path):
    engine = CodexifyEngine()

    inc_file = tmp_path / "Sample.swift"
    oth_file = tmp_path / "Example.txt"
    inc_file.write_text("", encoding="utf-8")
    oth_file.write_text("", encoding="utf-8")

    engine.state.include_files = {str(inc_file)}
    engine.state.other_files = {str(oth_file)}

    engine.remove_files({str(inc_file), str(oth_file)})

    action = engine._undo_stack[-1]

    assert action["from_include"] == {str(inc_file)}
    assert action["from_other"] == {str(oth_file)}
