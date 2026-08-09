import argparse
import json
from pathlib import Path

CHUNK_SIZE = 1600
OVERLAP = 250


def criar_chunks_texto(texto, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Divide text into overlapping chunks, preferring paragraph or sentence boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size tem de ser superior a zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap tem de estar entre zero e chunk_size - 1")

    chunks = []
    inicio = 0
    tamanho = len(texto)

    while inicio < tamanho:
        fim = min(inicio + chunk_size, tamanho)
        fragmento = texto[inicio:fim]
        corte_paragrafo = fragmento.rfind("\n\n")
        corte_frase = max(
            fragmento.rfind(". "),
            fragmento.rfind("! "),
            fragmento.rfind("? "),
        )

        if fim < tamanho:
            if corte_paragrafo > chunk_size * 0.55:
                fim = inicio + corte_paragrafo
            elif corte_frase > chunk_size * 0.55:
                fim = inicio + corte_frase + 1

        fragmento = texto[inicio:fim].strip()
        if fragmento:
            chunks.append(fragmento)

        novo_inicio = fim - overlap
        inicio = fim if novo_inicio <= inicio else novo_inicio

    return chunks


def criar_corpus_chunks(input_path, output_path, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    corpus = json.loads(input_path.read_text(encoding="utf-8"))
    todos_chunks = []

    for doc in corpus:
        fragmentos = criar_chunks_texto(doc.get("texto", ""), chunk_size, overlap)
        for i, fragmento in enumerate(fragmentos):
            todos_chunks.append(
                {
                    "chunk_id": f"{doc['id']}_{i:04d}",
                    "doc_id": doc["id"],
                    "chunk_index": i,
                    "titulo": doc.get("titulo", ""),
                    "data": doc.get("data", ""),
                    "ano": doc.get("ano", ""),
                    "fase": doc.get("fase", ""),
                    "periodo_interpretativo": doc.get("periodo_interpretativo", ""),
                    "genero": doc.get("genero", ""),
                    "tema_principal": doc.get("tema_principal", ""),
                    "temas": doc.get("temas", []),
                    "fonte": doc.get("fonte", ""),
                    "texto": fragmento,
                    "caracteres": len(fragmento),
                    "palavras_aprox": len(fragmento.split()),
                }
            )

    output_path.write_text(
        json.dumps(todos_chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return todos_chunks


def parse_args():
    parser = argparse.ArgumentParser(description="Cria chunks a partir do corpus-mestre.")
    parser.add_argument("--input", type=Path, default=Path("corpus_mestre.json"))
    parser.add_argument("--output", type=Path, default=Path("corpus_chunks.json"))
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=OVERLAP)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Não encontrei: {args.input}")

    chunks = criar_corpus_chunks(
        args.input, args.output, args.chunk_size, args.overlap
    )
    print("Chunks criados.")
    print(f"Chunks totais: {len(chunks)}")
    print(f"Ficheiro criado: {args.output}")
    if chunks:
        media = sum(chunk["caracteres"] for chunk in chunks) / len(chunks)
        print(f"Tamanho médio dos chunks: {media:.0f} caracteres")
    else:
        print("Nenhum chunk foi produzido; confirme se os documentos contêm texto.")


if __name__ == "__main__":
    main()
