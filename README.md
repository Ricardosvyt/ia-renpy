# Renplay AI - Motor de Tradução e Mods para Jogos Ren'Py

Repositório oficial da inteligência artificial especializada em localização, extração e geração de patches para visual novels e jogos desenvolvidos no motor **Ren'Py**.

---

## 1. Visão Geral da Arquitetura

O sistema é dividido em três pilares integrados:

1. **Downloader Pixeldrain & Fila Dinâmica:** Suporte a links diretos (`pixeldrain.com/u/{id}`) com download fragmentado e descompactação automática. Permite enfileirar novos jogos enquanto a IA processa o jogo atual.
2. **Proteção de Tags & Memória SQLite:**
   - Mascaramento determinístico de tags de estilo (`{b}`, `{color}`) e variáveis (`[player_name]`, `%(hero)s`), impedindo que a LLM quebre a sintaxe do jogo.
   - Cache de traduções em SQLite com persistência no Google Drive e exportação para fine-tuning periódico.
3. **Patch de Arquivo Único com Seletor de Idiomas Drop-in:**
   - Gera um único arquivo `.rpy` (ex: `99_renplay_nomedojogo_portuguese.rpy`).
   - O jogador **apenas copia esse arquivo para a pasta `game/`** do jogo original.
   - O patch inclui detecção automática do idioma do Windows e adiciona um seletor visual de idiomas (Português, Espanhol, Francês, Inglês) com atalho de teclado `[L]` e botão no menu.

---

## 2. Estrutura do Repositório

```text
inteligência artificial/
├── core/
│   ├── pixeldrain_downloader.py   # Download via Pixeldrain API e descompactacao
│   ├── queue_manager.py          # Fila de jogos (fila_jogos.json) persistida no Drive
│   ├── renpy_extractor.py        # Varredura da pasta game/ e extracao de dialogos
│   ├── tag_protector.py          # Mascaramento de tags, variaveis e aspas
│   ├── sqlite_memory.py          # Memoria de traducao e dataset para treino
│   ├── language_injector.py      # Gerador da tela de selecao de idiomas
│   └── patch_builder.py          # Empacotador do patch de arquivo unico (.rpy)
├── colab/
│   ├── renplay_ai_colab.ipynb    # Notebook oficial para Google Colab (GPU T4 16GB)
│   └── colab_requirements.txt    # Dependencias otimizadas para Colab
├── templates/
│   └── renplay_language_ui.rpy   # Script Ren'Py com a tela de idiomas e atalho [L]
├── tests/
│   ├── test_tag_protector.py     # Testes unitarios de protecao de sintaxe
│   └── test_patch_builder.py     # Testes do gerador de patch
├── config.py                     # Configuracoes globais e idiomas suportados
├── requirements.txt              # Dependencias Python padrao
├── .gitignore                    # Bloqueio de commits de jogos pesados e caches
└── README.md                     # Documentacao do projeto
```

---

## 3. Como Subir este Projeto para o GitHub

No terminal (PowerShell ou Bash) dentro da pasta `d:\Projetos-Renplay\inteligência artificial`:

```bash
cd "d:\Projetos-Renplay\inteligência artificial"

# 1. Inicializar o repositorio Git
git init

# 2. Adicionar os arquivos (o .gitignore ja ignora jogos baixados e caches)
git add .

# 3. Criar o commit inicial
git commit -m "feat: Renplay AI v1 - Pixeldrain downloader, queue system, tag protection and single-file patch"

# 4. Vincular com o seu repositorio remoto no GitHub
git branch -M main
git remote add origin https://github.com/Ricardosvyt/ia-renpy.git

# 5. Enviar para o GitHub
git push -u origin main
```

---

## 4. Como Executar no Google Colab

1. Abra o [Google Colab](https://colab.research.google.com/).
2. Faça o upload do arquivo `colab/renplay_ai_colab.ipynb` ou selecione diretamente do GitHub.
3. Altere o tipo de ambiente de execução para **GPU T4** (*Ambiente de Execução > Alterar tipo de ambiente de execução > T4 GPU*).
4. Execute as células na sequência:
   - **Célula 1 & 2:** Verificam a GPU e montam o Google Drive em `/content/drive/MyDrive/RenplayAI/`.
   - **Célula 3:** Clona o repositório do GitHub no ambiente virtual do Colab.
   - **Célula 4:** Adicione links do Pixeldrain na fila com `queue_mgr.add_game(url="...", name="...")`.
   - **Célula 5 & 6:** Carrega o modelo **Qwen3.5-4B** (Unsloth FP16) e processa os jogos da fila automaticamente.
5. O patch final gerado é salvo automaticamente em seu Google Drive na pasta `/RenplayAI/patches/`.

---

## 5. Como o Jogador Usa o Patch

1. O jogador baixa o arquivo único gerado pela IA (ex: `99_renplay_meujogo_portuguese.rpy`).
2. O jogador move esse arquivo para a pasta `game/` do jogo.
3. Ao abrir o jogo:
   - O jogo detecta o idioma do sistema operacional e ativa o Português automaticamente.
   - Para trocar de idioma a qualquer momento, basta pressionar a tecla **`L`** ou clicar no botão **`[ Idioma (L) ]`** na tela de opções.

---

## 6. Execução de Testes Automatizados

Para validar o funcionamento dos módulos localmente:

```bash
python -m unittest discover -s tests -t .
```

