# integration-map-skills

Três skills de agente que leem repositórios de aplicação, levantam as integrações com
evidência de código, escrevem a documentação técnica de cada uma e consolidam tudo num mapa
de integração interativo em HTML.

Feito para um parque grande e heterogêneo — Java em WebLogic, Spring Boot, Node e Python,
um repositório por aplicação, sem repositório central de arquitetura.

```
scan-integrations       1 repositório  →  docs/architecture/integrations.json
document-application    JSON + código  →  docs/architecture/<id>.md
build-integration-map   todos os JSON  →  graph.json + map.html
```

O que liga as três não é orquestração: é o **formato do `integrations.json`**. Cada fase lê
arquivo e escreve arquivo, sem estado em memória. Isso permite rodar, refazer ou substituir
qualquer uma sem tocar nas outras — e automatizar depois, quando quiser.

---

## Índice

- [Por que três skills e não uma](#por-que-três-skills-e-não-uma)
- [Ordem de execução](#ordem-de-execução)
- [O que é cada arquivo](#o-que-é-cada-arquivo)
- [Instalação](#instalação)
- [Os dois arquivos que você mantém à mão](#os-dois-arquivos-que-você-mantém-à-mão)
- [Regras que sustentam a confiabilidade](#regras-que-sustentam-a-confiabilidade)
- [Regressão com as fixtures](#regressão-com-as-fixtures)
- [Automatizar depois](#automatizar-depois)

---

## Por que três skills e não uma

O motivo não é organização, é **frequência e custo de execução**:

| | roda quantas vezes | custo | quando re-roda |
|---|---|---|---|
| `scan-integrations` | uma por repositório | baixo | quando o código muda |
| `document-application` | uma por repositório | alto (exige julgamento) | quando alguém revisa |
| `build-integration-map` | uma vez sobre tudo | baixo | sempre que quiser o mapa |

Numa skill única, você pagaria o custo caro da documentação toda vez que quisesse só
atualizar o mapa. Separadas, dá para escanear todas as aplicações e documentar só as que
importam — as demais continuam aparecendo no mapa, apenas sem ficha.

Custo real de separar: o agente não encadeia skills sozinho. Você invoca cada uma
explicitamente, ou monta o script que percorre os repositórios.

---

## Ordem de execução

### Uma vez, na instalação

**1.** Instale as três skills (veja [Instalação](#instalação)).

**2.** Crie a pasta de trabalho e liste os repositórios:

```bash
mkdir -p ~/integration-map && cd ~/integration-map
cat > repos.txt <<'EOF'
https://dev.azure.com/minha-org/meu-projeto/_git/svc-cotacao
https://dev.azure.com/minha-org/meu-projeto/_git/consulta-cobertura
EOF
```

**3.** Clone tudo:

```bash
~/.copilot/skills/build-integration-map/scripts/sync-repos.sh ~/repos repos.txt
```

### Por repositório

**4.** Abra o repositório no editor e peça: *"escaneia as integrações desse projeto"*
→ gera `docs/architecture/integrations.json`.

**5.** *"documenta essa aplicação"* → gera `docs/architecture/<id>.md`.
Comece só pelas críticas; esta é a fase cara.

### Uma vez, sobre tudo

**6.** Valide antes de gerar:

```bash
python ~/.copilot/skills/build-integration-map/scripts/build_graph.py ~/repos \
  --out ~/integration-map --aliases ~/integration-map/aliases.yml --check
```

**7.** Leia os avisos, ajuste o `aliases.yml`, rode de novo **sem** o `--check`.

**8.** Abra o `map.html` (duplo clique, não precisa de servidor).

### Depois

O ciclo vira **4 → 6 → 8**: re-escanear o que mudou, reconstruir, abrir. O passo 5 você roda
quando quiser.

### Antes de soltar nas 80

Rode 4 e 5 em **três aplicações de perfis diferentes** — um WebLogic legado, um Spring Boot e
um script Python — e revise os JSON com quem conhece os sistemas. É essa rodada que calibra
o que a skill trata como evidência suficiente no seu parque. Ajuste as referências e só
então escale.

---

## O que é cada arquivo

### `scan-integrations/`

| Arquivo | Para que serve |
|---|---|
| `SKILL.md` | A skill. Passo a passo do scan, regra de normalização de host, o que não fazer |
| `references/detect-java.md` | Onde procurar cada tipo de integração em Java: Kafka, JMS, JDBC, REST, SOAP, jobs, arquivos, WebLogic. Inclui a seção de **legado** — scriptlet de JSP, `Runtime.exec`, tabela usada como fila |
| `references/detect-node-python.md` | O mesmo para Node (front e serviço) e Python (script de automação e serviço) |
| `references/schema.md` | O contrato do `integrations.json`: campos, valores válidos, convenção de id. **É o documento central do conjunto** — as outras duas skills dependem dele |

### `document-application/`

| Arquivo | Para que serve |
|---|---|
| `SKILL.md` | A skill. Regra de origem obrigatória para regra de negócio, ordem por urgência de leitura |
| `references/doc-tiers.md` | Como dimensionar a ficha ao tamanho da aplicação: tabela de porte (mínima/padrão/completa) e blocos condicionais disparados pelo conteúdo do `integrations.json` |

### `build-integration-map/`

| Arquivo | Para que serve |
|---|---|
| `SKILL.md` | A skill. Comandos, como ler os avisos, o papel do `aliases.yml` |
| `scripts/build_graph.py` | Varre os `integrations.json`, funde nós compartilhados, valida, gera `graph.json` e injeta no `map.html`. Só biblioteca padrão (`pyyaml` opcional, só para o `aliases.yml`) |
| `scripts/sync-repos.sh` | Clona ou atualiza em lote os repositórios do `repos.txt`, usando o git já autenticado na máquina. Clone parcial e raso |
| `assets/map.html` | O visualizador — **modelo**. Arquivo único, HTML+CSS+JS puro, sem dependência externa além das fontes |

### `fixtures/`

Quatro repositórios de mentira usados para testar as skills, com as armadilhas reais de um
parque legado. Veja [Regressão](#regressão-com-as-fixtures).

---

## Instalação

Com um repositório por aplicação e sem repo central, instalar em `.github/skills/` de cada
um significaria abrir dezenas de pull requests para distribuir e outros tantos a cada ajuste.
Instale **no seu perfil**:

```bash
git clone <este-repositorio> ~/src/integration-map-skills
mkdir -p ~/.copilot/skills
ln -s ~/src/integration-map-skills/scan-integrations     ~/.copilot/skills/
ln -s ~/src/integration-map-skills/document-application  ~/.copilot/skills/
ln -s ~/src/integration-map-skills/build-integration-map ~/.copilot/skills/
```

Com link simbólico, `git pull` atualiza as skills sem precisar copiar nada de novo.

Confira com `/skills` no chat do editor.

As mesmas pastas funcionam em outros agentes: `~/.claude/skills/` no Claude Code,
`.agent/skills/` no Cursor e no Codex — o formato `SKILL.md` é o mesmo.

### Requisitos

- **Python 3.9+** para o `build_graph.py`
- **git autenticado** no seu provedor (Git Credential Manager ou PAT). O `sync-repos.sh`
  usa a sua credencial e não guarda token nenhum

---

## Os dois arquivos que você mantém à mão

Todo o resto é gerado e pode ser refeito sem medo. Estes dois carregam conhecimento que não
está em repositório nenhum:

**`repos.txt`** — a lista de repositórios. Uma URL por linha, `#` para comentário.

**`aliases.yml`** — reconciliação de identidade. É o mais valioso do conjunto. Quando o mesmo
sistema aparece com nomes diferentes em equipes diferentes, é aqui que você resolve — sem
mexer nos scans, que devem continuar fiéis ao que está no código:

```yaml
# id canônico: [outros nomes vistos pelos scans]
api.osb: [barramento, ESB_CORP, api.esb]
db.orcl-prd.SEGURO: [db.oracle.seguro, ORCL_SEGURO]
consulta-cobertura: [api.consulta-cobertura, svc-cobertura]
```

Ele cresce a cada rodada, alimentado pelos avisos do `build_graph.py`.

---

## Regras que sustentam a confiabilidade

Três decisões explicam quase todo o comportamento das skills. Vale entendê-las antes de
alterar qualquer coisa.

### 1. Toda integração precisa de evidência

`caminho/arquivo.ext:linha`. Sem prova, a integração entra com `confidence: low` e uma nota
honesta, ou vai para `unresolved` como pergunta objetiva para o time.

O motivo: numa dezena de aplicações uma aresta errada é um incômodo; em 80, alguém vai tomar
decisão em cima dela. Uma aresta faltando é visível — uma aresta errada não é.

### 2. Regra de negócio precisa de origem

Na ficha, toda regra afirmada vem com `arquivo:linha` ou marcada como *a confirmar*.
Aplicação legada tem regra espalhada entre JSP, servlet, DAO e procedure: é exatamente o
cenário em que um modelo escreve com confiança total uma regra que não existe.

Ficha com dez regras confirmadas e três marcadas a confirmar é útil. Ficha com treze
afirmadas, três delas erradas, é pior que ficha nenhuma — porque as pessoas confiam.

### 3. Identidade de nó é o trabalho de verdade

Gerar o grafo é o passo fácil. O que decide se o mapa presta é o mesmo sistema aparecer uma
vez só, e não três.

O erro mais caro é silencioso: um front que chama `http://svc-cotacao.interno:8080` gera
`api.svc-cotacao.interno`, enquanto o repositório `svc-cotacao` gera outro nó — e o mapa
passa a afirmar que **ninguém chama o svc-cotacao**. Parece certo e está errado.

Por isso há defesa em dois níveis: o scan normaliza o host antes de gravar (primeiro rótulo,
sem sufixo de ambiente) e, se ainda assim escapar, o `build_graph.py` funde `api.<host>` com
a aplicação de mesmo nome — sempre registrando o que fundiu, para você auditar.
`--no-auto-merge` desliga a fusão.

### O que esperar da primeira rodada

Feio. Muitos órfãos, aliases faltando, várias integrações com confiança baixa. Isso não é
falha do processo: é o inventário revelando o que ninguém tinha perguntado ainda sobre o
parque. O sinal de que está funcionando não é o mapa ficar bonito de primeira — é a lista de
avisos encolher a cada rodada.

---

## Regressão com as fixtures

`fixtures/` tem quatro repositórios de mentira, cada um com uma armadilha real:

| Fixture | O que exercita |
|---|---|
| `sinistro-legado` | WAR em WebLogic: SQL dentro de scriptlet de JSP, `Runtime.exec` chamando shell que faz SFTP, tabela usada como fila (`FOR UPDATE SKIP LOCKED`), leitura direta em schema de terceiro, datasource JNDI declarado e nunca usado, endpoint configurado sem referência no código |
| `svc-cotacao` | Spring Boot: tópico Kafka vindo de constante, Feign com URL em variável não resolvida, circuit breaker, migration Flyway, `@Scheduled` |
| `auto-conciliacao` | Python: script pequeno que grava em produção, planilha em file server como fonte de regra, SFTP, segredo só em variável de ambiente |
| `portal-campo` | Next: rewrite no `next.config.js` escondendo o destino, chamadas via `NEXT_PUBLIC_*`, rota de API própria |

Como usar depois de mexer nas skills:

```bash
python build-integration-map/scripts/build_graph.py fixtures --out /tmp/eval --check
```

Os `integrations.json` versionados nas fixtures são a saída esperada. Se você alterar uma
skill, rode o scan de novo sobre as fixtures e compare com o que está commitado — a
diferença mostra o efeito da sua mudança.

---

## Automatizar depois

Quando quiser o mapa se atualizando sozinho, o encaixe natural é:

1. agendador chama o `sync-repos.sh`;
2. para cada repositório cujo `HEAD` difere do `scanned_commit` do `integrations.json`,
   chama o agente em modo não interativo pedindo o scan;
3. `build_graph.py` no fim.

As skills já estão preparadas para isso: cada fase é um comando com entrada e saída em
arquivo. O `scanned_commit` existe exatamente para permitir o passo 2 — re-escanear só o que
mudou, em vez do parque inteiro.

---

## Estrutura dos artefatos gerados

```
~/repos/<cada-repositorio>/docs/architecture/
├── integrations.json      gerado — sobrescreva à vontade
└── <id>.md                ficha — contém edição humana, preserve

~/integration-map/
├── repos.txt              mantido à mão
├── aliases.yml            mantido à mão
├── graph.json             gerado
└── map.html               gerado, abre com duplo clique
```

Só dois arquivos são mantidos à mão. É isso que permite rodar de novo sem medo.
