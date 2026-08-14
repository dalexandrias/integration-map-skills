<%@ page import="java.sql.*" %>
<html><body>
<%
  Connection c = DriverManager.getConnection(
      "jdbc:oracle:thin:@orclprd-scan:1521/SEGPRD", "APP_SINISTRO", System.getProperty("db.pwd"));
  PreparedStatement ps = c.prepareStatement(
      "SELECT S.NUM_SINISTRO, A.NUM_APOLICE FROM SEGURO.TB_SINISTRO S " +
      "JOIN APOLICE_OWNER.TB_APOLICE A ON A.ID = S.ID_APOLICE WHERE S.STATUS = ?");
  ps.setString(1, request.getParameter("st"));
  ResultSet rs = ps.executeQuery();
  while (rs.next()) { out.println(rs.getString(1)); }
%>
</body></html>
