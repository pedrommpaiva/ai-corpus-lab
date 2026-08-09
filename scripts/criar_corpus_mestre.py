import argparse
import csv
import json
import pathlib


def ler_csv(path):
    """
    Lê o CSV com separador ;.
    O encoding utf-8-sig evita problemas com BOM do Excel/Windows.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def separar_temas(valor):
    """
    Transforma 'imprensa;religiao;ordem_moral'
    em ['imprensa', 'religiao', 'ordem_moral'].
    """
    if not valor:
        return []
    return [t.strip() for t in valor.split(";") if t.strip()]


def parse_args():
    parser = argparse.ArgumentParser(description="Cria um corpus JSON a partir de CSV e TXT.")
    parser.add_argument("--metadata", type=pathlib.Path, default=pathlib.Path("metadados_corpus_revisto.csv"))
    parser.add_argument("--text-dir", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("corpus_mestre.json"))
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.metadata.exists():
        raise FileNotFoundError(f"Não encontrei: {args.metadata}")

    linhas = ler_csv(args.metadata)

    corpus = []
    erros = []

    for linha in linhas:
        ficheiro_txt = linha.get("ficheiro_txt", "").strip()

        if not ficheiro_txt:
            erros.append({
                "id": linha.get("id", ""),
                "erro": "ficheiro_txt vazio"
            })
            continue

        caminho_txt = args.text_dir / ficheiro_txt

        if not caminho_txt.exists():
            erros.append({
                "id": linha.get("id", ""),
                "ficheiro_txt": ficheiro_txt,
                "erro": "ficheiro TXT não encontrado"
            })
            continue

        texto = caminho_txt.read_text(encoding="utf-8")

        doc = {
            "id": linha.get("id", "").strip(),
            "ficheiro_txt": ficheiro_txt,
            "ficheiro_json_original": linha.get("ficheiro_json", "").strip(),
            "titulo": linha.get("titulo", "").strip(),
            "data": linha.get("data", "").strip(),
            "ano": linha.get("ano", "").strip(),
            "precisao_data": linha.get("precisao_data", "").strip(),
            "fase": linha.get("fase", "").strip(),
            "periodo_interpretativo": linha.get("periodo_interpretativo", "").strip(),
            "genero": linha.get("genero", "").strip(),
            "tema_principal": linha.get("tema_principal", "").strip(),
            "temas": separar_temas(linha.get("temas", "")),
            "fonte": linha.get("fonte", "").strip(),
            "estado_texto": linha.get("estado_texto", "").strip(),
            "notas": linha.get("notas", "").strip(),
            "caracteres": len(texto),
            "palavras_aprox": len(texto.split()),
            "texto": texto
        }

        corpus.append(doc)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    print("Corpus-mestre criado.")
    print(f"Documentos incluídos: {len(corpus)}")
    print(f"Erros: {len(erros)}")
    print(f"Ficheiro criado: {args.output}")

    total_chars = sum(doc["caracteres"] for doc in corpus)
    total_words = sum(doc["palavras_aprox"] for doc in corpus)

    print(f"Caracteres totais: {total_chars:,}".replace(",", " "))
    print(f"Palavras aproximadas: {total_words:,}".replace(",", " "))

    if erros:
        print("\nERROS ENCONTRADOS:")
        for erro in erros:
            print(erro)


if __name__ == "__main__":
    main()
