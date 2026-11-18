import unittest
import sys
import tempfile
import shutil
from pathlib import Path

# Adicionar raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.patch_builder import PatchBuilder


class TestPatchBuilder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.builder = PatchBuilder(output_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_single_file_patch(self):
        sample_translations = [
            {"original_text": "Start Game", "translated_text": "Iniciar Jogo"},
            {"original_text": "Preferences", "translated_text": "Configurações"},
            {"original_text": 'He said "Hello"', "translated_text": 'Ele disse "Olá"'},
        ]

        patch_file = self.builder.build_single_file_patch(
            game_name="TestGame",
            translations=sample_translations,
            target_lang="pt-BR",
        )

        self.assertTrue(patch_file.exists())
        content = patch_file.read_text(encoding="utf-8")

        # Verificar cabecalho e injetor
        self.assertIn("RENPLAY AI - PATCH DE TRADUCAO", content)
        self.assertIn("screen renplay_language_modal", content)
        self.assertIn("translate portuguese strings:", content)

        # Verificar pares de traducao
        self.assertIn('old "Start Game"', content)
        self.assertIn('new "Iniciar Jogo"', content)
        self.assertIn(r'old "He said \"Hello\""', content)
        self.assertIn(r'new "Ele disse \"Olá\""', content)


if __name__ == "__main__":
    unittest.main()

