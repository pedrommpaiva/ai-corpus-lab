import json
import pathlib
import re
from statistics import mean, median

CORPUS_MESTRE = pathlib.Path("corpus_mestre.json")
CORPUS_CHUNKS = pathlib.Path("corpus_chunks.json")


def dividir_frases(texto):
    """
    Divisão simples por pontuação final.
    Não é perfeita, mas chega para estimar tamanhos.
    """
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    frases = re.split(r"(?<=[.!?])\s+", texto)
    frases = [f.strip() for f in frases if f.strip()]

    return frases


def criar_janelas(frases, tamanho_janela, passo):
    janelas = []

    for i in range(0, len(frases), passo):
        janela = frases[i:i + tamanho_janela]
        if len(janela) < 1:
            continue
        texto = " ".join(janela)
        janelas.append(texto)

    return janelas


def estatisticas(nome, textos):
    tamanhos = [len(t) for t in textos if t.strip()]

    if not tamanhos:
        print(f"{nome}: sem dados")
        return

    print(f"\n{nome}")
    print("-" * 60)
    print(f"Número de blocos: {len(tamanhos)}")
    print(f"Média caracteres: {mean(tamanhos):.0f}")
    print(f"Mediana caracteres: {median(tamanhos):.0f}")
    print(f"Mínimo: {min(tamanhos)}")
    print(f"Máximo: {max(tamanhos)}")


def main():
    corpus = json.loads(CORPUS_MESTRE.read_text(encoding="utf-8"))
    chunks_atuais = json.loads(CORPUS_CHUNKS.read_text(encoding="utf-8"))

    textos_integrais = [doc["texto"] for doc in corpus]
    todos_chunks_atuais = [chunk["texto"] for chunk in chunks_atuais]

    todas_frases = []
    for texto in textos_integrais:
        todas_frases.extend(dividir_frases(texto))

    estatisticas("Chunks atuais", todos_chunks_atuais)
    estatisticas("Frases isoladas", todas_frases)

    configuracoes = [
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 2),
        (6, 3),
        (8, 4),
    ]

    for tamanho_janela, passo in configuracoes:
        todas_janelas = []

        for texto in textos_integrais:
            frases = dividir_frases(texto)
            janelas = criar_janelas(frases, tamanho_janela, passo)
            todas_janelas.extend(janelas)

        nome = f"Janelas de {tamanho_janela} frases, passo {passo}"
        estatisticas(nome, todas_janelas)


if __name__ == "__main__":
    main()