import os
import tempfile
from codexify.core.analyzer import ProjectAnalyzer


def test_symbol_index_and_import_graph():
    with tempfile.TemporaryDirectory() as tmp:
        a = os.path.join(tmp, 'moda.py')
        b = os.path.join(tmp, 'modb.py')
        with open(a, 'w', encoding='utf-8') as f:
            f.write('''\nclass C:\n    pass\n\ndef f():\n    return 1\n''')
        with open(b, 'w', encoding='utf-8') as f:
            f.write('''\nimport moda\n''')
        pa = ProjectAnalyzer()
        res = pa.analyze_project({a,b}, tmp)
        sym = res.get('symbols', {}).get('python', {}).get('modules', {})
        assert 'moda' in sym
        assert 'C' in sym['moda']['classes']
        assert 'f' in sym['moda']['functions']
        edges = set(tuple(e) for e in (res.get('import_graph') or {}).get('edges', []))
        assert ('modb','moda') in edges


