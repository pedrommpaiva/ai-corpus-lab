import json
import pathlib
from sentence_transformers import SentenceTransformer
import chromadb

PASTA_BASE = pathlib.Path(".")
INPUT = PASTA_BASE / "corpus_janelas_frases.json"
VECTORDB_PATH = PASTA_BASE / "vectordb"

MODELO_EMBEDDINGS = "intfloat/multilingual-e5-base"
NOME_COLECAO = "salazar_janelas"

BATCH_SIZE = 64
MIN_CARACTERES = 40


def metadata_chroma(janela):
    temas = janela.get("temas", [])
    if isinstance(temas, list):
        temas = ";".join(temas)

    return {
        "doc_id": janela.get("doc_id", ""),
        "janela_index": int(janela.get("janela_index", 0)),
        "paragrafo_index": int(janela.get("paragrafo_index", 0)),
        "titulo": janela.get("titulo", ""),
        "data": janela.get("data", ""),
        "ano": janela.get("ano", ""),
        "fase": janela.get("fase", ""),
        "periodo_interpretativo": janela.get("periodo_interpretativo", ""),
        "genero": janela.get("genero", ""),
        "tema_principal": janela.get("tema_principal", ""),
        "temas": temas,
        "fonte": janela.get("fonte", ""),
        "tipo": janela.get("tipo", ""),
        "n_frases": int(janela.get("n_frases", 0)),
        "caracteres": int(janela.get("caracteres", 0)),
        "palavras_aprox": int(janela.get("palavras_aprox", 0)),
    }


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Não encontrei: {INPUT}")

    janelas = json.loads(INPUT.read_text(encoding="utf-8"))

    janelas_validas = [
        j for j in janelas
        if len(j.get("texto", "").strip()) >= MIN_CARACTERES
    ]

    ignoradas = len(janelas) - len(janelas_validas)

    print(f"Janelas carregadas: {len(janelas)}")
    print(f"Janelas válidas: {len(janelas_validas)}")
    print(f"Janelas ignoradas por serem demasiado curtas: {ignoradas}")
    print(f"A carregar modelo: {MODELO_EMBEDDINGS}")

    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    cliente = chromadb.PersistentClient(path=str(VECTORDB_PATH))

    # Recria a coleção do zero para evitar restos de versões anteriores
    try:
        cliente.delete_collection(NOME_COLECAO)
        print(f"Coleção antiga removida: {NOME_COLECAO}")
    except Exception:
        pass

    colecao = cliente.create_collection(NOME_COLECAO)

    total = len(janelas_validas)

    for inicio in range(0, total, BATCH_SIZE):
        lote = janelas_validas[inicio:inicio + BATCH_SIZE]

        ids = [j["janela_id"] for j in lote]
        textos = [j["texto"] for j in lote]

        textos_para_embedding = ["passage: " + texto for texto in textos]

        embeddings = modelo.encode(
            textos_para_embedding,
            normalize_embeddings=True
        ).tolist()

        metadatas = [metadata_chroma(j) for j in lote]

        colecao.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=textos,
            metadatas=metadatas
        )

        print(f"Indexadas {min(inicio + BATCH_SIZE, total)}/{total}")

    print("\nIndexação das janelas concluída.")
    print(f"Base vetorial: {VECTORDB_PATH}")
    print(f"Coleção: {NOME_COLECAO}")
    print(f"Total na coleção: {colecao.count()}")


if __name__ == "__main__":
    main()