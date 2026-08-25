import difflib
import json
import re
import time
import urllib.request

ACTIONS = (
    "pause",
    "resume",
    "gain_up",
    "gain_down",
    "smooth_suave",
    "smooth_normal",
    "smooth_reactivo",
    "save",
    "left_click",
    "right_click",
    "scroll_up",
    "scroll_down",
    "exit",
    "help",
    "autotune_toggle",
    "assistant",
    "assistant_close",
    "magnify_on",
    "magnify_off",
    "snap_toggle",
)

_PATTERNS = (
    ("right_click", (r"clique?\s+direito", r"clica?\s+direito", r"botao\s+direito")),
    ("left_click", (r"\bclique?s?\b", r"\bcarrega\b", r"\btoca\b")),
    ("magnify_off", (r"(tira|desativa|deslig(a|ar)|cancela)\w*\s*(a\s+)?(amplia\w*|lupa|zoom)", r"menos\s+amplia\w*", r"^sem\s+lupa$")),
    ("magnify_on", (r"\bamplia(r|cao|ção)?\b", r"\blupa\b", r"\bzoom\b")),
    ("assistant_close", (r"(fech(a|ar)|sa(i|r))\s+(o\s+)?(assistente|mesa|barehands)",)),
    ("assistant", (r"\bassistente\b", r"\bbarehands\b", r"\bmesa\s+3d\b", r"abr(e|ir)\s+(o\s+)?jarvis\s*3d")),
    ("snap_toggle", (r"\bsnap\b", r"\bmagnet\w*\b", r"\bima(n|)\b")),
    ("scroll_up", (r"scroll\s+\w*\s*(cima|acima|sobe)", r"(sobe|cima)\s+\w*\s*scroll", r"^sobe$")),
    ("scroll_down", (r"scroll\s+\w*\s*(baixo|desce)", r"(desce|baixo)\s+\w*\s*scroll", r"^desce$")),
    ("pause", (r"\bpaus(a|ar)\b", r"\bcongela\b", r"\bparalisa\b", r"^para$", r"\bparar\b")),
    ("resume", (r"\bcontinu(a|ar)\b", r"\bretom(a|ar)\b", r"\bvolta\b", r"\bsegue\b")),
    ("gain_up", (r"mais\s+rapido", r"\bacelera\w*", r"aumenta\s+(o\s+)?(cursor|velocidade|rapidez)")),
    ("gain_down", (r"mais\s+(devagar|lento)", r"\bdesacelera\w*", r"baixa\s+(a\s+)?(velocidade|rapidez)")),
    ("smooth_reactivo", (r"\breactiv\w+\b", r"\breativ\w+\b")),
    ("smooth_suave", (r"\bsuav\w+\b",)),
    ("smooth_normal", (r"\bnormal\b", r"\bmedio\b")),
    ("autotune_toggle", (r"auto\s*-?\s*(afin\w*|tune|ajuste)",)),
    ("save", (r"\bgrav(a|ar)\b", r"\bguard(a|ar)\b", r"\bsalva(r)?\b")),
    ("help", (r"\bajuda\b", r"\bcomandos\b", r"\bsocorro\b")),
    ("exit", (r"\bsai(r)?\b", r"\btermin(a|ar)\b", r"\bfech(a|ar)\b", r"\bdesliga(r)?\b", r"\baborta\b")),
)

_FUZZY_KEYWORDS = {
    "pausa": "pause",
    "pausar": "pause",
    "continua": "resume",
    "retoma": "resume",
    "clica": "left_click",
    "clique": "left_click",
    "direito": "right_click",
    "sobe": "scroll_up",
    "desce": "scroll_down",
    "cima": "scroll_up",
    "baixo": "scroll_down",
    "rapido": "gain_up",
    "devagar": "gain_down",
    "lento": "gain_down",
    "suave": "smooth_suave",
    "reactivo": "smooth_reactivo",
    "normal": "smooth_normal",
    "gravar": "save",
    "guardar": "save",
    "ajuda": "help",
    "sair": "exit",
    "sai": "exit",
    "termina": "exit",
    "assistente": "assistant",
    "ampliar": "magnify_on",
    "ampliacao": "magnify_on",
    "lupa": "magnify_on",
    "zoom": "magnify_on",
    "snap": "snap_toggle",
}

_LLM_SYS = (
    "Es um interpretador de comandos para um app que controla o rato por gestos. "
    "Responde APENAS com JSON: {\"action\": \"...\", \"value\": null}. "
    "Accoes validas: " + ", ".join(ACTIONS) + ". "
    "Se nada se aplicar responde {\"action\": \"unknown\"}."
)

_llm_state = {"down_until": 0.0}


def parse_local(text):
    t = text.lower().strip()
    if not t:
        return None, None
    for action, patterns in _PATTERNS:
        for pat in patterns:
            if re.search(pat, t):
                return action, None
    words = re.findall(r"[a-z]+", t)
    for w in words:
        close = difflib.get_close_matches(w, _FUZZY_KEYWORDS.keys(), n=1, cutoff=0.8)
        if close:
            return _FUZZY_KEYWORDS[close[0]], None
    return None, None


def parse_with_llm(text, cfg):
    action, value = parse_local(text)
    if action is not None:
        return action, value
    if not cfg.llm_enabled:
        return None, None
    now = time.monotonic()
    if now < _llm_state["down_until"]:
        return None, None
    try:
        payload = json.dumps(
            {
                "model": cfg.llm_model,
                "messages": [
                    {"role": "system", "content": _LLM_SYS},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=cfg.llm_timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data.get("message", {}).get("content", "")
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return None, None
        obj = json.loads(match.group(0))
        action = str(obj.get("action", "")).strip()
        value = obj.get("value")
        if action in ACTIONS:
            return action, value
        return None, None
    except Exception:
        _llm_state["down_until"] = time.monotonic() + 60.0
        return None, None


ACTION_LABELS = {
    "pause": "PAUSA",
    "resume": "RETOMAR",
    "gain_up": "GANHO +",
    "gain_down": "GANHO -",
    "smooth_suave": "SUAVE",
    "smooth_normal": "NORMAL",
    "smooth_reactivo": "REACTIVO",
    "save": "GRAVAR",
    "left_click": "CLIQUE ESQ",
    "right_click": "CLIQUE DIR",
    "scroll_up": "SCROLL +",
    "scroll_down": "SCROLL -",
    "exit": "SAIR",
    "help": "AJUDA",
    "autotune_toggle": "AUTO-AFIN",
    "assistant": "ASSISTENTE 3D",
    "assistant_close": "FECHAR ASSISTENTE",
    "magnify_on": "LUPA ON",
    "magnify_off": "LUPA OFF",
    "snap_toggle": "SNAP",
}
