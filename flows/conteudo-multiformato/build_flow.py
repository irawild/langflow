# ruff: noqa: E501, INP001, RUF001, T201
"""Build the 'Conteudo Multiformato' Langflow flow JSON.

Generates a ready-to-import flow:
  Tese + Contexto -> Estrategista (LLM) -> 3 ramos (Reel, Stories, Post estatico)

The flow is built with lfx's flow_builder, which uses the bundled component
registry so no running Langflow server is required.
"""

from __future__ import annotations

import json
from pathlib import Path

from lfx.base.prompts.api_utils import process_prompt_template
from lfx.graph.flow_builder.builder import load_local_registry
from lfx.graph.flow_builder.component import add_component, configure_component
from lfx.graph.flow_builder.connect import add_connection
from lfx.graph.flow_builder.flow import empty_flow
from lfx.graph.flow_builder.layout import layout_flow

OUTPUT = Path(__file__).with_name("Conteudo Multiformato.json")

# ---------------------------------------------------------------------------
# Prompts (static instructions live in each LLM's system_message; the Prompt
# Template nodes only inject dynamic values, which keeps literal JSON braces
# out of f-string templates).
# ---------------------------------------------------------------------------

STRATEGIST_SYSTEM = """Você é um estrategista-chefe de conteúdo e copywriter sênior, especializado em transformar ideias complexas em conteúdo que retém atenção e gera ação. Você pensa como editor: escolhe UM ângulo, define a tensão, a virada e a prova. Nunca inventa dados; quando não houver prova real, use raciocínio lógico, cálculo simples ou um exemplo hipotético declarado como exemplo.

Sua saída será usada por três roteiristas (Reel, Stories e Post estático). Eles não podem se contradizer. Portanto, seu briefing precisa fixar: a tese central, o ganho, o público, a resposta esperada, a surpresa, o mecanismo, a prova, os passos e o CTA.

Regras de qualidade:
- Especificidade > generalidade. Substitua "as pessoas" por um público concreto; substitua "resultados" por um número ou cenário.
- A "resposta esperada" deve ser a resposta mais óbvia e defensável que o público daria — não um espantalho.
- A "surpresa" deve contrariar essa resposta e explicar POR QUE a tese funciona, com um mecanismo nomeável.
- O "ganho" deve ser uma transformação concreta (economizar tempo/dinheiro, evitar erro, ganhar clareza/status, reduzir risco).
- A "prova" deve ser verificável ou explicitamente hipotética. Se for hipotética, rotule: "exemplo ilustrativo".
- Nada de clichês: "no mundo de hoje", "você sabia", "desbloqueie", "segredo", "hack", "mindset".
- Sem promessas de resultado garantido.
- Se a tese for polêmica, assuma o ponto de vista com responsabilidade e reconheça o contra-argumento mais forte.

Responda APENAS com JSON válido (sem markdown, sem comentários, sem texto antes ou depois), exatamente neste formato:
{
  "tese_central": "a tese em uma frase forte, específica e defensável (máx. 20 palavras)",
  "ganho": "transformação concreta que o público obtém ao entender a tese",
  "publico": "quem precisa ouvir isso agora (dor + desejo, 1 frase)",
  "dor_desejo": "a dor ou o desejo por trás do problema",
  "resposta_esperada": "a resposta óbvia/senso comum que o público daria",
  "surpresa": "a virada contraintuitiva que contraria a resposta esperada",
  "mecanismo": "por que a tese funciona (2-3 frases, com mecanismo nomeável)",
  "prova": "dado, exemplo, cálculo, demonstração ou analogia; se hipotético, rotule",
  "passos": ["passo acionável 1", "passo acionável 2", "passo acionável 3"],
  "satisfacao": "como a promessa é entregue e o loop do gancho é fechado",
  "cta": "ação única e específica",
  "palavra_chave": "1-2 palavras fáceis de comentar",
  "angulo_reel": "melhor ângulo para o Reel em 1 frase",
  "angulo_story": "melhor ângulo para os Stories em 1 frase",
  "angulo_post": "melhor ângulo para o post estático em 1 frase"
}"""

STRATEGIST_PROMPT = """TESE PARA DESENVOLVER:
{tese}

CONTEXTO ADICIONAL (marca, público, produto, tom de voz — pode estar vazio):
{contexto}

Transforme a tese acima em um briefing estratégico para três peças irmãs: um Reel de 90-120s, um roteiro de Stories de 5-7 frames e um post estático de feed que funciona como isca.

Antes de responder, faça internamente:
1. Identifique a afirmação central e o que ela contradiz.
2. Escolha o público que mais se beneficia (ou se sente provocado).
3. Encontre a resposta óbvia desse público.
4. Encontre o mecanismo não óbvio que sustenta a tese.
5. Escolha a prova mais concreta disponível.
6. Defina a palavra-chave do CTA (1-2 palavras, fácil de comentar).

Se o contexto estiver vazio, declare a suposição de público no campo "publico".
Se a tese já contiver dados, use-os; não invente números.
Não escreva as peças. Responda só o JSON."""

REEL_SYSTEM = """Você é roteirista de Reels de alta retenção. Seu trabalho é transformar um briefing em um roteiro falado de 90-120 segundos que uma pessoa grava em talking head + b-roll simples.

Princípios:
- O gancho é uma frase específica, não uma pergunta genérica. Ele promete um ganho e cria tensão.
- A "resposta esperada" aparece cedo: diga o que o público provavelmente pensa. Isso gera identificação.
- A "surpresa" é a virada: contrarie a resposta esperada e nomeie o mecanismo.
- A "satisfação" entrega a promessa: 3 passos, exemplo aplicado e prova. Feche o loop do gancho.
- Uma ideia por frase. Frases curtas. Ritmo de conversa.
- Escreva o texto falado, não descrições vagas. Marque [texto na tela], [b-roll] e [corte] quando necessário.
- A tese central deve ser dita com clareza pelo menos duas vezes, com palavras diferentes.
- Sem jargão de marketing, sem "pessoal", sem "é isso aí", sem promessa garantida.

Estrutura obrigatória com timecodes (ajuste a duração, mas mantenha a ordem):
[0-3s] GANCHO
[3-15s] RESPOSTA ESPERADA
[15-40s] SURPRESA + MECANISMO
[40-85s] SATISFAÇÃO + PROVA + 3 PASSOS
[85-110s] CTA ÚNICO
[110-120s] FECHAMENTO COM A TESE

Requisitos de tamanho:
- 225 a 300 palavras faladas (sem contar marcações), em ritmo de 140-160 palavras por minuto.
- Duração estimada entre 90 e 120 segundos.
- Se o texto passar de 300 palavras, corte adjetivos e exemplos redundantes; não corte a prova nem o CTA.

Entregue:
TÍTULO INTERNO
DURAÇÃO ESTIMADA
PALAVRAS FALADAS
--- ROTEIRO ---
[timecode] BLOCO
FALA: ...
TELA: ...
--- FIM ---"""

REEL_PROMPT = """TESE ORIGINAL:
{tese}

BRIEFING ESTRATÉGICO (JSON):
{estrategia}

Escreva o roteiro completo do Reel seguindo rigorosamente o briefing e a estrutura do sistema. Não repita o JSON; não explique o que vai fazer. Entregue apenas o roteiro no formato pedido."""

STORY_SYSTEM = """Você é roteirista de Stories para Instagram. Escreve como quem conversa no bastidor: direto, pessoal, sem cara de anúncio. Cada frame tem no máximo 15 segundos e precisa fazer a pessoa querer tocar no próximo.

Objetivo narrativo: gancho → resposta esperada (com enquete/quiz) → surpresa → satisfação → prova → CTA.

Princípios:
- Frame 1: uma promessa específica em no máximo 8 palavras na tela + 1 frase falada.
- Frame 2: materialize a resposta esperada com uma enquete ou quiz de 2 opções. A pergunta deve ser respondível em 1 segundo.
- Frame 3: cite o resultado ("a maioria respondeu X") e revele a virada. É aqui que a surpresa acontece.
- Frames 4-5: entregue 2-3 passos rápidos ou um antes/depois. Uma ideia por frame.
- Frame 6: prova concreta (print, cálculo, demonstração, resultado). Se não houver, use uma demonstração lógica.
- Frame 7: CTA único com a palavra-chave do briefing; diga exatamente o que a pessoa recebe ao comentar/chamar.
- Texto na tela: máximo 8 palavras, alto contraste, sem parágrafos.
- Linguagem falada, sem roteiro literário. Pode usar "eu", "você", "olha isso".
- Não use enquetes com mais de 2 opções. Não peça follow genérico.

Entregue frame a frame:
FRAME 1 — [função narrativa] — [duração em segundos]
FALA: ...
TEXTO NA TELA: ...
O QUE MOSTRAR: ...
STICKER/INTERAÇÃO: ...
TRANSIÇÃO: ...
...
Ao final: TOTAL ESTIMADO (45-60s) e CHECKLIST (gancho, enquete, virada, prova, CTA) em uma linha."""

STORY_PROMPT = """TESE ORIGINAL:
{tese}

BRIEFING ESTRATÉGICO (JSON):
{estrategia}

Crie o roteiro de Stories completo, frame a frame, seguindo o briefing e a estrutura do sistema. O frame 2 precisa ter enquete/quiz de 2 opções; o frame 3 precisa citar o resultado da enquete. Entregue apenas o roteiro."""

POST_SYSTEM = """Você é diretor de arte e copywriter de posts estáticos para feed. Cria uma peça 1080x1350 (4:5) que para o scroll, entrega uma ideia completa e funciona como isca de topo de funil: o CTA principal é uma palavra-chave comentada, não "link na bio".

Princípios:
- Headline: no máximo 7 palavras, alto contraste, afirmação específica. A tese deve aparecer na headline ou na subheadline.
- Subheadline: 12-18 palavras, explicando o ganho.
- 3 bullets: no máximo 6 palavras cada, escaneáveis.
- Hierarquia visual: 1 ideia por bloco, no máximo 2 fontes, contraste alto, margem de segurança de 64px.
- Legenda: primeira linha é o gancho; depois resposta esperada, surpresa/mecanismo, satisfação/prova e CTA com a palavra-chave.
- Sem emojis em excesso (máx. 3). Sem hashtags no meio do texto.
- Sem promessas irreais. Se a prova for hipotética, rotule.
- O post precisa fazer sentido sozinho, sem depender do Reel.

Entregue exatamente estas seções:
1. CONCEITO VISUAL (headline, subheadline, 3 bullets, elemento central, paleta/hierarquia, posição do CTA, regra de legibilidade)
2. COPY DA IMAGEM (o texto exato na ordem de leitura)
3. LEGENDA (150-250 palavras, com quebras de linha; inclua a palavra-chave)
4. DISTRIBUIÇÃO (8-12 hashtags, primeira resposta fixada, 2 variações de headline para teste A/B)"""

POST_PROMPT = """TESE ORIGINAL:
{tese}

BRIEFING ESTRATÉGICO (JSON):
{estrategia}

Crie o post estático completo, com conceito visual, copy da imagem, legenda e distribuição, seguindo o briefing e as regras do sistema. Entregue apenas o post no formato pedido."""


# ---------------------------------------------------------------------------
# Flow construction
# ---------------------------------------------------------------------------


def _add(flow, registry, component_type, **params):
    node = add_component(flow, component_type, registry)
    if params:
        configure_component(flow, node["id"], params)
    return node["id"]


def _rename(flow, component_id, display_name, description=""):
    node_data = next(n for n in flow["data"]["nodes"] if n["id"] == component_id)["data"]["node"]
    node_data["display_name"] = display_name
    if description:
        node_data["description"] = description


def _add_prompt(flow, registry, template, **params):
    node = add_component(flow, "Prompt Template", registry)
    configure_component(flow, node["id"], {"template": template, **params})
    node_data = next(n for n in flow["data"]["nodes"] if n["id"] == node["id"])["data"]["node"]
    process_prompt_template(
        template=template,
        name="template",
        custom_fields=node_data.setdefault("custom_fields", {}),
        frontend_node_template=node_data["template"],
    )
    return node["id"]


def _connect(flow, source, output, target, input_):
    add_connection(flow, source, output, target, input_)


def _add_note(flow, text, x=0, y=-620, width=560, height=640):
    note_id = "note-conteudo-multiformato"
    flow["data"]["nodes"].append(
        {
            "data": {
                "id": note_id,
                "node": {
                    "description": text,
                    "display_name": "",
                    "documentation": "",
                    "template": {"backgroundColor": "blue"},
                },
                "type": "note",
            },
            "dragging": False,
            "height": height,
            "id": note_id,
            "measured": {"height": height, "width": width},
            "position": {"x": x, "y": y},
            "positionAbsolute": {"x": x, "y": y},
            "resizing": False,
            "selected": False,
            "type": "noteNode",
            "width": width,
        }
    )


def build() -> dict:
    registry = load_local_registry()
    flow = empty_flow(
        name="Conteúdo Multiformato (Reel + Stories + Post)",
        description=(
            "Recebe uma tese e gera três peças irmãs: roteiro de Reel de 90-120s, "
            "roteiro de Stories frame a frame e post estático de feed como isca. "
            "Todas passam por gancho → resposta esperada → surpresa → satisfação de expectativa."
        ),
    )

    tese = _add(flow, registry, "ChatInput")
    _rename(
        flow,
        tese,
        "Tese (Playground)",
        "Digite a tese no Playground (ou edite o campo Input deste nó). Ela alimenta os três formatos.",
    )

    contexto = _add(
        flow,
        registry,
        "TextInput",
        input_value="",
    )
    _rename(
        flow,
        contexto,
        "Contexto (opcional)",
        "Marca, público, produto, tom de voz, provas disponíveis. Pode ficar vazio.",
    )

    estrategista_prompt = _add_prompt(flow, registry, STRATEGIST_PROMPT)
    _rename(
        flow,
        estrategista_prompt,
        "Briefing Estratégico",
        "Transforma a tese em um briefing único: ganho, público, resposta esperada, surpresa e prova.",
    )
    estrategista = _add(
        flow,
        registry,
        "LanguageModelComponent",
        system_message=STRATEGIST_SYSTEM,
        temperature=0.4,
        stream=False,
    )
    _rename(
        flow, estrategista, "Estrategista", "Define o ângulo e o briefing que será compartilhado pelos três formatos."
    )
    estrategista_out = _add(flow, registry, "ChatOutput", sender_name="Briefing Estratégico")
    _rename(
        flow,
        estrategista_out,
        "Briefing (interno)",
        "Saída de auditoria: mostra o briefing usado pelos três roteiristas.",
    )

    reel_prompt = _add_prompt(flow, registry, REEL_PROMPT)
    _rename(flow, reel_prompt, "Prompt do Reel", "Injeta a tese e o briefing no roteirista do Reel.")
    reel = _add(
        flow,
        registry,
        "LanguageModelComponent",
        system_message=REEL_SYSTEM,
        temperature=0.8,
        stream=False,
    )
    _rename(flow, reel, "Roteirista do Reel", "Escreve o roteiro falado de 90-120s com timecodes, tela e b-roll.")
    reel_out = _add(flow, registry, "ChatOutput", sender_name="Roteiro do Reel")
    _rename(flow, reel_out, "Reel (90-120s)")

    story_prompt = _add_prompt(flow, registry, STORY_PROMPT)
    _rename(flow, story_prompt, "Prompt dos Stories", "Injeta a tese e o briefing no roteirista de Stories.")
    story = _add(
        flow,
        registry,
        "LanguageModelComponent",
        system_message=STORY_SYSTEM,
        temperature=0.9,
        stream=False,
    )
    _rename(flow, story, "Roteirista de Stories", "Escreve 5-7 frames com enquete, virada, prova e CTA.")
    story_out = _add(flow, registry, "ChatOutput", sender_name="Stories")
    _rename(flow, story_out, "Stories (5-7 frames)")

    post_prompt = _add_prompt(flow, registry, POST_PROMPT)
    _rename(flow, post_prompt, "Prompt do Post", "Injeta a tese e o briefing no diretor de arte/copywriter.")
    post = _add(
        flow,
        registry,
        "LanguageModelComponent",
        system_message=POST_SYSTEM,
        temperature=0.7,
        stream=False,
    )
    _rename(flow, post, "Diretor do Post Estático", "Cria conceito visual, copy da imagem, legenda e distribuição.")
    post_out = _add(flow, registry, "ChatOutput", sender_name="Post Estático")
    _rename(flow, post_out, "Post Estático (isca)")

    # Tese -> todos os prompts; contexto -> estrategista
    for target in (estrategista_prompt, reel_prompt, story_prompt, post_prompt):
        _connect(flow, tese, "message", target, "tese")
    _connect(flow, contexto, "text", estrategista_prompt, "contexto")

    # Estrategista -> prompts dos três formatos + saída de auditoria
    _connect(flow, estrategista_prompt, "prompt", estrategista, "input_value")
    _connect(flow, estrategista, "text_output", estrategista_out, "input_value")
    for target in (reel_prompt, story_prompt, post_prompt):
        _connect(flow, estrategista, "text_output", target, "estrategia")

    # Ramo Reel
    _connect(flow, reel_prompt, "prompt", reel, "input_value")
    _connect(flow, reel, "text_output", reel_out, "input_value")

    # Ramo Stories
    _connect(flow, story_prompt, "prompt", story, "input_value")
    _connect(flow, story, "text_output", story_out, "input_value")

    # Ramo Post
    _connect(flow, post_prompt, "prompt", post, "input_value")
    _connect(flow, post, "text_output", post_out, "input_value")

    layout_flow(flow)
    _add_note(
        flow,
        """# 🎯 Conteúdo Multiformato

Recebe **uma tese** e devolve **três peças irmãs**:
- **Reel** de 90–120s (roteiro falado + tela/b-roll)
- **Stories** de 5–7 frames (com enquete e virada)
- **Post estático** de feed como isca (copy + legenda + distribuição)

## Antes de rodar
1. Selecione o **mesmo modelo** nos 4 nós de LLM (Estrategista, Roteirista do Reel, Roteirista de Stories, Diretor do Post).
2. Configure a **API key** do provider.
3. Abra o **Playground** e digite a **tese**. Se quiser, preencha o **Contexto (opcional)** no canvas.

## Estrutura narrativa
**Gancho → Resposta esperada → Surpresa → Satisfação de expectativa → CTA**

O nó **Briefing (interno)** mostra a estratégia que os três formatos compartilham. Se as peças divergirem, ajuste o briefing — não os três roteiros.""",
    )
    return flow


if __name__ == "__main__":
    flow = build()
    payload = {
        "name": flow["name"],
        "description": flow["description"],
        "data": flow["data"],
        "is_component": False,
        "last_tested_version": "1.10.0",
        "tags": ["conteudo", "social-media", "reel", "stories", "copywriting"],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"nodes={len(flow['data']['nodes'])} edges={len(flow['data']['edges'])}")
