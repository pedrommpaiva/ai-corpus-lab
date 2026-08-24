import json
import pathlib
from sentence_transformers import SentenceTransformer
import chromadb

PASTA_BASE = pathlib.Path(".")
INPUT = PASTA_BASE / "corpus_chunks.json"
VECTORDB_PATH = PASTA_BASE / "vectordb"

MODELO_EMBEDDINGS = "intfloat/multilingual-e5-base"
NOME_COLECAO = "salazar"

BATCH_SIZE = 32


def metadata_chroma(chunk):
    """
    O Chroma não gosta de listas como metadata.
    Por isso, temas vira string.
    """
    temas = chunk.get("temas", [])
    if isinstance(temas, list):
        temas = ";".join(temas)

    return {
        "doc_id": chunk.get("doc_id", ""),
        "chunk_index": int(chunk.get("chunk_index", 0)),
        "titulo": chunk.get("titulo", ""),
        "data": chunk.get("data", ""),
        "ano": chunk.get("ano", ""),
        "fase": chunk.get("fase", ""),
        "periodo_interpretativo": chunk.get("periodo_interpretativo", ""),
        "genero": chunk.get("genero", ""),
        "tema_principal": chunk.get("tema_principal", ""),
        "temas": temas,
        "fonte": chunk.get("fonte", ""),
        "caracteres": int(chunk.get("caracteres", 0)),
        "palavras_aprox": int(chunk.get("palavras_aprox", 0)),
    }


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Não encontrei: {INPUT}")

    chunks = json.loads(INPUT.read_text(encoding="utf-8"))

    print(f"Chunks carregados: {len(chunks)}")
    print(f"A carregar modelo: {MODELO_EMBEDDINGS}")

    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    cliente = chromadb.PersistentClient(path=str(VECTORDB_PATH))
    colecao = cliente.get_or_create_collection(NOME_COLECAO)

    total = len(chunks)

    for inicio in range(0, total, BATCH_SIZE):
        lote = chunks[inicio:inicio + BATCH_SIZE]

        ids = [chunk["chunk_id"] for chunk in lote]
        textos = [chunk["texto"] for chunk in lote]

        # Prefixo recomendado para modelos E5 em documentos
        textos_para_embedding = ["passage: " + texto for texto in textos]

        embeddings = modelo.encode(
            textos_para_embedding,
            normalize_embeddings=True
        ).tolist()

        metadatas = [metadata_chroma(chunk) for chunk in lote]

        colecao.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=textos,
            metadatas=metadatas
        )

        print(f"Indexados {min(inicio + BATCH_SIZE, total)}/{total}")

    print("\nIndexação concluída.")
    print(f"Base vetorial: {VECTORDB_PATH}")
    print(f"Coleção: {NOME_COLECAO}")
    print(f"Total na coleção: {colecao.count()}")


if __name__ == "__main__":
    main()