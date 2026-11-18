import unittest
import sys
from pathlib import Path

# Adicionar raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.tag_protector import TagProtector


class TestTagProtector(unittest.TestCase):
    def setUp(self):
        self.protector = TagProtector()

    def test_protect_and_restore_tags(self):
        original = "Hello {b}World{/b}! Welcome to {color=#ffd400}Renplay{/color}."
        masked, mask_map = self.protector.protect(original)

        self.assertNotIn("{b}", masked)
        self.assertNotIn("{color=#ffd400}", masked)
        self.assertIn("__TAG_", masked)

        # Simular traducao preservando os tokens
        simulated_translation = masked.replace("Hello", "Olá").replace("Welcome to", "Bem-vindo ao")
        restored = self.protector.restore(simulated_translation, mask_map)

        self.assertEqual(restored, "Olá {b}World{/b}! Bem-vindo ao {color=#ffd400}Renplay{/color}.")
        is_valid, errors = self.protector.validate(original, restored)
        self.assertTrue(is_valid, f"Erros encontrados: {errors}")

    def test_protect_and_restore_variables(self):
        original = "Good morning, [player_name]! Your score is %(score)d."
        masked, mask_map = self.protector.protect(original)

        self.assertNotIn("[player_name]", masked)
        self.assertNotIn("%(score)d", masked)
        self.assertIn("__VAR_", masked)

        simulated_translation = masked.replace("Good morning", "Bom dia").replace("Your score is", "Sua pontuação é")
        restored = self.protector.restore(simulated_translation, mask_map)

        self.assertEqual(restored, "Bom dia, [player_name]! Sua pontuação é %(score)d.")
        is_valid, errors = self.protector.validate(original, restored)
        self.assertTrue(is_valid)

    def test_validation_detects_corrupted_variables(self):
        original = "Hello [player_name], are you ready?"
        corrupted = "Olá [nome_jogador], você está pronto?"

        is_valid, errors = self.protector.validate(original, corrupted)
        self.assertFalse(is_valid)
        self.assertTrue(any("player_name" in e for e in errors))


if __name__ == "__main__":
    unittest.main()

