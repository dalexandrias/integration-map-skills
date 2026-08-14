---
name: scan-integrations
description: >-
  Lê UM repositório de aplicação e levanta todas as integrações dela — chamadas REST e SOAP,
  tópicos Kafka, filas JMS, bancos e schemas, procedures, caches, jobs agendados, arquivos e
  SFTP — gravando tudo em docs/architecture/integrations.json com evidência de arquivo e linha.
  Use sempre que pedirem para levantar, mapear, escanear ou descobrir as integrações e
  dependências de uma aplicação, entender com o que este projeto conversa, listar os endpoints
  que ele consome ou expõe, ou preparar os dados do mapa de arquitetura. Use também quando a
  pessoa não usar a palavra "integração" — pedidos como "o que esse sistema chama", "de que
  esse projeto depende", "quais tabelas ele acessa" ou "escaneia esse repo" devem disparar
  esta skill. Funciona com Java em WebLogic, Spring Boot, Node e Python.
---

# scan-integrations

Levanta a superfície de integração de **uma** aplicação. Não escreve documentação em prosa
— isso é da `document-application`. Não desenha o mapa — isso é da `build-integration-map`.

A saída é sempre `docs/architecture/integrations.json`, no formato de `references/schema.md`.

## Regra que define a qualidade do resultado

**Toda integração precisa de evidência: `caminho/arquivo.ext:linha`.**

Se você suspeita de uma integração mas não achou a prova, existem duas saídas legítimas:

- achou o código mas não o valor (ex.: `${PARTNER_URL}`) → registre com `confidence: medium`
  e coloque o placeholder em `unresolved`;
- só há indício circunstancial (nome de classe, comentário, nome de fila) → registre com
  `confidence: low` e explique em `note`.

O que não é aceitável é escrever uma integração como se fosse fato. Este arquivo vai virar
o mapa de 80 aplicações; uma aresta errada custa mais caro que uma aresta faltando, porque
alguém vai tomar decisão em cima dela.

## Passos

### 1. Identificar a aplicação

Descubra o que é o projeto antes de sair procurando padrão. Marcadores de raiz: `pom.xml`,
`build.gradle`, `package.json`, `pyproject.toml`, `requirements.txt`, `*.csproj`,
`Dockerfile`, `Chart.yaml`, `application.xml` (EAR).

Preencha o bloco `app`: `id` (slug estável, use o nome do repositório), `name`, `type`,
`subtype` (`spring-boot`, `weblogic-ear`, `next`, `python-script`…), `owner`, `criticality`,
`tech` com **versões**.

Preencha também `scanned_commit` com `git rev-parse --short HEAD`. É o que permite saber
depois se o inventário está velho em relação ao código, e o que torna possível re-escanear
só o que mudou em vez dos 80 repositórios.

Para o `owner`, procure nesta ordem: `CODEOWNERS`, pipeline (`azure-pipelines.yml` costuma
citar variable group ou service connection do time), README, e nome do projeto no Azure
DevOps. Se nada disso resolver, **pergunte à pessoa** em vez de deixar `null` — dono é o
campo que permite fatiar um parque de 80 aplicações, e é a única informação da ficha que o
código nunca vai dar.

Em multi-módulo Maven, a aplicação é o módulo empacotado como `war`/`ear`, não o pom pai.
Se o repositório contiver duas aplicações de verdade, gere dois blocos — mas confirme com a
pessoa antes, porque isso é raro e costuma ser módulo mal interpretado.

### 2. Ler o guia da stack certa

- **Java** (WebLogic, JEE, Spring Boot, MVC e camadas): `references/detect-java.md`
- **Node e Python**: `references/detect-node-python.md`

Leia o que se aplica. Um repositório Node com script Python de deploy usa os dois.

### 3. Resolver os placeholders antes de desistir

Valor como `${KAFKA_TOPIC}` não é resposta. Persiga nesta ordem: perfis de configuração do
próprio projeto (`application-prd.yml`, `.env.example`, `values-prd.yaml`) → manifests do
Kubernetes → pipeline (`azure-pipelines.yml`) → README. Só depois disso registre em
`unresolved`, com a pergunta pronta para um humano responder.

### 4. Escrever o JSON

Grave em `docs/architecture/integrations.json`. Formato completo em `references/schema.md`.

Convenção de id dos nós compartilhados — **isso é o que faz o mapa fechar**, porque duas
aplicações que citam o mesmo Kafka precisam gerar o mesmo id:

```
topic.<nome-do-topico>      queue.<nome-jndi>       db.<instancia>.<schema>
api.<sistema>               cache.<nome>            file.<nome-do-fluxo>
```

Para aplicações internas, o id é o **nome do repositório** — e aqui está o erro que mais
estraga o mapa. Escaneando um repositório isolado você quase nunca sabe o nome do
repositório do outro lado: você só tem `http://svc-cotacao.interno:8080`. Se registrar
`api.svc-cotacao.interno`, o mapa vai criar um nó separado e passar a afirmar que **ninguém
chama o svc-cotacao** — errado, e silencioso, que é o pior tipo de erro aqui.

Então normalize o host antes de escrever o `target`:

1. pegue o **primeiro rótulo** do host: `svc-cotacao.interno:8080` → `svc-cotacao`
2. remova sufixo de ambiente quando existir: `svc-cotacao-prd`, `-hml`, `-dev` → `svc-cotacao`
3. se o resultado parece nome de aplicação da casa, use-o direto como `target`, com
   `target_type: app`, e guarde o host completo em `note`
4. se parece sistema de terceiro (domínio externo, nome comercial), aí sim `api.<sistema>`
   com `target_type: external-api`

```
http://svc-cotacao.interno:8080/cotacoes   → target: svc-cotacao          (app)
${COBERTURA_URL} = consulta-cobertura.interno → target: consulta-cobertura  (app)
https://api.serasa.com.br/v2/score          → target: api.serasa           (external-api)
```

Na dúvida entre os dois, prefira tratar como aplicação interna: a `build-integration-map`
avisa quando um `api.<host>` bate com uma aplicação conhecida e funde os dois, mas ela não
tem como adivinhar o contrário. Errar para o lado de "interno" é reversível; errar para o
lado de "externo" cria um nó órfão que ninguém percebe.

### 4.1 Três casos que aparecem o tempo todo e confundem

**Granularidade de banco.** Uma integração por par (schema, relação) — não uma por tabela.
As tabelas se acumulam no `contract`. Ler e escrever no mesmo schema são duas entradas, uma
`reads` e uma `writes`, porque a diferença entre ser dono e ser leitor de terceiro é a
informação mais útil do inventário.

**Endpoint configurado que ninguém chama.** Achou `url.osb` no `.properties` mas nenhuma
referência a ele no código? Registre com `confidence: low` e `note: "configurado mas sem
referência no código — possível integração morta"`. Não omita: em legado isso é comum, e
descobrir que a config sobrou é tão útil quanto descobrir a chamada. Remover é decisão do
time, não sua.

**Evidência espalhada em dois arquivos.** Java chamando shell que faz o SFTP, config que
guarda a URL usada em outro ponto. Use a seta no próprio campo:
`evidence: "IntegracaoUtil.java:6 → scripts/envia_arquivo.sh:3"`. Uma linha só, os dois
pontos rastreáveis.

### 5. Fechar com o resumo

Em texto, no chat, não no arquivo:

- quantas integrações por protocolo;
- o que ficou em `confidence: low` e por quê;
- o que ficou em `unresolved`, como perguntas objetivas ("qual o valor de `PARTNER_URL` em
  produção?") — pergunta específica um colega responde em um minuto, "me explica as
  integrações" ninguém responde nunca.

## Quando re-executar

O `integrations.json` é gerado, pode ser sobrescrito à vontade. Re-escaneie quando o código
mudar. Não edite à mão: edição manual é perdida no próximo scan, e o certo é corrigir a
detecção nas referências desta skill.

## O que NÃO fazer aqui

- Não escreva regra de negócio nem responsabilidade da aplicação. Outra skill.
- Não invente `criticality` — se não houver sinal, use `medium` e diga que é chute.
- Não copie segredo, string de conexão completa, token ou senha para o JSON. Nome da
  variável e onde ela mora, só.
