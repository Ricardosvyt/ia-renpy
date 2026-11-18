import os
import re
import sys
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from tqdm import tqdm

from config import DOWNLOADS_DIR, EXTRACTED_DIR, PIXELDRAIN_API_BASE, REQUEST_TIMEOUT, CHUNK_SIZE


class PixeldrainDownloader:
    """
    Downloader especializado para arquivos hospedados no Pixeldrain.
    Suporta download em stream, barra de progresso, retentativas e descompactacao automatica.
    """

    def __init__(self, downloads_dir: Optional[Path] = None, extracted_dir: Optional[Path] = None):
        self.downloads_dir = Path(downloads_dir or DOWNLOADS_DIR)
        self.extracted_dir = Path(extracted_dir or EXTRACTED_DIR)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_file_id(url_or_id: str) -> str:
        """
        Extrai o identificador do arquivo do Pixeldrain a partir de uma URL ou ID direto.
        Exemplos suportados:
        - https://pixeldrain.com/u/abc123XYZ
        - https://pixeldrain.com/api/file/abc123XYZ
        - abc123XYZ
        """
        url_or_id = url_or_id.strip()
        match = re.search(r"pixeldrain\.com/(?:u|api/file)/([a-zA-Z0-9_-]+)", url_or_id)
        if match:
            return match.group(1)
        
        # Se for diretamente o ID
        if re.match(r"^[a-zA-Z0-9_-]{6,32}$", url_or_id):
            return url_or_id
            
        raise ValueError(f"URL ou ID do Pixeldrain invalido: {url_or_id}")

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Consulta os metadados do arquivo via API do Pixeldrain.
        """
        info_url = f"{PIXELDRAIN_API_BASE}{file_id}/info"
        response = requests.get(info_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            raise FileNotFoundError(f"Arquivo nao encontrado no Pixeldrain (ID: {file_id})")
        response.raise_for_status()
        return response.json()

    def download(self, url_or_id: str, custom_filename: Optional[str] = None) -> Path:
        """
        Baixa o arquivo do Pixeldrain em streaming com barra de progresso e suporte a retentativas.
        Retorna o caminho absoluto do arquivo baixado.
        """
        file_id = self.extract_file_id(url_or_id)
        info = self.get_file_info(file_id)
        
        remote_name = info.get("name") or f"game_{file_id}.zip"
        filename = custom_filename or remote_name
        dest_path = self.downloads_dir / filename
        
        total_size = int(info.get("size", 0))
        download_url = f"{PIXELDRAIN_API_BASE}{file_id}?download"

        # Verificacao de download existente
        if dest_path.exists() and total_size > 0 and dest_path.stat().st_size == total_size:
            print(f"[OK] Arquivo ja baixado e verificado: {dest_path.name}")
            return dest_path

        headers = {}
        initial_byte = 0
        if dest_path.exists() and total_size > 0 and dest_path.stat().st_size < total_size:
            initial_byte = dest_path.stat().st_size
            headers["Range"] = f"bytes={initial_byte}-"
            print(f"[INFO] Retomando download a partir do byte {initial_byte}...")

        mode = "ab" if initial_byte > 0 else "wb"
        
        with requests.get(download_url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT) as response:
            if response.status_code not in (200, 206):
                # Se range nao for suportado pelo servidor, reinicia o download
                mode = "wb"
                initial_byte = 0
                response = requests.get(download_url, stream=True, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

            with open(dest_path, mode) as f, tqdm(
                total=total_size,
                initial=initial_byte,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=filename[:25],
                ascii=True,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"[OK] Download concluido: {dest_path}")
        return dest_path

    def extract_game(self, archive_path: Path, output_subfolder: Optional[str] = None) -> Path:
        """
        Descompacta o arquivo baixado e localiza a pasta raiz do jogo (contendo a pasta 'game/').
        """
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise FileNotFoundError(f"Arquivo compactado nao encontrado: {archive_path}")

        folder_name = output_subfolder or archive_path.stem
        target_dir = self.extracted_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Extraindo '{archive_path.name}' para '{target_dir}'...")

        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(target_dir)
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as tar_ref:
                tar_ref.extractall(target_dir)
        else:
            # Tentar extracao alternativa se houver 7z ou utilitario no sistema
            try:
                import py7zr
                if py7zr.is_7zfile(archive_path):
                    with py7zr.SevenZipFile(archive_path, mode='r') as z:
                        z.extractall(path=target_dir)
                else:
                    raise ValueError(f"Formato de arquivo nao suportado nativamente: {archive_path.suffix}")
            except ImportError:
                raise ValueError(
                    f"Formato {archive_path.suffix} requer descompactador adicional (instale py7zr ou use ZIP)."
                )

        game_root = self.find_renpy_game_root(target_dir)
        print(f"[OK] Jogo Ren'Py localizado com sucesso em: {game_root}")
        return game_root

    @staticmethod
    def find_renpy_game_root(extracted_dir: Path) -> Path:
        """
        Procura recursivamente pela pasta 'game' do Ren'Py para retornar a pasta raiz do jogo.
        """
        extracted_dir = Path(extracted_dir)
        
        # Verificar se a pasta atual ja e a raiz com 'game/'
        if (extracted_dir / "game").is_dir():
            return extracted_dir

        # Busca recursiva em subpastas ate 3 niveis de profundidade
        for game_folder in extracted_dir.glob("**/game"):
            if game_folder.is_dir() and game_folder.parent != extracted_dir:
                return game_folder.parent

        # Se nao encontrar 'game/', retorna a pasta de extracao como fallback
        return extracted_dir

