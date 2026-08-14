package br.com.seg.sinistro.util;
public class IntegracaoUtil {
  public static void enviarRemessa(String arquivo) throws Exception {
    // dispara o shell que sobe o arquivo para o banco conveniado
    Process p = Runtime.getRuntime().exec(new String[]{"/opt/app/scripts/envia_arquivo.sh", arquivo});
    p.waitFor();
  }
}
