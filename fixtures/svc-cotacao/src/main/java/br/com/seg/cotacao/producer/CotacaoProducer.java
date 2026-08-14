package br.com.seg.cotacao.producer;
import org.springframework.kafka.core.KafkaTemplate;
import br.com.seg.cotacao.config.Topics;
public class CotacaoProducer {
  private final KafkaTemplate<String,Object> kafka;
  public CotacaoProducer(KafkaTemplate<String,Object> k){ this.kafka = k; }
  public void publicar(String proposta, Object payload){
    kafka.send(Topics.COTACAO_SOLICITADA, proposta, payload);
  }
}
