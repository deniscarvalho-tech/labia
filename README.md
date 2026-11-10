# Lábia

Um LLM pequeno e aberto treinado para não cair em engenharia social em português, medido em fraude × atrito, custo e latência.

**Status: em construção.** Nenhum resultado foi publicado ainda. As hipóteses e o plano de análise foram registrados antes de qualquer dado, na tag [`pre-registro`](https://github.com/deniscarvalho-tech/labia/releases/tag/pre-registro): veja [docs/plano.md](docs/plano.md).

## Como rodar

```bash
uv sync          # instala as dependências travadas
make check       # lint, tipos e testes
make scenarios   # gera os cenários de treino e teste (semente fixa)
```

O passo a passo completo está em [docs/como-rodar.md](docs/como-rodar.md).
