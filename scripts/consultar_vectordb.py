import pathlib
from sentence_transformers import SentenceTransformer
import chromadb

PASTA_BASE = pathlib.Path(".")
VECTORDB_PATH = PASTA_BASE / "vectordb"

MODELO_EMBEDDINGS = "intfloat/multilingual-e5-base"
NOME_COLECAO = "salazar"

N_RESULTADOS = 8


def cortar_texto(texto, limite=700):
    texto = texto.replace("\n", " ").strip()
    if len(texto) <= limite:
        return texto
    return texto[:limite].rstrip() + "..."


def consultar(pergunta, modelo, colecao):
    embedding = modelo.encode(
        "query: " + pergunta,
        normalize_embeddings=True
    ).tolist()

    resultados = colecao.query(
        query_embeddings=[embedding],
        n_results=N_RESULTADOS,
        include=["documents", "metadatas", "distances"]
    )

    documentos = resultados["documents"][0]
    metadados = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    print("\n" + "=" * 80)
    print(f"CONSULTA: {pergunta}")
    print("=" * 80)

    for i, (doc, meta, dist) in enumerate(zip(documentos, metadados, distancias), 1):
        print(f"\n--- Resultado {i} ---")
        print(f"Distância: {dist:.4f}")
        print(f"Título: {meta.get('titulo', '')}")
        print(f"Data: {meta.get('data', '')}")
        print(f"Género: {meta.get('genero', '')}")
        print(f"Tema principal: {meta.get('tema_principal', '')}")
        print(f"Temas: {meta.get('temas', '')}")
        print(f"Doc ID: {meta.get('doc_id', '')}")
        print()
        print(cortar_texto(doc))


def main():
    print("A carregar modelo de embeddings...")
    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    cliente = chromadb.PersistentClient(path=str(VECTORDB_PATH))
    colecao = cliente.get_collection(NOME_COLECAO)

    print(f"Coleção carregada: {NOME_COLECAO}")
    print(f"Total de chunks na coleção: {colecao.count()}")

    while True:
        pergunta = input("\nConsulta: ").strip()

        if pergunta.lower() in {"sair", "exit", "q"}:
            break

        if not pergunta:
            continue

        consultar(pergunta, modelo, colecao)


if __name__ == "__main__":
    main()