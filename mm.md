menu help ficou o horrivel fundo transparente esta bem melhor , não estas usando css?
- ✔ RESOLVIDO: fundo sólido via CSS em `ui/help_panel.py` (`HelpPanel { background-color: #16162A }` + `WA_StyledBackground` + estilos de viewport/scrollbar).

mover o mouse esta instavel com uma performance estranha oque foi?
- ✔ RESOLVIDO: o loop do `SmoothEmitter` compensava o atraso do sistema em rajadas (movimento "aos solavancos"); agora ressincroniza (`core/motion.py`). Curva de aceleração com ganho mínimo 1.0 (controlo 1:1 em movimentos precisos) e máx 2.6 / expo 1.5 (`config.py`, `core/filters.py`).

a camerasó deve aparecer quando irmos nas opcões e em ver camera !
- ✔ RESOLVIDO: a câmara deixou de ser o fundo da janela. Só aparece com `📷 VER CÂMARA` (botão no menu ou tecla `C`). Há agora um dashboard com marca por defeito.

isso não deve atrapalhar a identificação erfeito dos gestos, a webcam é apenas para configurações e não como principal, o principal é a funcionaliadade perfeita dos gestões, precisamos aprimorar esta area critica de forma altamente proficional com as melhores tecnicas existentes e critividade dos nostroas agents e subagents experientes
- ✔ RESOLVIDO: o `process_frame` (gestos) corre sempre em cada `_tick`; o toggle da câmara só afeta o render. Deteção aprimorada com deadband (Schmitt trigger) por dedo (dobrado/esticado) para eliminar tremulação entre gestos (`core/gestures.py`). Testes: 23/23 + 13/13 PASS.
