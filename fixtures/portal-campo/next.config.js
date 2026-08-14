module.exports = { async rewrites(){ return [
  { source: "/bff/cotacao/:p*", destination: "http://svc-cotacao.interno:8080/:p*" }
]; } };
