# Detecção — Java (WebLogic, JEE, Spring Boot, MVC e camadas)

Cobre o core da empresa. Registre sempre `caminho/arquivo.ext:linha`.

## Índice

1. [Identificar o tipo de aplicação Java](#1-identificar-o-tipo-de-aplicação-java)
2. [Kafka](#2-kafka)
3. [JMS e filas WebLogic](#3-jms-e-filas-weblogic)
4. [Banco de dados](#4-banco-de-dados)
5. [REST consumido](#5-rest-consumido)
6. [SOAP e WSDL](#6-soap-e-wsdl)
7. [O que a aplicação expõe](#7-o-que-a-aplicação-expõe)
8. [Jobs e agendamento](#8-jobs-e-agendamento)
9. [Arquivos e SFTP](#9-arquivos-e-sftp)
10. [Cache](#10-cache)
11. [Deploy: WebLogic, Kubernetes, Azure Pipelines](#11-deploy-weblogic-kubernetes-azure-pipelines)
12. [Legado: onde a integração se esconde](#12-legado-onde-a-integração-se-esconde)

---

## 1. Identificar o tipo de aplicação Java

| Sinal | Conclusão | `subtype` |
|---|---|---|
| `application.xml`, `.ear`, `weblogic-application.xml` | EAR em WebLogic | `weblogic-ear` |
| `web.xml` + `weblogic.xml`, sem Spring Boot | WAR em WebLogic (MVC/camadas) | `weblogic-war` |
| `spring-boot-maven-plugin`, `@SpringBootApplication` | Spring Boot | `spring-boot` |
| `ejb-jar.xml`, `@Stateless`, `@MessageDriven` | EJB | `weblogic-ejb` |
| Só `pom.xml` com `packaging: jar` e sem main | biblioteca | `library` |

Biblioteca não é aplicação: não vira nó no mapa. Registre e avise a pessoa — o que interessa
é quem depende dela, e isso aparece pelo `pom.xml` dos outros.

Pegue a versão do Java em `maven.compiler.source`/`release`, no `Dockerfile` ou no
`azure-pipelines.yml`. Versão exata importa: é o que decide se uma correção é viável hoje.

---

## 2. Kafka

**Onde:** `application*.yml/properties`, classes `*Config`, `values*.yaml`, ConfigMaps.

- Produção: `KafkaTemplate`, `.send(`, `spring.kafka.producer.*`, `default-topic`
- Consumo: `@KafkaListener(topics=)`, `spring.kafka.consumer.group-id`, `containerFactory`
- Streams: `StreamsBuilder`, `.stream(`, `.to(`
- Nome do tópico costuma vir de constante ou enum — **siga até o literal**

Registre `contract` com o formato (avro/json/protobuf) e a versão do schema quando houver;
o `group-id` no `note`, porque é o que indica concorrência e reprocessamento. Se existir DLQ
(`.DLT`, `-dlq`, `-retry`), gere uma integração separada para ela.

`relation`: `publishes` ou `consumes`. `target`: `topic.<nome>`.

---

## 3. JMS e filas WebLogic

**Onde:** `weblogic-ejb-jar.xml`, `ejb-jar.xml`, `weblogic.xml`, `web.xml`, `*-jms.xml`.

- `@JmsListener(destination=)`, `MessageListener`, `onMessage(`
- MDB: `@MessageDriven` + `activationConfig` → `destinationLookup`
- Envio: `JmsTemplate.convertAndSend`, `send(`
- JNDI: `jms/`, `java:comp/env/jms/`, `resource-ref`, `message-destination-ref`
- `XAConnectionFactory` → transação distribuída, anote no `note`: muda o comportamento em
  falha e é a primeira coisa que se pergunta em incidente de mensagem duplicada

`target`: `queue.<nome-jndi>`. Se for tópico JMS e não fila, ainda use `queue.` como prefixo
e diga no `target_detail` que é tópico — o prefixo é convenção de id, não classificação.

---

## 4. Banco de dados

**Onde:** `application*.yml`, `persistence.xml`, `weblogic.xml`, `*-datasource.xml`,
`db/migration/`, `mappers/*.xml`, `*.sql`.

- `jdbc:oracle:thin:@`, TNS alias, wallet/`TNS_ADMIN` (ADW)
- Datasource por JNDI no WebLogic: `jdbc/NomeDS` — o host real está no domínio, não no
  repositório; registre o JNDI e mande para `unresolved`
- `@Entity`/`@Table`, `@SequenceGenerator`
- MyBatis `namespace=`, `<select>`, `<insert>` — SQL cru revela tabela de outro schema
- `JdbcTemplate`, `createNativeQuery`, e em legado: `Statement`, `PreparedStatement` com SQL
  concatenado dentro do DAO
- `CALL `, `{call `, `@Procedure` → **procedure é integração**, registre como tal
- Migrations (Flyway/Liquibase) → dizem de quais tabelas a aplicação é dona

**Distinção que importa:** tabela com migration = a aplicação é dona (`relation: writes`,
`criticality` conforme uso). Tabela de outro sistema lida direto = acoplamento escondido,
o mais perigoso do parque. Use `relation: reads` e deixe explícito no `contract`
("TB_X — schema de terceiro").

`target`: `db.<instancia>.<schema>`. As tabelas vão no `contract`, não viram nós.

---

## 5. REST consumido

- `@FeignClient(name=, url=)`
- `RestTemplate`, `WebClient.create(`, `.baseUrl(`, `.uri(`
- Legado: `HttpURLConnection`, `HttpClient` do Apache, `URL(...).openConnection()`
- Qualquer propriedade com `.url`, `.endpoint`, `.host`, `.base-path`
- Resiliência: `@CircuitBreaker`, Resilience4j, Hystrix, `@Retryable`

Preencha `timeout` e `retry` sempre que achar. São os dois campos que a sustentação procura
primeiro quando algo duplica ou trava, e quase nunca estão documentados.

`target`: `api.<sistema>` para sistema externo; o **nome do repositório** quando for
aplicação interna que você reconhece.

---

## 6. SOAP e WSDL

**Onde:** `*.wsdl`, `*.xsd`, `wsdlLocation`, `cxf-codegen-plugin`, `jaxws-maven-plugin`,
`generated-sources/`.

- `@WebServiceClient`, `@WebServiceRef`, `Service.create(`, `getPort(`
- `javax.xml.ws.service.endpoint.address`
- Handlers de WS-Security

Registre `contract` com a operação (`consultarTarifa`), não só o serviço. Se o WSDL é baixado
em tempo de build em vez de versionado, anote — é risco de build quebrado por indisponibilidade
de terceiro.

---

## 7. O que a aplicação expõe

`@RestController`, `@RequestMapping`, `@GetMapping`, `@Path` (JAX-RS), `servlet-mapping` no
`web.xml`, `@WebService` do lado servidor, `context-root` no `weblogic.xml`.

Isso vai no bloco `exposes`, não em `integrations` — daqui você não sabe quem chama. Mas é o
que permite a `build-integration-map` fechar a aresta quando outra aplicação chamar essa rota.

Em MVC legado, conte também as telas: `*.jsp`, `*.xhtml`, Struts `action`. Uma tela é
superfície exposta mesmo sem API.

---

## 8. Jobs e agendamento

- `@Scheduled(cron=)`, Quartz (`JobDetail`, `Trigger`, tabelas `QRTZ_*`)
- Spring Batch: `Job`, `Step`, `ItemReader/Writer`
- `CronJob` do Kubernetes
- Timer EJB: `@Schedule`, `TimerService`
- Agendador corporativo (Control-M e afins) citado em README ou nome de script

**Traduza o cron para linguagem humana** no `target_detail` ("todo dia às 3h05"). Ninguém lê
`5 3 * * *` em plantão. Se conseguir determinar idempotência pelo código, anote — job não
idempotente é o defeito mais caro de descobrir tarde.

---

## 9. Arquivos e SFTP

- `JSch`, `SftpSession`, `FTPClient`, `Files.copy`, `FileSystemResource`
- Spring Integration: `@InboundChannelAdapter`, `FileReadingMessageSource`
- Propriedades com `.path`, `.directory`, `/interface/`, `/entrada/`, `/saida/`
- Padrão de nome (`RET_*.txt`, `*_YYYYMMDD.csv`) → **o layout é o contrato**

`relation`: `reads-file` ou `sends-file`. `target`: `file.<nome-do-fluxo>`.

---

## 10. Cache

`@Cacheable`, `RedisTemplate`, `spring.redis.*`, Coherence, Ehcache, Infinispan, e sessão
replicada (`<session-descriptor>` no `weblogic.xml`).

Cache **compartilhado entre aplicações** vira nó `cache.<nome>`. Cache local em memória não
vira nó — no máximo uma linha em `note`.

---

## 11. Deploy: WebLogic, Kubernetes, Azure Pipelines

Não vira integração, mas alimenta `app.envs` e a ficha depois:

- **WebLogic:** managed server/cluster, `context-root`, `library-ref`, startup classes,
  datasources JNDI. Se o `config.xml` do domínio não está no repositório, mande para
  `unresolved` — é informação que só o time tem.
- **Kubernetes:** `env`/`envFrom` revelam endpoints que não estão no código; `Service` name
  mostra como outros pods chamam; `secretKeyRef` → **só o nome**.
- **Azure Pipelines:** `azure-pipelines.yml`, templates em `/templates`, variable groups
  (o nome do grupo é pista de onde a config real mora), `environment:` → ambientes reais.

---

URL que aparece em `.properties`, `.yml` ou constante: além de normalizar o host para o
`target`, grave o literal completo em `endpoint`. É o que permite o `tools.yml` reconhecer
barramento, cofre e observabilidade sem re-escanear os repositórios.

## 12. Legado: onde a integração se esconde

Em aplicação WebLogic antiga em MVC ou camadas, integração raramente está numa camada de
cliente bem definida. Procure também:

- **Dentro de JSP**: scriptlet com `DriverManager.getConnection` ou chamada HTTP
- **Servlet fazendo tudo**: `doPost` com SQL e chamada externa no mesmo método
- **Classe `Util`, `Helper`, `Facade`, `Integracao`, `Conector`** — nomes genéricos que
  concentram acesso externo
- **`.properties` na raiz ou em `WEB-INF/classes`** com URL e usuário de banco
- **Chamada por linha de comando**: `Runtime.exec`, `ProcessBuilder` chamando script shell
  que por sua vez chama outro sistema — integração real, invisível no código Java
- **Tabela usada como fila**: `SELECT ... FOR UPDATE` num loop com `status = 'PENDENTE'`.
  Registre como banco, mas anote no `note` que funciona como fila — muda completamente o
  raciocínio de quem for modernizar.

Quando o código estiver espalhado demais para ter certeza, prefira `confidence: low` com uma
`note` honesta a deixar de fora. Uma aresta marcada como indício convida alguém a confirmar;
uma aresta ausente não convida nada.
