import json
import csv
import pathlib
import re
import unicodedata

PASTA_BASE = pathlib.Path(".")
PASTA_CORPUS = PASTA_BASE / "corpus"
OUTPUT = PASTA_BASE / "metadados_corpus.csv"


def normalizar(s):
    """Remove acentos, espaços e sinais para comparar nomes."""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def inferir_fase(data):
    """Classificação provisória por data."""
    if not data:
        return "por_classificar"

    ano_match = re.search(r"\d{4}", data)
    if not ano_match:
        return "por_classificar"

    ano = int(ano_match.group())

    if ano <= 1910:
        return "jovem_catolico_seminarista"
    elif ano <= 1927:
        return "pre_poder_catolico_social"
    elif ano <= 1932:
        return "entrada_no_poder_financeira"
    elif ano <= 1939:
        return "consolidacao_estado_novo"
    elif ano <= 1945:
        return "guerra_neutralidade"
    elif ano <= 1960:
        return "pos_guerra_estado_novo"
    else:
        return "fase_tardia_ultramar"


def inferir_temas(titulo, genero, contexto):
    """Inferência muito provisória a partir de palavras-chave."""
    texto = f"{titulo} {genero} {contexto}".lower()

    regras = {
        "religiao": ["jesus", "maria", "oração", "resurrexit", "deus", "católico", "religião"],
        "imprensa": ["imprensa", "propaganda", "jornal"],
        "educacao": ["escola", "educação", "ensino", "aluno", "professor"],
        "financas": ["financeira", "finanças", "económicos", "produção industrial"],
        "estado": ["estado", "governo", "ditadura", "constituição"],
        "revolucao_nacional": ["revolução", "nacional"],
        "corporativismo": ["corporativa", "corporação", "intp"],
        "exercito": ["exército", "militares", "virtudes militares"],
        "colonial": ["colonial", "brasil", "ultramar"],
        "patria_nacao": ["nação", "pátria", "portugueses", "portugal"],
    }

    temas = []
    for tema, palavras in regras.items():
        if any(p in texto for p in palavras):
            temas.append(tema)

    return ";".join(temas) if temas else "por_classificar"


def encontrar_txt_correspondente(doc, txts):
    """Tenta ligar o JSON ao TXT correspondente."""
    candidatos = []

    id_norm = normalizar(doc.get("id", ""))
    titulo_norm = normalizar(doc.get("titulo", ""))

    for txt in txts:
        stem_norm = normalizar(txt.stem)

        score = 0
        if stem_norm and stem_norm in id_norm:
            score += 2
        if stem_norm and stem_norm in titulo_norm:
            score += 3
        if titulo_norm and titulo_norm in stem_norm:
            score += 3

        if score > 0:
            candidatos.append((score, txt.name))

    if not candidatos:
        return ""

    candidatos.sort(reverse=True)
    return candidatos[0][1]


# TXT disponíveis na raiz
txts = list(PASTA_BASE.glob("*.txt"))

# JSON integrais: exclui chunks
jsons = sorted([
    f for f in PASTA_CORPUS.glob("*.json")
    if "_chunks" not in f.name
])

linhas = []

for path in jsons:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Erro ao ler {path.name}: {e}")
        continue

    texto = doc.get("texto", "")
    titulo = doc.get("titulo", "")
    genero = doc.get("genero", "")
    contexto = doc.get("contexto", "")
    data = doc.get("data", "")

    linha = {
        "id": doc.get("id", path.stem),
        "ficheiro_json": path.name,
        "ficheiro_txt": encontrar_txt_correspondente(doc, txts),
        "titulo": titulo,
        "data": data,
        "precisao_data": doc.get("precisao_data", ""),
        "fase": inferir_fase(data),
        "genero": genero,
        "temas": inferir_temas(titulo, genero, contexto),
        "fonte": doc.get("fonte", ""),
        "estado_texto": "limpo",
        "caracteres": len(texto),
        "palavras_aprox": len(texto.split()),
        "notas": contexto,
    }

    linhas.append(linha)


campos = [
    "id",
    "ficheiro_json",
    "ficheiro_txt",
    "titulo",
    "data",
    "precisao_data",
    "fase",
    "genero",
    "temas",
    "fonte",
    "estado_texto",
    "caracteres",
    "palavras_aprox",
    "notas",
]

with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=campos, delimiter=";")
    writer.writeheader()
    writer.writerows(linhas)

print(f"Metadados criados em: {OUTPUT}")
print(f"Documentos processados: {len(linhas)}")