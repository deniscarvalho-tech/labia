# Experimentos

O resumo de cada execução no Kaggle, como saiu do notebook. Nenhum número aqui foi digitado à mão.

| Pasta | Notebook | Commit do código | O que mediu | Resultado |
|---|---|---|---|---|
| `ambiente-kaggle.json` | `00-teste-de-fumaca` | — | o hardware do Kaggle | 2× T4 de 14,6 GB, CUDA 13, sem bfloat16, 20 GB de disco de trabalho |
| `01-piloto-professor-v1` | `01-piloto-professor` (versão 1) | `308910d` | os dois candidatos a professor | **inválido**: o simulador encerrava na primeira mensagem (defeito corrigido em `5e58662`); guardado para registro |
| `01-piloto-professor-v2` | `01-piloto-professor` (versão 2) | `5e58662` | os dois candidatos a professor, de novo | gpt-oss-20b escolhido pela regra definida antes do piloto |
| `02-teste-treino` | `02-teste-treino` | `cf41166` | QLoRA do aluno numa T4 | funciona (pico de 11,2 GB), mas só 154 tokens/s |
| `03-velocidade-treino` | `03-velocidade-treino` | `4e001af` | alternativas mais rápidas | todas falharam por incompatibilidade de versão (corrigida em `ab3c24e`); o notebook de treino passou a medir e escolher sozinho |

Os dados completos de cada execução (todas as conversas) ficam fora do git, em `data/`, e vão para o Hugging Face.
