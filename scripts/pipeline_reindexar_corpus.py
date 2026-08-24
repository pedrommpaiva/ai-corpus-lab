import csv
import json
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime

PASTA_BASE = pathlib.Path(".")
PASTA_SCRIPTS = PASTA_BASE / "scripts"

CSV_PATH = PASTA_BASE / "metadados_corpus_revisto.csv"
VECTORDB = PASTA_BASE / "vectordb"
PASTA_BACKUPS = PASTA_BASE / "backups_vectordb"

SCRIPTS_PIPELINE = [
    "criar_corpus_mestre.py",
    "criar_chunks.py",
    "criar_janelas_frases.py",
    "indexar_vectordb.py",
    "indexar_janelas_vectordb.py",
]


def correr_script(nome_script):
    caminho_script = PASTA_SCRIPTS / nome_script

    if not caminho_script.exists():
        raise FileNotFoundError(f"Não encontrei o script: {caminho_script}")

    print("\n" + "=" * 80)
    print(f"A correr: {caminho_script}")
    print("=" * 80)

    resultado = subprocess.run(
        [sys.executable, str(caminho_script)],
        cwd=PASTA_BASE,
        text=True
    )

    if resultado.returncode != 0:
        raise RuntimeError(f"O script falhou: {nome_script}")


def validar_metadados():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Não encontrei: {CSV_PATH}")

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        linhas = list(reader)

    if not linhas:
        raise RuntimeError("O CSV não tem linhas.")

    erros = []
    ids = set()
    ficheiros = set()

    for i, linha in enumerate(linhas, start=2):
        doc_id = linha.get("id", "").strip()
        ficheiro_txt = linha.get("ficheiro_txt", "").strip()

        if not doc_id:
            erros.append(f"Linha {i}: id vazio")

        if doc_id in ids:
            erros.append(f"Linha {i}: id duplicado: {doc_id}")
        ids.add(doc_id)

        if not ficheiro_txt:
            erros.append(f"Linha {i}: ficheiro_txt vazio")
            continue

        caminho_txt = PASTA_BASE / ficheiro_txt

        if not caminho_txt.exists():
            erros.append(f"Linha {i}: TXT não encontrado: {ficheiro_txt}")

        if ficheiro_txt in ficheiros:
            erros.append(f"Linha {i}: ficheiro_txt duplicado: {ficheiro_txt}")
        ficheiros.add(ficheiro_txt)

    print(f"Linhas no CSV: {len(linhas)}")
    print(f"IDs únicos: {len(ids)}")
    print(f"TXT únicos: {len(ficheiros)}")

    if erros:
        print("\nERROS NOS METADADOS:")
        for erro in erros:
            print("-", erro)
        raise RuntimeError("Corrige os erros acima antes de continuar.")

    print("Metadados validados sem erros.")


def validar_scripts():
    if not PASTA_SCRIPTS.exists():
        raise FileNotFoundError(f"Não encontrei a pasta: {PASTA_SCRIPTS}")

    faltam = []

    for nome_script in SCRIPTS_PIPELINE:
        caminho = PASTA_SCRIPTS / nome_script
        if not caminho.exists():
            faltam.append(str(caminho))

    if faltam:
        print("\nSCRIPTS EM FALTA:")
        for f in faltam:
            print("-", f)
        raise RuntimeError("Faltam scripts na pasta scripts.")

    print("Scripts encontrados.")


def fazer_backup_vectordb():
    if not VECTORDB.exists():
        print("Não existe vectordb anterior. Será criada uma nova.")
        return

    PASTA_BACKUPS.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = PASTA_BACKUPS / f"vectordb_backup_{timestamp}"

    print(f"A fazer backup da vectordb atual para: {backup}")
    shutil.move(str(VECTORDB), str(backup))


def contar_json(path):
    if not path.exists():
        return None

    try:
        dados = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(dados, list):
            return len(dados)
    except Exception:
        return None

    return None


def resumo_final():
    docs = contar_json(PASTA_BASE / "corpus_mestre.json")
    chunks = contar_json(PASTA_BASE / "corpus_chunks.json")
    janelas = contar_json(PASTA_BASE / "corpus_janelas_frases.json")

    print("\n" + "=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)

    print(f"Documentos no corpus_mestre.json: {docs}")
    print(f"Chunks longos em corpus_chunks.json: {chunks}")
    print(f"Janelas de frases em corpus_janelas_frases.json: {janelas}")
    print("\nFicheiros atualizados:")
    print("- corpus_mestre.json")
    print("- corpus_chunks.json")
    print("- corpus_janelas_frases.json")
    print("- vectordb/")
    print("\nColeções esperadas na vectordb:")
    print("- salazar")
    print("- salazar_janelas")


def main():
    print("PIPELINE COMPLETO DE REINDEXAÇÃO DO CORPUS")
    print("=" * 80)

    validar_metadados()
    validar_scripts()

    # 1. Recria corpus central.
    correr_script("criar_corpus_mestre.py")

    # 2. Recria chunks longos.
    correr_script("criar_chunks.py")

    # 3. Recria janelas finas.
    correr_script("criar_janelas_frases.py")

    # 4. Remove/guarda a vectordb antiga antes de indexar.
    fazer_backup_vectordb()

    # 5. Indexa chunks longos na coleção salazar.
    correr_script("indexar_vectordb.py")

    # 6. Indexa janelas de frases na coleção salazar_janelas.
    correr_script("indexar_janelas_vectordb.py")

    print("\n" + "=" * 80)
    print("PIPELINE CONCLUÍDO")
    print("=" * 80)

    resumo_final()

    print("\nAgora podes correr:")
    print("py consultar_vectordb.py")
    print("ou")
    print("py preparar_prompt_salazar.py")


if __name__ == "__main__":
    main()