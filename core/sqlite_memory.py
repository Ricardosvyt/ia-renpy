import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from config import MEMORY_DB


class SQLiteMemory:
    """
    Memoria de traducao e persistencia de correcoes aprovadas em SQLite.
    Permite reutilizacao imediata de traducoes identicas, glossarios e geracao
    de datasets JSONL consolidados para o proximo ciclo de treinamento LoRA.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or MEMORY_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_lang TEXT NOT NULL DEFAULT 'en',
                    target_lang TEXT NOT NULL DEFAULT 'pt-BR',
                    context TEXT,
                    character TEXT,
                    game_name TEXT,
                    is_approved INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(original_text, source_lang, target_lang, character)
                );
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trans_lookup 
                ON translations(original_text, source_lang, target_lang);
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trans_game 
                ON translations(game_name);
                """
            )
            conn.commit()

    def get_translation(
        self,
        original_text: str,
        target_lang: str = "pt-BR",
        source_lang: str = "en",
        character: Optional[str] = None,
    ) -> Optional[str]:
        """
        Busca uma traducao existente na memoria. Da prioridade a entradas com mesmo personagem.
        """
        text = original_text.strip()
        if not text:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tentativa com mesmo personagem
            if character:
                cursor.execute(
                    """
                    SELECT translated_text, id, usage_count FROM translations
                    WHERE original_text = ? AND target_lang = ? AND source_lang = ? AND character = ?
                    ORDER BY is_approved DESC, usage_count DESC LIMIT 1;
                    """,
                    (text, target_lang, source_lang, character),
                )
                row = cursor.fetchone()
                if row:
                    self._increment_usage(row["id"], row["usage_count"])
                    return row["translated_text"]

            # 2. Tentativa generica sem personagem
            cursor.execute(
                """
                SELECT translated_text, id, usage_count FROM translations
                WHERE original_text = ? AND target_lang = ? AND source_lang = ?
                ORDER BY is_approved DESC, usage_count DESC LIMIT 1;
                """,
                (text, target_lang, source_lang),
            )
            row = cursor.fetchone()
            if row:
                self._increment_usage(row["id"], row["usage_count"])
                return row["translated_text"]

        return None

    def _increment_usage(self, entry_id: int, current_count: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE translations SET usage_count = ?, updated_at = ?
                WHERE id = ?;
                """,
                (current_count + 1, datetime.now().isoformat(), entry_id),
            )
            conn.commit()

    def save_translation(
        self,
        original_text: str,
        translated_text: str,
        target_lang: str = "pt-BR",
        source_lang: str = "en",
        context: Optional[str] = None,
        character: Optional[str] = None,
        game_name: Optional[str] = None,
        is_approved: bool = False,
    ) -> None:
        """
        Salva ou atualiza uma traducao no banco.
        """
        orig = original_text.strip()
        trans = translated_text.strip()
        if not orig or not trans:
            return

        now_str = datetime.now().isoformat()
        approved_int = 1 if is_approved else 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO translations (
                    original_text, translated_text, source_lang, target_lang,
                    context, character, game_name, is_approved, usage_count,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(original_text, source_lang, target_lang, character)
                DO UPDATE SET
                    translated_text = excluded.translated_text,
                    is_approved = MAX(translations.is_approved, excluded.is_approved),
                    usage_count = translations.usage_count + 1,
                    updated_at = excluded.updated_at;
                """,
                (
                    orig,
                    trans,
                    source_lang,
                    target_lang,
                    context,
                    character,
                    game_name,
                    approved_int,
                    now_str,
                    now_str,
                ),
            )
            conn.commit()

    def export_training_dataset(
        self,
        target_lang: str = "pt-BR",
        only_approved: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Exporta os pares de traducao para a estrutura de instrucao JSONL para fine-tuning.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT original_text, translated_text, source_lang, target_lang, context, character
                FROM translations
                WHERE target_lang = ?
            """
            params: List[Any] = [target_lang]
            if only_approved:
                query += " AND is_approved = 1"
            query += " ORDER BY usage_count DESC;"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            dataset = []
            for r in rows:
                instruction = (
                    f"Traduza o seguinte dialogo de jogo Ren'Py de {r['source_lang']} para {r['target_lang']}.\n"
                    f"Personagem: {r['character'] or 'Narrador'}\n"
                    f"Preserve tags {{b}}, {{color}} e variaveis [variavel] sem alterar o codigo."
                )
                dataset.append(
                    {
                        "instruction": instruction,
                        "input": r["original_text"],
                        "output": r["translated_text"],
                        "character": r["character"],
                    }
                )
            return dataset

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatisticas da memoria de traducao.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM translations;")
            total = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as approved FROM translations WHERE is_approved = 1;")
            approved = cursor.fetchone()["approved"]
            
            cursor.execute(
                "SELECT target_lang, COUNT(*) as count FROM translations GROUP BY target_lang;"
            )
            langs = {row["target_lang"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_entries": total,
                "approved_entries": approved,
                "by_language": langs,
            }

