"""Smoke test do cliente de conversa por IA (core/llm).

Sem rede: mocka _post_json para simular respostas de Groq / Ollama.
Corre:  .venv\\Scripts\\python.exe tools\\test_voice_llm.py
"""

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import llm  # noqa: E402


def make_cfg(**kw):
    cfg = types.SimpleNamespace(
        llm_enabled=True,
        llm_provider="groq",
        llm_model="llama-3.1-8b-instant",
        llm_base_url="https://api.groq.com/openai/v1",
        llm_api_key_env="GROQ_API_KEY",
        llm_timeout_s=20.0,
        llm_history=8,
        llm_fallback_local=True,
        ollama_model="llama3.2:3b",
    )
    for k, v in kw.items():
        setattr(cfg, k, v)
    return cfg


class FakeNet:
    """Substitui llm._post_json e conta chamadas + respostas."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _install(self):
        self._orig = llm._post_json
        llm._post_json = self._fake

    def _restore(self):
        llm._post_json = self._orig

    def _fake(self, url, payload, headers, timeout):
        self.calls.append(url)
        idx = min(len(self.calls), len(self.responses)) - 1
        r = self.responses[idx]
        if isinstance(r, str):
            return {"choices": [{"message": {"content": r}}]}
        raise RuntimeError(r)


def complete(content):
    return content


def check(cond, name):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


def test_classify_cmd_via_cloud():
    os.environ["GROQ_API_KEY"] = "gsk_test"
    fake = FakeNet([complete('{"mode":"cmd","action":"scroll_down"}')])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg())
        mode, action = client._call_classifier("rola a pagina para baixo")
        check(mode == "cmd" and action == "scroll_down",
              "classifier -> cmd/scroll_down via cloud")
        check(len(fake.calls) == 1, "usou 1 chamada de rede (cloud)")
    finally:
        fake._restore()


def test_classify_chat_via_cloud():
    os.environ["GROQ_API_KEY"] = "gsk_test"
    fake = FakeNet([complete('{"mode":"chat"}')])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg())
        mode, action = client._call_classifier("qual e o teu modelo preferido?")
        check(mode == "chat" and action is None, "classifier -> chat (pergunta)")
    finally:
        fake._restore()


def test_classify_cmd_ollama_fallback():
    os.environ.pop("GROQ_API_KEY", None)
    fake = FakeNet([complete('{"mode":"cmd","action":"pause"}')])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg())
        mode, action = client._call_classifier("para tudo")
        check(mode == "cmd" and action == "pause",
              "classifier -> cmd via fallback ollama (sem chave cloud)")
        check(any("11434" in u for u in fake.calls), "usou endpoint localhost:11434")
    finally:
        fake._restore()


def test_respond_cloud_and_history():
    os.environ["GROQ_API_KEY"] = "gsk_test"
    fake = FakeNet(["Olá! Estou bem, obrigado."])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg())
        reply = client.respond("olá, como estás?")
        check(reply == "Olá! Estou bem, obrigado.", "respond devolve texto da cloud")
        check(len(client._history) == 2, "historico com user+assistant")
        check(client.status.startswith("ia:"), "status indica IA ligada")
    finally:
        fake._restore()


def test_respond_fallback_ollama():
    os.environ.pop("GROQ_API_KEY", None)
    fake = FakeNet(["Resposta local do Ollama."])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg(llm_fallback_local=True))
        reply = client.respond("conta uma piada")
        check(reply == "Resposta local do Ollama.",
              "respond cai para fallback local (ollama)")
        check(client.status == "ia:ollama", "status indica ollama")
    finally:
        fake._restore()


def test_respond_no_key_no_network():
    os.environ.pop("GROQ_API_KEY", None)
    fake = FakeNet([])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg(llm_fallback_local=False))
        reply = client.respond("bom dia")
        check("nao consegui" in reply.lower(), "sem chave/rede devolve aviso amigavel")
    finally:
        fake._restore()


def test_classify_cmd_local_regex_no_network():
    os.environ.pop("GROQ_API_KEY", None)
    fake = FakeNet([])
    fake._install()
    try:
        client = llm.ChatClient(make_cfg())
        mode, action = client.classify("clica uma vez")
        check(mode == "cmd" and action == "left_click", "classify -> cmd por regex local")
        check(len(fake.calls) == 0, "regex local nao usa rede")
    finally:
        fake._restore()


# --- Integracao com o VoiceEngine._dispatch -------------------------------

def _voice_engine(cfg=None, chat=None, speaker=None):
    from core.voice import VoiceEngine

    ve = VoiceEngine(cfg or make_cfg(), __import__("queue").Queue())
    ve.speaker = speaker
    ve.chat = chat
    ve.status = "wake"
    return ve


class FakeSpeaker:
    def __init__(self):
        self.spoken = []

    def say(self, text, interrupt=False):
        self.spoken.append(text)


class FakeChat:
    """Chat fake: define classify/respond por argumento."""

    def __init__(self, mode="chat", action=None, reply="tudo bem!"):
        self._mode, self._action, self._reply = mode, action, reply

    def classify(self, text):
        return self._mode, self._action

    def respond(self, text):
        return self._reply


def test_dispatch_regex_command_to_queue():
    ve = _voice_engine(chat=FakeChat(mode="chat"))
    ve._dispatch("clica uma vez")
    q = []
    while not ve.cmd_queue.empty():
        q.append(ve.cmd_queue.get_nowait())
    check(len(q) == 1 and q[0]["action"] == "left_click",
          "_dispatch: regex local envia comando para a fila")


def test_dispatch_llm_command_to_queue():
    ve = _voice_engine(chat=FakeChat(mode="cmd", action="scroll_down"))
    ve._dispatch("desce a pagina que quero ler")
    q = []
    while not ve.cmd_queue.empty():
        q.append(ve.cmd_queue.get_nowait())
    check(len(q) == 1 and q[0]["action"] == "scroll_down",
          "_dispatch: comando via IA vai para a fila")


def test_dispatch_conversation_spoken():
    spk = FakeSpeaker()
    ve = _voice_engine(chat=FakeChat(mode="chat", reply="Claro! Podes perguntar."),
                       speaker=spk)
    ve._dispatch("podes explicar como funcionas?")
    check(spk.spoken == ["Claro! Podes perguntar."],
          "_dispatch: conversa livre e falada pelo TTS")
    check(ve.status == "wake", "_dispatch: volta ao estado wake apos conversa")


def test_dispatch_conversation_unknown_phrase():
    spk = FakeSpeaker()
    ve = _voice_engine(speaker=spk)  # chat=None
    ve.cfg.llm_enabled = False
    ve._dispatch("sacas o que me disseres")
    check(spk.spoken == ["Nao entendi."],
          "_dispatch: sem chat e sem comando, diz 'Nao entendi'")


def test_reply_conversation_fallback_no_chat():
    spk = FakeSpeaker()
    ve = _voice_engine(speaker=spk, chat=None)
    ve.cfg.llm_enabled = False
    ve._dispatch("o que pensas do universo?")
    check(spk.spoken == ["Nao entendi."],
          "_reply: sem chat fallback educado")


if __name__ == "__main__":
    test_classify_cmd_via_cloud()
    test_classify_chat_via_cloud()
    test_classify_cmd_ollama_fallback()
    test_respond_cloud_and_history()
    test_respond_fallback_ollama()
    test_respond_no_key_no_network()
    test_classify_cmd_local_regex_no_network()
    test_dispatch_regex_command_to_queue()
    test_dispatch_llm_command_to_queue()
    test_dispatch_conversation_spoken()
    test_dispatch_conversation_unknown_phrase()
    test_reply_conversation_fallback_no_chat()
    print("\nTODOS OS TESTES DE IA DE CONVERSA PASSARAM")
