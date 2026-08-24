import json
import re
import shutil
import unicodedata
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# =========================
# CONFIGURAÇÃO
# =========================

INPUT_JSONL = Path("corpus_janelas.jsonl")

VECTORDB_DIR = Path("vectordb_janelas")
COLLECTION_NAME = "salazar_janelas_v1"

MODEL_NAME = "intfloat/multilingual-e5-base"

RESET_COLLECTION = True

BATCH_SIZE = 64

MIN_CHARS = 25

DROP_EXACT_DUPLICATES = True

# Só elimina blocos longos se parecerem tabela/bloco numérico.
NUMERIC_TABLE_MIN_CHARS = 2500
NUMERIC_DENSITY_LIMIT = 0.18


# =========================
# FILTROS
# =========================

def normalizar_texto_para_duplicado(texto: str) -> str:
    texto = texto.strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def parece_lixo_curto(texto: str) -> bool:
    texto = texto.strip()

    if len(texto) < MIN_CHARS:
        return True

    # Ex.: I., II., V., S., a), b), 1., etc.
    if re.fullmatch(r"[IVXLCDMivxlcdm]+\.?", texto):
        return True

    if re.fullmatch(r"[A-Za-z]\)?\.?", texto):
        return True

    if re.fullmatch(r"\d+\.?", texto):
        return True

    return False


def densidade_numerica(texto: str) -> float:
    if not texto:
        return 0.0

    caracteres = len(texto)
    algarismos = sum(1 for c in texto if c.isdigit())

    return algarismos / caracteres


def parece_tabela_numerica_longa(texto: str) -> bool:
    texto = texto.strip()

    if len(texto) < NUMERIC_TABLE_MIN_CHARS:
        return False

    if densidade_numerica(texto) >= NUMERIC_DENSITY_LIMIT:
        return True

    # Muitos padrões de frações antigas: 53 1/8, 42 13/16, etc.
    fracoes = re.findall(r"\b\d+\s+\d+/\d+\b", texto)

    if len(fracoes) >= 20:
        return True

    return False


# =========================
# METADADOS
# =========================

def normalizar_chave(chave: str) -> str:
    chave = chave.strip().lower()
    chave = unicodedata.normalize("NFKD", chave)
    chave = "".join(c for c in chave if not unicodedata.combining(c))
    chave = re.sub(r"[^a-z0-9_]+", "_", chave)
    chave = re.sub(r"_+", "_", chave)
    return chave.strip("_")


def valor_metadata_valido(valor):
    if valor is None:
        return ""

    if isinstance(valor, (str, int, float, bool)):
        return valor

    if isinstance(valor, list):
        return "; ".join(str(v) for v in valor)

    return str(valor)


def achatar_metadados(entry: dict) -> dict:
    metadata = {
        "janela_id": valor_metadata_valido(entry.get("janela_id", "")),
        "doc_id": valor_metadata_valido(entry.get("doc_id", "")),
        "ficheiro": valor_metadata_valido(entry.get("ficheiro", "")),
        "window_size": int(entry.get("window_size", 0)),
        "sentence_start": int(entry.get("sentence_start", 0)),
        "sentence_end": int(entry.get("sentence_end", 0)),
    }

    metadados_originais = entry.get("metadados", {})

    if isinstance(metadados_originais, dict):
        for chave, valor in metadados_originais.items():
            chave_norm = normalizar_chave(chave)

            if not chave_norm:
                continue

            # Evita colisões com os campos principais.
            if chave_norm in metadata:
                chave_norm = f"meta_{chave_norm}"

            metadata[chave_norm] = valor_metadata_valido(valor)

    # Chroma não aceita valores None nem objetos aninhados.
    metadata = {
        k: valor_metadata_valido(v)
        for k, v in metadata.items()
        if v is not None
    }

    return metadata


# =========================
# LEITURA
# =========================

def carregar_janelas():
    total_lidas = 0
    total_aceites = 0
    ignoradas_curto = 0
    ignoradas_tabela = 0
    ignoradas_duplicado = 0
    linhas_invalidas = 0

    textos_vistos = set()

    entradas = []

    with INPUT_JSONL.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            total_lidas += 1

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                linhas_invalidas += 1
                continue

            texto = entry.get("texto", "")

            if parece_lixo_curto(texto):
                ignoradas_curto += 1
                continue

            if parece_tabela_numerica_longa(texto):
                ignoradas_tabela += 1
                continue

            texto_norm = normalizar_texto_para_duplicado(texto)

            if DROP_EXACT_DUPLICATES:
                if texto_norm in textos_vistos:
                    ignoradas_duplicado += 1
                    continue

                textos_vistos.add(texto_norm)

            entradas.append(entry)
            total_aceites += 1

    estatisticas = {
        "total_lidas": total_lidas,
        "total_aceites": total_aceites,
        "ignoradas_curto": ignoradas_curto,
        "ignoradas_tabela": ignoradas_tabela,
        "ignoradas_duplicado": ignoradas_duplicado,
        "linhas_invalidas": linhas_invalidas,
    }

    return entradas, estatisticas


# =========================
# INDEXAÇÃO
# =========================

def criar_colecao():
    if RESET_COLLECTION and VECTORDB_DIR.exists():
        shutil.rmtree(VECTORDB_DIR)

    client = chromadb.PersistentClient(path=str(VECTORDB_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def indexar():
    entradas, stats = carregar_janelas()

    print("Janelas lidas:", stats["total_lidas"])
    print("Janelas aceites:", stats["total_aceites"])
    print("Ignoradas por lixo curto:", stats["ignoradas_curto"])
    print("Ignoradas por tabela/bloco numérico longo:", stats["ignoradas_tabela"])
    print("Ignoradas por duplicado exato:", stats["ignoradas_duplicado"])
    print("Linhas inválidas:", stats["linhas_invalidas"])
    print()

    if not entradas:
        raise RuntimeError("Nenhuma janela válida para indexar.")

    print("A carregar modelo de embeddings...")
    model = SentenceTransformer(MODEL_NAME)

    print("A criar/abrir ChromaDB...")
    collection = criar_colecao()

    total = len(entradas)

    for start in range(0, total, BATCH_SIZE):
        batch = entradas[start:start + BATCH_SIZE]

        ids = [entry["janela_id"] for entry in batch]
        documents = [entry["texto"] for entry in batch]
        metadatas = [achatar_metadados(entry) for entry in batch]

        textos_para_embedding = [
            "passage: " + entry["texto"]
            for entry in batch
        ]

        embeddings = model.encode(
            textos_para_embedding,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        print(f"Indexadas {min(start + BATCH_SIZE, total)} / {total}")

    print()
    print("Indexação concluída.")
    print("Base:", VECTORDB_DIR)
    print("Coleção:", COLLECTION_NAME)
    print("Total na coleção:", collection.count())


if __name__ == "__main__":
    indexar()