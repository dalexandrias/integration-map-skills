# Detecção — Node e Python

Node aparece em front-end e em aplicações novas. Python aparece principalmente em scripts de
automação. São perfis diferentes e merecem tratamento diferente.

## Índice

1. [Classificar antes de escanear](#1-classificar-antes-de-escanear)
2. [Node — front-end](#2-node--front-end)
3. [Node — serviço](#3-node--serviço)
4. [Python — script de automação](#4-python--script-de-automação)
5. [Python — serviço](#5-python--serviço)
6. [Variáveis de ambiente nas duas stacks](#6-variáveis-de-ambiente-nas-duas-stacks)

---

## 1. Classificar antes de escanear

| Sinal | `type` | `subtype` |
|---|---|---|
| `next.config.*`, `vite.config.*`, `angular.json`, pasta `public/` | `frontend` | `next`, `vite`, `angular` |
| `express`, `fastify`, `@nestjs/core` em `package.json` | `app` | `node-service` |
| `fastapi`, `flask`, `django` em `requirements`/`pyproject` | `app` | `fastapi`, `flask` |
| script Python solto, `if __name__ == "__main__"`, cron, sem servidor | `job` | `python-script` |
| só notebooks, `.ipynb` | não é aplicação | — |

A distinção que mais importa aqui é **script de automação × serviço**. Script de automação é
`type: job`, entra no mapa porque toca banco e arquivo de verdade, mas não merece ficha
completa depois. Serviço tem ciclo de vida, deploy e consumidor — merece.

---

## 2. Node — front-end

O front raramente fala com banco; ele fala com APIs. É isso que você procura.

- `fetch(`, `axios.create({ baseURL })`, `axios.get(`, `ky`, `got`
- Next.js: `app/api/**/route.ts` (isso é **backend** — vira `exposes`), `getServerSideProps`,
  Server Actions, `next.config.js` → `rewrites`/`proxy` (revela para onde o tráfego vai)
- Angular: classes `*.service.ts` com `HttpClient`
- `.env.example`, `NEXT_PUBLIC_*` → URLs de API, muitas vezes o único lugar onde o endpoint
  real aparece
- Proxy de desenvolvimento (`vite.config.ts` → `server.proxy`) costuma denunciar o backend
  de produção

Um front que chama três aplicações internas gera três integrações `calls` com `protocol: rest`.
Use o **nome do repositório** da aplicação de destino como `target` sempre que reconhecer;
quando só tiver a URL, use `api.<host>` e explique no `note` — o `aliases.yml` reconcilia depois.

Rotas de API do próprio Next vão em `exposes` com `kind: rest`.

---

## 3. Node — serviço

- Rotas expostas: `app.get(`, `router.post(`, `@Controller` + `@Get()` (Nest)
- Kafka: `kafkajs` → `producer.send({ topic })`, `consumer.subscribe({ topic })`, `groupId`
- AMQP/RabbitMQ: `amqplib`, `assertQueue`, `sendToQueue`, `consume`
- Banco: `oracledb`, `pg`, `mysql2`, `mongodb`, Prisma (`schema.prisma` → tabelas e
  ownership), TypeORM (`@Entity`), Knex
- Redis: `ioredis`, `redis` → se for cache compartilhado, vira nó
- Agendamento: `node-cron`, `bull`/`bullmq` (fila baseada em Redis — é fila de verdade,
  registre como `queue.`)
- HTTP externo: mesma lista do front

`schema.prisma` e as migrations do Prisma/TypeORM dizem de quais tabelas o serviço é dono —
mesma distinção de dono × leitura de terceiro que vale em Java.

---

## 4. Python — script de automação

Esse é o caso mais comum de Python aqui, e o que mais engana: parece pequeno e mexe em
produção.

- Banco: `oracledb`/`cx_Oracle`, `psycopg2`, `sqlalchemy.create_engine(`, `pyodbc`
- HTTP: `requests.get/post`, `httpx`
- SOAP: `zeep` → `Client(wsdl=)`
- Arquivo e SFTP: `paramiko`, `pysftp`, `ftplib`, `open(` com caminho de rede, `pandas.read_csv`
  de diretório compartilhado
- Planilha como fonte de dados: `openpyxl`, `pandas.read_excel` — **conta como integração**,
  `target: file.<nome>`, e vale marcar no `note` que a origem é planilha, porque é
  fragilidade conhecida
- Agendamento: `APScheduler`, crontab citado no README, Task Scheduler do Windows,
  `schedule`
- Celery: `broker_url` → o broker é fila; as tasks são jobs

Para script, `criticality` costuma ser `low`, **exceto** quando escreve em banco de produção
ou alimenta processo contábil/regulatório. Aí é `high` mesmo tendo 80 linhas. Se o script
escreve em produção, diga isso no `note` — é exatamente o tipo de coisa que ninguém sabe que
existe até parar.

---

## 5. Python — serviço

- FastAPI: `@app.get`, `APIRouter`, `include_router` → `exposes`
- Flask: `@app.route`
- Django: `urls.py`, `models.py` (ownership de tabela), `settings.py` (`DATABASES`, `CACHES`)
- Kafka: `confluent_kafka`, `kafka-python` (`KafkaConsumer`, `KafkaProducer`)
- Pydantic settings / `os.getenv(` → onde os endpoints moram

---

## 6. Variáveis de ambiente nas duas stacks

Em Node e Python o endpoint quase nunca está no código — está em variável. Ordem de busca:

1. `.env.example` (nunca leia `.env` real, e se ele estiver versionado, **avise**: é achado
   de segurança e vale mais que o mapa)
2. `docker-compose.yml`, `Dockerfile` (`ENV`)
3. Manifests do Kubernetes / `values*.yaml`
4. `azure-pipelines.yml` e variable groups referenciados
5. README

Se o valor não aparecer, registre a integração com o nome da variável em `note`, use
`confidence: medium`, e coloque o placeholder em `unresolved`. Nunca copie valor de segredo
para o JSON, mesmo que encontre — se encontrar segredo commitado, isso vira aviso para a
pessoa, não conteúdo do arquivo.
