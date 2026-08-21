# Esquema do `integrations.json`

Um por repositório, em `docs/architecture/integrations.json`. É o contrato entre as três
skills: `scan-integrations` escreve, `document-application` lê, `build-integration-map`
consolida.

Chaves em inglês, valores de texto livre em português.

```json
{
  "schema": 1,
  "app": {
    "id": "svc-cotacao",
    "name": "Serviço de Cotação",
    "type": "app",
    "subtype": "spring-boot",
    "repo": "https://dev.azure.com/org/projeto/_git/svc-cotacao",
    "owner": "ISS",
    "criticality": "high",
    "tech": ["Java 17", "Spring Boot 3.2", "Oracle 19c"],
    "envs": ["dev", "hml", "prd"],
    "detail": null,
    "scanned_at": "2026-08-10",
    "scanned_commit": "a1b2c3d"
  },
  "exposes": [
    { "kind": "rest", "route": "POST /cotacoes", "evidence": "CotacaoController.java:31" },
    { "kind": "soap", "route": "consultarCotacao", "evidence": "CotacaoWS.java:18" }
  ],
  "integrations": [
    {
      "target": "topic.cotacao-solicitada",
      "target_name": "cotacao-solicitada",
      "target_type": "topic",
      "target_detail": "12 partições · retenção 7d",
      "relation": "publishes",
      "endpoint": null,
      "protocol": "kafka",
      "contract": "avro CotacaoSolicitada v2",
      "criticality": "high",
      "timeout": null,
      "retry": null,
      "evidence": "src/main/java/br/com/x/CotacaoProducer.java:41",
      "confidence": "high",
      "note": "partition key = numeroProposta"
    }
  ],
  "unresolved": [
    {
      "hint": "${PARTNER_URL}",
      "where": "src/main/resources/application-prd.yml:12",
      "why": "variável não definida em nenhum arquivo do repositório"
    }
  ]
}
```

## Campos

Obrigatórios: `app.id`, `app.name`, `app.type`; e em cada integração `target`, `relation`,
`evidence`, `confidence`. O resto é opcional — omita em vez de preencher com `null` inventado.

`evidence` é uma string `caminho:linha`. Quando a prova estiver em dois arquivos (Java que
chama shell, config que guarda a URL usada em outro ponto), use a seta:
`"IntegracaoUtil.java:6 → scripts/envia_arquivo.sh:3"`.

`exposes[].kind` aceita `rest`, `soap`, `graphql`, `grpc`, `page` (tela JSP/JSF/SPA),
`servlet`, `topic` (quando a aplicação é o dono do contrato do tópico) e `cli`.

`criticality` na integração é a criticidade **daquela** integração. Para nós compartilhados
(tópico, banco, fila), a `build-integration-map` calcula a criticidade do nó como o maior
valor entre as integrações que chegam nele — um schema lido por três aplicações críticas é
crítico, mesmo que a primeira aresta encontrada fosse baixa. Não tente ajustar isso no scan.

`endpoint` é a URL, host ou caminho **verbatim**, exatamente como está no código ou na
configuração, sem a normalização de host que o `target` sofre. `target` é identidade;
`endpoint` é prova. É contra ele que a `build-integration-map` casa o catálogo de
ferramentas (`tools.yml`), por trecho de URL. Nunca grave credencial embutida:
`https://user:senha@host/x` vira `https://host/x`. Omita quando não houver URL literal —
variável não resolvida continua indo para `unresolved`.

`target_name`, `target_type` e `target_detail` descrevem o nó do outro lado. Você só precisa
preencher quando for um nó compartilhado (tópico, fila, banco, sistema externo); se o alvo é
outra aplicação que tem repositório próprio, basta o `target` com o nome do repositório — a
ficha dela descreve o resto.

## Valores válidos

**`type` / `target_type`** — define a faixa do nó no mapa:

| valor | faixa | uso |
|---|---|---|
| `frontend` | Entradas | portal, app web, SPA |
| `job` | Entradas | batch, cron, script de automação |
| `app` | Aplicações | serviço, EAR, WAR, microserviço |
| `topic` | Mensageria | tópico Kafka |
| `queue` | Mensageria | fila ou tópico JMS, RabbitMQ, bullmq |
| `database` | Dados | schema de banco |
| `cache` | Dados | Redis, Coherence, cache compartilhado |
| `external-api` | Externos | sistema fora do domínio da área |
| `file` | Externos | fluxo de arquivo, SFTP, diretório, planilha |
| `tool` | Ferramentas | ferramenta corporativa reconhecida pelo catálogo |

O `tool` normalmente **não é escrito pelo scan**: ele nasce na `build-integration-map`,
quando o `endpoint` de uma integração casa com uma entrada do `tools.yml`. Escreva
`target_type: tool` à mão só se a ferramenta for óbvia e você quiser garantir a faixa mesmo
sem catálogo.

**`relation`** — o gerador inverte `consumes` e `reads-file` para a seta apontar no sentido
do fluxo de dados, então declare sempre do ponto de vista da aplicação:

| valor | sentido no mapa | linha |
|---|---|---|
| `publishes` | app → tópico/fila | tracejada |
| `consumes` | tópico/fila → app | tracejada |
| `calls` | app → app/externo | sólida |
| `reads` | app → banco/cache | sólida |
| `writes` | app → banco/cache | sólida |
| `schedules` | job → app | sólida |
| `sends-file` | app → arquivo | tracejada |
| `reads-file` | arquivo → app | tracejada |

**`protocol`**: `rest`, `soap`, `kafka`, `jms`, `amqp`, `jdbc`, `sftp`, `file`, `grpc`,
`websocket`, `redis`.

**`criticality`** e **`confidence`**: `high`, `medium`, `low`.

## Convenção de id

O que faz duas aplicações apontarem para o mesmo nó em vez de criarem dois:

```
topic.<nome-do-topico>     queue.<nome-jndi>      db.<instancia>.<schema>
api.<sistema>              cache.<nome>           file.<nome-do-fluxo>
tool.<nome-da-ferramenta>  ← cadastrada no tools.yml da build-integration-map
<nome-do-repositorio>      ← para aplicação interna
```

Quando você só tem o hostname, normalize antes: primeiro rótulo do host, sem sufixo de
ambiente. `svc-cotacao.interno:8080` → `svc-cotacao`, e não `api.svc-cotacao.interno`. O
passo 4 do SKILL.md explica por que isso é o que mais estraga o mapa quando sai errado.

Ids são case-sensitive e devem ser estáveis entre execuções. Quando o mesmo sistema acabar
citado com nomes diferentes por equipes diferentes, não corrija os scans: registre no
`aliases.yml` da `build-integration-map`. Assim o scan continua fiel ao que está no código,
e a reconciliação fica num lugar só.

## Como o mapa codifica isso

| propriedade | aparência |
|---|---|
| `type` | cor da barra do nó e faixa horizontal |
| `criticality: high` no nó | contorno reforçado |
| protocolo/relação assíncrona | linha tracejada |
| `criticality: high` na integração | traço mais espesso |
| `confidence: low` | linha translúcida, marcada como "indício" no dossiê |
| várias integrações entre o mesmo par | uma linha só com contador |
