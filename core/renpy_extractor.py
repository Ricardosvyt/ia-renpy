import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class RenpyExtractor:
    """
    Extrator de dialogos e textos de interface de jogos Ren'Py.
    Varre a pasta 'game/' e identifica falas de personagens, menus e strings traduziveis.
    """

    # Padrao para falas com personagem: e "Ola mundo!" ou "narrador" "Ola!"
    RE_DIALOGUE = re.compile(r'^\s*(?:([a-zA-Z0-9_]+)\s+)?"((?:[^"\\]|\\.)*)"\s*$')

    # Padrao para opcoes de menu: "Investigar quarto":
    RE_MENU_CHOICE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*$')

    # Padrao para blocos translate strings do Ren'Py
    RE_TRANSLATE_OLD = re.compile(r'^\s*old\s+"((?:[^"\\]|\\.)*)"\s*$')

    def __init__(self, game_root: Path):
        self.game_root = Path(game_root)
        self.game_dir = self.game_root / "game" if (self.game_root / "game").is_dir() else self.game_root

    def scan_rpy_files(self) -> List[Path]:
        """
        Localiza todos os arquivos .rpy da pasta do jogo, ignorando a pasta de traducoes antigas.
        """
        files = []
        for rpy in self.game_dir.rglob("*.rpy"):
            # Ignorar arquivos dentro de tl/ (ja sao traducoes)
            if "tl" in rpy.parts:
                continue
            files.append(rpy)
        return sorted(files)

    def extract_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extrai falas e textos de um arquivo .rpy individual.
        """
        extracted = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[AVISO] Nao foi possivel ler {file_path.name}: {e}")
            return []

        rel_path = file_path.relative_to(self.game_root).as_posix()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Pular linhas vazias, comentarios e comandos puros de Python
            if not stripped or stripped.startswith("#") or stripped.startswith("$") or stripped.startswith("python:"):
                continue

            # 1. Opcao de menu
            match_menu = self.RE_MENU_CHOICE.match(line)
            if match_menu:
                text = match_menu.group(1).replace(r'\"', '"')
                if text:
                    extracted.append({
                        "file": rel_path,
                        "line_num": idx,
                        "type": "menu_choice",
                        "character": "Menu",
                        "original_text": text,
                    })
                continue

            # 2. Dialogo com ou sem personagem
            match_diag = self.RE_DIALOGUE.match(line)
            if match_diag:
                char = match_diag.group(1) or "Narrador"
                text = match_diag.group(2).replace(r'\"', '"')
                
                # Ignorar identificadores de imagem ou animacao simples
                if text and not text.endswith((".png", ".jpg", ".webp", ".ogg", ".mp3")):
                    extracted.append({
                        "file": rel_path,
                        "line_num": idx,
                        "type": "dialogue",
                        "character": char,
                        "original_text": text,
                    })
                continue

            # 3. String de traducao antiga (old "...")
            match_old = self.RE_TRANSLATE_OLD.match(line)
            if match_old:
                text = match_old.group(1).replace(r'\"', '"')
                if text:
                    extracted.append({
                        "file": rel_path,
                        "line_num": idx,
                        "type": "string",
                        "character": "UI",
                        "original_text": text,
                    })

        return extracted

    def extract_all(self) -> List[Dict[str, Any]]:
        """
        Extrai todos os dialogos e textos traduziveis de todos os arquivos .rpy do jogo.
        """
        rpy_files = self.scan_rpy_files()
        all_units = []
        for rpy in rpy_files:
            units = self.extract_from_file(rpy)
            all_units.extend(units)
            
        print(f"[OK] Extracao concluida: {len(all_units)} textos encontrados em {len(rpy_files)} arquivos .rpy.")
        return all_units

