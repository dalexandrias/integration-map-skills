# Changelog

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
