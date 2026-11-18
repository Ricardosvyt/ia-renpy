from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import PATCHES_DIR, LANGUAGES
from core.language_injector import LanguageInjector


class PatchBuilder:
    """
    Construtor do Patch de Arquivo Unico da Renplay AI.
    Empacota todas as traducoes de dialogos, menus e o sistema de troca de idiomas
    em um unico arquivo .rpy independente (ex: 99_renplay_traducao_ptbr.rpy).
    O jogador precisa apenas colar esse arquivo dentro da pasta 'game/' do jogo.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir or PATCHES_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.language_injector = LanguageInjector()

    def build_single_file_patch(
        self,
        game_name: str,
        translations: List[Dict[str, Any]],
        target_lang: str = "pt-BR",
        custom_filename: Optional[str] = None,
    ) -> Path:
        """
        Gera o arquivo unico de patch de traducao.
        translations deve ser uma lista de dicts com 'original_text' e 'translated_text'.
        """
        lang_info = LANGUAGES.get(target_lang, LANGUAGES["pt-BR"])
        renpy_lang = lang_info["renpy_code"]
        
        safe_game_name = "".join(c if c.isalnum() else "_" for c in game_name).lower()
        filename = custom_filename or f"99_renplay_{safe_game_name}_{renpy_lang}.rpy"
        output_path = self.output_dir / filename

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines: List[str] = []

        # 1. Cabecalho
        lines.append("## ==========================================================")
        lines.append(f"## RENPLAY AI - PATCH DE TRADUCAO [{lang_info['display_name']}]")
        lines.append(f"## Jogo: {game_name}")
        lines.append(f"## Gerado em: {now_str}")
        lines.append("## INSTRUCAO: Coloque este unico arquivo dentro da pasta 'game/'")
        lines.append("## ==========================================================\n")

        # 2. Injetor de Interface e Selecao de Idiomas
        ui_script = self.language_injector.get_ui_script()
        lines.append(ui_script)
        lines.append("\n## ==========================================================")
        lines.append(f"## TABELA DE TRADUCAO - {renpy_lang.upper()}")
        lines.append("## ==========================================================\n")

        # 3. Bloco de Traducao de Strings do Ren'Py
        lines.append(f"translate {renpy_lang} strings:\n")

        # Deduplicar pares de traducao
        seen = set()
        for item in translations:
            orig = item.get("original_text", "").strip()
            trans = item.get("translated_text", "").strip()

            if not orig or not trans or orig == trans:
                continue

            if orig in seen:
                continue
            seen.add(orig)

            # Escapar aspas duplas internas de forma segura
            safe_orig = orig.replace('\\"', '"').replace('"', '\\"')
            safe_trans = trans.replace('\\"', '"').replace('"', '\\"')

            lines.append(f'    old "{safe_orig}"')
            lines.append(f'    new "{safe_trans}"\n')

        # Gravar arquivo final
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[OK] Patch de Arquivo Unico gerado com sucesso: {output_path} ({len(seen)} traducoes incluídas)")
        return output_path

