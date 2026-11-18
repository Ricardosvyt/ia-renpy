from pathlib import Path
from typing import Optional, List
from config import BASE_DIR, LANGUAGES


class LanguageInjector:
    """
    Injeta telas de configuracao de idioma e auto-deteccao diretamente
    no arquivo de traducao final do Ren'Py.
    """

    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = Path(
            template_path or (BASE_DIR / "templates" / "renplay_language_ui.rpy")
        )

    def get_ui_script(self, active_languages: Optional[List[str]] = None) -> str:
        """
        Gera o script Ren'Py que injeta o seletor de idiomas.
        """
        if self.template_path.exists():
            with open(self.template_path, "r", encoding="utf-8") as f:
                return f.read()

        # Fallback caso o arquivo template nao seja encontrado
        return """
init -10 python:
    if persistent._renplay_lang_initialized is None:
        persistent._renplay_lang_initialized = True
        _preferences.language = "portuguese"

screen renplay_language_modal():
    modal True
    zorder 200
    frame:
        align (0.5, 0.5)
        vbox:
            text "Selecionar Idioma"
            textbutton "[PT-BR] Português":
                action [Language("portuguese"), Hide("renplay_language_modal")]
            textbutton "[EN] Original":
                action [Language(None), Hide("renplay_language_modal")]
"""

