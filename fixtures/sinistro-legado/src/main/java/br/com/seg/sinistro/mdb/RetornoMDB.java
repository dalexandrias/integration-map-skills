package br.com.seg.sinistro.mdb;
import javax.ejb.*; import javax.jms.*;
@MessageDriven(activationConfig = {
  @ActivationConfigProperty(propertyName="destinationLookup", propertyValue="jms/RetornoParceiroQueue"),
  @ActivationConfigProperty(propertyName="destinationType", propertyValue="javax.jms.Queue")
})
public class RetornoMDB implements MessageListener {
  public void onMessage(Message m) { /* processa retorno do parceiro */ }
}
