import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import QUEUE_FILE


class QueueManager:
    """
    Gerenciador da fila de processamento de jogos para a Renplay AI.
    Permite adicionar novos links enquanto o modelo treina ou traduz,
    mantendo o estado persistido em JSON para integracao com Google Colab e Google Drive.
    """

    def __init__(self, queue_file_path: Optional[Path] = None):
        self.queue_file = Path(queue_file_path or QUEUE_FILE)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_file.exists():
            self._save_queue([])

    def _load_queue(self) -> List[Dict[str, Any]]:
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_queue(self, data: List[Dict[str, Any]]) -> None:
        temp_file = self.queue_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.queue_file)

    def add_game(
        self,
        url: str,
        name: Optional[str] = None,
        target_languages: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Adiciona um novo link de jogo na fila de espera.
        """
        queue = self._load_queue()
        now_str = datetime.now().isoformat()
        
        # Evitar duplicatas pendentes
        for item in queue:
            if item.get("url") == url and item.get("status") in ("pending", "downloading", "translating"):
                print(f"[INFO] Jogo ja esta na fila com status '{item.get('status')}': {url}")
                return item

        item_id = str(uuid.uuid4())[:8]
        game_name = name or f"jogo_{item_id}"
        languages = target_languages or ["pt-BR"]

        new_entry = {
            "id": item_id,
            "url": url,
            "name": game_name,
            "status": "pending",
            "target_languages": languages,
            "created_at": now_str,
            "updated_at": now_str,
            "patch_path": None,
            "error_message": None,
        }

        queue.append(new_entry)
        self._save_queue(queue)
        print(f"[OK] Jogo adicionado a fila [{new_entry['id']}]: {game_name} ({url})")
        return new_entry

    def get_next_pending(self) -> Optional[Dict[str, Any]]:
        """
        Retorna o proximo item pendente na fila para ser processado.
        """
        queue = self._load_queue()
        for item in queue:
            if item.get("status") == "pending":
                return item
        return None

    def update_status(
        self,
        item_id: str,
        status: str,
        error_message: Optional[str] = None,
        patch_path: Optional[str] = None,
    ) -> bool:
        """
        Atualiza o status de um item da fila (pending, downloading, translating, completed, error).
        """
        queue = self._load_queue()
        found = False
        now_str = datetime.now().isoformat()

        for item in queue:
            if item.get("id") == item_id:
                item["status"] = status
                item["updated_at"] = now_str
                if error_message:
                    item["error_message"] = str(error_message)
                if patch_path:
                    item["patch_path"] = str(patch_path)
                found = True
                break

        if found:
            self._save_queue(queue)
            return True
        return False

    def list_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna a lista de itens da fila, opcionalmente filtrando por status.
        """
        queue = self._load_queue()
        if status:
            return [item for item in queue if item.get("status") == status]
        return queue

    def clear_completed(self) -> int:
        """
        Remove itens concluidos da fila e retorna quantos foram removidos.
        """
        queue = self._load_queue()
        initial_count = len(queue)
        filtered = [item for item in queue if item.get("status") != "completed"]
        self._save_queue(filtered)
        return initial_count - len(filtered)

