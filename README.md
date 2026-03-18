# API Test Framework

> Framework de automação de testes para APIs REST — Framework opiniunado e pronto para produção.

---

## Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar os Testes](#como-executar-os-testes)
  - [Via Makefile](#via-makefile)
  - [Via Script Python](#via-script-python)
  - [Via pytest direto](#via-pytest-direto)
- [Como Escrever Novos Testes](#como-escrever-novos-testes)
  - [Anatomia de um teste](#anatomia-de-um-teste)
  - [Usando fixtures](#usando-fixtures)
  - [Usando factories](#usando-factories)
  - [Validando schemas](#validando-schemas)
  - [Testes de segurança](#testes-de-segurança)
  - [Marcadores (markers)](#marcadores-markers)
- [Módulos do Framework](#módulos-do-framework)
  - [core/config_loader](#coreconfigloader)
  - [core/http_client](#corehttpclient)
  - [core/auth/oauth_manager](#coreauthоauthmanager)
  - [core/schema_validator](#coreschemavalidator)
  - [core/logger](#corelogger)
  - [factories/](#factories)
- [Gerenciamento de Dados de Teste](#gerenciamento-de-dados-de-teste)
- [Schemas de Contrato](#schemas-de-contrato)
- [Relatórios](#relatórios)
- [Integração com CI/CD](#integração-com-cicd)
- [Adicionando um Novo Endpoint](#adicionando-um-novo-endpoint)
- [Boas Práticas](#boas-práticas)
- [FAQ](#faq)

---

## Visão Geral

O **API Test Framework** é um framework Python opinado para automação de testes de APIs REST. Foi construído para fornecer uma base robusta, escalável e fácil de manter para suítes de testes de APIs em produção.

### O que ele resolve

| Problema                            | Solução                                          |
| ----------------------------------- | ------------------------------------------------ |
| Token JWT expira durante os testes  | Cache automático com renovação transparente      |
| Configuração diferente por ambiente | YAML por ambiente + variáveis de ambiente        |
| Boilerplate repetitivo nos testes   | Fixtures reutilizáveis via pytest                |
| Dados de teste frágeis e acoplados  | Factories com Faker — dados dinâmicos e isolados |
| Falta de padronização no time       | Framework opinionado com convenções claras       |
| Dificuldade de onboarding           | README completo + exemplos em cada módulo        |

### Stack Técnica

| Biblioteca      | Versão | Papel                                  |
| --------------- | ------ | -------------------------------------- |
| `pytest`        | ≥ 8.x  | Test runner                            |
| `httpx`         | ≥ 0.27 | HTTP client com suporte a async        |
| `pydantic`      | ≥ 2.x  | Validação e tipagem                    |
| `jsonschema`    | ≥ 4.x  | Validação de contratos JSON Schema     |
| `faker`         | ≥ 25.x | Geração de dados de teste realistas    |
| `pyyaml`        | ≥ 6.x  | Configuração por ambiente              |
| `pytest-html`   | ≥ 4.x  | Relatório HTML local                   |
| `allure-pytest` | ≥ 2.x  | Relatório rico para CI/CD              |
| `pytest-xdist`  | ≥ 3.x  | Execução paralela                      |
| `python-dotenv` | ≥ 1.x  | Gerenciamento de variáveis de ambiente |

---

## Pré-requisitos

- **Python 3.11+**
- **pip** atualizado (`pip install --upgrade pip`)
- **make** (opcional — para usar o Makefile)
- **Allure CLI** (opcional — para visualizar relatórios Allure localmente)
  ```bash
  brew install allure        # macOS
  scoop install allure       # Windows
  ```

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-time/jornada-test-framework.git
cd jornada-test-framework
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
# Produção + Dev (recomendado para o time)
make install-dev

# Ou sem make:
pip install -e ".[dev]"
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com as credenciais do ambiente:

```dotenv
ENV=dev
OAUTH_CLIENT_ID=seu-client-id
OAUTH_CLIENT_SECRET=seu-client-secret
OAUTH_TOKEN_URL=https://auth.com.br/oauth/token
OAUTH_SCOPE=jornada:read jornada:write
```

> ⚠️ **Nunca commite o arquivo `.env`** — ele está no `.gitignore`.

### 5. Verifique a instalação

```bash
make check-env     # verifica variáveis de ambiente
pytest --collect-only  # lista todos os testes disponíveis
```

---

## Configuração

### Ambientes disponíveis

| Ambiente  | Arquivo               | Uso                       |
| --------- | --------------------- | ------------------------- |
| `dev`     | `config/dev.yaml`     | Desenvolvimento local     |
| `staging` | `config/staging.yaml` | Homologação / Pipeline CI |
| `prod`    | `config/prod.yaml`    | Apenas smoke tests        |

O ambiente é selecionado pela variável `ENV`:

```bash
ENV=staging pytest tests/
```

### Estrutura de um arquivo de configuração

```yaml
# config/dev.yaml
api:
  base_url: "http://localhost:8080"
  timeout: 60

auth:
  token_url: "http://localhost:9090/oauth/token"
  client_id: "${OAUTH_CLIENT_ID}" # lido do .env
  client_secret: "${OAUTH_CLIENT_SECRET}"
  scope: "jornada:read jornada:write"
```

Os valores `${VARIAVEL}` são resolvidos automaticamente do ambiente. Você nunca coloca credenciais direto no YAML.

---

## Estrutura do Projeto

```
jornada-test-framework/
│
├── config/                    # Configuração por ambiente
│   ├── base.yaml              # Configurações compartilhadas
│   ├── dev.yaml               # Sobrescreve base para DEV
│   ├── staging.yaml           # Sobrescreve base para STAGING
│   └── prod.yaml              # Sobrescreve base para PROD
│
├── core/                      # Núcleo do framework — não modificar para criar testes
│   ├── auth/
│   │   ├── oauth_manager.py   # Obtém, cacheia e renova tokens JWT
│   │   └── token_cache.py     # Cache de token com TTL
│   ├── config_loader.py       # Carrega e mescla YAML por ambiente
│   ├── http_client.py         # Wrapper httpx com auth, retry e logs
│   ├── logger.py              # Logger estruturado (JSON ou texto)
│   └── schema_validator.py    # Valida responses contra JSON Schema
│
├── factories/                 # Geração de dados de teste
│   ├── base_factory.py        # Classe base com helpers compartilhados
│   └── mfe_factory.py         # Factories do domínio: MFE, Route, Manifest, Journey
│
├── schemas/                   # Contratos JSON Schema das APIs
│   ├── manifest/
│   │   └── manifest_response.json
│   ├── pages/
│   │   └── pages_response.json
│   ├── journeys/
│   │   └── journeys_response.json
│   └── shared/
│       └── error_response.json
│
├── tests/                     # Suíte de testes
│   ├── conftest.py            # Fixtures globais (api_client, schema_validator, etc.)
│   ├── contrato/              # Testes funcionais de contrato
│   │   ├── test_manifest.py
│   │   └── test_pages_journeys.py
│   └── seguranca/             # Testes de segurança
│       └── test_autenticacao.py
│
├── reports/                   # Relatórios gerados (gitignored)
├── .env.example               # Template de variáveis de ambiente
├── .gitignore
├── Makefile                   # Comandos do time
├── pyproject.toml             # Dependências e configuração
├── pytest.ini                 # Configuração do pytest
└── run_tests.py               # Script de execução alternativo ao Makefile
```

---

## Como Executar os Testes

### Via Makefile

```bash
# Todos os testes em DEV
make test

# Todos os testes com ambiente específico
make test-dev
make test-staging

# Por categoria
make test-contrato
make test-seguranca

# Por endpoint/marker
make test-manifest
make test-pages
make test-journeys

# Modo CI/CD (Allure + JUnit XML)
make test-ci

# Execução paralela
make test-parallel

# Ver todos os comandos disponíveis
make help
```

### Via Script Python

Para ambientes sem `make` (ex: Windows):

```bash
# Todos os testes em DEV
python run_tests.py

# Ambiente específico
python run_tests.py --env staging

# Suíte específica
python run_tests.py --suite contrato
python run_tests.py --suite seguranca

# Marker específico
python run_tests.py --marker manifest
python run_tests.py --marker pages

# Modo CI/CD
python run_tests.py --ci --env staging

# Paralelo
python run_tests.py --parallel --workers 4
```

### Via pytest direto

```bash
# Todos os testes
pytest tests/

# Com ambiente específico
ENV=staging pytest tests/

# Por marker
pytest tests/ -m manifest
pytest tests/ -m "contrato and not seguranca"

# Teste específico
pytest tests/contrato/test_manifest.py::TestManifestContrato::test_manifest_retorna_200

# Com output detalhado
pytest tests/ -v --tb=long

# Para de executar no primeiro erro
pytest tests/ -x

# Reexecuta apenas testes que falharam
pytest tests/ --lf
```

---

## Como Escrever Novos Testes

### Anatomia de um teste

```python
# tests/contrato/test_meu_endpoint.py

import pytest

@pytest.mark.contrato          # marker obrigatório para categorização
@pytest.mark.meu_marker        # marker opcional para filtros
class TestMeuEndpoint:
    """Docstring descrevendo o que esta classe testa."""

    def test_retorna_200(self, api_client):
        """Descrição clara do que este teste valida."""
        response = api_client.get("/meu-endpoint")
        assert response.status_code == 200
```

**Regras de nomenclatura:**

- Classes: `Test<NomeDoRecurso>` — ex: `TestManifest`, `TestPages`
- Métodos: `test_<o_que_valida>` — ex: `test_retorna_200`, `test_schema_valido`
- Arquivos: `test_<recurso>.py` — ex: `test_manifest.py`, `test_permissions.py`

### Usando fixtures

Todas as fixtures estão disponíveis automaticamente via `tests/conftest.py`. Basta declarar como parâmetro:

```python
def test_exemplo(
    api_client,         # Client autenticado
    schema_validator,   # Validador de schema
    assert_response,    # Helpers de asserção
    config,             # Configuração do ambiente
):
    response = api_client.get("/manifest")
    assert_response.ok(response)
    assert_response.has_json(response)
    schema_validator.validate(response.json(), "manifest/manifest_response")
```

**Fixtures disponíveis:**

| Fixture                    | Escopo   | Descrição                                      |
| -------------------------- | -------- | ---------------------------------------------- |
| `config`                   | session  | Configuração completa do ambiente ativo        |
| `oauth_manager`            | session  | Gerenciador OAuth — token cacheado na sessão   |
| `auth_token`               | session  | Token JWT como string `"Bearer eyJ..."`        |
| `api_client`               | function | Client HTTP autenticado — recriado por teste   |
| `api_client_no_auth`       | function | Client sem autenticação — para testes 401      |
| `api_client_invalid_token` | function | Client com token inválido — para testes 401    |
| `api_client_wrong_role`    | function | Client com role insuficiente — para testes 403 |
| `schema_validator`         | session  | Validador de JSON Schema                       |
| `assert_response`          | session  | Helpers de asserção de response                |
| `manifest_payload`         | function | Payload de manifest gerado por factory         |
| `mfe_payload`              | function | Payload de MFE gerado por factory              |
| `route_payload`            | function | Payload de rota gerado por factory             |
| `journey_payload`          | function | Payload de jornada gerado por factory          |

### Usando factories

As factories geram dados dinâmicos e realistas. Use-as para construir payloads de request ou dados de setup:

```python
from factories.mfe_factory import MfeFactory, ManifestFactory, JourneyFactory, RouteFactory

# MFE com dados aleatórios válidos
mfe = MfeFactory.build()

# MFE com valores específicos
mfe_home = MfeFactory.build(name="home", active=True, roles=["USER", "ADMIN"])

# MFE inativo
mfe_inativo = MfeFactory.inactive()

# Lista de 5 MFEs
mfes = MfeFactory.build_list(5)

# Manifest completo com 3 MFEs e 8 rotas
manifest = ManifestFactory.build(mfe_count=3, route_count=8)

# Dados inválidos para testes negativos
mfe_invalido = MfeFactory.invalid()
```

**Exemplo completo com factory em teste POST:**

```python
def test_criar_mfe_retorna_201(self, api_client):
    payload = MfeFactory.build()
    response = api_client.post("/mfes", json=payload)
    assert response.status_code == 201

def test_criar_mfe_invalido_retorna_400(self, api_client):
    payload = MfeFactory.invalid()
    response = api_client.post("/mfes", json=payload)
    assert response.status_code == 400
```

### Validando schemas

Crie o arquivo JSON Schema em `schemas/<dominio>/<nome>.json` e valide com:

```python
def test_schema_response(self, api_client, schema_validator):
    response = api_client.get("/meu-endpoint")
    # Valida body completo contra schema
    schema_validator.validate(response.json(), "meu_dominio/meu_response")

    # Valida campo específico
    schema_validator.validate_field(response.json(), "items", expected_type=list)

    # Valida múltiplos campos de uma vez
    schema_validator.assert_has_fields(response.json(), ["id", "name", "active"])
```

### Testes de segurança

```python
@pytest.mark.seguranca
class TestSegurancaMeuEndpoint:

    def test_sem_token_retorna_401(self, api_client_no_auth):
        response = api_client_no_auth.get("/meu-endpoint")
        assert response.status_code == 401

    def test_token_invalido_retorna_401(self, api_client_invalid_token):
        response = api_client_invalid_token.get("/meu-endpoint")
        assert response.status_code == 401

    def test_sem_permissao_retorna_403(self, api_client_wrong_role):
        response = api_client_wrong_role.get("/meu-endpoint/admin")
        assert response.status_code == 403
```

Ou usando os métodos utilitários do `api_client`:

```python
def test_variantes_de_auth(self, api_client):
    # Sem auth
    r1 = api_client.without_auth().get("/manifest")
    assert r1.status_code == 401

    # Token inválido customizado
    r2 = api_client.with_invalid_token("meu.token.fake").get("/manifest")
    assert r2.status_code == 401
```

### Marcadores (markers)

Sempre marque seus testes para permitir execução filtrada:

```python
@pytest.mark.contrato      # teste funcional de contrato
@pytest.mark.seguranca     # teste de segurança
@pytest.mark.manifest      # relacionado ao endpoint /manifest
@pytest.mark.pages         # relacionado ao endpoint /pages
@pytest.mark.journeys      # relacionado ao endpoint /journeys
@pytest.mark.smoke         # incluir no subset de smoke test
@pytest.mark.regressao     # incluir na regressão completa
```

Executar por marker:

```bash
pytest tests/ -m "contrato and manifest"
pytest tests/ -m "smoke"
pytest tests/ -m "not seguranca"
```

---

## Módulos do Framework

### core/config_loader

Carrega e mescla configurações YAML por ambiente. Suporta substituição de variáveis de ambiente via `${VAR}`.

```python
from core.config_loader import get_config

config = get_config()
base_url = config["api"]["base_url"]
timeout  = config["api"]["timeout"]
```

A configuração é **cacheada** após a primeira chamada. Para testes que precisem de ambientes diferentes:

```python
from core.config_loader import reset_config
reset_config()   # limpa o cache
```

### core/http_client

Wrapper do `httpx` com autenticação automática, retry e logging. Use sempre via fixture `api_client`.

```python
# Métodos disponíveis
response = api_client.get("/manifest")
response = api_client.get("/pages", params={"role": "USER"})
response = api_client.post("/mfes", json={"name": "home"})
response = api_client.put("/mfes/123", json={"active": False})
response = api_client.patch("/mfes/123", json={"version": "2.0.0"})
response = api_client.delete("/mfes/123")

# Headers extras por request
response = api_client.get("/manifest", headers={"X-Trace-Id": "abc-123"})

# Variantes sem auth (para testes de segurança)
response = api_client.without_auth().get("/manifest")
response = api_client.with_invalid_token().get("/manifest")
```

### core/auth/oauth_manager

Gerencia o ciclo de vida do token JWT. Transparente para quem escreve testes — o `api_client` o usa automaticamente.

```python
# Uso direto (raramente necessário)
from core.auth.oauth_manager import OAuthManager

manager = OAuthManager(config)
token = manager.get_token()          # obtém/renova do cache
headers = manager.get_auth_headers() # {"Authorization": "Bearer eyJ..."}

# Forçar renovação (após 401 inesperado)
headers = manager.get_auth_headers(force_refresh=True)
```

### core/schema_validator

Valida responses JSON contra arquivos `.json` em `/schemas/`.

```python
from core.schema_validator import SchemaValidator

validator = SchemaValidator()

# Validação completa
validator.validate(response.json(), "manifest/manifest_response")

# Validação de campo específico
value = validator.validate_field(data, "mfes", expected_type=list)

# Validação de múltiplos campos
validator.assert_has_fields(data, ["version", "mfes", "routes", "environment"])
```

### core/logger

Logger estruturado — JSON para pipelines, texto colorido para desenvolvimento.

```python
from core.logger import get_logger

logger = get_logger(__name__)
logger.info("Enviando request para /manifest")
logger.debug("Headers da request", extra={"headers": headers})
logger.error("Falha inesperada", extra={"status": 500, "body": body})
```

### factories/

Gera dados de teste realistas e isolados. Nunca use dados hardcoded nos testes.

```python
from factories.mfe_factory import (
    MfeFactory,
    RouteFactory,
    ManifestFactory,
    JourneyFactory,
    PermissionFactory,
)
```

---

## Gerenciamento de Dados de Teste

O framework adota uma estratégia de **3 camadas** para dados de teste:

### Camada 1 — Factories dinâmicas (uso padrão)

```python
# Dados únicos por execução — isolamento total
mfe = MfeFactory.build()
journey = JourneyFactory.build(name="abertura-conta", step_count=5)
```

Use para: maioria dos testes, dados de entrada em POST/PUT, dados de setup.

### Camada 2 — Fixtures estáticas (cenários de borda)

Para dados com valores muito específicos (CPF bloqueado, permissão negada, config de produção), crie arquivos YAML em `tests/fixtures/`:

```yaml
# tests/fixtures/mfe_bloqueado.yaml
id: "mfe-id-bloqueado-fixo"
name: "mfe-suspenso"
active: false
roles: []
```

```python
import yaml
from pathlib import Path

def load_fixture(name: str) -> dict:
    path = Path(__file__).parent / "fixtures" / f"{name}.yaml"
    return yaml.safe_load(path.read_text())

mfe_bloqueado = load_fixture("mfe_bloqueado")
```

### Camada 3 — Setup via API (estado controlado)

Para testes que precisam de estado específico no sistema, crie e limpe via endpoints:

```python
@pytest.fixture
def mfe_criado(api_client):
    """Cria um MFE antes do teste e remove após."""
    payload = MfeFactory.build()
    response = api_client.post("/mfes", json=payload)
    assert response.status_code == 201
    mfe_id = response.json()["id"]

    yield response.json()   # dados disponíveis no teste

    # Teardown: remove o MFE criado
    api_client.delete(f"/mfes/{mfe_id}")
```

---

## Schemas de Contrato

Os schemas ficam em `schemas/<dominio>/<nome>.json` no formato [JSON Schema Draft-07](https://json-schema.org/).

### Criando um novo schema

1. Crie o arquivo em `schemas/meu_dominio/meu_response.json`
2. Defina os campos obrigatórios e seus tipos:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MeuResponse",
  "type": "object",
  "required": ["id", "name", "active"],
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string", "minLength": 1 },
    "active": { "type": "boolean" },
    "items": { "type": "array", "items": { "type": "object" } }
  }
}
```

3. Use no teste:

```python
schema_validator.validate(response.json(), "meu_dominio/meu_response")
```

### Schemas existentes

| Schema                       | Endpoint        | Descrição                          |
| ---------------------------- | --------------- | ---------------------------------- |
| `manifest/manifest_response` | `GET /manifest` | Manifest completo com MFEs e rotas |
| `pages/pages_response`       | `GET /pages`    | Lista de páginas paginada          |
| `journeys/journeys_response` | `GET /journeys` | Lista de jornadas com steps        |
| `shared/error_response`      | Todos (4xx/5xx) | Formato padrão de erro             |

---

## Relatórios

### HTML (desenvolvimento local)

Gerado automaticamente em `reports/`:

```bash
make test          # gera reports/report.html
make test-contrato # gera reports/report-contrato.html
make reports       # abre o relatório no navegador
```

### Allure (CI/CD e apresentações)

```bash
# Executa e gera os dados Allure
make test-staging

# Serve relatório interativo localmente
make allure-serve

# Gera relatório estático
make allure-generate
```

### JUnit XML (integração com pipelines)

Gerado pelo modo CI:

```bash
make test-ci
# Gera: reports/junit.xml
```

---

## Integração com CI/CD

### GitHub Actions

```yaml
# .github/workflows/api-tests.yml
name: API Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  api-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run API Tests
        env:
          ENV: staging
          OAUTH_CLIENT_ID: ${{ secrets.OAUTH_CLIENT_ID }}
          OAUTH_CLIENT_SECRET: ${{ secrets.OAUTH_CLIENT_SECRET }}
          OAUTH_TOKEN_URL: ${{ secrets.OAUTH_TOKEN_URL }}
        run: make test-ci

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: |
            reports/junit.xml
            allure-results/

      - name: Publish Allure Report
        uses: simple-elf/allure-report-action@v1
        if: always()
        with:
          allure_results: allure-results
```

### Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        ENV = 'staging'
        OAUTH_CLIENT_ID     = credentials('oauth-client-id')
        OAUTH_CLIENT_SECRET = credentials('oauth-client-secret')
        OAUTH_TOKEN_URL     = credentials('oauth-token-url')
    }

    stages {
        stage('Install') {
            steps {
                sh 'pip install -e ".[dev]"'
            }
        }
        stage('API Tests') {
            steps {
                sh 'make test-ci'
            }
        }
    }

    post {
        always {
            junit 'reports/junit.xml'
            allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
    }
}
```

### Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: "ubuntu-latest"

variables:
  ENV: staging

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: "3.11"

  - script: pip install -e ".[dev]"
    displayName: "Install dependencies"

  - script: make test-ci
    displayName: "Run API Tests"
    env:
      OAUTH_CLIENT_ID: $(OAUTH_CLIENT_ID)
      OAUTH_CLIENT_SECRET: $(OAUTH_CLIENT_SECRET)
      OAUTH_TOKEN_URL: $(OAUTH_TOKEN_URL)

  - task: PublishTestResults@2
    inputs:
      testResultsFormat: "JUnit"
      testResultsFiles: "reports/junit.xml"
```

---

## Adicionando um Novo Endpoint

Checklist completo para cobrir um novo endpoint:

### 1. Crie o schema de contrato

```bash
# Crie o arquivo em schemas/<dominio>/<nome>_response.json
touch schemas/permissions/permissions_response.json
```

### 2. Adicione a factory (se necessário)

```python
# factories/mfe_factory.py — adicione a nova factory ao arquivo existente
class PermissionFactory(BaseFactory):
    @classmethod
    def build(cls, role=None, resource=None) -> dict:
        return {
            "id": cls.random_uuid(),
            "role": role or random.choice(ROLES),
            "resource": resource or random.choice(MFE_NAMES),
            "actions": ["GET", "POST"],
            "active": True,
        }
```

### 3. Crie o arquivo de testes

```python
# tests/contrato/test_permissions.py
import pytest

@pytest.mark.contrato
class TestPermissionsContrato:
    def test_permissions_retorna_200(self, api_client): ...
    def test_permissions_schema_valido(self, api_client, schema_validator): ...
```

### 4. Adicione o marker no `pyproject.toml`

```toml
markers = [
    "permissions: testes do endpoint de permissões",
    # ... outros markers
]
```

### 5. Adicione o comando no Makefile

```makefile
test-permissions: ## Apenas testes de permissões
    ENV=$(ENV) pytest tests/ -m permissions -v
```

---

## Boas Práticas

### ✅ Faça

```python
# Use fixtures — não instancie diretamente
def test_algo(api_client, schema_validator): ...

# Use factories — nunca hardcode dados
payload = MfeFactory.build(name="home")

# Nomeie testes descritivamente
def test_manifest_mfe_active_e_boolean(self, api_client): ...

# Use markers sempre
@pytest.mark.contrato
@pytest.mark.manifest

# Documente o que o teste valida
def test_algo(self, api_client):
    """O endpoint deve retornar apenas MFEs com active=true quando filtrado."""
```

### ❌ Evite

```python
# Não hardcode URLs
response = httpx.get("http://localhost:8080/manifest")  # ❌

# Não hardcode tokens
headers = {"Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9..."}  # ❌

# Não hardcode dados de teste
payload = {"name": "home", "id": "abc-123"}  # ❌ — use factories

# Não crie dependência entre testes
def test_b(self):
    # Nunca assuma que test_a rodou antes  # ❌

# Não faça múltiplas asserções não relacionadas em um teste
def test_tudo_de_uma_vez(self, api_client):  # ❌ — quebre em testes menores
    ...
```

---

## FAQ

**Q: Como trocar o ambiente sem alterar código?**

```bash
ENV=staging pytest tests/    # ou
export ENV=staging && pytest tests/
```

**Q: Como rodar apenas um teste específico?**

```bash
pytest tests/contrato/test_manifest.py::TestManifestContrato::test_manifest_retorna_200 -v
```

**Q: Os testes de segurança estão falhando com 404 em vez de 401. Por quê?**
Provavelmente o endpoint ainda não está implementado. O framework trata isso com `assert response.status_code in (401, 404)` em alguns casos. Ajuste o teste quando o endpoint estiver disponível.

**Q: Como adicionar um header customizado em todos os testes?**
Configure em `config/base.yaml` na seção `headers.default`.

**Q: Como mockar uma dependência externa nos testes?**
Use `respx` para mockar chamadas HTTP do `httpx`:

```python
import respx
import httpx

@respx.mock
def test_com_mock(api_client):
    respx.get("http://localhost:8080/manifest").mock(
        return_value=httpx.Response(200, json={"mfes": []})
    )
    response = api_client.get("/manifest")
    assert response.status_code == 200
```

**Q: O token expira durante uma execução longa de testes. O framework lida com isso?**
Sim. O `OAuthManager` renova o token automaticamente quando ele está a menos de 60 segundos de expirar. Em caso de 401 inesperado, ele invalida o cache e renova na próxima request.

**Q: Como ver os logs de debug durante os testes?**

```bash
ENV=dev pytest tests/ -v -s --log-cli-level=DEBUG
```

---

## Suporte

Dúvidas ou sugestões de melhoria? Abra uma issue ou fale com o time responsável pelo framework.

---
