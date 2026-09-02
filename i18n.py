"""Minimal i18n layer (PT/EN) for the AirMouse desktop UI.

A simple, dependency-free translation map driven by a module-level language
flag. Every UI string is looked up through ``tr()``; unknown keys fall back to
the Portuguese source text so the app never shows an empty label.
"""
from PySide6.QtCore import QObject, Signal

PT = "pt"
EN = "en"

_lang = PT

# {key: {pt: ..., en: ...}}
_STRINGS = {
    "menu.toggle_ui": {
        "pt": "INTERFACE ON",
        "en": "UI ON",
    },
    "section.controlo": {
        "pt": "CONTROLO",
        "en": "CONTROL",
    },
    "section.sistema": {
        "pt": "SISTEMA",
        "en": "SYSTEM",
    },
    "btn.pause": {"pt": "PAUSA", "en": "PAUSE"},
    "btn.resume": {"pt": "RETOMAR", "en": "RESUME"},
    "btn.save": {"pt": "GRAVAR", "en": "SAVE"},
    "btn.voice": {"pt": "VOZ", "en": "VOICE"},
    "btn.snap": {"pt": "SNAP", "en": "SNAP"},
    "btn.camera": {"pt": "VER CÂMERA", "en": "CAMERA"},
    "btn.help": {"pt": "AJUDA", "en": "HELP"},
    "btn.config": {"pt": "CONFIG", "en": "SETTINGS"},
    "btn.quit": {"pt": "SAIR", "en": "QUIT"},
    "btn.upgrade": {"pt": "UPGRADE PRO", "en": "UPGRADE PRO"},
    "btn.pro_active": {"pt": "PRO ATIVO", "en": "PRO ACTIVE"},
    "license.free_badge": {"pt": "MODO FREE — TESTE SEMPRE", "en": "FREE MODE — ALWAYS TRIAL"},
    "license.free_sub": {"pt": "Está no modo de teste: gratuito, sem data de fim.", "en": "You are in trial mode: free, with no expiry date."},
    "license.hero": {"pt": "Uma nova experiência tecnológica", "en": "A brand-new tech experience"},
    "license.hero_sub": {"pt": "Tudo o que já usa ficou mágico. Desbloqueie todo o poder do AirMouse.", "en": "Everything you use just got magical. Unlock the full power of AirMouse."},
    "license.unlocks_title": {"pt": "O QUE DESBLOQUEIA — EXPERIÊNCIA REVOLUCIONÁRIA", "en": "WHAT YOU UNLOCK — REVOLUTIONARY EXPERIENCE"},
    "license.cta": {"pt": "ATIVAR PRO · EXPERIÊNCIA COMPLETA", "en": "ACTIVATE PRO · FULL EXPERIENCE"},
    "license.has_key": {"pt": "Já tem uma chave Pro? Cole-a aqui", "en": "Already have a Pro key? Paste it here"},
    "license.activate_key": {"pt": "Ativar Chave", "en": "Activate Key"},
    "license.pro_active_title": {"pt": "A sua licença Pro está ativa 💎", "en": "Your Pro license is active 💎"},
    "license.pro_active_sub": {"pt": "Obrigado por apoiar o AirMouse. Toda a experiência tecnológica está desbloqueada.", "en": "Thank you for supporting AirMouse. The full tech experience is unlocked."},
    "license.remove": {"pt": "Remover Licença (voltar a Free)", "en": "Remove License (back to Free)"},
    "benefit.snap": {"pt": "Snap magnético", "en": "Magnetic snap"},
    "benefit.snap_d": {"pt": "O cursor “gruda” nos botões — cliques certeiros à primeira.", "en": "The cursor sticks to buttons — perfect clicks every time."},
    "benefit.voice": {"pt": "Voz “Jarvis” + TTS neural", "en": "“Jarvis” voice + neural TTS"},
    "benefit.voice_d": {"pt": "Controle tudo por voz, com resposta natural e incrível.", "en": "Control everything by voice, with natural, incredible responses."},
    "benefit.hands": {"pt": "Duas mãos", "en": "Two hands"},
    "benefit.hands_d": {"pt": "Lupa de zoom, brilho e gestos avançados com as duas mãos.", "en": "Zoom magnifier, brightness and advanced gestures with both hands."},
    "benefit.ai": {"pt": "IA avançada + auto-afinação", "en": "Advanced AI + auto-tuning"},
    "benefit.ai_d": {"pt": "O sistema aprende consigo e fica cada vez mais rápido.", "en": "The system learns from you and gets faster every time."},
    "benefit.lowlight": {"pt": "Modo luz baixa", "en": "Low-light mode"},
    "benefit.lowlight_d": {"pt": "Funciona perfeitamente mesmo no escuro.", "en": "Works perfectly even in the dark."},
    "benefit.boot": {"pt": "Arranque automático", "en": "Auto-start"},
    "benefit.boot_d": {"pt": "Pronto a usar assim que liga o computador.", "en": "Ready to use the moment you turn on your PC."},
    "benefit.precision": {"pt": "Precisão cirúrgica", "en": "Surgical precision"},
    "benefit.precision_d": {"pt": "Resposta mais rápida e movimentos ultra-suaves.", "en": "Faster response and ultra-smooth movement."},
    "benefit.custom": {"pt": "Personalização total", "en": "Full customization"},
    "benefit.custom_d": {"pt": "Tudo à sua medida: gestos, sensibilidade, atalhos.", "en": "Everything tailored to you: gestures, sensitivity, shortcuts."},
    "benefit.snap_short": {"pt": "cliques certeiros à primeira", "en": "perfect clicks, first time"},
    "benefit.voice_short": {"pt": "controle tudo por voz natural", "en": "control everything by natural voice"},
    "benefit.hands_short": {"pt": "zoom, brilho e gestos avançados", "en": "zoom, brightness & advanced gestures"},
    "benefit.ai_short": {"pt": "o sistema aprende consigo e acelera", "en": "the system learns from you and speeds up"},
    "toast.pause": {"pt": "PAUSA", "en": "PAUSED"},
    "toast.resume": {"pt": "RETOMAR", "en": "RESUMED"},
    "toast.saved": {"pt": "GRAVAR", "en": "SAVED"},
    "toast.voice_on": {"pt": "VOZ ON", "en": "VOICE ON"},
    "toast.voice_off": {"pt": "VOZ OFF", "en": "VOICE OFF"},
    "toast.snap_on": {"pt": "SNAP ON", "en": "SNAP ON"},
    "toast.snap_off": {"pt": "SNAP OFF", "en": "SNAP OFF"},
    "toast.camera_on": {"pt": "CÂMARA ON", "en": "CAMERA ON"},
    "toast.camera_off": {"pt": "CÂMARA OFF", "en": "CAMERA OFF"},
    "toast.ui_on": {"pt": "INTERFACE ON", "en": "UI ON"},
    "toast.ui_off": {"pt": "INTERFACE OFF", "en": "UI OFF"},
    "lang.pt": {"pt": "PT", "en": "PT"},
    "lang.en": {"pt": "EN", "en": "EN"},
    "help.title": {"pt": "AJUDA", "en": "HELP"},
    "help.subtitle": {"pt": "GESTOS & ATALHOS", "en": "GESTURES & SHORTCUTS"},
    "help.sec.move": {"pt": "MOVER & CLIQUE", "en": "MOVE & CLICK"},
    "help.sec.scroll": {"pt": "SCROLL & VOLUME", "en": "SCROLL & VOLUME"},
    "help.sec.bright": {"pt": "BRILHO · 2 MÃOS", "en": "BRIGHTNESS · 2 HANDS"},
    "help.sec.media": {"pt": "MULTIMÉDIA & SISTEMA", "en": "MEDIA & SYSTEM"},
    "help.sec.window": {"pt": "INTERFACE & JANELAS", "en": "UI & WINDOWS"},
    "help.sec.kb": {"pt": "ATALHOS TECLADO", "en": "KEYBOARD SHORTCUTS"},
    "help.sec.voice": {"pt": "VOZ", "en": "VOICE"},
    "help.voice_tip": {
        "pt": "jarvis &lt;comando natural&gt;",
        "en": "jarvis &lt;natural command&gt;",
    },
    "help.g.move": {"pt": "mover cursor", "en": "move cursor"},
    "help.g.one": {"pt": "mão aberta / 1 dedo", "en": "open hand / 1 finger"},
    "help.g.click": {"pt": "clique esq · manter = arrastar", "en": "left click · hold = drag"},
    "help.g.mid": {"pt": "pinça (médio)", "en": "pinch (middle)"},
    "help.g.right": {"pt": "clique direito", "en": "right click"},
    "help.g.scroll": {"pt": "punho + cima/baixo", "en": "fist + up/down"},
    "help.g.scroll_act": {"pt": "scroll", "en": "scroll"},
    "help.g.vol": {"pt": "três dedos + cima/baixo", "en": "three fingers + up/down"},
    "help.g.vol_act": {"pt": "volume", "en": "volume"},
    "help.g.peace_l": {"pt": "dois dedos · mão esq", "en": "two fingers · left hand"},
    "help.g.peace_r": {"pt": "dois dedos · mão dir", "en": "two fingers · right hand"},
    "help.g.dim": {"pt": "diminuir brilho", "en": "lower brightness"},
    "help.g.raise": {"pt": "aumentar brilho", "en": "raise brightness"},
    "help.g.thumb": {"pt": "polegar cima", "en": "thumb up"},
    "help.g.play": {"pt": "play / pausa", "en": "play / pause"},
    "help.g.pinky": {"pt": "mindinho", "en": "pinky"},
    "help.g.copy": {"pt": "copiar (Ctrl+C)", "en": "copy (Ctrl+C)"},
    "help.g.shaka": {"pt": "polegar + mindinho", "en": "thumb + pinky"},
    "help.g.paste": {"pt": "colar (Ctrl+V)", "en": "paste (Ctrl+V)"},
    "help.g.2fist": {"pt": "punho duplo ×2", "en": "double fist ×2"},
    "help.g.wind": {"pt": "Win+D", "en": "Win+D"},
    "help.g.bye": {"pt": "bye bye (onda)", "en": "bye bye (wave)"},
    "help.g.min": {"pt": "minimizar (Win+↓)", "en": "minimize (Win+↓)"},
    "help.g.zoomm": {"pt": "2 mãos abertas + afastar", "en": "2 open hands + apart"},
    "help.g.zoom": {"pt": "lupa (zoom)", "en": "magnifier (zoom)"},
    "help.g.swipe": {"pt": "swipe · mão esq", "en": "swipe · left hand"},
    "help.g.nextwin": {"pt": "próxima janela (Alt+Tab rápido)", "en": "next window (quick Alt+Tab)"},
    "help.g.swipel": {"pt": "swipe p/ esq · mão esq", "en": "swipe left · left hand"},
    "help.g.prevwin": {"pt": "janela anterior (Alt+Shift+Tab)", "en": "previous window (Alt+Shift+Tab)"},
    "help.g.hold": {"pt": "segurar mão esq aberta", "en": "hold left open hand"},
    "help.g.switch": {"pt": "escolher janela (alternador)", "en": "choose window (switcher)"},
    "help.g.peace_toggle": {"pt": "paz (2 dedos) · mão esq", "en": "peace (2 fingers) · left hand"},
    "help.g.ui_toggle": {"pt": "ligar/desligar interface", "en": "toggle interface"},
    "help.kb.gain": {"pt": "ganho −/+", "en": "gain −/+"},
    "help.kb.smooth": {"pt": "suavidade", "en": "smoothness"},
    "help.kb.snap": {"pt": "Snap ON/OFF", "en": "Snap ON/OFF"},
    "help.kb.cam": {"pt": "ver câmara (config)", "en": "view camera (config)"},
    "help.kb.auto": {"pt": "auto-afinação", "en": "auto-tune"},
    "help.kb.voice": {"pt": "voz", "en": "voice"},
    "help.kb.save": {"pt": "gravar", "en": "save"},
    "help.kb.pause": {"pt": "pausar", "en": "pause"},
    "help.kb.quit": {"pt": "sair", "en": "quit"},
    "help.kb.help": {"pt": "mostrar/ocultar ajuda", "en": "show/hide help"},
}


class _I18n(QObject):
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._lang = PT

    @property
    def lang(self):
        return self._lang

    def set_lang(self, lang):
        if lang not in (PT, EN) or lang == self._lang:
            return False
        self._lang = lang
        self.language_changed.emit(lang)
        return True

    def toggle(self):
        self.set_lang(EN if self._lang == PT else PT)
        return self._lang

    def tr(self, key):
        table = _STRINGS.get(key)
        if not table:
            return key
        return table.get(self._lang, table[PT])


I18N = _I18n()


def tr(key):
    return I18N.tr(key)
