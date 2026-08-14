package br.com.seg.cotacao.job;
import org.springframework.scheduling.annotation.Scheduled;
public class ExpiraJob {
  // expira cotacoes com mais de 30 dias
  @Scheduled(cron = "0 5 3 * * *")
  public void expirar(){ }
}
