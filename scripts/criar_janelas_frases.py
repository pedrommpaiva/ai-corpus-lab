import json
import pathlib
import re
from statistics import mean, median

PASTA_BASE = pathlib.Path(".")
INPUT = PASTA_BASE / "corpus_mestre.json"
OUTPUT = PASTA_BASE / "corpus_janelas_frases.json"

MAX_CHARS = 500
MAX_FRASES = 5
MIN_CHARS = 80


ABREVIATURAS = [
    "V. Ex.ª", "V. Exa.", "Ex.ª", "Exa.", "Ex.mo", "Ex.mos",
    "Sr.", "Sra.", "Dr.", "Dra.", "D.", "Prof.",
    "etc.", "ibid.", "cit.", "ob. cit.", "M.me", "Mme."
]


def proteger_abreviaturas(texto):
    substituicoes = {}

    for i, abrev in enumerate(sorted(ABREVIATURAS, key=len, reverse=True)):
        protegido = abrev.replace(".", "<PONTO>")
        chave = f"__ABREV_{i}__"
        substituicoes[chave] = abrev
        texto = texto.replace(abrev, chave)

    return texto, substituicoes


def restaurar_abreviaturas(texto, substituicoes):
    for chave, abrev in substituicoes.items():
        texto = texto.replace(chave, abrev)
    return texto


def dividir_frases(texto):
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    if not texto:
        return []

    texto_protegido, substituicoes = proteger_abreviaturas(texto)

    frases = re.split(r"(?<=[.!?])\s+", texto_protegido)

    frases = [
        restaurar_abreviaturas(f.strip(), substituicoes)
        for f in frases
        if f.strip()
    ]

    return frases


def cortar_texto_longo(texto, max_chars=MAX_CHARS):
    partes = []
    texto = texto.strip()

    while len(texto) > max_chars:
        corte = texto.rfind("; ", 0, max_chars)
        if corte < max_chars * 0.5:
            corte = texto.rfind(", ", 0, max_chars)
        if corte < max_chars * 0.5:
            corte = texto.rfind(" ", 0, max_chars)
        if corte < max_chars * 0.5:
            corte = max_chars

        parte = texto[:corte].strip()
        if parte:
            partes.append(parte)

        texto = texto[corte:].strip()

    if texto:
        partes.append(texto)

    return partes


def criar_janelas_de_frases(frases):
    janelas = []
    i = 0

    while i < len(frases):
        frase_inicial = frases[i]

        # Se uma frase isolada já for enorme, divide-a.
        if len(frase_inicial) > MAX_CHARS:
            for parte in cortar_texto_longo(frase_inicial):
                janelas.append({
                    "texto": parte,
                    "n_frases": 1,
                    "tipo": "frase_longa_partida"
                })
            i += 1
            continue

        melhor_texto = ""
        melhor_n = 0

        for n in range(1, MAX_FRASES + 1):
            grupo = frases[i:i + n]
            if not grupo:
                break

            candidato = " ".join(grupo).strip()

            if len(candidato) <= MAX_CHARS:
                melhor_texto = candidato
                melhor_n = n
            else:
                break

        if melhor_texto and (len(melhor_texto) >= MIN_CHARS or melhor_n == 1):
            janelas.append({
                "texto": melhor_texto,
                "n_frases": melhor_n,
                "tipo": "janela_frases"
            })

        # Sobreposição móvel:
        # 1-3 frases: avança 1 frase.
        # 4-5 frases: avança 2 frases.
        if melhor_n >= 4:
            i += 2
        else:
            i += 1

    return janelas


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Não encontrei: {INPUT}")

    corpus = json.loads(INPUT.read_text(encoding="utf-8"))

    todas_janelas = []

    for doc in corpus:
        texto = doc["texto"]

        # Trabalha por parágrafos para evitar juntar zonas distantes.
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]

        indice = 0

        for p_index, paragrafo in enumerate(paragrafos):
            frases = dividir_frases(paragrafo)
            janelas = criar_janelas_de_frases(frases)

            for janela in janelas:
                item = {
                    "janela_id": f"{doc['id']}_j{indice:05d}",
                    "doc_id": doc["id"],
                    "janela_index": indice,
                    "paragrafo_index": p_index,
                    "titulo": doc.get("titulo", ""),
                    "data": doc.get("data", ""),
                    "ano": doc.get("ano", ""),
                    "fase": doc.get("fase", ""),
                    "periodo_interpretativo": doc.get("periodo_interpretativo", ""),
                    "genero": doc.get("genero", ""),
                    "tema_principal": doc.get("tema_principal", ""),
                    "temas": doc.get("temas", []),
                    "fonte": doc.get("fonte", ""),
                    "texto": janela["texto"],
                    "tipo": janela["tipo"],
                    "n_frases": janela["n_frases"],
                    "caracteres": len(janela["texto"]),
                    "palavras_aprox": len(janela["texto"].split())
                }

                todas_janelas.append(item)
                indice += 1

    OUTPUT.write_text(
        json.dumps(todas_janelas, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    tamanhos = [j["caracteres"] for j in todas_janelas]

    print("Janelas de frases criadas.")
    print(f"Documentos processados: {len(corpus)}")
    print(f"Janelas totais: {len(todas_janelas)}")
    print(f"Ficheiro criado: {OUTPUT}")

    if tamanhos:
        print(f"Média caracteres: {mean(tamanhos):.0f}")
        print(f"Mediana caracteres: {median(tamanhos):.0f}")
        print(f"Mínimo: {min(tamanhos)}")
        print(f"Máximo: {max(tamanhos)}")


if __name__ == "__main__":
    main()