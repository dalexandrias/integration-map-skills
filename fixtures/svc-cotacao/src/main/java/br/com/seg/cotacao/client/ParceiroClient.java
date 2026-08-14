package br.com.seg.cotacao.client;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
@FeignClient(name="parceiro", url="${parceiro.url}")
public interface ParceiroClient {
  @CircuitBreaker(name="parceiro")
  @PostMapping("/v1/tarifas")
  Object consultarTarifa(@RequestBody Object req);
}
