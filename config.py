import os
from pathlib import Path

# Diretorio raiz do projeto
BASE_DIR = Path(__file__).resolve().parent

# Pastas de trabalho
DOWNLOADS_DIR = BASE_DIR / "downloads"
EXTRACTED_DIR = BASE_DIR / "extracted_games"
PATCHES_DIR = BASE_DIR / "patches_export"
DATA_DIR = BASE_DIR / "data"

# Arquivos de estado e persistencia
QUEUE_FILE = DATA_DIR / "fila_jogos.json"
MEMORY_DB = DATA_DIR / "memoria_traducoes.sqlite"

# Criar pastas caso nao existam
for path in [DOWNLOADS_DIR, EXTRACTED_DIR, PATCHES_DIR, DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Configuracao de Idiomas Suportados no Ren'Py
LANGUAGES = {
    "pt-BR": {
        "display_name": "Português (Brasil)",
        "renpy_code": "portuguese",
        "iso": "pt_BR",
    },
    "es": {
        "display_name": "Español",
        "renpy_code": "spanish",
        "iso": "es_ES",
    },
    "fr": {
        "display_name": "Français",
        "renpy_code": "french",
        "iso": "fr_FR",
    },
    "en": {
        "display_name": "English",
        "renpy_code": "None",
        "iso": "en_US",
    },
}

# Configuracoes de Rede & Pixeldrain
PIXELDRAIN_API_BASE = "https://pixeldrain.com/api/file/"
REQUEST_TIMEOUT = 60
CHUNK_SIZE = 1024 * 1024  # 1 MB por bloco

# Configuracoes do Modelo de Inteligencia Artificial
DEFAULT_MODEL = "Qwen/Qwen3.5-4B"
MAX_SEQ_LENGTH = 2048
TRAIN_DTYPE = "float16"  # Para total compatibilidade com Nvidia T4 (Turing)
LORA_R = 16
LORA_ALPHA = 16

