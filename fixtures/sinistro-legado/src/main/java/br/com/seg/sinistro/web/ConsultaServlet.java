package br.com.seg.sinistro.web;
import java.io.*; import java.net.*; import javax.servlet.http.*;
public class ConsultaServlet extends HttpServlet {
  protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
    // regra: sinistro acima de 50 mil vai para analise manual
    double valor = Double.parseDouble(req.getParameter("valor"));
    if (valor > 50000.00) { req.setAttribute("fluxo", "ANALISE_MANUAL"); }
    URL url = new URL(Config.get("url.cobertura") + "/coberturas/" + req.getParameter("apolice"));
    HttpURLConnection con = (HttpURLConnection) url.openConnection();
    con.setConnectTimeout(30000);
    con.setRequestMethod("GET");
    BufferedReader in = new BufferedReader(new InputStreamReader(con.getInputStream()));
    resp.getWriter().write(in.readLine());
  }
}
