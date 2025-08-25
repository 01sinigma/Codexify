import os
import tempfile
from codexify.core.analyzer import ProjectAnalyzer


def test_analyzer_smoke_on_small_project():
    with tempfile.TemporaryDirectory() as tmp:
        a_py = os.path.join(tmp, 'a.py')
        b_py = os.path.join(tmp, 'b.py')
        with open(a_py, 'w', encoding='utf-8') as f:
            f.write('''
class A:\n    def x(self):\n        return 1\n\n''')
        with open(b_py, 'w', encoding='utf-8') as f:
            f.write('''\nimport a\n\ndef foo():\n    return a.A()\n''')

        pa = ProjectAnalyzer()
        result = pa.analyze_project({a_py, b_py}, tmp)

        assert 'symbols' in result
        assert 'import_graph' in result
        assert 'hot_files' in result
        assert result['languages']['total_languages'] >= 1


