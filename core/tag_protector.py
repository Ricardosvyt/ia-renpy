import re
from typing import Tuple, Dict, List


class TagProtector:
    """
    Protege sintaxes criticas do motor Ren'Py durante a traducao por modelos de linguagem (LLMs).
    Mascara tags de estilo {b}, {color}, interpolacoes de variaveis [player_name], %(nome)s
    e sequencias de escape para impedir corrupcao de variaveis ou quebras de sintaxe no jogo.
    """

    # 1. Tags de estilo do Ren'Py: {b}, {/b}, {color=#fff}, {size=20}, {w}, {p}, {nw}, etc.
    RE_TAGS = re.compile(r"\{/?[a-zA-Z0-9_#=.:+\-]+?\}")

    # 2. Variaveis interpoladas: [player_name], [hero.stats], [persistent.route], %(name)s
    RE_VARS = re.compile(r"\[[a-zA-Z0-9_.\'\"\[\]!]+\]|%\([a-zA-Z0-9_]+\)[sd]")

    # 3. Sequencias de escape essenciais
    RE_ESCAPES = re.compile(r'\\[nrt"\'\\]')

    def __init__(self):
        pass

    def protect(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Substitui tags e variaveis por mascaras neutras.
        Retorna o texto mascarado e o mapa de restauracao.
        """
        if not text:
            return text, {}

        mask_map: Dict[str, str] = {}
        counter = 0

        # Proteger sequencias de escape primeiro
        def mask_escape(m):
            nonlocal counter
            key = f"__ESC_{counter}__"
            counter += 1
            mask_map[key] = m.group(0)
            return key

        masked = self.RE_ESCAPES.sub(mask_escape, text)

        # Proteger variaveis interpoladas
        def mask_var(m):
            nonlocal counter
            key = f"__VAR_{counter}__"
            counter += 1
            mask_map[key] = m.group(0)
            return key

        masked = self.RE_VARS.sub(mask_var, masked)

        # Proteger tags do Ren'Py
        def mask_tag(m):
            nonlocal counter
            key = f"__TAG_{counter}__"
            counter += 1
            mask_map[key] = m.group(0)
            return key

        masked = self.RE_TAGS.sub(mask_tag, masked)

        return masked, mask_map

    def restore(self, translated_text: str, mask_map: Dict[str, str]) -> str:
        """
        Restaura as tags e variaveis originais a partir do mapa de substituicao.
        """
        if not translated_text or not mask_map:
            return translated_text

        result = translated_text
        for token, original in mask_map.items():
            # Trata possíveis espacos inseridos por alguns LLMs ao redor dos marcadores
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            result = pattern.sub(original, result)

        return result

    def validate(self, original: str, restored: str) -> Tuple[bool, List[str]]:
        """
        Validador deterministico para garantir que nenhuma tag ou variavel do original
        foi perdida ou corrompida na traducao.
        """
        errors: List[str] = []

        # Verificar variaveis
        orig_vars = set(self.RE_VARS.findall(original))
        rest_vars = set(self.RE_VARS.findall(restored))
        missing_vars = orig_vars - rest_vars
        if missing_vars:
            errors.append(f"Variaveis ausentes ou corrompidas: {', '.join(missing_vars)}")

        # Verificar tags de formato
        orig_tags = set(self.RE_TAGS.findall(original))
        rest_tags = set(self.RE_TAGS.findall(restored))
        missing_tags = orig_tags - rest_tags
        if missing_tags:
            errors.append(f"Tags ausentes ou alteradas: {', '.join(missing_tags)}")

        # Verificar balanceamento de aspas duplas nao escapadas
        def count_unescaped_quotes(s: str) -> int:
            return len(re.findall(r'(?<!\\)"', s))

        if count_unescaped_quotes(original) % 2 != count_unescaped_quotes(restored) % 2:
            errors.append("Desbalanceamento de aspas duplas nao escapadas.")

        return len(errors) == 0, errors

