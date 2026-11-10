# Lábia: receitas de comandos. `make help` lista tudo.
# Cada alvo é um passo reproduzível; a CI roda `make check`.

.PHONY: help setup lint format typecheck test check schemas samples scenarios clean

help:  ## Lista os comandos disponíveis
	@grep -E '^[a-z-]+:.*## ' Makefile | sed 's/:.*## /\t/'

setup:  ## Instala as dependências travadas no uv.lock
	uv sync --locked

lint:  ## Confere estilo e erros comuns (ruff)
	uv run ruff check .
	uv run ruff format --check .

format:  ## Formata o código automaticamente
	uv run ruff check --fix .
	uv run ruff format .

typecheck:  ## Confere os tipos (mypy em modo estrito)
	uv run mypy

test:  ## Roda todos os testes
	uv run pytest

check: lint typecheck test  ## Tudo o que a CI roda

schemas:  ## Gera os JSON Schemas do contrato de dados a partir dos modelos Pydantic
	uv run labia schemas

scenarios:  ## Gera os cenários de treino e de teste (semente fixa)
	uv run labia scenarios

samples:  ## Gera os arquivos de resultado de exemplo (is_sample: true) rodando agentes roteirizados
	uv run labia samples

clean:  ## Apaga caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
