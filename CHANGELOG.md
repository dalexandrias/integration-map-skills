# Changelog

## 0.3.2

- **Setas soltavam das caixas ao arrastar um nó.** O traçado era escolhido por `lane`/`row`,
  e o ramo de "mesma faixa" ancorava **as duas pontas** na altura do nó de origem — verdade
  só logo depois do layout. Arrastar muda `x` e `y` e não toca em `lane`/`row`, então a ponta
  no destino continuava desenhada na altura da origem e a seta ficava pairando no vazio: uma
  medição registrou 258 px de descolamento. Como só pares dentro da mesma faixa caíam nesse
  ramo — e num parque real quase todo par mesma-faixa é aplicação→aplicação — era a fileira
  de aplicações que soltava as setas, enquanto as arestas que cruzam faixas seguiam certas.
  O grafo de exemplo embutido no `map.html` não tem nenhuma aresta dentro da mesma faixa, e
  por isso o defeito não aparecia com os nós de teste. `pathOf` passa a decidir pela distância
  vertical real e a ancorar cada ponta no seu próprio nó. Num layout recém-calculado o desenho
  é byte a byte o mesmo de antes — verificado sobre 657 arestas em dois grafos.
- **Curva estufando por cima da caixa de origem.** Com dois nós arrastados para perto na
  vertical, o deslocamento de canal ficava maior que o vão e jogava os pontos de controle
  para trás do início. Agora o canal é limitado pelo tamanho do vão, sem efeito no layout
  normal.
- **Arrastar selecionava o texto do rótulo**, deixando rastro azul sobre o desenho. A
  seleção foi desligada só dentro do SVG; o texto da ficha continua copiável.

## 0.3.1

Correções vindas do uso do mapa novo:

- **Cursor de mão sobre a ficha.** O palco declara `cursor:grab` porque o fundo é
  arrastável, e a ficha, o HUD, o banner, a tooltip e o estado vazio são HTML sobreposto
  dentro dele — todos herdavam a mãozinha. Ler a ficha, rolar o painel ou selecionar um
  trecho de evidência tinha cara de arrasto. Os sobrepostos passam a declarar cursor próprio.
- **A busca agora lista as opções enquanto você digita**, e diz **onde** cada uma casou.
  Antes ela só acendia nós no canvas e mostrava um número: quem buscava `kafka` via "2" e
  precisava caçar visualmente o que tinha acendido. A lista ordena por relevância — nome
  exato, prefixo, trecho do nome, id, campos do nó e, por último, protocolo ou contrato de
  uma integração — e etiqueta o motivo quando não foi o nome, porque num mapa de integração
  o nó costuma aparecer pelo contrato de uma aresta. `↑` `↓` andam na lista, `Enter` abre.
- **O que casaria mas está escondido pelo filtro** aparece contado no rodapé da lista, com
  botão de limpar. Antes esses resultados sumiam sem explicação e a busca parecia quebrada.
- **Botão de limpar próprio** no lugar do `::-webkit-search-cancel-button`, que não segue o
  tema nem tem estado de foco. O campo deixou de ser `type=search`: o controle nativo já
  estava escondido e o `Esc` nativo limpava o campo antes de a lista fechar.
- **`[hidden]` não escondia o botão de limpar.** A regra do navegador perde para um
  `display` declarado pelo autor, então o botão aparecia mesmo com o campo vazio.
- **Bytes NUL no template.** Três separadores de chave ficaram como caractere NUL literal em
  vez do escape `\u0000`. Não quebrava o navegador, mas `file` classificava o `map.html` —
  o modelo e todo mapa gerado — como `data` em vez de HTML, `grep` se recusava a imprimir as
  linhas encontradas, e qualquer ferramenta que normalize texto poderia corromper o arquivo.

## 0.3.0

Reescrita do visualizador. A avaliação anterior cobriu a qualidade dos dados; esta rodada
cobriu o artefato que as pessoas de fato abrem — e ele estava quebrado no caminho principal:

- **Clicar num nó não abria nada.** O `pointerdown` capturava o ponteiro no palco, e a
  especificação manda redirecionar os eventos seguintes para o elemento que capturou. O
  `pointerup` então relia `e.target`, achava o palco em vez do nó e caía no ramo que
  *limpa* a seleção. Resultado: a ficha — entradas, saídas, evidência, link do documento,
  a razão de o mapa existir — era inalcançável por clique, e todo clique apagava o que
  estivesse selecionado. O alvo agora é lido uma vez, no `pointerdown`, e guardado. A mesma
  armadilha engolia os cliques dos controles sobrepostos ao palco (zoom, estado vazio,
  links de navegação da própria ficha); o palco passou a só reagir ao que nasce dentro do SVG.
- **O raio de impacto respondia a pergunta errada.** Ele seguia as setas, que mostram fluxo
  de dados. Numa chamada síncrona a falha sobe *contra* a seta: se o serviço cai, quem para
  é quem chamou. O mapa afirmava o contrário com aparência de resposta certa. Agora há um
  grafo de falha derivado por tipo de relação, dois modos explícitos — *quem quebra se cair*
  e *do que depende* — e cada salto marcado como **imediato** ou **degrada**, porque fila e
  arquivo seguram um tempo antes de faltar dado.
- **Layout por camadas com redução de cruzamentos**, no lugar do laço de força em X. Sobre
  um grafo de 400 nós e 643 integrações: comprimento médio de aresta caiu de 3.253 px para
  1.311 px (−60%) e a área de 7.469×3.024 para 3.052×2.388 — proporção que cabe numa tela em
  vez de um fio horizontal. Determinístico: mesmo `graph.json`, mesmo desenho.
- **Redesenho incremental.** O arrasto de um nó reconstruía faixas, arestas e nós inteiros
  por `innerHTML`, a cada evento de movimento. Agora o DOM é montado uma vez e o arrasto move
  um atributo. Primeiro desenho de 13,6 s para 0,7 s; arrasto de 122 ms para 48 ms por passo.
- **Zero dependência externa, agora inclusive fontes.** O modelo baixava IBM Plex do Google
  Fonts — numa máquina sem internet isso é espera e depois fonte trocada, com a largura das
  caixas estimada por contagem de caracteres estourando o texto. Pilha do sistema, largura
  medida de verdade, e o canvas de exportação deixa de ser contaminado por recurso remoto.
- **Caminho entre dois nós.** Origem, destino, e as rotas mínimas destacadas com protocolo e
  contrato de cada salto. Sem rota no sentido do fluxo, tenta sem direção e avisa; sem
  caminho nenhum, diz que pode ser aresta ainda não escaneada em vez de deixar concluir.
- **Exportar PNG e SVG, e imprimir.** O SVG sai com o próprio CSS e a paleta clara embutidos,
  independente do tema da tela. A impressão enquadra o grafo inteiro em paisagem, com título
  e data.
- **Tema claro e escuro**, respeitando a preferência do sistema, com alternador que persiste.
- **Filtro que mentia.** Ao recarregar um grafo, as caixas voltavam marcadas mas o estado
  interno do filtro não; nó marcado ficava invisível. Filtro zerado agora tem estado vazio
  com botão de limpar, em vez de tela em branco sem explicação.
- **Teclado e leitor de tela.** Nós focáveis com rótulo, `Tab` para percorrer, setas entre
  vizinhos, `Enter` abre a ficha. Antes o `role="img"` escondia o grafo inteiro e não havia
  como operar o mapa sem mouse.
- **Busca mais larga** — id, dono, subtipo, tecnologia, protocolo e contrato, com contagem de
  resultados e `Enter` percorrendo e centralizando cada um.
- **`</script>` num campo de evidência derrubava a página.** O `build_graph.py` injetava o
  JSON cru no HTML; agora escapa `<`, `>` e U+2028/2029 no bloco embutido. O `graph.json`
  em disco continua JSON limpo.
- **`aplicações` no resumo contava fichas**, não aplicações. Passaram a ser duas métricas.

## 0.2.0

Rodada de avaliação contra quatro repositórios de teste (WebLogic legado, Spring Boot,
Python de automação, Next). Correções vindas do que a avaliação expôs:

- **Identidade de nó por hostname.** Um front que chamava `http://svc-cotacao.interno:8080`
  gerava um nó separado da aplicação `svc-cotacao`, e o mapa afirmava que ninguém a chamava —
  erro silencioso. Corrigido em dois níveis: regra de normalização de host no
  `scan-integrations` e fusão automática auditável no `build_graph.py` (`--no-auto-merge`
  desliga).
- **Criticidade de nó compartilhado.** Vinha da primeira aresta encontrada; agora é o maior
  valor entre as integrações que chegam no nó.
- **Aviso de aplicação não escaneada.** Aplicação citada por outra mas sem scan próprio agora
  aparece nos avisos — é a fila de trabalho do próximo ciclo.
- **`scanned_commit`.** Passo do scan agora pede o commit, viabilizando re-scan incremental.
- **Descoberta de dono.** Ordem de busca (CODEOWNERS → pipeline → README) e, falhando,
  perguntar em vez de gravar nulo.
- **Granularidade de banco.** Uma integração por par (schema, relação); tabelas no `contract`.
- **Endpoint configurado sem uso.** Registrado com `confidence: low` em vez de omitido.
- **Evidência em dois arquivos.** Formato com seta: `A.java:6 → script.sh:3`.

## 0.1.0

Versão inicial: skill única de mapeamento e documentação.
