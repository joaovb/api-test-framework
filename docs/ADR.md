# ADR — Architectural Decision Records

Registro das decisões arquiteturais do framework e suas justificativas.

---

## ADR-001: pytest como test runner

**Decisão**: Usar pytest como test runner principal.

**Justificativa**: Padrão de mercado em Python. Fixtures poderosas, plugins robustos (xdist, html, allure), parametrização nativa e curva de aprendizado mínima para o time.

**Alternativas consideradas**: unittest (verboso, sem fixtures), nose2 (descontinuado).

---

## ADR-002: httpx em vez de requests

**Decisão**: Usar `httpx` como HTTP client.

**Justificativa**: API idêntica ao `requests` (zero fricção na migração), suporte nativo a async para evolução futura, tipagem mais robusta e manutenção ativa.

**Alternativas consideradas**: `requests` (sem suporte async nativo).

---

## ADR-003: Configuração por ambiente via YAML

**Decisão**: Configurações em arquivos YAML por ambiente, com merge da configuração base.

**Justificativa**: Separação clara de configurações, sem necessidade de condicionais no código. Suporte a substituição de variáveis de ambiente via `${VAR}`.

---

## ADR-004: Token JWT cacheado por sessão

**Decisão**: Token OAuth 2.0 cacheado em memória durante toda a sessão de testes.

**Justificativa**: Evita N chamadas ao servidor de autenticação (uma por teste). O cache é TTL-aware e renova automaticamente antes da expiração.

---

## ADR-005: Factories com Faker para dados de teste

**Decisão**: Dados de teste gerados programaticamente via factories + Faker.

**Justificativa**: Isolamento total entre execuções, sem dependência de banco de dados externo. Dados realistas sem necessidade de fixtures estáticas para casos comuns.

---

## ADR-006: Relatórios duais (HTML local + Allure CI)

**Decisão**: pytest-html para desenvolvimento local, Allure para pipeline CI.

**Justificativa**: pytest-html é zero-config e rápido para uso diário. Allure oferece histórico, tendências e rastreabilidade necessários no pipeline.
