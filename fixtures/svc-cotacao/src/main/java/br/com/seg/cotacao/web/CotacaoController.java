package br.com.seg.cotacao.web;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/cotacoes")
public class CotacaoController {
  @PostMapping public Object criar(@RequestBody Object c){ return null; }
  @GetMapping("/{id}") public Object buscar(@PathVariable String id){ return null; }
}
