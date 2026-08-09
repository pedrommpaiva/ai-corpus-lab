import argparse
from pathlib import Path


def contar_corpus(pasta):
    ficheiros = sorted(pasta.rglob("*.txt"))
    totais = {
        "ficheiros": len(ficheiros),
        "caracteres_com_espacos": 0,
        "caracteres_sem_espacos": 0,
        "palavras": 0,
        "linhas": 0,
    }

    for ficheiro in ficheiros:
        texto = ficheiro.read_text(encoding="utf-8", errors="replace")
        totais["caracteres_com_espacos"] += len(texto)
        totais["caracteres_sem_espacos"] += sum(
            1 for caractere in texto if not caractere.isspace()
        )
        totais["palavras"] += len(texto.split())
        totais["linhas"] += len(texto.splitlines())

    return totais


def main():
    parser = argparse.ArgumentParser(description="Conta ficheiros e texto num corpus TXT.")
    parser.add_argument("pasta", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args()
    if not args.pasta.is_dir():
        raise NotADirectoryError(f"Pasta inválida: {args.pasta}")

    totais = contar_corpus(args.pasta)
    print(f"Ficheiros TXT: {totais['ficheiros']}")
    print(f"Linhas: {totais['linhas']}")
    print(f"Caracteres com espaços: {totais['caracteres_com_espacos']}")
    print(f"Caracteres sem espaços: {totais['caracteres_sem_espacos']}")
    print(f"Palavras aproximadas: {totais['palavras']}")


if __name__ == "__main__":
    main()
