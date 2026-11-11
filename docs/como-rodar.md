# Como rodar

O passo a passo para rodar cada etapa sozinho, do zero. Os comandos são para o terminal do VS Code no Windows (PowerShell), mas funcionam igual no Linux e no Mac.

## 0. Uma vez só: ferramentas e contas

### Ferramentas no computador

| Ferramenta | Para que serve | Como instalar |
|---|---|---|
| git | versionar o código | já vem com o Git for Windows |
| uv | instalar o Python certo e as dependências travadas | `winget install --id astral-sh.uv -e` |
| make | rodar as receitas do Makefile | `winget install --id ezwinports.make -e` |
| kaggle | enviar e acompanhar notebooks no Kaggle | `uv tool install kaggle --with six` |

Sobre o `--with six`: a versão 2.2.5 do cliente do Kaggle usa a biblioteca `six` sem declará-la como dependência e quebra ao abrir. O `--with six` instala as duas juntas.

Depois de instalar, **feche e abra o terminal** (ou o VS Code inteiro). O terminal só enxerga programas instalados antes de ele abrir. Se não quiser fechar, rode esta linha, que recarrega a lista de pastas onde o terminal procura programas (o PATH):

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
```

### Contas

| Conta | Para que | Observação |
|---|---|---|
| GitHub | repositório e CI | o primeiro `git push` abre o login pelo navegador |
| Kaggle | GPU gratuita para piloto, geração, treino e avaliação | **verifique o telefone** em Settings, senão não há GPU nem internet no notebook |
| Hugging Face | publicar o modelo, o dataset e o Space | a GPU gratuita dos Spaces (ZeroGPU) só libera para contas com mais de 30 dias |
| Google AI Studio | avaliar o Gemini (só avaliação) | chave em `.env` |
| NVIDIA (build.nvidia.com) | avaliar o DeepSeek (só avaliação) | chave em `.env` |

### Login no Kaggle (sem token)

```powershell
kaggle auth login
```

Abre o navegador, você autoriza, e a credencial fica em `C:\Users\<você>\.kaggle\credentials.json`. Ela se renova sozinha. **Não use o token da página de configurações** e nunca mande print de token: se um token aparecer num print, expire-o na hora.

### Chaves de API

```powershell
copy .env.example .env
```

Abra o `.env` no editor e preencha. Ele está no `.gitignore` e nunca vai para o git. Nunca cole chave no chat, num print ou num commit.

## 1. Preparar o projeto

```powershell
git clone https://github.com/deniscarvalho-tech/labia.git
cd labia
uv sync            # cria o ambiente com o Python 3.13 e instala as versões travadas no uv.lock
make check         # lint, tipos e os testes: tem que terminar com "passed"
```

## 2. Gerar os cenários

```powershell
make scenarios
```

Cria `data/scenarios/train.jsonl` (2.010 cenários) e `data/scenarios/test.jsonl` (212), e atualiza o `scenarios-manifest.json`. Rodar de novo produz arquivos idênticos: os hashes no manifesto não mudam. Se mudarem sem você ter mexido no gerador, algo está errado.

## 3. Ver o pipeline funcionando sem GPU

```powershell
make samples
```

Roda agentes roteirizados (regras fixas, não modelos) nos cenários de teste e grava `results/*.json` e `site-data/versions.json` com `is_sample: true`. Serve para o painel ter dados de exemplo e para você ver o caminho inteiro em 15 segundos. **Esses números nunca vão para o README.**

## 4. Rodar o piloto no Kaggle

```powershell
kaggle kernels push -p notebooks/01-piloto-professor --accelerator NvidiaTeslaT4
kaggle kernels status deniscarvalhotech/labia-01-piloto-do-professor
```

Quando o status virar `COMPLETE`, baixe a saída:

```powershell
kaggle kernels output deniscarvalhotech/labia-01-piloto-do-professor -p data/piloto
```

O notebook fixa o commit do código que usa (`LABIA_COMMIT` na primeira célula). Para rodar uma versão nova do código, faça o push para o GitHub e troque esse commit.

## 5. Rodar conversas com qualquer modelo (fora do Kaggle)

Qualquer servidor no formato da API da OpenAI serve. Exemplo com um Ollama local:

```powershell
uv run labia run --scenarios data/scenarios/test.jsonl --limit 10 --runs 1 `
  --model-id teste --agent-url http://127.0.0.1:11434/v1 --agent-model qwen3:4b-instruct-2507-q4_K_M `
  --sim-url http://127.0.0.1:11434/v1 --sim-model qwen3:4b-instruct-2507-q4_K_M `
  --max-calls 500 --out data/runs/teste.jsonl
```

- `--max-calls` é o teto de chamadas da rodada (controle de gasto).
- As respostas ficam em cache em `.cache/llm`: rodar de novo não chama o modelo.
- Se a rodada parar no meio, rode o mesmo comando: ela continua de onde parou.

## 6. Filtrar e exportar o dataset de treino

```powershell
uv run labia filter data/runs/professor.jsonl --scenarios data/scenarios/train.jsonl --out data/sft/train.jsonl
```

Mostra quantas conversas passaram no filtro duplo e por que as outras foram reprovadas.

## 7. Avaliar os modelos de ponta pelas APIs gratuitas

O notebook `08-avaliacao-api` chama o DeepSeek (pelo teste gratuito da NVIDIA) e o Gemini (pela camada gratuita do Google AI Studio). As chaves ficam nos **Kaggle Secrets**: quem roda o notebook lê a chave, mas ela nunca aparece no código, na saída ou no git.

1. **NVIDIA:** em build.nvidia.com, entre (ou crie a conta gratuita), abra a página do DeepSeek-V4.1-Flash e clique em "Get API Key". Copie.
2. **Google:** em aistudio.google.com, entre com o Gmail e clique em "Get API key" e depois "Create API key". Copie.
3. **Kaggle:** abra kaggle.com/code/deniscarvalhotech/labia-08-avaliacao-api, clique em **Edit**, depois no menu **Add-ons → Secrets → Add Secret**:
   - Label `NVIDIA_API_KEY`, Value: a chave da NVIDIA;
   - Label `GOOGLE_AI_STUDIO_API_KEY`, Value: a chave do Google.
   Confira se os dois aparecem marcados como anexados a este notebook. Feche o editor sem rodar.

Nunca cole as chaves no chat, num print ou num arquivo do projeto. Os termos dessas camadas permitem só teste e avaliação: nada do que esses modelos escreverem entra no dado de treino.

## 8. A cadeia completa no Kaggle: gerar, treinar, avaliar

Cada notebook fixa o commit do código que usa (`LABIA_COMMIT`). O Kaggle permite **2 sessões de GPU ao mesmo tempo**, então a ordem importa. Envie cada notebook com:

```powershell
kaggle kernels push -p notebooks/<pasta> --accelerator NvidiaTeslaT4
kaggle kernels status deniscarvalhotech/<id-do-notebook>
```

| Ordem | Pasta | O que faz | Depende de | Tempo medido |
|---|---|---|---|---|
| 1 | `04-geracao-fatia-1` e `04-geracao-fatia-2` | o professor atende os cenários de treino (metade em cada) | nada | 4,0 h e 4,5 h |
| 2 | `05-avaliacao-base` | o modelo-base, com prompt padrão e reforçado, nos 212 cenários de teste × 3 rodadas | nada | — |
| 3 | `06-treino-sft` | treina com as conversas aprovadas, funde o adaptador e gera o GGUF | as duas fatias (`kernel_sources`) | — |
| 4 | `06-treino-sem-filtro` | a ablação: mesma configuração e mesmas épocas do treino principal, sem o filtro | as duas fatias | — |
| 5 | `07-avaliacao-sft` e `07-avaliacao-sem-filtro` | avaliam os modelos treinados, com o mesmo código da avaliação do base | o notebook de treino correspondente | — |

Os traços viram números quando cada execução terminar.

Para ligar um notebook ao outro, o `kernel-metadata.json` lista em `kernel_sources` os notebooks cuja saída ele lê. O Kaggle monta essa saída em `/kaggle/input/<id>/`.

Quando um notebook terminar, baixe a saída para `data/`:

```powershell
kaggle kernels output deniscarvalhotech/labia-04-geracao-fatia-1 -p data/geracao/fatia-1
```

## 9. Analisar no seu computador

Tudo daqui em diante roda sem GPU, a partir dos arquivos baixados:

```powershell
# o raio-x da geração: acertos do professor e composição do dado de treino
uv run labia generation-report data/geracao/fatia-1/geracao/runs.jsonl data/geracao/fatia-2/geracao/runs.jsonl

# das conversas da avaliação aos results/*.json reais, com as hipóteses e a análise de sensibilidade
uv run labia evaluate data/avaliacao/*.jsonl

# custo estimado por mil conversas e ponto de equilíbrio GPU própria × API (preços em configs/precos.json)
uv run labia cost data/avaliacao/*.jsonl --sessions data/avaliacao/*/resumo.json

# os gráficos (docs/img, tema claro e escuro), a seção de resultados do README e os cards do Hugging Face
make charts
uv run labia report
uv run labia cards
```

Todos esses comandos recusam dado de exemplo.

`labia evaluate` imprime as hipóteses H1 a H3 duas vezes: a análise principal e a de sensibilidade, sem os 2 cenários de gabarito contestável ([ADR 0008](decisoes/0008-gabarito-contestavel.md)).

## 10. A demo

Para ver a interface sem baixar o modelo, com um agente de regras fixas:

```powershell
cd space
$env:LABIA_AGENT = "scripted"; $env:LABIA_REPLAY = "../results/replay.json"
uv run --with gradio==6.31.0 python app.py
```

Abre em `http://127.0.0.1:7860`. Sem `LABIA_AGENT`, a aba "Tente enganar o agente" baixa o GGUF do Hugging Face e roda na CPU.

## 11. Publicar no Hugging Face

Crie um token de escrita em huggingface.co → Settings → Access Tokens e coloque-o no `.env` como `HF_TOKEN`. Nunca no chat, num print ou num commit.

```powershell
uv run python scripts/publicar_hf.py --gguf data/modelos/labia-sft-q8_0.gguf             # ensaio: mostra o que faria
uv run python scripts/publicar_hf.py --gguf data/modelos/labia-sft-q8_0.gguf --publicar  # publica de verdade
```

O script roda `labia publish-check` antes. Se algum arquivo de resultado for de exemplo, ele para.

## Problemas comuns

| Sintoma | Causa | Solução |
|---|---|---|
| `uv` ou `kaggle` "não é reconhecido" | o terminal abriu antes da instalação | feche e abra o terminal, ou rode a linha do PATH acima |
| `ModuleNotFoundError: No module named 'six'` no kaggle | defeito da versão 2.2.5 | `uv tool install kaggle --with six --reinstall` |
| erro de codificação ao instalar com Python 3.11 no Windows | o acento no nome da pasta | use o Python 3.13 (`.python-version` já pede) |
| o notebook do Kaggle não liga GPU | telefone não verificado | Settings do Kaggle, verificação por telefone |
| `Permission 'kernels.get' was denied` num notebook seu | o kaggle 2.2.5 não renova a credencial quando ela vence (a cada 12 h) e cai no modo anônimo | `& "$env:APPDATA\uv\tools\kaggle\Scripts\python.exe" scripts/kaggle_renovar_login.py` |
| `Maximum batch GPU session count of 2 reached` | o Kaggle permite só 2 sessões de GPU ao mesmo tempo | espere uma terminar e envie de novo |
| `make check` falha só no Windows por quebra de linha | arquivo gravado com CRLF | os geradores do projeto gravam LF; rode `make schemas` e `make scenarios` de novo |
