import os, oracledb, pandas as pd, paramiko
from apscheduler.schedulers.blocking import BlockingScheduler

PLANILHA = r"\\fileserver\financeiro\parametros_conciliacao.xlsx"

def baixar_retorno():
    t = paramiko.Transport(("sftp.bancoconveniado.com.br", 22))
    t.connect(username="remessa", password=os.getenv("SFTP_PWD"))
    sftp = paramiko.SFTPClient.from_transport(t)
    sftp.get("/saida/RET_%s.txt" % pd.Timestamp.today().strftime("%Y%m%d"), "/tmp/ret.txt")

def gravar(df):
    con = oracledb.connect(user="APP_CONC", password=os.getenv("ADW_PWD"), dsn="adw_high")
    cur = con.cursor()
    # grava na tabela que o faturamento le todo dia 1
    cur.executemany("INSERT INTO DW_SINISTRO.FT_CONCILIACAO VALUES (:1,:2,:3)", df.values.tolist())
    con.commit()

def rodar():
    param = pd.read_excel(PLANILHA, sheet_name="regras")
    baixar_retorno()
    df = pd.read_fwf("/tmp/ret.txt", widths=[20,20,200])
    gravar(df.merge(param, on="cod"))

if __name__ == "__main__":
    s = BlockingScheduler(); s.add_job(rodar, "cron", hour=3, minute=5); s.start()
