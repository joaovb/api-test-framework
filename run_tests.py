#!/usr/bin/env python3
"""
run_tests.py
------------
Script único de execução do framework — alternativa ao Makefile.
Útil em ambientes Windows ou onde o make não está disponível.

Uso:
    python run_tests.py                        # todos os testes em DEV
    python run_tests.py --env staging          # testes em STAGING
    python run_tests.py --suite contrato       # apenas testes de contrato
    python run_tests.py --suite seguranca      # apenas testes de segurança
    python run_tests.py --marker manifest      # testes marcados com @manifest
    python run_tests.py --parallel             # execução paralela (4 workers)
    python run_tests.py --ci                   # modo CI (Allure + JUnit XML)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
ALLURE_DIR = BASE_DIR / "allure-results"


def ensure_dirs():
    REPORTS_DIR.mkdir(exist_ok=True)
    ALLURE_DIR.mkdir(exist_ok=True)


def build_pytest_args(args) -> list[str]:
    pytest_args = ["pytest"]

    # Diretório / marker de teste
    if args.suite:
        pytest_args.append(f"tests/{args.suite}/")
    elif args.marker:
        pytest_args += ["tests/", "-m", args.marker]
    else:
        pytest_args.append("tests/")

    # Verbosidade
    if args.ci:
        pytest_args += ["--tb=short", "-q"]
    else:
        pytest_args.append("-v")

    # Relatórios
    if args.ci:
        pytest_args += [
            f"--alluredir={ALLURE_DIR}",
            f"--junitxml={REPORTS_DIR}/junit.xml",
        ]
    else:
        report_name = f"report-{args.suite or 'all'}.html"
        pytest_args += [
            f"--html={REPORTS_DIR}/{report_name}",
            "--self-contained-html",
        ]

    # Paralelismo
    if args.parallel:
        pytest_args += ["-n", str(args.workers)]

    return pytest_args


def main():
    parser = argparse.ArgumentParser(
        description="Jornada Test Framework — Runner de testes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--env", default="dev",
        choices=["dev", "staging", "prod"],
        help="Ambiente de execução (padrão: dev)",
    )
    parser.add_argument(
        "--suite", default=None,
        choices=["contrato", "seguranca"],
        help="Suíte específica de testes",
    )
    parser.add_argument(
        "--marker", default=None,
        help="Marker pytest (ex: manifest, pages, journeys, smoke)",
    )
    parser.add_argument(
        "--parallel", action="store_true",
        help="Executa testes em paralelo",
    )
    parser.add_argument(
        "--workers", type=int, default=4,
        help="Número de workers paralelos (padrão: 4)",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="Modo CI/CD: Allure + JUnit XML, sem relatório HTML",
    )

    args = parser.parse_args()

    # Configura variável de ambiente
    os.environ["ENV"] = args.env
    print(f"\n🚀 Jornada Test Framework")
    print(f"   Ambiente : {args.env.upper()}")
    print(f"   Suíte    : {args.suite or 'todas'}")
    print(f"   Marker   : {args.marker or 'todos'}")
    print(f"   Modo CI  : {'sim' if args.ci else 'não'}\n")

    ensure_dirs()
    pytest_args = build_pytest_args(args)

    print(f"Executando: {' '.join(pytest_args)}\n")
    result = subprocess.run(pytest_args, cwd=BASE_DIR)

    if result.returncode == 0:
        print("\n✅ Todos os testes passaram!")
    else:
        print(f"\n❌ Testes falharam (código de saída: {result.returncode})")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
