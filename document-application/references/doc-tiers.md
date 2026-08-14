# Porte da ficha e blocos condicionais

Resolve o problema de "documentação engessada": em vez de um template fixo, o **conteúdo do
`integrations.json` decide quais seções existem**.

## 1. Escolher o porte

Some os sinais. O maior atingido vence.

| Sinal | Porte mínimo |
|---|---|
| até 3 integrações, `criticality: low`, sem job, sem mensageria | **Mínima** |
| 4 a 12 integrações, ou `criticality: medium` | **Padrão** |
| mais de 12 integrações | **Completa** |
| `criticality: high` | **Completa** |
| runtime legado (`weblogic-*`) | **Completa** |
| escreve em banco de produção que outra aplicação lê | **Completa** |
| processo contábil, regulatório ou financeiro | **Completa** |

Um script Python de 80 linhas que grava numa tabela lida pelo faturamento é **Completa**,
não Mínima. O que define o porte é o estrago, não o tamanho do código.

Diga no chat qual porte você escolheu e por quê. Se a pessoa discordar, ela troca — é uma
frase, não uma negociação.

## 2. Blocos

### Fixos — existem em qualquer porte

**Cabeçalho** — nome, uma linha do que faz, criticidade, dono, repositório, data da revisão.

**O que faz** — em linguagem de negócio, sem jargão de framework. Qual processo sustenta,
quem usa, o que deixa de acontecer no mundo real se parar. Mínima: um parágrafo. Completa:
dois ou três.

**Integrações** — tabela legível espelhando o `integrations.json`:

| Sistema | Direção | Protocolo | Contrato | Timeout / retry | Criticidade |
|---|---|---|---|---|---|

Nunca contradiga o JSON. Se você discordar dele, corrija o JSON re-executando o scan.

**Raio de impacto** — o que quebra se isso cair, e do que isso depende. Duas listas curtas.
Sai direto do mapa e é a pergunta que a gestão faz primeiro.

### Padrão — soma aos fixos

**Regras de negócio** — cada uma com `arquivo:linha` ou marcada como *a confirmar*. Esta é a
seção que justifica a ficha existir: é o conhecimento que não está em lugar nenhum.

**Sintomas e primeiras verificações** — tabela `sintoma → causa provável → o que fazer →
quando escalar`. Só o que você conseguir sustentar pelo código, log ou tratamento de erro
encontrado. Cinco linhas verdadeiras valem mais que quinze genéricas. Se não achar nada,
escreva "a levantar com o time" em vez de inventar.

**Onde olhar** — caminho de log, formato, índice, dashboard, métricas, alertas.

**Configuração** — tabela `variável | para que serve | onde o valor mora | obrigatória`.
Nunca o valor.

**Como rodar localmente** — pré-requisitos, comandos, o que precisa ser mockado.

### Completa — soma aos anteriores

**Arquitetura e stack** — versões exatas, padrão arquitetural, divisão do projeto. Em legado,
descreva o padrão real (servlet fazendo tudo), não o que deveria ser.

**Dados** — tabelas próprias (com migration) × tabelas de terceiros lidas direto; procedures
chamadas; volume e retenção; dados sensíveis presentes.

**Deploy e rollback** — pipeline, ordem de promoção, janela, aprovação, artefato, e o
**comando de rollback**. Rollback é procedimento de emergência: não pode ser improvisado.

**Riscos e débitos conhecidos** — versão sem suporte, dependência descontinuada, ponto único
de falha, gambiarra que ainda não pode sair, teste que não existe. Escreva sem eufemismo, é
documento interno.

**Decisões e histórico** — três a cinco linhas com data e motivo. Evita que a próxima pessoa
refaça a discussão e desfaça uma decisão consciente.

**Contatos** — time responsável, canal, e o dono de cada sistema externo integrado.

### Condicionais — só se o inventário mostrar o gatilho

| Gatilho no `integrations.json` | Bloco a incluir |
|---|---|
| algum `protocol: kafka` ou `jms` | **Mensageria** — tópicos, grupo de consumo, ordenação, DLQ, o que fazer com lag |
| algum nó `type: job` ou cron detectado | **Rotinas agendadas** — quando (em português), duração, idempotência, o que fazer se falhar ou rodar duas vezes |
| `protocol: sftp` ou `file` | **Arquivos** — diretório, padrão de nome, layout, periodicidade, tratamento de arquivo com erro |
| `relation: reads` em schema de terceiro | **Acoplamento de dados** — quais tabelas, de quem são, por que se lê direto, qual o risco |
| `protocol: soap` | **Contratos SOAP** — operações, WSDL versionado ou baixado em build, política de versão |
| `subtype: weblogic-*` | **Particularidades do WebLogic** — managed server, JNDI, libs compartilhadas, o que precisa existir no domínio |
| `unresolved` não vazio | **Pendências de configuração** — a lista, como perguntas objetivas |
| `confidence: low` em alguma integração | **Integrações a confirmar** — quais e por quê |

Se o gatilho não apareceu, o bloco não existe. Sem "N/A", sem seção vazia.

## 3. Formato

Markdown puro, títulos `##`, tabelas onde há estrutura repetida, prosa onde há raciocínio.
Sem front-matter: o `integrations.json` já carrega os metadados, e duplicar cria duas
verdades que divergem na primeira semana.

Comece o arquivo por um bloco de citação de três linhas — o que é, criticidade, dono, data
da revisão e **o commit do scan que originou a ficha** (`scanned_commit` do
`integrations.json`). Sem esse último dado ninguém consegue saber se a ficha está velha em
relação ao código, e uma ficha silenciosamente desatualizada é pior que uma ausente.

Quando o dono não for conhecido, escreva *a definir* e inclua a pergunta na lista de
pendências do fim — não invente time e não omita o campo. Em um parque de 80 aplicações,
"não se sabe quem cuida disto" é uma das informações mais acionáveis que a ficha pode
carregar.
