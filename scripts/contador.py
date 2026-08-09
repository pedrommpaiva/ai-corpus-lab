import argparse
import re
from pathlib import Path


def contar_texto(path):
    texto = path.read_text(encoding="utf-8")
    palavras = re.findall(
        r"\b[\wÀ-ÿ]+(?:[-'][\wÀ-ÿ]+)?\b", texto, flags=re.UNICODE
    )
    linhas = [linha for linha in texto.splitlines() if linha.strip()]
    return {
        "caracteres_com_espacos": len(texto),
        "caracteres_sem_espacos": len(re.sub(r"\s+", "", texto)),
        "palavras": len(palavras),
        "linhas": len(linhas),
    }


def main():
    parser = argparse.ArgumentParser(description="Conta texto num ficheiro UTF-8.")
    parser.add_argument("ficheiro", type=Path)
    args = parser.parse_args()
    if not args.ficheiro.is_file():
        raise FileNotFoundError(f"Não encontrei: {args.ficheiro}")

    totais = contar_texto(args.ficheiro)
    print(f"Ficheiro: {args.ficheiro}")
    print(f"Linhas/frases: {totais['linhas']}")
    print(f"Caracteres com espaços: {totais['caracteres_com_espacos']:,}")
    print(f"Caracteres sem espaços: {totais['caracteres_sem_espacos']:,}")
    print(f"Palavras aproximadas: {totais['palavras']:,}")
    print(f"Tokens estimados: {int(totais['caracteres_com_espacos'] / 4):,}")

    try:
        import tiktoken
    except ImportError:
        print("tiktoken não instalado; a contagem exata foi omitida.")
    else:
        tokens = len(tiktoken.get_encoding("cl100k_base").encode(args.ficheiro.read_text(encoding="utf-8")))
        print(f"Tokens cl100k_base: {tokens:,}")


if __name__ == "__main__":
    main()
