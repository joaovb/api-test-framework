# Guia de Contribuição

## Fluxo para adicionar novos testes

1. Crie uma branch: `git checkout -b test/nome-do-endpoint`
2. Siga a estrutura de arquivos do framework
3. Execute localmente: `make test-dev`
4. Garanta que `make lint` passa sem erros
5. Abra PR com descrição do que foi coberto

## Convenções de código

- **Classes de teste**: `Test<Recurso>` — ex: `TestPermissions`
- **Métodos**: `test_<comportamento_esperado>` — ex: `test_retorna_200`
- **Markers**: sempre adicione ao menos um marker de domínio e um de tipo
- **Docstrings**: descreva *o que* o teste valida, não *como*

## Adicionando um novo marker

1. Declare em `pyproject.toml` na seção `[tool.pytest.ini_options].markers`
2. Adicione o comando correspondente no `Makefile`
3. Documente no README na seção de markers

## Rodando o linter antes do commit

```bash
make lint
make format-check
make type-check
```
