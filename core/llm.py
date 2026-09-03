"""Cliente de conversa por IA responsivo.

Usa qualquer API compatível com OpenAI (Groq, OpenAI, DeepSeek, OpenRouter)
e cai para Ollama local quando a cloud nao esta disponivel.
Nao adiciona dependencias: usa urllib (como o resto do projeto).
"""

import json
import os
import threading
import time
import urllib.request

# Provider -> (base_url por omissao, env var da chave, modelo por omissao)
PROVIDERS = {
    "groq": (
        "https://api.groq.com/openai/v1",
        "GROQ_API_KEY",
        "llama-3.1-8b-instant",
    ),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
    "deepseek": (
        "https://api.deepseek.com/v1",
        "DEEPSEEK_API_KEY",
        "deepseek-chat",
    ),
    "openrouter": (
        "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY",
        "meta-llama/llama-3.1-8b-instruct:free",
    ),
}

OLLAMA_BASE = "http://localhost:11434/v1"

_PERSONA = (
    "Tu es o Jarvis, um assistente pessoal por voz, simpatico e direto, que vive "
    "num PC com controlo por gestos. Fala SEMPRE em portugues (pt-PT). Responde "
    "de forma curta e natural, como numa conversa falada: 1 a 3 frases, sem "
    "listas, sem markdown, sem tabuas. Se te pedirem uma acao do computador "
    "(como clicar, scroll, pausar, abrir assistente), responde com uma frase curta "
    "confirmando que vais fazer, sem inventar acoes concretas."
)

_SYSTEM_CMD = (
    "Interpretas o que o utilizador disse e devolves APENAS JSON valido. "
    "Se for um comando do rato/gestos (clicar, scroll, pausa, continuar, "
    "velocidade, suavidade, gravar, snap, ampliar/lupa, abrir/fechar assistente, "
    "sair, ajuda) devolve {\"mode\":\"cmd\",\"action\":\"<acao>\"} com action um "
    "destes: pause, resume, gain_up, gain_down, smooth_suave, smooth_normal, "
    "smooth_reactivo, save, left_click, right_click, scroll_up, scroll_down, "
    "exit, help, autotune_toggle, assistant, assistant_close, magnify_on, "
    "magnify_off, snap_toggle. Em qualquer outro caso (pergunta, conversa, "
    "piada, curiosidade) devolve {\"mode\":\"chat\"}. "
    "Exemplos: {\"mode\":\"cmd\",\"action\":\"scroll_up\"} ou {\"mode\":\"chat\"}."
)


def _load_api_key(name, env_files=(".env",)):
    val = os.environ.get(name)
    if val:
        return val.strip()
    for ef in env_files:
        if not os.path.isfile(ef):
            continue
        try:
            with open(ef, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    if k.strip() == name:
                        return v.strip().strip('"').strip("'")
        except OSError:
            continue
    return None


def _post_json(url, payload, headers, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_reply(obj):
    return obj.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


class ChatClient:
    """Conversa por IA responsivo com historico e fallback local."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._history = []  # lista de {"role": ..., "content": ...}
        self._lock = threading.Lock()
        self._state = {"down_until": 0.0, "mode": "off", "err": ""}

    @property
    def status(self):
        if self._state["mode"] == "cloud":
            return f"ia:{self.cfg.llm_model}"
        if self._state["mode"] == "ollama":
            return "ia:ollama"
        if self._state["mode"] == "off" and self._state.get("down_until", 0) > time.monotonic():
            return "ia:lento"
        return "ia:off"

    def reset(self):
        with self._lock:
            self._history = []

    def _provider(self):
        name = (self.cfg.llm_provider or "groq").lower()
        base, env, model = PROVIDERS.get(
            name, PROVIDERS["groq"]
        )
        return (
            getattr(self.cfg, "llm_base_url", None) or base,
            _load_api_key(getattr(self.cfg, "llm_api_key_env", None) or env),
            getattr(self.cfg, "llm_model", None) or model,
        )

    def _setup_cloud(self):
        name = (self.cfg.llm_provider or "groq").lower()
        if name == "ollama-local":
            # sem chave cloud: usa apenas o Ollama local (fallback)
            self._base = OLLAMA_BASE
            self._key = None
            self._model = getattr(self.cfg, "ollama_model", "llama3.2:3b")
            return
        base, key, model = self._provider()
        self._base, self._key, self._model = base, key, model

    def _fallback_ollama(self, messages, timeout):
        payload = {
            "model": getattr(self.cfg, "ollama_model", "llama3.2:3b"),
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.6},
        }
        headers = {"Content-Type": "application/json"}
        obj = _post_json(
            OLLAMA_BASE + "/chat/completions",
            payload,
            headers,
            timeout=timeout,
        )
        return _extract_reply(obj)

    def classify(self, text):
        """Devolve ('cmd', action) ou ('chat', None).

        Comando: tenta primeiro por regras locais (rapido e sem rede);
        depois, se nao for claro, pede a LLM para classificar e extrair a acao.
        """
        from core.nlu import parse_local

        action, value = parse_local(text)
        if action is not None:
            return "cmd", action
        return self._call_classifier(text)

    @staticmethod
    def _parse_llm_json(raw):
        if not raw:
            return {}
        lo = raw.find("{")
        hi = raw.rfind("}")
        if lo == -1 or hi <= lo:
            return {}
        try:
            return json.loads(raw[lo:hi + 1])
        except Exception:
            return {}

    def _classifier_call(self, text, timeout):
        """Devolve o JSON interpretado, ou {} em caso de erro."""
        for base, model, _key, headers, desc in self._classifier_candidates():
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_CMD},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "temperature": 0,
                "max_tokens": 50,
            }
            try:
                obj = _post_json(
                    base.rstrip("/") + "/chat/completions",
                    payload,
                    headers,
                    timeout=timeout,
                )
                raw = _extract_reply(obj)
                j = self._parse_llm_json(raw)
                if j:
                    return j, desc
            except Exception:
                continue
        return {}, "none"

    def _classifier_candidates(self):
        """Lista de (base, key, model, headers, desc) para tentar em ordem."""
        cands = []
        self._setup_cloud()
        if self._key:
            cands.append(
                (
                    self._base,
                    self._model,
                    self._key,
                    {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._key}",
                    },
                    "cloud",
                )
            )
        if getattr(self.cfg, "llm_fallback_local", True):
            cands.append(
                (
                    OLLAMA_BASE,
                    getattr(self.cfg, "ollama_model", "llama3.2:3b"),
                    None,
                    {"Content-Type": "application/json"},
                    "ollama",
                )
            )
        return cands

    def _call_classifier(self, text):
        j, _ = self._classifier_call(text, 6.0)
        mode = str(j.get("mode", "")).lower()
        if mode == "cmd":
            action = str(j.get("action", "") or "").strip()
            return "cmd", (action if action else None)
        return "chat", None

    def respond(self, user_text, beep=None):
        """Ava uma resposta falada para a fala do utilizador.

        Devolve a resposta em texto (pronta para TTS), ou uma mensagem de erro
        se a IA nao estiver disponivel.
        """
        if not getattr(self.cfg, "llm_enabled", True):
            return None
        now = time.monotonic()
        if now < self._state["down_until"]:
            return "Ainda nao consigo ligar a minha inteligencia. Tenta de novo daqui a pouco."

        self._setup_cloud()
        with self._lock:
            self._history.append({"role": "user", "content": user_text})
            clipped = self._history[-int(getattr(self.cfg, "llm_history", 8)):]

        messages = [{"role": "system", "content": _PERSONA}] + list(clipped)
        err = None

        # Tenta a cloud
        if self._key:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._key}",
            }
            payload = {
                "model": self._model,
                "messages": messages,
                "stream": False,
                "temperature": 0.6,
                "max_tokens": 180,
            }
            try:
                obj = _post_json(
                    self._base.rstrip("/") + "/chat/completions",
                    payload,
                    headers,
                    timeout=getattr(self.cfg, "llm_timeout_s", 20.0),
                )
                reply = _extract_reply(obj)
                if reply:
                    self._state.update(mode="cloud", err="")
                    self._history.append({"role": "assistant", "content": reply})
                    return reply
                err = "resposta vazia"
            except Exception as exc:
                err = exc

        # Fallback local (Ollama)
        if getattr(self.cfg, "llm_fallback_local", True):
            try:
                reply = self._fallback_ollama(
                    messages, timeout=getattr(self.cfg, "llm_timeout_s", 20.0)
                )
                if reply:
                    self._state.update(mode="ollama", err="")
                    self._history.append({"role": "assistant", "content": reply})
                    return reply
                err = "resposta vazia (ollama)"
            except Exception as exc:
                err = exc

        self._state["down_until"] = time.monotonic() + 30.0
        self._state["err"] = str(err)
        return (
            "Nao consegui ligar a inteligencia agora. "
            "Verifica a ligacao a internet ou a chave da API."
        )
