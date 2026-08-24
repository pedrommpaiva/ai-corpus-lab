# Corpus Salazar — RAG sobre discursos e escritos

Pipeline de construção e interrogação de um corpus textual dos discursos e escritos de António de Oliveira Salazar, com recuperação semântica (RAG) sobre uma base vetorial.

## O que este projeto é — e o que não é

É uma ferramenta para **interrogar** um corpus histórico: fazer uma pergunta, recuperar as passagens que lhe respondem, e ler o que foi efetivamente dito, com a fonte à vista.

**Não é um sistema de personificação.** A proibição está escrita no próprio código. O `scripts/gerar_ficha_intermedia.py`, que traduz perguntas em consultas ao corpus, tem isto no seu *prompt* de sistema:

> Não respondas à pergunta.
> Não simules Salazar.
> Apenas traduz a pergunta para uma forma pesquisável no corpus.

Esta distinção é deliberada e é a decisão de desenho mais importante do projeto. Um corpus de discursos de um chefe de Estado autoritário é material que se presta a mau uso — gerar texto novo na voz dele, atribuir-lhe posições que não tomou, produzir citações que não existem. O sistema está construído para recuperar e citar, não para gerar na primeira pessoa.

## Porquê este corpus

Os discursos de Salazar são uma fonte primária central para o estudo do Estado Novo, e estão dispersos por edições que não são pesquisáveis de forma útil. Tornar um corpus destes interrogável — com metadados de proveniência preservados em cada fragmento — é trabalho de história aplicada. A escolha do objeto não é uma aprovação dele.

## Estrutura

### Construção do corpus

| Script | Função |
|---|---|
| `criar_corpus_mestre.py` | Constrói o corpus mestre em JSON a partir dos TXT e dos metadados em CSV. |
| `criar_metadados.py`, `atualizar_metadados.py` | Criação e atualização da tabela de metadados por documento. |
| `agregadordefrases.py` | Extração de frases, com tratamento das abreviaturas correntes em português. |
| `criar_chunks.py` | Fragmentos longos sobrepostos, preservando os metadados do documento de origem. |
| `criar_janelas_frases.py`, `gerar_janelas.py` | Janelas de frases — a unidade de recuperação mais fina. |
| `contador.py`, `count_corpus.py` | Contagens de documentos, palavras e tokens. |

### Indexação e consulta

| Script | Função |
|---|---|
| `indexar_vectordb.py`, `indexar_janelas_vectordb.py` | Indexação das duas granularidades em base vetorial. |
| `indexar_janelas_chroma.py` | Indexação em ChromaDB. |
| `consultar_vectordb.py` | Consulta por semelhança semântica. |
| `sondar_janelas.py` | Sondagem manual do índice, para inspecionar o que é recuperado. |
| `gerar_ficha_intermedia.py` | Traduz uma pergunta em consulta ao corpus, sem lhe responder. |
| `pipeline_reindexar_corpus.py` | Reconstrução completa: corpus, fragmentos, janelas e reindexação. |
| `comparar_chunks_frases.py` | Compara o que cada granularidade recupera para a mesma consulta. |

## Duas granularidades

O corpus é indexado duas vezes: em fragmentos longos sobrepostos e em janelas de frases. Fragmentos longos dão contexto mas diluem a consulta; janelas de frases são precisas mas perdem o fio do argumento. Nenhuma das duas serve para tudo, e o `comparar_chunks_frases.py` existe para tornar essa diferença observável em vez de teórica.

## Dados

**O corpus não está aqui.** O repositório contém o código e um pequeno exemplo neutro em `examples/`. Os textos de origem têm estatutos de direitos variáveis e a sua reunião é trabalho do utilizador.

## Dependências

Ver `requirements.txt`. As principais são `chromadb`, `sentence-transformers` e `pandas`.

## Limitações

A qualidade da recuperação não foi avaliada formalmente — não há conjunto de perguntas de referência nem medição de precisão. Os metadados de proveniência foram construídos à mão e podem conter erros. Há testes automatizados apenas para as funções de fragmentação; o resto do pipeline não é testado.
## Authorship

These repositories are built by AI systems under my direction. I do not write the code.

What I bring is the domain — judicial transcription, Portuguese public-contracting data, archival sources — the formulation of the problem, and the verification of the output against the sources it claims to describe.

I publish them because the methods are worth showing and because the results are checkable. Read them as documented working practice, not as a portfolio of software engineering.
