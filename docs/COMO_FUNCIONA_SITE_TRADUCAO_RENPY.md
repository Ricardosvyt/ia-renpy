# Como Funciona um Site de Tradução de Jogos Ren'Py

> Documento técnico e arquitetural da plataforma Renplay explicando o funcionamento completo de um portal web especializado na tradução, localização e distribuição de patches para jogos e visual novels desenvolvidas no motor Ren'Py.

---

## 1. O Que É uma Plataforma Web de Tradução Ren'Py?

Um site de tradução de jogos Ren'Py (como o portal integrado da plataforma **Renplay**) é um sistema web colaborativo e automatizado projetado para solucionar os três maiores gargalos da localização de visual novels:

1. **A Barreira Técnica dos Arquivos:** Jogos Ren'Py não distribuem seus textos em arquivos de texto comuns; eles utilizam pacotes criptografados/arquivados (`.rpa`) e scripts compilados em bytecode (`.rpyc`). A plataforma web automatiza a extração e descompilação sem exigir conhecimentos técnicos do usuário.
2. **A Escala Massiva de Textos:** Uma visual novel comum possui entre 20.000 e 150.000 palavras. A plataforma combina **inteligência artificial especializada (Renplay AI)** para tradução em massa com **revisão humana colaborativa (crowdsourcing)**.
3. **A Distribuição Simplificada:** O jogador comum não sabe editar códigos ou criar pastas internas. O site entrega a tradução em um **Patch de Arquivo Único (Drop-in)**, onde basta colocar um único arquivo na pasta `game/` do jogo e ele já abre traduzido e com seletor de idiomas.

---

## 2. Visão Geral da Arquitetura do Sistema

O ecossistema opera através da integração de quatro camadas principais:

```text
[ JOGADOR / REVISOR ]
         |
         v
+-------------------------------------------------------------+
| 1. PORTAL WEB & CAT TOOL (Next.js 16 / React / Tailwind)    |
| - Catalogo de Jogos e Status de Traducao (% Concluido)      |
| - Editor de Textos Lado a Lado (Ingles vs Portugues)        |
| - Sistema de Votacao e Sugestoes da Comunidade              |
+-------------------------------------------------------------+
         |                                           ^
         v (Chamadas REST / JSON)                    | (Patches prontos)
+-------------------------------------------------------------+
| 2. BACKEND API & BANCO DE DADOS (Node.js / PostgreSQL)      |
| - Gerenciamento de Usuarios e Permissoes                    |
| - Fila de Processamento de Jogos (Job Queue)                |
| - Banco de Strings de Dialogo e Dicionario de Termos        |
+-------------------------------------------------------------+
         |                                           ^
         v (Jobs de Download e Traducao)             | (Envio de Resultados)
+-------------------------------------------------------------+
| 3. MOTOR DE PROCESSAMENTO & IA (Python / Google Colab / GPU)|
| - Downloader Direto (Pixeldrain / Drive / Upload)           |
| - Descompilador (.rpa -> .rpyc -> .rpy com unrpyc/unrpa)    |
| - Protecao de Variaveis e Tags (TagProtector)               |
| - LLM Especializada (Qwen3.5-4B via Unsloth FP16)           |
| - Memoria de Traducao em SQLite                             |
| - Construtor do Patch de Arquivo Unico (.rpy / .rpa)        |
+-------------------------------------------------------------+
         |
         v (Distribuicao)
+-------------------------------------------------------------+
| 4. CLIENTES FINAIS                                          |
| - Desktop Launcher Renplay (Tauri v2 + React 19)            |
| - Aplicativo Mobile Android (Flutter)                       |
| - Download Manual de Patch no Site                          |
+-------------------------------------------------------------+
```

---

## 3. Fluxo de Trabalho Passo a Passo (Do Link ao Jogo Traduzido)

### Etapa 1: Solicitação e Ingestão do Jogo
1. O usuário ou administrador acessa a plataforma e insere o link de download direto do jogo (exemplo: Pixeldrain, Google Drive, Mega) ou envia o arquivo compactado.
2. O sistema registra a requisição na fila com status **`PENDING`** e cria uma página dedicada para o jogo no site (`/games/[slug]`), exibindo inicialmente 0% traduzido.

### Etapa 2: Extração e Descompilação Automática (Backend Worker)
1. O worker Python baixa o jogo em stream de alta velocidade.
2. **Descompactação do Container:** Descompacta o arquivo `.zip`, `.rar` ou `.7z`.
3. **Extração de Arquivos RPA:** Localiza arquivos de pacote proprietário do Ren'Py (`.rpa`) e os extrai usando o `unrpa`.
4. **Descompilação RPYC:** Converte todo arquivo compilado `.rpyc` de volta para o código-fonte legível `.rpy` usando o motor `unrpyc`.
5. **Relatório Analítico:** O sistema analisa a árvore do jogo e extrai:
   * Total de falas narrativas.
   * Opções de escolhas de menu (`menu:`).
   * Textos de botões e interface (`strings:`).
   * Lista de personagens e variáveis interpoladas detectadas (`[player]`, `[score]`, `{b}`).
6. Todas as linhas são salvas no banco de dados com seus identificadores de arquivo e cena.

### Etapa 3: Tradução Automatizada por Inteligência Artificial (Renplay AI)
1. O worker de inteligência artificial (executado no Google Colab ou servidor GPU dedicado com o **Qwen3.5-4B**) consome as linhas pendentes.
2. **Consulta à Memória de Tradução:** O sistema verifica se aquela fala ou termo idêntico já foi traduzido e aprovado em outro jogo ou cena. Se sim, reutiliza instantaneamente sem gastar GPU.
3. **Proteção Determinística de Tags:** As tags `{b}`, `{color}`, variáveis `[nome]` e caracteres de escape `\"` são substituídas por máscaras atômicas (`__TAG_0__`, `__VAR_0__`).
4. **Tradução com Adaptação de Tom:** A IA recebe a instrução informando o personagem que está falando, o tom da cena e a regra estrita de não alterar os códigos.
5. **Restauração e Validação:** As máscaras são revertidas para as variáveis originais e um validador verifica se nenhuma variável do Ren'Py foi corrompida.
6. A tradução preliminar da IA é salva, e o status no site sobe para **100% Tradução Preliminar (IA)**.

### Etapa 4: Estúdio de Revisão Web e Crowdsourcing (CAT Tool)
1. No site, tradutores humanos e membros da comunidade têm acesso ao editor web:
   * **Visão Lado a Lado:** Texto original em inglês na coluna esquerda; tradução na coluna direita.
   * **Filtros por Personagem:** Permite que um revisor filtre apenas as falas de um determinado personagem para garantir consistência de personalidade e gírias.
   * **Dicionário e Glossário Integrado:** Garante que nomes de lugares, termos do universo e apelidos sejam traduzidos sempre da mesma forma.
   * **Sistema de Votação:** Membros da comunidade podem sugerir adaptações melhores para trocadilhos ou piadas. A sugestão mais votada é marcada para aprovação do moderador.
2. Cada alteração aprovada pelo revisor alimenta a base de dados de **Memória Imediata**, evitando que o mesmo erro se repita em projetos futuros.

### Etapa 5: Geração e Distribuição do Patch de Arquivo Único
1. Quando uma versão de tradução é concluída ou atinge um marco de qualidade estável (v1.0, v1.1), o backend aciona o `PatchBuilder`.
2. O sistema gera **um único arquivo `.rpy`** (ex: `99_renplay_meujogo_portuguese.rpy`) contendo:
   * A tabela completa de tradução de strings e diálogos do Ren'Py.
   * O injetor de interface (`renplay_language_ui.rpy`), que detecta automaticamente se o Windows do jogador está em português e injeta a opção de idiomas no menu de preferências do jogo, além de registrar a tecla de atalho rápida **`[L]`**.
3. O patch é armazenado no servidor de arquivos e vinculado à página do jogo.

### Etapa 6: Instalação e Execução pelo Jogador
Existem duas formas pelas quais o jogador aproveita a tradução:

* **Pelo Launcher Renplay Desktop:**
  1. O usuário clica em "Instalar Tradução" na página do jogo dentro do launcher.
  2. O launcher baixa o patch e o copia diretamente para a pasta `game/` do jogo no computador.
  3. Ao clicar em "Jogar", o jogo abre 100% em português brasileiro.
* **Pelo Download Manual no Site:**
  1. O jogador faz o download do arquivo único `.rpy`.
  2. Arrasta o arquivo para a pasta `game/` da sua instalação local do jogo.
  3. Pronto! O jogo reconhece o script imediatamente.

---

## 4. Estrutura do Banco de Dados para um Site de Tradução

Para gerenciar o processo, o banco de dados relacional utiliza quatro tabelas fundamentais:

```text
1. GAMES (Tabela de Jogos)
   - id, slug, title, original_language, renpy_version, total_lines, translated_lines

2. SCRIPT_UNITS (Tabela de Linhas do Roteiro)
   - id, game_id, file_path, line_number, unit_type (dialogue, menu, string)
   - character_name, original_text, critical_variables (JSON)

3. TRANSLATIONS (Tabela de Traduções)
   - id, unit_id, target_language, translated_text, translated_by (AI ou User_ID)
   - status (draft, community_reviewed, approved), upvotes_count

4. GLOSSARY (Glossário de Termos e Personagens)
   - id, game_id, term_original, term_translation, notes, character_gender
```

---

## 5. Como Manter o Custo Próximo de Zero

O modelo adotado pela arquitetura Renplay permite operação de altíssimo desempenho com custos mínimos:

* **Servidor Web e API:** Hospedado em infraestrutura serverless (Next.js no Vercel/Node + banco de dados Neon PostgreSQL gratuito ou gerenciado).
* **Treinamento e Inferência Pesada:** Executado no **Google Colab gratuito com GPU Tesla T4 (16 GB)** utilizando o modelo **Qwen3.5-4B** e Unsloth FP16, sem necessidade de alugar servidores de GPU 24 horas por dia.
* **Armazenamento de Patches:** Como o patch de tradução do Ren'Py é puramente textual (`.rpy`), cada arquivo de tradução completo pesa geralmente **menos de 2 MB**, permitindo armazenar milhares de traduções completas gastando frações mínimas de banda e disco.

---

## 6. Integração com os Módulos do Ecossistema Renplay

* **[inteligência artificial](file:///d:/Projetos-Renplay/intelig%C3%AAncia%20artificial)**: Motor de IA, Colab, descompilador unrpyc e construtor de patch de arquivo único.
* **[Site-Api](file:///d:/Projetos-Renplay/Site-Api)**: Portal web, catálogo, autenticação e API de entrega de dados.
* **[Computador/launcher-renplay](file:///d:/Projetos-Renplay/Computador/launcher-renplay)**: Aplicativo desktop para gerenciar jogos, aplicar patches com 1 clique e controlar saves.
* **[PROJECT_CONTEXT_HANDOVER.md](file:///d:/Projetos-Renplay/PROJECT_CONTEXT_HANDOVER.md)**: Documento central de regras de negócio e continuidade do projeto.
