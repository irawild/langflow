# Plano de automação da esteira de conteúdo

**Fábrica de Conteúdo Financeiro | Brasil | Revisado em 24 de novembro de 2026**

## 1. Resumo executivo

**Sim: é possível automatizar a maior parte da produção e publicação**, preservando a sua participação onde ela agrega mais valor: escolher a tese, verificar os fatos, revisar e finalizar textos/prompts e aprovar a campanha.

### Arquitetura recomendada

**Você → Google Sheets (tese e aprovação) → n8n (orquestração) → Langflow (roteiros e prompts) → OpenAI Images (artes) → ElevenLabs + Creatomate ou FFmpeg (Reels) → Google Drive (arquivo) → Publer API (agenda/publica no Instagram e TikTok) → métricas de volta ao Sheets.**

- **Aproveitar o que já existe:** o fluxo Langflow já pesquisa a tese e gera Reel, post, carrossel, Stories, prompts visuais e pacote Markdown.
- **Adicionar:** saída estruturada para automação, n8n para coordenar as etapas, geração de arquivos de imagem, montagem de vídeo e ligação a um publicador social.
- **Manter aprovação humana:** nada é agendado/publicado até você marcar a campanha como aprovada. Depois de validar a qualidade, a etapa de revisão manual do arquivo final pode ser opcional.
- **Evitar publicar diretamente pela API do TikTok criada só para sua conta:** as diretrizes atuais do TikTok não aceitam clientes de publicação limitados a uso interno/privado; clientes não auditados ficam limitados a publicação privada. Use um publicador estabelecido que já integre a plataforma.

O resultado esperado é automatizar geração de roteiro, imagem, vídeo, organização, agendamento, publicação e registro de métricas. A exceção mais importante são Stories com enquetes, caixas de pergunta, links ou outros stickers interativos: frequentemente exigem conclusão manual no app ou notificação do publicador.

## 2. Fluxo de trabalho proposto

| Etapa | Você faz | Automação faz |
|---|---|---|
| 1. Nova tese | Preenche tese, contexto e objetivo no Sheets | Cria um ID único e inicia a execução no Langflow |
| 2. Rascunho | Confere tese, fontes e dados | Gera briefing, textos, roteiros e prompts visuais |
| 3. Revisão editorial | Edita e finaliza textos/prompts; muda o status para `APROVADO_TEXTO` | Guarda versões e aguarda aprovação — não publica |
| 4. Produção | Opcionalmente revisa os primeiros arquivos durante o piloto | Gera imagens, voz, carrossel e vídeo; exporta arquivos finais ao Drive |
| 5. Liberação | Marca `LIBERADO_PUBLICACAO` (ou uma etapa de revisão de mídia durante o piloto) | Faz verificações técnicas, envia ao publicador e agenda cada peça |
| 6. Publicação | Acompanha exceções e comentários | Publica no horário, grava IDs/URLs e sinaliza falhas |
| 7. Aprendizado | Revisa o desempenho e escolhe novas teses | Importa métricas disponíveis e atualiza o calendário |

### Estados sugeridos no calendário

`NOVA` → `RASCUNHO_PRONTO` → `EM_REVISAO` → `APROVADO_TEXTO` → `PRODUZINDO` → `LIBERADO_PUBLICACAO` → `AGENDADO` → `PUBLICADO`.

Saídas alternativas: `ERRO`, `CANCELADO`, `REVISAO_DE_MIDIA`. Cada peça também deve ter seu próprio estado e horário, para que Reel, carrossel, post e Stories não sejam publicados todos juntos.

**Regra de segurança:** a automação só pode chamar o publicador para registros com `LIBERADO_PUBLICACAO`, conteúdo final preenchido e horário futuro. Use `campaign_id + asset_id + rede` como chave idempotente para não publicar duas vezes numa repetição do workflow.

## 3. Ferramentas e função de cada uma

| Ferramenta | Função na esteira | Configuração principal |
|---|---|---|
| **Langflow (já existente)** | Pesquisa e geração das peças e prompts | Ajustar para entregar JSON estável além do pacote Markdown; manter modelo de estratégia com tool calling |
| **n8n Community self-hosted** | Gatilhos, chamadas de API, aprovações, repetição segura e logs | Google Sheets/Drive, Langflow, OpenAI, TTS, renderizador e Publer como credenciais separadas |
| **Google Sheets** | Fila de teses, revisão e controle de estados | Uma linha por campanha e uma tabela de assets/horários por formato e plataforma |
| **Google Drive** | Arquivo mestre e arquivos produzidos | Uma pasta por tese; preservar originais e versões finais |
| **OpenAI API / GPT Image 2.5 Sunburst** | Geração das imagens a partir dos prompts aprovados | `gpt-image-2.5-sunburst`, imagem PNG; credencial da API guardada no n8n |
| **ElevenLabs TTS (opcional)** | Narração em português para o Reel | Escolher voz licenciada para uso comercial, idioma/acento PT-BR e modelo apropriado |
| **Creatomate API ou FFmpeg** | Composição de MP4, capas, subtítulos e slides | Criar uma vez templates verticais e 4:5; preencher com roteiro, narração e imagens aprovadas |
| **Publer Business API (recomendado)** | Upload de mídia, agendamento, auto-publicação e estado do post | Conectar Instagram/TikTok via OAuth; API Business; guardar token e IDs de contas no n8n |
| **Metricool Advanced (alternativa)** | Planejamento, publicação, aprovações e API | API disponível no Advanced/Custom; alternativa mais cara, com planner/aprovação integrados |

### Por que usar Publer (ou Metricool) no meio

O Publer documenta uma API para enviar mídia, agendar/publicar e consultar o resultado, inclusive para Instagram e TikTok; o acesso à API requer plano Business ou Enterprise. Isso evita manter senhas de redes sociais ou construir um aplicativo de publicação próprio.

O Metricool também oferece agendamento via API; o acesso à API requer o plano Advanced ou Custom. A vantagem é ter aprovação de posts e calendário já incluídos. Preços e recursos por rede devem ser confirmados no checkout antes da contratação.

**Não usar automação de navegador/RPA que imite cliques ou guarde a senha do TikTok.** A integração deve ser OAuth pelo publicador escolhido e respeitar o fluxo de aprovação.

## 4. Configuração necessária

### A. Contas e publicação

1. **Instagram:** use conta profissional (Creator ou Business), conceda acesso ao publicador e conclua eventuais requisitos do Meta Business/Page Publishing Authorization. Teste Reels, carrossel, feed e Story separadamente.
2. **TikTok:** conecte pelo OAuth do publicador. Verifique a opção de auto-publicação por formato, idioma, conta e configurações comerciais; não assuma que um recurso liberado para vídeo também funciona para carrossel de fotos.
3. **Publicador:** contrate o plano com API se necessário. Crie token de API, identifique o workspace/brand e IDs das contas conectadas. Guarde tudo nas credenciais do n8n; nunca em Sheets, prompts, JSON do fluxo ou Git.
4. Configure horário `America/Sao_Paulo`, janelas por rede e um intervalo mínimo entre publicações. Mantenha uma publicação por rede como unidade independente, mesmo quando o material-base é o mesmo.
5. Durante o piloto, publique primeiro como rascunho ou use contas de teste; só habilite `autoPublish` depois de conferir o comportamento de cada formato.

### B. Sheets e Drive

Crie no Drive:

```text
Conteudo Financeiro/
  AAAA/
    AAAA-MM-DD__slug-da-tese/
      00_Briefing-e-Textos/
      01_Imagens-Originais/
      02_Videos-Finais/
      03_Publicados-e-Metricas/
```

Use um Google Sheet com, no mínimo, duas abas:

**Campanhas:** `campaign_id`, tese, contexto, fontes, briefing, link do documento, estado da revisão, responsável, data de criação.

**Assets/Posts:** `asset_id`, `campaign_id`, rede, formato, texto final, prompt visual final, link do original, link do arquivo final, horário, estado, ID do publicador, URL publicada, erro e métricas.

Configure no n8n credenciais Google OAuth2 para Sheets/Drive (ou uma service account com a pasta compartilhada). O Drive arquiva os arquivos; os estados no Sheet controlam a automação. Configure retenção/backup antes de guardar muitas imagens ou vídeos.

### C. Langflow e aprovação

O fluxo atual foi feito para uso no Playground, não como contrato de integração. Antes de ligar o n8n:

1. Dê ao fluxo um endpoint/API key e uma URL estável, acessível pelo n8n. O Langflow atual em Docker no Mac (`localhost:7860`) não é acessível por um n8n hospedado na nuvem e para de funcionar quando o Mac desliga.
2. Gere uma resposta com campos estruturados e nomes estáveis: briefing/fontes, roteiro Reel, legenda/copy por plataforma, slides do carrossel, frames dos Stories, prompts/parametrização por imagem, recomendações de data e `campaign_id`.
3. Configure modelo e credenciais no Langflow. O modelo do pesquisador precisa de tool calling; os roteiristas e o diretor visual não precisam necessariamente.
4. O n8n salva o rascunho e marca `EM_REVISAO`. Você edita os campos finais no Sheet/documento. Só a mudança explícita para `APROVADO_TEXTO` inicia a geração de mídia.
5. No piloto, peça uma segunda aprovação para o MP4/imagens finais. Mais tarde, se a qualidade estiver estável, essa segunda pausa pode ser desativada.

**Migração do modelo:** o fluxo local tem `gpt-5.4-nano` selecionado. A tabela oficial informa US$ 0,20/M tokens de entrada e US$ 1,25/M de saída, mas o modelo está deprecated com desligamento previsto para 1º de abril de 2027. Planeje testar e migrar para um modelo suportado antes dessa data; custos dependem do modelo substituto e do volume real de tokens.

### D. Imagens e vídeo

1. Para cada prompt aprovado, n8n chama a Images API com `gpt-image-2.5-sunburst`, tamanho/qualidade do asset e `n=1`.
2. Decodifica `data[0].b64_json`, salva PNG no Drive e registra o ID/link. Imagens geradas não vêm como URL permanente.
3. Gere **backgrounds/elementos visuais sem texto**. O template de composição aplica headline, números verificados, legendas e fontes; nunca deixe o gerador inventar gráficos, cotações ou letras.
4. Para Reels, ElevenLabs gera narração a partir do roteiro final. Um template Creatomate ou processo FFmpeg combina áudio, imagens/B-roll, cortes, legendas e tela de fontes/aviso financeiro. Não use música protegida sem licença; som original/voz evita depender da biblioteca de música nativa.
5. Um template também pode renderizar o post 4:5 e slides do carrossel. Mantenha arquivos de texto editáveis no Drive para correção posterior.
6. Publer API faz upload da mídia para o próprio serviço antes de agendar; assim não é necessário abrir um endpoint público do seu Drive. Se uma integração exigir URLs públicas, use um storage/CDN controlado e com links estáveis, nunca links privados do Drive.

### E. n8n e publicação

Crie quatro workflows separados para facilitar teste e recuperação:

1. **Rascunho:** detecta tese nova, chama Langflow, cria documento/pacote e linhas de revisão.
2. **Produção:** detecta `APROVADO_TEXTO`, gera PNGs, áudio e MP4/slides, guarda tudo no Drive e registra arquivos.
3. **Agendamento/publicação:** processa somente `LIBERADO_PUBLICACAO`; carrega arquivos no publicador, agenda posts por rede/formato, grava IDs/status/URL e monitora falhas.
4. **Métricas:** consulta o publicador após 24h/7d e atualiza métricas de visualizações, alcance, retenção, salvamentos/compartilhamentos onde disponíveis.

Use retries com atraso para erros transitórios, um limite de tentativas, alertas por e-mail/Slack e uma fila de erro. Nunca repita cegamente uma chamada de publish cuja resposta se perdeu: consulte o estado do post pelo ID no publicador primeiro para evitar duplicatas.

## 5. Limites que afetam a automação

- **TikTok API própria:** as diretrizes proíbem um cliente de Direct Post limitado a contas/equipe internas. Além disso, cliente não auditado publica apenas em modo privado; publicar publicamente exige auditoria e UX com seleção/consentimento pelo criador. Por isso, o plano não propõe construir uma app privada direta para TikTok.
- **Instagram Stories:** a API permite publicar mídia, mas stickers/enquetes, links e interações podem não ser suportados pela API/publicador. Stories com esses elementos devem gerar notificação para finalizar manualmente. Sem stickers, frames simples podem ser automatizados.
- **Música/áudio:** áudio em tendência pode não estar disponível para publicação por API ou uso comercial. Use narração e trilha licenciada/original; valide as opções de áudio do publicador.
- **Rótulos de IA:** Meta possui `is_ai_generated` e TikTok `is_aigc` em endpoints de conteúdo. Confirme se o publicador expõe esses controles. Se não expuser, faça uma verificação manual e aplique o rótulo exigido pelo app antes de publicar.
- **Plataformas mudam:** formatos, limites, permissões e requisitos de contas podem mudar. Execute uma publicação de teste para cada rede/formato e consulte as limitações atuais do publicador.
- **Conteúdo financeiro:** faça revisão humana de taxas, datas, fontes, dados, riscos, conflito de interesse e linguagem de recomendação. Não publicar conselho individual de compra/venda nem promessas de retorno. O sinal de aprovação humana é obrigatório no desenho proposto.

## 6. Plano de implantação

| Fase | Entrega | Critério de conclusão |
|---|---|---|
| 0 — Preparação (1–2 dias) | Contas pro, Publer/Metricool, Drive/Sheet, chaves e servidor disponíveis | Publicação manual/teste funciona; chaves estão no cofre de credenciais |
| 1 — Saída automatizável (2–4 dias) | Langflow retorna JSON estável e salva rascunho/documento | Uma tese cria registros e campos editáveis sem publicar |
| 2 — Aprovação e imagens (2–4 dias) | n8n observa status, gera imagens aprovadas e guarda arquivos | Só status aprovado gera arquivos; IDs e erros ficam registrados |
| 3 — Renderização de vídeo (2–5 dias) | TTS + template vertical + legendas e exportação | Reel gerado, revisado, com áudio/licença e duração compatíveis |
| 4 — Agendamento (2–4 dias) | Integração do publicador, uploads, horários e confirmação | Teste de Instagram e TikTok agendado/publicado sem duplicatas |
| 5 — Piloto (2 semanas) | 2–4 campanhas em modo supervisionado | 10–20 posts sem erros críticos; só então remover revisão manual de mídia se desejado |

Os prazos são estimativas de planejamento para integração e testes; não incluem fila de aprovação de contas de terceiros nem produção de templates de marca.

## 7. Custos estimados

Valores em USD, salvo indicação. Estimativa para **8–13 teses/mês**, **11–14 assets visuais por tese** (aproximadamente 88–182 imagens) e 8–13 Reels. Não inclui impostos, variação cambial, desenvolvimento, música/licenças nem upgrades por mais canais. Preços podem mudar; confira os links antes de contratar.

| Item | Opção econômica | Opção conveniente | Observações |
|---|---:|---:|---|
| Langflow | US$ 0 licença | — | Software self-hosted; servidor e manutenção são custos separados |
| n8n | US$ 0 licença Community | €20/mês equivalente anual para n8n Cloud Starter | Self-hosted exige servidor e manutenção; Cloud Starter lista 2.500 execuções/mês |
| Servidor 24/7 | US$ 15–40/mês estimados | Incluído no n8n Cloud, mas não no Langflow se o flow continuar local | Faixa de orçamento para VPS simples; dimensionar se renderizar vídeo localmente |
| Publicador | Publer Business a partir de ~US$ 10/mês (API; preço depende de canais) | Metricool Advanced a partir de ~US$ 53/mês anual / ~US$ 67 mensal | Confirme preço, canais e auto-publish no checkout |
| GPT Image 2.5 Sunburst | ~US$ 5–20/mês estimados para o volume descrito | — | API cobra por tokens de entrada e saída, não por preço fixo por imagem; custo sobe com qualidade/tamanho/retries |
| Texto/pesquisa | ~US$ 1–5/mês estimados no modelo econômico | Mais se optar por modelo maior ou buscas pagas | Calcular com uso real por execução; `gpt-5.4-nano` tem desligamento anunciado para 2027-04-01 |
| Narração TTS | ~US$ 1–3 por uso leve, conforme caracteres/modelo | ElevenLabs Starter ~US$ 6/mês (US$ 5/mês equivalente anual) | Starter anuncia 30k créditos e licença comercial; verificar direitos de voz |
| Vídeo automático | US$ 0 de licença via FFmpeg | Creatomate Essential US$ 45/mês, 2.000 créditos | 30 s HD 720p ≈ 6,91 créditos; 50 créditos grátis servem para prévia, não produção full quality |
| Drive/Sheets | US$ 0 adicional com conta Google existente, dentro das quotas | Google Workspace Business Starter opcional | No Brasil, página oficial pode mostrar oferta e preço padrão por usuário; conferir preço final |

### Orçamento mensal orientativo

- **Automação econômica com FFmpeg:** cerca de **US$ 35–80/mês** (VPS + Publer/API + imagem, texto e TTS). Requer mais configuração/manutenção técnica.
- **Renderização gerenciada com Creatomate:** cerca de **US$ 80–125/mês** com o mesmo publicador e VPS; o plano inicial do renderizador pode ser maior que o volume necessário.
- **Trocando Publer por Metricool Advanced:** acrescente aproximadamente **US$ 43–57/mês**, conforme faturamento anual/mensal.
- **Workspace empresarial:** opcional; some a licença por usuário em reais. A API Sheets tem limites de uso e a tabela oficial deve ser consultada.

O custo variável de imagens deve ser limitado com teto mensal na OpenAI API e `quality=high` (não `max`) no início. Faça um lote de 10 imagens representativas, leia o `usage` retornado e substitua a faixa de planejamento pelo custo observado.

## 8. Recomendação final

**Começar com n8n Community self-hosted + VPS + Google Sheets/Drive + OpenAI Images + ElevenLabs + FFmpeg + Publer Business API.** É o equilíbrio de custo e automação para uma marca e 2–3 teses por semana. Se a manutenção do renderizador próprio não compensar, trocar FFmpeg por Creatomate; se valorizar aprovação e analytics prontos no calendário, avaliar Metricool Advanced.

Não habilite autopublicação no primeiro teste. Primeiro teste cada formato em rascunho, depois publique 2–4 campanhas supervisionadas. Após 10–20 posts corretos, deixe a aprovação de texto/prompts como a única barreira e permita que o restante — imagem, montagem, agendamento e publicação — rode sozinho. Preserve a opção de pausar/cancelar toda fila por um único estado no Sheets.

<!-- pagebreak -->

### Checklist de decisão antes de construir

- [ ] Confirmar que Instagram é Creator/Business e pode publicar via ferramenta escolhida.
- [ ] Confirmar que Publer Business API (ou Metricool Advanced API) auto-publica os formatos necessários em ambas as redes.
- [ ] Decidir se Reel terá voz sintética e qual voz tem licença comercial/consentimento.
- [ ] Escolher FFmpeg (custo baixo, manutenção maior) ou Creatomate (custo recorrente, template mais simples).
- [ ] Definir campos e estados do Google Sheet e quem pode aprovar.
- [ ] Hospedar Langflow/n8n em ambiente que permaneça online, com HTTPS, backups e alertas.
- [ ] Definir orçamento máximo para imagens, TTS e renderização; ativar alertas/limites.
- [ ] Validar disclosure de conteúdo sintético e revisão factual/financeira antes de autopublicar.

## 9. Fontes oficiais consultadas

- [Meta — Instagram Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing/)
- [Meta — Instagram Media Publish requirements](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media_publish)
- [Meta — Meta Business Suite (free)](https://www.facebook.com/business/help/205614130852988?id=916550222172854)
- [TikTok — Content Sharing Guidelines](https://developers.tiktok.com/docs/en/content-sharing-guidelines)
- [TikTok — Content Posting API, Direct Post](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post)
- [TikTok — Photo posting API](https://developers.tiktok.com/docs/en/content-posting-api-reference-photo-post)
- [Publer — Pricing](https://publer.io/pricing)
- [Publer — API overview](https://publer.com/docs/overview)
- [Publer — TikTok videos and photo posts](https://publer.com/docs/posting/create-posts/content-types/platform-specific-formats/tiktok-video-and-multi-photo-posts)
- [Metricool — API integration and scheduling](https://help.metricool.com/basic-guide-for-api-integration-r97af)
- [Metricool — Pricing](https://metricool.com/pricing/)
- [n8n — Pricing and self-hosted Community edition](https://n8n.io/pricing/)
- [n8n — Choosing Cloud vs. self-hosted](https://docs.n8n.io/choose-n8n/)
- [OpenAI — API pricing](https://developers.openai.com/api/docs/pricing)
- [OpenAI — Image generation guide/calculator](https://developers.openai.com/api/docs/guides/image-generation)
- [OpenAI — Model deprecations](https://developers.openai.com/api/docs/deprecations)
- [ElevenLabs — API pricing](https://elevenlabs.io/pricing/api)
- [Creatomate — Pricing](https://creatomate.com/pricing)
- [Creatomate — Render API](https://creatomate.com/docs/api/reference/create-a-render)
- [Google Workspace — pricing in Brazil](https://workspace.google.com/intl/pt-BR/business/)

**Observação:** links e valores consultados em 24/11/2026. Tarifas podem mudar e variam por região, plano, imposto, câmbio, tamanho/qualidade da imagem, duração/resolução do vídeo e quantidade de contas conectadas.
