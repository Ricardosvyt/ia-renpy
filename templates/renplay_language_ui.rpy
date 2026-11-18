## Renplay AI - Sistema Drop-in de Idiomas para Ren'Py
## Este script e injetado automaticamente dentro do arquivo unico de patch.

init -10 python:
    import locale

    # Deteccao automatica de idioma na primeira execucao do jogador
    if persistent._renplay_lang_initialized is None:
        persistent._renplay_lang_initialized = True
        try:
            sys_lang, _ = locale.getdefaultlocale()
            if sys_lang and sys_lang.lower().startswith("pt"):
                _preferences.language = "portuguese"
            elif sys_lang and sys_lang.lower().startswith("es"):
                _preferences.language = "spanish"
            elif sys_lang and sys_lang.lower().startswith("fr"):
                _preferences.language = "french"
        except:
            _preferences.language = "portuguese"

    # Atalho de teclado: Tecla 'L' abre o seletor de idiomas
    config.keymap["renplay_lang_toggle"] = ["K_l"]

# Escuta da tecla L para alternar idioma
init python:
    config.underlay.append(
        renpy.Keymap(
            renplay_lang_toggle=renpy.curry(renpy.show_screen)("renplay_language_modal")
        )
    )

## Botao rapido discreto fixado no topo da tela
screen renplay_lang_quick_button():
    zorder 150
    hbox:
        align (0.98, 0.02)
        textbutton "[ Idioma (L) ]":
            style "button"
            text_size 15
            text_color "#ffd400"
            text_hover_color "#ffffff"
            action Show("renplay_language_modal")

## Modal de Selecao de Idioma no mesmo estilo do Ren'Py
screen renplay_language_modal():
    modal True
    zorder 200
    style_prefix "renplay_lang"

    add Solid("#000000cc")

    frame:
        align (0.5, 0.5)
        xsize 480
        padding (25, 25)
        background Frame("#1e232ecc", 10, 10)

        vbox:
            spacing 15
            xalign 0.5

            text "Selecione o Idioma / Language":
                xalign 0.5
                size 22
                bold True
                color "#ffd400"

            text "Pressione [L] a qualquer momento para abrir este menu":
                xalign 0.5
                size 13
                color "#a0aec0"

            null height 10

            vbox:
                spacing 10
                xalign 0.5
                xfill True

                textbutton "[PT-BR] Português (Brasil)":
                    xfill True
                    text_xalign 0.5
                    text_size 16
                    action [Language("portuguese"), SetVariable("_preferences.language", "portuguese"), Hide("renplay_language_modal")]

                textbutton "[ES] Español":
                    xfill True
                    text_xalign 0.5
                    text_size 16
                    action [Language("spanish"), SetVariable("_preferences.language", "spanish"), Hide("renplay_language_modal")]

                textbutton "[FR] Français":
                    xfill True
                    text_xalign 0.5
                    text_size 16
                    action [Language("french"), SetVariable("_preferences.language", "french"), Hide("renplay_language_modal")]

                textbutton "[EN] English (Original)":
                    xfill True
                    text_xalign 0.5
                    text_size 16
                    action [Language(None), SetVariable("_preferences.language", None), Hide("renplay_language_modal")]

            null height 10

            textbutton "[ Fechar / Close ]":
                xalign 0.5
                text_size 15
                text_color "#e2e8f0"
                action Hide("renplay_language_modal")
