# ==============================================================
# Jornada Test Framework — Makefile
# Comandos padronizados para execução local e pipeline CI/CD
# ==============================================================

.PHONY: help install install-dev test test-dev test-staging test-ci \
        test-contrato test-seguranca test-manifest test-pages test-journeys \
        test-smoke test-regressao lint format type-check clean reports

# Ambiente padrão
ENV ?= dev

# Diretório de relatórios
REPORTS_DIR = reports
ALLURE_DIR  = allure-results

# ── Ajuda ─────────────────────────────────────────────────────────────────────

help: ## Exibe este menu de ajuda
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║       Jornada Test Framework — Comandos              ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Instalação ─────────────────────────────────────────────────────────────────

install: ## Instala dependências de produção
	pip install -e .

install-dev: ## Instala todas as dependências (prod + dev)
	pip install -e ".[dev]"
	cp -n .env.example .env || true
	@echo "✅ Instalação concluída. Configure o arquivo .env antes de rodar os testes."

# ── Execução de testes ────────────────────────────────────────────────────────

test: ## Executa todos os testes no ambiente DEV com relatório HTML
	ENV=$(ENV) pytest tests/ -v \
		--html=$(REPORTS_DIR)/report.html \
		--self-contained-html

test-dev: ## Testes completos em DEV (verbose + HTML report)
	ENV=dev pytest tests/ -v \
		--html=$(REPORTS_DIR)/report-dev.html \
		--self-contained-html

test-staging: ## Testes completos em STAGING com relatório Allure
	ENV=staging pytest tests/ -v \
		--alluredir=$(ALLURE_DIR)

test-ci: ## Execução para pipeline CI/CD (staging + Allure + JUnit XML)
	ENV=staging pytest tests/ \
		--tb=short \
		--alluredir=$(ALLURE_DIR) \
		--junitxml=$(REPORTS_DIR)/junit.xml \
		-q

# ── Execução por categoria ────────────────────────────────────────────────────

test-contrato: ## Apenas testes de contrato funcional
	ENV=$(ENV) pytest tests/contrato/ -v \
		--html=$(REPORTS_DIR)/report-contrato.html \
		--self-contained-html

test-seguranca: ## Apenas testes de segurança
	ENV=$(ENV) pytest tests/seguranca/ -v \
		--html=$(REPORTS_DIR)/report-seguranca.html \
		--self-contained-html

test-manifest: ## Apenas testes do endpoint /manifest
	ENV=$(ENV) pytest tests/ -m manifest -v

test-pages: ## Apenas testes dos endpoints /pages
	ENV=$(ENV) pytest tests/ -m pages -v

test-journeys: ## Apenas testes dos endpoints /journeys
	ENV=$(ENV) pytest tests/ -m journeys -v

test-smoke: ## Smoke tests — subset rápido para validação pós-deploy
	ENV=$(ENV) pytest tests/ -m smoke -v

test-regressao: ## Suíte completa de regressão
	ENV=$(ENV) pytest tests/ -m regressao -v \
		--alluredir=$(ALLURE_DIR)

# ── Execução paralela ─────────────────────────────────────────────────────────

test-parallel: ## Executa testes em paralelo (4 workers) — mais rápido em CI
	ENV=$(ENV) pytest tests/ -n 4 \
		--alluredir=$(ALLURE_DIR) \
		-q

# ── Relatórios ────────────────────────────────────────────────────────────────

reports: ## Abre relatório HTML no navegador
	@open $(REPORTS_DIR)/report.html 2>/dev/null || \
		xdg-open $(REPORTS_DIR)/report.html 2>/dev/null || \
		echo "Abra manualmente: $(REPORTS_DIR)/report.html"

allure-serve: ## Gera e serve relatório Allure localmente
	allure serve $(ALLURE_DIR)

allure-generate: ## Gera relatório Allure estático em reports/allure-report
	allure generate $(ALLURE_DIR) -o $(REPORTS_DIR)/allure-report --clean

# ── Qualidade de código ───────────────────────────────────────────────────────

lint: ## Verifica código com Ruff
	ruff check .

format: ## Formata código com Black
	black .

format-check: ## Verifica formatação sem alterar arquivos
	black --check .

type-check: ## Verifica tipagem com Mypy
	mypy core/ factories/ --ignore-missing-imports

# ── Utilitários ───────────────────────────────────────────────────────────────

clean: ## Remove artefatos gerados (relatórios, cache, pyc)
	rm -rf $(REPORTS_DIR)/* $(ALLURE_DIR) .pytest_cache __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Limpeza concluída"

mkdir-reports: ## Cria diretório de relatórios se não existir
	mkdir -p $(REPORTS_DIR) $(ALLURE_DIR)

check-env: ## Verifica se as variáveis de ambiente necessárias estão configuradas
	@python -c "\
import os; \
required = ['OAUTH_CLIENT_ID', 'OAUTH_CLIENT_SECRET', 'OAUTH_TOKEN_URL']; \
missing = [v for v in required if not os.environ.get(v)]; \
print('❌ Variáveis ausentes:', missing) if missing else print('✅ Todas as variáveis configuradas')"
