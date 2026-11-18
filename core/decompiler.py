import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Adicionar lib/unrpyc ao path
CURRENT_DIR = Path(__file__).resolve().parent
LIB_DIR = CURRENT_DIR.parent / "lib"
UNRPYC_PATH = LIB_DIR / "unrpyc"

if UNRPYC_PATH.exists() and str(UNRPYC_PATH) not in sys.path:
    sys.path.insert(0, str(UNRPYC_PATH))


class DecompilerManager:
    """
    Gerenciador de descompilacao de arquivos Ren'Py (.rpyc para .rpy)
    e extracao de pacotes de arquivo (.rpa).
    """

    def __init__(self):
        self._unrpyc = None
        self._init_unrpyc()

    def _init_unrpyc(self):
        try:
            import unrpyc  # type: ignore
            self._unrpyc = unrpyc
            print("[INFO] Motor unrpyc carregado com sucesso.")
        except Exception as e:
            print(f"[AVISO] Falha ao carregar unrpyc embutido: {e}")

    def extract_rpa_archives(self, game_dir: Path) -> int:
        """
        Localiza e descompacta todos os arquivos .rpa na pasta do jogo usando unrpa.
        """
        game_dir = Path(game_dir)
        rpa_files = list(game_dir.rglob("*.rpa"))
        if not rpa_files:
            return 0

        print(f"[EXTRACAO] Encontrados {len(rpa_files)} arquivos .rpa. Descompactando...")
        extracted_count = 0

        for rpa in rpa_files:
            try:
                # Tentar usar unrpa via linha de comando ou modulo
                cmd = [sys.executable, "-m", "unrpa", "-p", str(rpa.parent), str(rpa)]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0:
                    extracted_count += 1
                else:
                    print(f"[AVISO] unrpa retornou aviso para {rpa.name}: {res.stderr[:200]}")
            except Exception as e:
                print(f"[AVISO] Erro ao extrair {rpa.name}: {e}")

        print(f"[OK] {extracted_count} pacotes .rpa descompactados com sucesso.")
        return extracted_count

    def find_rpyc_files(self, game_dir: Path) -> List[Path]:
        """
        Localiza todos os arquivos .rpyc dentro da pasta do jogo.
        """
        results = []
        for rpyc in Path(game_dir).rglob("*.rpyc"):
            if "cache" in rpyc.parts or "tl" in rpyc.parts:
                continue
            if not rpyc.name.endswith(".rpymc"):
                results.append(rpyc)
        return sorted(results)

    def decompile_file(self, rpyc_path: Path, overwrite: bool = True) -> bool:
        """
        Descompila um unico arquivo .rpyc para .rpy
        """
        rpyc_path = Path(rpyc_path)
        rpy_path = rpyc_path.with_suffix(".rpy")

        if rpy_path.exists() and not overwrite:
            return True

        if self._unrpyc:
            try:
                ctx = self._unrpyc.Context()
                self._unrpyc.decompile_rpyc(
                    rpyc_path,
                    ctx,
                    overwrite=overwrite,
                    try_harder=True,
                )
                return rpy_path.exists()
            except Exception as e:
                # Fallback via subprocess chamando unrpyc.py
                pass

        # Fallback via chamada direta do script unrpyc.py
        unrpyc_script = UNRPYC_PATH / "unrpyc.py"
        if unrpyc_script.exists():
            try:
                cmd = [sys.executable, str(unrpyc_script), "-c", str(rpyc_path)]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return rpy_path.exists()
            except Exception:
                pass

        return False

    def decompile_all(self, game_dir: Path, overwrite: bool = False) -> Dict[str, Any]:
        """
        Descompila todos os arquivos .rpyc da pasta do jogo para .rpy.
        """
        self.extract_rpa_archives(game_dir)
        files = self.find_rpyc_files(game_dir)
        total = len(files)
        success = 0
        skipped = 0

        print(f"[DESCOMPILACAO] Processando {total} arquivos .rpyc...")
        for rpyc in files:
            rpy = rpyc.with_suffix(".rpy")
            if rpy.exists() and not overwrite:
                skipped += 1
                continue

            if self.decompile_file(rpyc, overwrite=overwrite):
                success += 1

        print(f"[OK] Descompilacao concluida: {success} convertidos, {skipped} ja existentes, {total} total.")
        return {"total": total, "success": success, "skipped": skipped}
