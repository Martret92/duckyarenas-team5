"""La interfaz normal no debe importar la aplicación de demostración."""
import ast
from pathlib import Path
from django.test import SimpleTestCase

class DemoIndependenceTests(SimpleTestCase):
    def test_ui_views_do_not_import_demo(self):
        source=Path(__file__).resolve().parents[1] / 'team5_ui' / 'views.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        imported=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        imported += [alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names]
        self.assertFalse(any('team5_demo' in name for name in imported))
