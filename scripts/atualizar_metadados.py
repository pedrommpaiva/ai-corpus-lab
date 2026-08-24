import csv
import pathlib
import re
import shutil
import unicodedata
from datetime import datetime

CSV_PATH = pathlib.Path("metadados_corpus_revisto.csv")
TXT_PATH = pathlib.Path("contagens_tokens_palavras.txt")

CRIAR_BACKUP = True

# True = o TXT manda, mesmo quando a célula do CSV já tem valor.
# False = só preenche células vazias.
SOBREPOR_VALORES_EXISTENTES = True

COL_FICHEIRO = "ficheiro_txt"
COL_TOKENS = "tokens"
COL_PALAVRAS = "palavras_aprox"
COL_CARACTERES = "caracteres"

NUMERO = r"\d+(?: \d{3})*"

PADRAO_LINHA = re.compile(
    rf"^(?P<ficheiro>.+?\.txt)\s+"
    rf"(?P<tokens>{NUMERO})\s+"
    rf"(?P<palavras>{NUMERO})\s+"
    rf"(?P<caracteres>{NUMERO})\s*$"
)


def normalizar_nome(valor):
    return unicodedata.normalize("NFC", (valor or "").strip())


def limpar_numero(valor):
    return str(int(str(valor).replace(" ", "").strip()))


def valor_vazio(valor):
    return valor is None or str(valor).strip() == ""


def inserir_coluna(campos, nova_coluna, depois_de=None):
    if nova_coluna in campos:
        return campos

    if depois_de in campos:
        pos = campos.index(depois_de) + 1
        return campos[:pos] + [nova_coluna] + campos[pos:]

    return campos + [nova_coluna]


def ler_contagens_txt(path):
    contagens = {}
    duplicados = []
    linhas_invalidas = []

    for numero_linha, linha in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(),
        start=1
    ):
        texto = linha.strip()

        if (
            not texto
            or texto.startswith("FICHEIRO")
            or texto.startswith("---")
            or texto.startswith("TOTAL")
        ):
            continue

        m = PADRAO_LINHA.match(linha.rstrip())

        if not m:
            linhas_invalidas.append((numero_linha, linha))
            continue

        ficheiro = normalizar_nome(m.group("ficheiro"))

        if ficheiro in contagens:
            duplicados.append(ficheiro)

        contagens[ficheiro] = {
            COL_TOKENS: limpar_numero(m.group("tokens")),
            COL_PALAVRAS: limpar_numero(m.group("palavras")),
            COL_CARACTERES: limpar_numero(m.group("caracteres")),
        }

    if duplicados:
        raise RuntimeError(
            "Ficheiros duplicados no TXT: "
            + ", ".join(sorted(set(duplicados)))
        )

    if linhas_invalidas:
        exemplo = "\n".join(
            f"linha {n}: {l}" for n, l in linhas_invalidas[:10]
        )
        raise RuntimeError(
            "Há linhas do TXT que não foram reconhecidas:\n" + exemplo
        )

    return contagens


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV não encontrado: {CSV_PATH}")

    if not TXT_PATH.exists():
        raise FileNotFoundError(f"TXT não encontrado: {TXT_PATH}")

    contagens = ler_contagens_txt(TXT_PATH)

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        campos = reader.fieldnames
        linhas = list(reader)

    if not campos:
        raise RuntimeError("Não consegui ler as colunas do CSV.")

    if COL_FICHEIRO not in campos:
        raise RuntimeError(f"O CSV não tem a coluna obrigatória: {COL_FICHEIRO}")

    campos = inserir_coluna(campos, COL_CARACTERES, depois_de=COL_FICHEIRO)
    campos = inserir_coluna(campos, COL_PALAVRAS, depois_de=COL_CARACTERES)
    campos = inserir_coluna(campos, COL_TOKENS, depois_de=COL_PALAVRAS)

    ficheiros_csv = set()

    linhas_com_correspondencia = 0
    celulas_preenchidas = 0
    celulas_sobrescritas = 0

    sem_correspondencia_no_txt = []
    divergencias_nao_sobrescritas = []

    for linha in linhas:
        ficheiro = normalizar_nome(linha.get(COL_FICHEIRO, ""))
        ficheiros_csv.add(ficheiro)

        for coluna in (COL_CARACTERES, COL_PALAVRAS, COL_TOKENS):
            linha.setdefault(coluna, "")

        if ficheiro not in contagens:
            sem_correspondencia_no_txt.append(ficheiro)
            continue

        linhas_com_correspondencia += 1
        novos_valores = contagens[ficheiro]

        for coluna, novo_valor in novos_valores.items():
            valor_antigo = (linha.get(coluna) or "").strip()

            if valor_vazio(valor_antigo):
                linha[coluna] = novo_valor
                celulas_preenchidas += 1

            elif valor_antigo != novo_valor:
                if SOBREPOR_VALORES_EXISTENTES:
                    linha[coluna] = novo_valor
                    celulas_sobrescritas += 1
                else:
                    divergencias_nao_sobrescritas.append(
                        (ficheiro, coluna, valor_antigo, novo_valor)
                    )

    ficheiros_txt_sem_linha_csv = sorted(set(contagens) - ficheiros_csv)

    if CRIAR_BACKUP:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = CSV_PATH.with_name(
            f"{CSV_PATH.stem}.backup_{stamp}{CSV_PATH.suffix}"
        )
        shutil.copy2(CSV_PATH, backup_path)
    else:
        backup_path = None

    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        writer.writeheader()
        writer.writerows(linhas)

    print(f"Entradas lidas no TXT: {len(contagens)}")
    print(f"Linhas lidas no CSV: {len(linhas)}")
    print(f"Linhas do CSV com correspondência no TXT: {linhas_com_correspondencia}")
    print(f"Células preenchidas que estavam vazias: {celulas_preenchidas}")
    print(f"Células sobrescritas por divergirem do TXT: {celulas_sobrescritas}")
    print(f"Linhas do CSV sem correspondência no TXT: {len(sem_correspondencia_no_txt)}")
    print(f"Entradas do TXT sem linha no CSV: {len(ficheiros_txt_sem_linha_csv)}")

    if ficheiros_txt_sem_linha_csv:
        print("\nEntradas do TXT sem linha no CSV:")
        for ficheiro in ficheiros_txt_sem_linha_csv:
            print(f"  - {ficheiro}")

    if sem_correspondencia_no_txt:
        print("\nLinhas do CSV sem correspondência no TXT:")
        for ficheiro in sem_correspondencia_no_txt:
            print(f"  - {ficheiro}")

    if divergencias_nao_sobrescritas:
        print("\nDivergências mantidas, porque SOBREPOR_VALORES_EXISTENTES = False:")
        for ficheiro, coluna, antigo, novo in divergencias_nao_sobrescritas[:50]:
            print(f"  - {ficheiro} | {coluna}: CSV={antigo} / TXT={novo}")

    if backup_path:
        print(f"\nBackup criado: {backup_path}")

    print("CSV atualizado.")


if __name__ == "__main__":
    main()