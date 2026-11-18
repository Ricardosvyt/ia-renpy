import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.decompiler import DecompilerManager
from core.tag_protector import TagProtector


class RenpyExtractor:
    """
    Extrator e analisador aprofundado de jogos Ren'Py.
    Descompila automaticamente pacotes .rpa e arquivos compilados .rpyc,
    identifica personagens, rotas, dialogos e gera relatorios de analise.
    """

    RE_DIALOGUE = re.compile(r'^\s*(?:([a-zA-Z0-9_]+)\s+)?"((?:[^"\\]|\\.)*)"\s*$')
    RE_MENU_CHOICE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*$')
    RE_TRANSLATE_OLD = re.compile(r'^\s*old\s+"((?:[^"\\]|\\.)*)"\s*$')

    def __init__(self, game_root: Path):
        self.game_root = Path(game_root)
        self.game_dir = self.game_root / "game" if (self.game_root / "game").is_dir() else self.game_root
        self.decompiler = DecompilerManager()
        self.tag_protector = TagProtector()

    def ensure_decompiled(self) -> None:
        """
        Garante que todos os pacotes .rpa sejam extraidos e todos os .rpyc descompilados para .rpy.
        """
        print("[EXTRATOR] Verificando descompilacao de scripts do jogo...")
        self.decompiler.decompile_all(self.game_dir)

    def scan_rpy_files(self) -> List[Path]:
        """
        Localiza todos os arquivos .rpy da pasta do jogo.
        """
        files = []
        for rpy in self.game_dir.rglob("*.rpy"):
            if "tl" in rpy.parts:
                continue
            files.append(rpy)
        return sorted(files)

    def extract_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extrai falas, menus e textos de interface de um arquivo .rpy.
        """
        extracted = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[AVISO] Falha ao ler {file_path.name}: {e}")
            return []

        rel_path = file_path.relative_to(self.game_root).as_posix()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
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
                if text and not text.endswith((".png", ".jpg", ".webp", ".ogg", ".mp3")):
                    extracted.append({
                        "file": rel_path,
                        "line_num": idx,
                        "type": "dialogue",
                        "character": char,
                        "original_text": text,
                    })
                continue

            # 3. String de traducao (old "...")
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

    def analyze_and_extract(self) -> Dict[str, Any]:
        """
        Executa descompilacao completa, analisa as caracteristicas narrativas do jogo
        e extrai todos os textos traduziveis com estatisticas detalhadas.
        """
        self.ensure_decompiled()
        rpy_files = self.scan_rpy_files()
        
        all_units: List[Dict[str, Any]] = []
        characters: Dict[str, int] = {}
        variables_detected: set = set()
        dialogue_count = 0
        menu_count = 0
        ui_count = 0

        for rpy in rpy_files:
            units = self.extract_from_file(rpy)
            all_units.extend(units)
            for u in units:
                c = u["character"]
                characters[c] = characters.get(c, 0) + 1
                
                t = u["type"]
                if t == "dialogue":
                    dialogue_count += 1
                elif t == "menu_choice":
                    menu_count += 1
                elif t == "string":
                    ui_count += 1

                # Detectar variaveis no texto original
                vars_in_text = self.tag_protector.RE_VARS.findall(u["original_text"])
                variables_detected.update(vars_in_text)

        report = {
            "game_name": self.game_root.name,
            "total_files": len(rpy_files),
            "total_units": len(all_units),
            "dialogue_count": dialogue_count,
            "menu_count": menu_count,
            "ui_count": ui_count,
            "character_stats": characters,
            "detected_variables": sorted(list(variables_detected)),
            "units": all_units,
        }

        # Imprimir relatorio visual no terminal
        self.print_report(report)
        return report

    @staticmethod
    def print_report(report: Dict[str, Any]) -> None:
        print("\n" + "=" * 65)
        print(f" [RELATORIO DE ANALISE DO JOGO: {report['game_name']}]")
        print("=" * 65)
        print(f" Arquivos de Script (.rpy): {report['total_files']}")
        print(f" Total de Unidades Traduziveis: {report['total_units']}")
        print(f" - Dialogos de Historia: {report['dialogue_count']}")
        print(f" - Opcoes de Escolha (Menu): {report['menu_count']}")
        print(f" - Textos de Sistema/UI: {report['ui_count']}")
        print(f" Variaveis Ren'Py Detectadas: {len(report['detected_variables'])}")
        
        # Top 5 personagens mais ativos
        top_chars = sorted(report["character_stats"].items(), key=lambda x: x[1], reverse=True)[:6]
        print("\n Principais Personagens Identificados:")
        for char, count in top_chars:
            print(f"   * {char}: {count} falas")
        print("=" * 65 + "\n")

    def extract_all(self) -> List[Dict[str, Any]]:
        """
        Metodo de conveniencia compativel com a interface padrao.
        """
        analysis = self.analyze_and_extract()
        return analysis["units"]
