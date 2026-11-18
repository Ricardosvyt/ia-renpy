from pathlib import Path
from typing import List, Dict, Any, Optional
import os


class RenplayTrainer:
    """
    Modulo de treinamento e fine-tuning LoRA contínuo para Qwen3.5-4B
    utilizando a biblioteca Unsloth no Google Colab com GPU T4 (FP16).
    """

    def __init__(self, model, tokenizer, checkpoint_dir: Optional[Path] = None):
        self.model = model
        self.tokenizer = tokenizer
        self.checkpoint_dir = Path(checkpoint_dir or "/content/drive/MyDrive/RenplayAI/checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def prepare_dataset(self, units: List[Dict[str, Any]], target_lang: str = "pt-BR") -> List[Dict[str, str]]:
        """
        Gera o dataset de pares de treinamento adaptado ao estilo do jogo e dos personagens.
        """
        training_samples = []
        for unit in units:
            orig = unit.get("original_text", "").strip()
            char = unit.get("character", "Narrador")
            if not orig or len(orig) < 3:
                continue

            instruction = (
                f"Você é a Renplay AI, modelo especializado em tradução e localização de jogos Ren'Py.\n"
                f"Traduza a linha de diálogo de Inglês para Português (Brasil).\n"
                f"Personagem: {char}\n"
                f"Regra estrita: Preserve tags {{b}}, {{color}} e variáveis [variavel] sem alterar nomes ou quebrar código."
            )

            prompt = (
                f"<|im_start|>system\n{instruction}<|im_end|>\n"
                f"<|im_start|>user\n{orig}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )

            training_samples.append({
                "text": prompt + orig + "<|im_end|>"
            })

        print(f"[DATASET] {len(training_samples)} amostras de treino preparadas com o contexto do jogo.")
        return training_samples

    def train_lora(
        self,
        training_data: List[Dict[str, str]],
        max_steps: int = 60,
        output_name: str = "lora_renplay_adapter",
    ) -> Path:
        """
        Executa o fine-tuning LoRA no modelo Qwen3.5-4B em precisao FP16.
        """
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import Dataset

        print(f"\n[TREINAMENTO] Iniciando Fine-Tuning LoRA no Qwen3.5-4B ({max_steps} passos)...")
        
        # Configurar adaptadores LoRA PEFT
        peft_model = FastLanguageModel.get_peft_model(
            self.model,
            r=16,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=16,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing=True,
            random_state=3407,
        )

        dataset = Dataset.from_list(training_data)

        trainer = SFTTrainer(
            model=peft_model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=2048,
            dataset_num_proc=2,
            packing=False,
            args=TrainingArguments(
                per_device_train_batch_size=2,
                gradient_accumulation_steps=4,
                warmup_steps=5,
                max_steps=max_steps,
                learning_rate=2e-4,
                fp16=True,
                bf16=False,
                logging_steps=10,
                optim="adamw_8bit",
                weight_decay=0.01,
                lr_scheduler_type="linear",
                seed=3407,
                output_dir=str(self.checkpoint_dir / "temp_run"),
                report_to="none",
            ),
        )

        # Treinar
        trainer_stats = trainer.train()
        print(f"[OK] Treinamento concluido com sucesso! Perda final (loss): {trainer_stats.training_loss:.4f}")

        # Salvar adaptador LoRA no Google Drive
        save_path = self.checkpoint_dir / output_name
        peft_model.save_pretrained(str(save_path))
        self.tokenizer.save_pretrained(str(save_path))
        print(f"[OK] Adaptador LoRA salvo no Google Drive em: {save_path}")

        # Voltar modelo para modo de inferencia otimizado
        FastLanguageModel.for_inference(peft_model)
        return save_path
