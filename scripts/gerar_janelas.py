import csv
import json
import re
from pathlib import Path


# === AJUSTAR SE NECESSÁRIO ===

TXT_DIR = Path(".")
METADATA_CSV = Path("metadados/metadados_corpus.csv")
OUTPUT_JSONL = Path("corpus_janelas.jsonl")


# === CONFIGURAÇÃO DAS JANELAS ===

WINDOW_CONFIG = {
    1: 1,  # janela 1, avanço 1
    2: 1,  # janela 2, sobreposição 1
    3: 1,  # janela 3, sobreposição 2
    4: 2,  # janela 4, sobreposição 2
    5: 2,  # janela 5, sobreposição 3
}


# === FUNÇÕES ===

def detectar_delimitador(csv_path: Path) -> str:
    amostra = csv_path.read_text(encoding="utf-8-sig")[:5000]
    try:
        return csv.Sniffer().sniff(amostra).delimiter
    except Exception:
        return ";"


def ler_metadados(csv_path: Path) -> list[dict]:
    delimitador = detectar_delimitador(csv_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimitador)
        return list(reader)


def encontrar_coluna_ficheiro(colunas: list[str]) -> str | None:
    candidatos = [
        "ficheiro",
        "ficheiro_txt",
        "arquivo",
        "filename",
        "file",
        "txt",
        "path",
        "caminho",
        "nome_ficheiro",
    ]

    colunas_norm = {c.lower().strip(): c for c in colunas}

    for candidato in candidatos:
        if candidato in colunas_norm:
            return colunas_norm[candidato]

    return None


def encontrar_coluna_doc_id(colunas: list[str]) -> str | None:
    candidatos = [
        "doc_id",
        "id",
        "codigo",
        "código",
        "identificador",
    ]

    colunas_norm = {c.lower().strip(): c for c in colunas}

    for candidato in candidatos:
        if candidato in colunas_norm:
            return colunas_norm[candidato]

    return None


def normalizar_espacos(texto: str) -> str:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def dividir_em_frases(texto: str) -> list[str]:
    """
    Segmentador simples para português.
    Não é perfeito, mas é suficiente para primeira versão.
    Evita algumas quebras erradas em abreviaturas comuns.
    """

    texto = normalizar_espacos(texto)

    abreviaturas = [
        "Sr.", "Sra.", "Dr.", "Dra.", "Prof.", "Exmo.", "Exma.",
        "V. Exa.", "V. Ex.ª", "S. Exa.", "S. Ex.ª",
        "etc.", "pág.", "pp.", "n.º", "art.", "vol.",
    ]

    placeholders = {}

    for i, abrev in enumerate(abreviaturas):
        placeholder = f"__ABREV_{i}__"
        placeholders[placeholder] = abrev
        texto = texto.replace(abrev, placeholder)

    # Quebra depois de ponto, ponto de interrogação ou exclamação,
    # quando seguidos de espaço e letra maiúscula ou quebra de linha.
    partes = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÀÇ])", texto)

    frases = []

    for parte in partes:
        for placeholder, abrev in placeholders.items():
            parte = parte.replace(placeholder, abrev)

        parte = parte.strip()

        if parte:
            frases.append(parte)

    return frases


def resolver_txt(row: dict, coluna_ficheiro: str | None, coluna_doc_id: str | None) -> Path | None:
    if coluna_ficheiro:
        nome = row.get(coluna_ficheiro, "").strip()

        if nome:
            path = TXT_DIR / nome

            if path.exists():
                return path

            if not nome.lower().endswith(".txt"):
                path = TXT_DIR / f"{nome}.txt"

                if path.exists():
                    return path

    if coluna_doc_id:
        doc_id = row.get(coluna_doc_id, "").strip()

        if doc_id:
            path = TXT_DIR / f"{doc_id}.txt"

            if path.exists():
                return path

    return None


def gerar_janelas(frases: list[str], window_size: int, step: int) -> list[tuple[int, int, str]]:
    janelas = []

    if len(frases) < window_size:
        return janelas

    for start in range(0, len(frases) - window_size + 1, step):
        end = start + window_size - 1
        texto = " ".join(frases[start:start + window_size]).strip()
        janelas.append((start + 1, end + 1, texto))

    return janelas


# === EXECUÇÃO PRINCIPAL ===

def main():
    rows = ler_metadados(METADATA_CSV)

    if not rows:
        raise RuntimeError("O ficheiro de metadados está vazio.")

    colunas = list(rows[0].keys())

    coluna_ficheiro = encontrar_coluna_ficheiro(colunas)
    coluna_doc_id = encontrar_coluna_doc_id(colunas)

    total_docs = 0
    total_frases = 0
    total_janelas = 0
    docs_sem_txt = []

    with OUTPUT_JSONL.open("w", encoding="utf-8") as out:
        for row in rows:
            txt_path = resolver_txt(row, coluna_ficheiro, coluna_doc_id)

            if txt_path is None:
                docs_sem_txt.append(row)
                continue

            texto = txt_path.read_text(encoding="utf-8")
            frases = dividir_em_frases(texto)

            if not frases:
                continue

            total_docs += 1
            total_frases += len(frases)

            doc_id = None

            if coluna_doc_id:
                doc_id = row.get(coluna_doc_id, "").strip()

            if not doc_id:
                doc_id = txt_path.stem

            for window_size, step in WINDOW_CONFIG.items():
                janelas = gerar_janelas(frases, window_size, step)

                for sentence_start, sentence_end, texto_janela in janelas:
                    janela_id = f"{doc_id}_w{window_size}_f{sentence_start}_{sentence_end}"

                    entrada = {
                        "janela_id": janela_id,
                        "doc_id": doc_id,
                        "ficheiro": txt_path.name,
                        "window_size": window_size,
                        "sentence_start": sentence_start,
                        "sentence_end": sentence_end,
                        "texto": texto_janela,
                        "metadados": row,
                    }

                    out.write(json.dumps(entrada, ensure_ascii=False) + "\n")
                    total_janelas += 1

    print("Ficheiro criado:", OUTPUT_JSONL)
    print("Documentos processados:", total_docs)
    print("Frases detetadas:", total_frases)
    print("Janelas criadas:", total_janelas)

    if docs_sem_txt:
        print("Aviso: documentos sem TXT correspondente:", len(docs_sem_txt))


if __name__ == "__main__":
    main()