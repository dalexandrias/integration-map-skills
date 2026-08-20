---
name: build-integration-map
description: >-
  Consolida os integrations.json de todos os repositórios clonados numa pasta e gera o mapa
  de integração interativo em HTML — graph.json mais map.html, com faixas por camada
  arquitetural, filtros, busca e raio de impacto. Use sempre que pedirem para gerar,
  atualizar ou reconstruir o mapa de arquitetura, consolidar as integrações de vários
  repositórios, montar a visão macro de como as aplicações conversam entre si, ver o
  desenho de integração da área, ou responder quem consome um tópico e o que quebra se um
  serviço cair. Use também para clonar ou atualizar em lote os repositórios do Azure DevOps
  antes de escanear.
---

# build-integration-map

Roda **uma vez** sobre a pasta que contém todos os repositórios clonados. Não lê código —
lê os `integrations.json` que a `scan-integrations` já produziu.

```
~/repos/                                   ← raiz (você escolhe)
├── svc-cotacao/docs/architecture/integrations.json
├── svc-cotacao/docs/architecture/svc-cotacao.md
├── consulta-cobertura/docs/architecture/...
└── ... (×80)
```

## Comandos

```bash
# validar sem escrever nada
python scripts/build_graph.py ~/repos --check

# gerar o mapa
python scripts/build_graph.py ~/repos --out ~/integration-map

# com reconciliação de nomes
python scripts/build_graph.py ~/repos --out ~/integration-map --aliases ~/integration-map/aliases.yml
```

Saída: `graph.json` e `map.html` na pasta `--out`. O `map.html` abre com duplo clique, sem
servidor — os dados vão embutidos nele. Só depende da biblioteca padrão do Python; `pyyaml`
é opcional e só para o `aliases.yml`.

## Clonar e atualizar os repositórios

`scripts/sync-repos.sh` lê um `repos.txt` (um repositório por linha) e clona ou atualiza
todos. Usa o git já autenticado na máquina — não precisa de MCP nem de token no script.

```bash
./scripts/sync-repos.sh ~/repos repos.txt
```

Ele usa `--filter=blob:none --depth 1`: traz a árvore completa de arquivos e baixa o
conteúdo só do que for realmente aberto. Em 80 repositórios a diferença de tempo e disco é
grande, e para escanear é suficiente.

## O trabalho de verdade é a identidade dos nós

Gerar o grafo é o passo fácil. O que decide se o mapa presta é resolver quando o mesmo
sistema foi citado com nomes diferentes por equipes diferentes: `api.osb`, `barramento`,
`ESB_CORP`. Se não reconciliar, um sistema vira três nós e o mapa mente.

Não corrija os scans — eles devem continuar fiéis ao que está no código. Reconcilie em
`aliases.yml`, na pasta de saída:

```yaml
# id canônico: [outros nomes vistos pelos scans]
api.osb: [barramento, ESB_CORP, api.esb]
db.orcl-prd.SEGURO: [db.oracle.seguro, ORCL_SEGURO]
consulta-cobertura: [api.consulta-cobertura, svc-cobertura]
```

Esse arquivo é mantido à mão e cresce a cada rodada. É o único artefato do conjunto que
justifica edição manual, porque codifica conhecimento que não está em nenhum repositório.

## Passos

1. **Sincronizar** os repositórios (ou confirmar que a pasta está atualizada).
2. **Rodar com `--check`** primeiro. Ele não escreve nada e lista todos os avisos.
3. **Ler os avisos.** Eles são o produto tão quanto o mapa. Os que mais importam:
   - *nome X usado por A e B* → candidato a alias
   - *sem evidência* → o scan daquele repositório precisa ser refeito
   - *sem ficha markdown* → falta rodar `document-application` ali
   - *não tem nenhuma integração ligada* → nó órfão, geralmente id errado num scan
   - *não resolvido* → pergunta em aberto para o time
4. **Atualizar o `aliases.yml`** com o que os avisos revelaram e rodar de novo.
5. **Gerar** sem `--check`.
6. **Resumir no chat**: aplicações, nós, integrações por protocolo, quantas com confiança
   baixa, e as três a cinco pendências mais relevantes. Não repita a lista inteira de avisos
   — ela já está no painel lateral do mapa.

Espere que a primeira rodada saia feia: muitos órfãos e muitos aliases faltando. Isso é
normal e é justamente o valor — cada aviso é uma pergunta que ninguém tinha feito ainda
sobre o parque de 80 aplicações.

## O mapa

Faixas horizontais por camada — Entradas, Aplicações, Mensageria, Dados, Externos. A faixa
não é enfeite: é o que mantém 80 aplicações legíveis sem ninguém arrastar caixa. Dentro da
faixa, a ordem dos nós é calculada para reduzir cruzamentos (mediana dos vizinhos, guardando
a melhor ordenação encontrada), e o resultado é determinístico: mesmo `graph.json`, mesmo
desenho.

- clique num nó → ficha com entradas, saídas, evidência de cada integração e link do
  documento; a vista se desloca sozinha se o nó estiver atrás da ficha
- várias integrações entre o mesmo par viram uma linha com contador
- tracejado = assíncrono, traço grosso = crítico, pontilhado translúcido = indício
- filtros por tipo, criticidade e dono
- a busca lista as opções conforme você digita, dizendo **onde** cada uma casou — nome, id,
  dono, tecnologia, ou o protocolo/contrato de uma integração do nó. O que casaria mas está
  escondido pelo filtro atual aparece contado no rodapé da lista, com botão de limpar
- tema claro e escuro; exportação em PNG e SVG; impressão/PDF em paisagem
- `/` foca a busca, `↑` `↓` andam na lista e `Enter` abre; `0` ajusta, `Esc` limpa,
  `Tab` percorre os nós e `Enter` abre a ficha do nó focado

### As três perguntas do topo

Com um nó selecionado:

| Botão | Responde |
|---|---|
| **Quem quebra se cair** | o que para de funcionar se este nó cair |
| **Do que depende** | de quem este nó precisa para funcionar |
| **Caminho** | por onde o dado passa entre dois nós; clique na origem, ative, clique no destino |

As setas do mapa mostram o **fluxo de dados**. A falha não segue o mesmo sentido, e é por
isso que estes dois primeiros botões não são o mesmo botão invertido:

- **chamada síncrona** (`calls`, `reads`, `writes` — REST, SOAP, JDBC): quem quebra é quem
  chamou, **a montante da seta**. Se o `svc-cotacao` cai, quem para é o `portal-campo`.
- **assíncrono** (`publishes`, `consumes`, `sends-file`, `reads-file` — Kafka, JMS, SFTP):
  quem seca é o consumidor, **a jusante**. E não quebra na hora: a fila segura um tempo.

Cada salto vem marcado como **imediato** ou **degrada** por esse motivo — a diferença muda
decisão de plantão.

Quando o `Caminho` não acha rota seguindo o fluxo de dados, ele tenta ignorando a direção
das setas e avisa que fez isso. Não achar caminho nenhum pode ser real ou pode ser aresta
que ninguém escaneou ainda; a ficha diz isso em vez de deixar você concluir sozinho.

O `map.html` em `assets/` é o modelo. Não edite o `map.html` gerado na pasta de saída — ele
é sobrescrito. Mudança de visual vai no modelo. Arquivo único, sem nenhuma dependência
externa — nem fontes: abre por `file://` em máquina sem internet, e é isso que também
permite exportar PNG sem contaminar o canvas.

## Referências

- Esquema do `integrations.json`: veja `references/schema.md` da skill `scan-integrations`.
- Para adicionar um tipo de nó novo: acrescente em `TYPES` no `assets/map.html`, crie o
  token `--t-<tipo>` nas duas paletas (clara e escura) e registre em `LANES` no
  `scripts/build_graph.py`. Antes disso, confirme que não é só um `subtype` de um tipo
  existente — poucos tipos bem escolhidos é o que mantém o mapa legível.
- Para mudar como uma relação propaga falha, mexa em `SYNC_REL`/`ASYNC_REL` no
  `assets/map.html`: é de lá que saem os dois modos de impacto.
