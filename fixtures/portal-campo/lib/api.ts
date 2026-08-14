const COBERTURA = process.env.NEXT_PUBLIC_COBERTURA_URL!;
export async function criarCotacao(body: unknown) {
  return fetch("/bff/cotacao/cotacoes", { method: "POST", body: JSON.stringify(body) });
}
export async function buscarCobertura(apolice: string) {
  return fetch(`${COBERTURA}/coberturas/${apolice}`);
}
export async function buscarCarencia(apolice: string) {
  return fetch(`${COBERTURA}/carencias/${apolice}`);
}
