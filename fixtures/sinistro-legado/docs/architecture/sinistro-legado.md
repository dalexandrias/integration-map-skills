> **Sinistro (legado)** — consulta e encaminhamento de sinistros de apólice.
> Criticidade **alta** · Dono: *a definir* · Revisão: 2026-08-11 · Scan: 2026-08-11

## O que faz

Atende a consulta de sinistros pela tela `/sinistro/consulta.jsp` e pelo endpoint
`POST /sinistro/consultar`, cruzando os dados do sinistro com a apólice e as coberturas.
Quando o valor informado ultrapassa o limite de alçada, marca o caso para análise manual em
vez de seguir o fluxo automático.

Também consome retornos do parceiro por fila JMS e envia a remessa diária ao banco
conveniado. Se parar, a consulta de sinistro pela rede de atendimento para, e a remessa
diária deixa de subir.

## Regras de negócio

- Sinistro com valor acima de R$ 50.000,00 é encaminhado para análise manual
  (`ConsultaServlet.java:7`).
- O processamento consome a próxima pendência da fila em banco, uma por vez, com trava
  pessimista (`SinistroMapper.xml:3`).

> ⚠️ **A confirmar:** não há no código nenhuma regra de prazo, carência ou elegibilidade.
> Ou elas estão em procedure no banco, ou no sistema de cobertura chamado por HTTP. Precisa
> ser levantado com o time — o código deste repositório não permite afirmar.

## Integrações

| Sistema | Direção | Protocolo | Contrato | Timeout | Criticidade |
|---|---|---|---|---|---|
| SEGPRD / SEGURO | entrada e saída | JDBC | TB_SINISTRO, TB_FILA_PROCESSAMENTO | — | alta |
| SEGPRD / APOLICE_OWNER | entrada | JDBC | TB_APOLICE, TB_COBERTURA (terceiro) | — | alta |
| consulta-cobertura | saída | REST | GET /coberturas/{apolice} | 30s | alta |
| jms/RetornoParceiroQueue | entrada | JMS | — | — | média |
| Remessa banco conveniado | saída | SFTP | REM_AAAAMMDD.txt | — | média |
| Barramento OSB | saída | SOAP | ConsultaTarifa | — | *a confirmar* |

## Raio de impacto

- **Se cair, para:** consulta de sinistro na rede, processamento da fila em banco, remessa diária.
- **Depende de:** SEGPRD (dois schemas), consulta-cobertura, fila JMS do domínio, SFTP do banco conveniado.

## Acoplamento de dados

O `SinistroMapper.xml:12` lê `APOLICE_OWNER.TB_COBERTURA` **direto no banco de outro
sistema**, sem API no meio — ao mesmo tempo em que o servlet consulta a mesma informação por
HTTP. São dois caminhos para o mesmo dado, com risco de divergência, e qualquer mudança de
schema do dono quebra esta aplicação sem aviso.

`TB_FILA_PROCESSAMENTO` é uma **tabela usada como fila** (`SELECT ... FOR UPDATE SKIP LOCKED`
seguido de `UPDATE STATUS`). Funciona, mas não tem DLQ, retentativa nem visibilidade de lag:
registro travado em `PENDENTE` só aparece por consulta manual.

## Particularidades do WebLogic

- `context-root`: `/sinistro` (`weblogic.xml:2`)
- Datasource `jdbc/SinistroDS` está declarado (`weblogic.xml:4`) mas **nenhum código o usa** —
  o JSP abre conexão via `DriverManager` com host fixo no fonte (`consulta.jsp:6`). Ou o
  datasource é resquício, ou existe caminho de acesso que não está neste repositório.
- Senha do banco vem de `System.getProperty("db.pwd")`, definida no start do managed server.

## Pendências de configuração

| O quê | Onde | Pergunta para o time |
|---|---|---|
| `jdbc/SinistroDS` | `weblogic.xml:4` | O datasource ainda é usado? Aponta para o mesmo SEGPRD? |
| `db.pwd` | `consulta.jsp:5` | Em qual arquivo de start do domínio a propriedade é definida? |
| `url.osb` | `config.properties:2` | A chamada ao OSB ainda existe ou é integração morta? |

## Integrações a confirmar

- **Barramento OSB** (`config.properties:2`) — URL configurada, nenhuma referência a
  `url.osb` no código. Ou a chamada foi removida e a config ficou, ou ela acontece por um
  caminho não encontrado.

## Riscos e débitos conhecidos

- Java 8 e servlet 3.x em WebLogic: fora de suporte para novas correções de segurança.
- Credencial de banco e SQL dentro de JSP — qualquer mudança de schema exige mexer na tela.
- Leitura direta em schema de terceiro, sem contrato.
- Integração por shell script (`Runtime.exec`) invisível para quem lê só o código Java.
- Fila em tabela sem DLQ nem observabilidade.

## Contatos

*A definir* — nenhum CODEOWNERS, pipeline ou README no repositório indica o time responsável.
