---
name: document-application
description: >-
  Escreve a ficha técnica de UMA aplicação em Markdown — o que ela faz em linguagem de
  negócio, as regras de negócio que estão no código, runbook de plantão, configuração,
  deploy e riscos conhecidos — dimensionando o tamanho da ficha ao tamanho da aplicação.
  Use sempre que pedirem para documentar uma aplicação, escrever ou atualizar a
  documentação técnica de um projeto, explicar o que um sistema faz e quais são suas regras
  de negócio, criar ficha de sustentação, README de arquitetura ou runbook. Use também
  quando não usarem a palavra "documentação" — pedidos como "me explica o que essa
  aplicação faz", "levanta as regras de negócio desse sistema" ou "escreve a ficha desse
  repo" devem disparar esta skill. Lê o docs/architecture/integrations.json quando existir.
---

# document-application

Escreve `docs/architecture/<id-da-aplicação>.md`. O `id` é o mesmo do `integrations.json`,
para que a `build-integration-map` ligue a ficha ao nó do mapa.

## Comece lendo o inventário

Se existir `docs/architecture/integrations.json`, **leia primeiro**. Ele já tem as
integrações com evidência, a stack e as versões — não refaça esse trabalho, e não contradiga
o que está lá. A ficha referencia; o JSON é a fonte.

Se não existir, avise a pessoa que rodar `scan-integrations` antes deixa a ficha bem melhor,
e siga assim mesmo se ela preferir.

## A regra mais importante: regra de negócio precisa de origem

Aplicação legada em WebLogic tem regra espalhada entre JSP, servlet, DAO e procedure. É
exatamente o cenário onde um modelo escreve com confiança total uma regra que não existe.

Para cada regra de negócio afirmada, uma das duas coisas:

- **Confirmada** — cite `arquivo:linha`. Exemplo:
  `Proposta acima de R$ 50 mil exige aprovação manual (CotacaoService.java:214).`
- **Inferida** — marque explicitamente:
  `> ⚠️ A confirmar: parece haver carência de 30 dias para cobertura X, mas a regra só
  > aparece num literal em CoberturaDAO.java:88 sem contexto.`

Nunca escreva regra sem uma das duas marcas. Uma ficha com dez regras confirmadas e três
marcadas a confirmar é útil. Uma ficha com treze regras afirmadas, três delas erradas, é
pior que ficha nenhuma — porque as pessoas vão confiar.

O mesmo vale para o propósito da aplicação: se o código não deixa claro o que ela resolve no
negócio, escreva o que dá para afirmar e liste a pergunta em aberto no fim. Não preencha
lacuna com plausibilidade.

## Dimensione a ficha à aplicação

Não existe ficha padrão. Um script Python de conciliação com 80 linhas e um EAR de 2011 com
40 integrações não pedem o mesmo documento — e formulário com seção vazia ensina o time a
não ler documentação.

Leia `references/doc-tiers.md`: ele traz a tabela de decisão do porte, quais blocos são fixos,
e quais blocos só existem quando o inventário mostrou o gatilho (só tem seção de mensageria
se houver Kafka ou JMS; só tem seção de rotinas se houver job).

Regra geral: **seção sem conteúdo real não entra**. Melhor uma ficha de 30 linhas verdadeira
que uma de 300 com "N/A" em metade.

## Ordem: urgência, não hierarquia

Quem abre a ficha às 2h da manhã lê de cima para baixo e para quando resolveu. Então o topo
é sempre o que serve em incidente — o que a aplicação faz, sintomas comuns, onde estão os
logs, o que quebra se ela cair. Arquitetura, deploy e débito técnico vêm depois. O critério
de inclusão de qualquer seção é o mesmo:

> Isso ajuda alguém a **operar** ou a **mudar** esta aplicação com segurança?

Se não ajuda nenhum dos dois, fica de fora. Explicação genérica de tecnologia ("o que é
Kafka"), Javadoc em prosa, print de tela e roadmap não entram.

## Nunca entram na ficha

- Valor de segredo, senha, token, string de conexão completa. Nome da variável e onde o
  valor mora, só.
- Dado real de cliente, mesmo em exemplo.
- Regra de negócio sem origem (ver acima).

## Ao terminar

Diga no chat, em texto curto:

- que porte você escolheu e por quê;
- as regras marcadas como "a confirmar", como lista de perguntas para o time;
- o que você não conseguiu determinar (dono, janela de deploy, contato do sistema externo).

Essa lista é o que faz a ficha melhorar na segunda passada. Sem ela, a documentação nasce
congelada.

## Atualizando uma ficha existente

Preserve o que foi escrito ou corrigido por humano — runbook, contatos, histórico de
decisão, avisos. Esse conteúdo não está no código e é o mais valioso do arquivo. Atualize as
seções derivadas do código, ajuste a data, e liste no chat o que você mudou.
