import json
import random
import re
from pathlib import Path
from collections import Counter, defaultdict
from statistics import mean, median


INPUT_JSONL = Path("corpus_janelas.jsonl")
OUTPUT_REPORT = Path("relatorio_sondagem_janelas.txt")

RANDOM_SEED = 42
SAMPLES_PER_WINDOW_SIZE = 5
N_EXTREMES = 15


REQUIRED_FIELDS = [
    "janela_id",
    "doc_id",
    "ficheiro",
    "window_size",
    "sentence_start",
    "sentence_end",
    "texto",
]


def contar_palavras(texto: str) -> int:
    return len(re.findall(r"\S+", texto))


def obter_metadado(entry: dict, nomes_possiveis: list[str]) -> str:
    metadados = entry.get("metadados", {})
    if not isinstance(metadados, dict):
        return ""

    normalizados = {k.lower().strip(): v for k, v in metadados.items()}

    for nome in nomes_possiveis:
        valor = normalizados.get(nome.lower())
        if valor:
            return str(valor).strip()

    return ""


def resumo_janela(entry: dict) -> str:
    texto = entry.get("texto", "").replace("\n", " ").strip()

    titulo = obter_metadado(entry, ["titulo", "título", "title"])
    data = obter_metadado(entry, ["data", "date", "ano"])
    genero = obter_metadado(entry, ["genero", "género", "tipo"])

    cabecalho = (
        f"ID: {entry.get('janela_id', '')}\n"
        f"Doc: {entry.get('doc_id', '')}\n"
        f"Ficheiro: {entry.get('ficheiro', '')}\n"
        f"Window size: {entry.get('window_size', '')}\n"
        f"Frases: {entry.get('sentence_start', '')}-{entry.get('sentence_end', '')}\n"
    )

    if titulo:
        cabecalho += f"Título: {titulo}\n"
    if data:
        cabecalho += f"Data: {data}\n"
    if genero:
        cabecalho += f"Género: {genero}\n"

    cabecalho += f"Caracteres: {len(texto)} | Palavras: {contar_palavras(texto)}\n"
    cabecalho += f"Texto: {texto}\n"

    return cabecalho


def main():
    random.seed(RANDOM_SEED)

    entries = []
    linhas_invalidas = 0

    with INPUT_JSONL.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                linhas_invalidas += 1

    total = len(entries)

    window_counter = Counter()
    ficheiro_counter = Counter()
    doc_counter = Counter()
    missing_fields = Counter()
    chars = []
    words = []
    exact_text_counter = Counter()
    samples_by_window = defaultdict(list)

    for entry in entries:
        ws = entry.get("window_size")
        texto = entry.get("texto", "")

        window_counter[ws] += 1
        ficheiro_counter[entry.get("ficheiro", "")] += 1
        doc_counter[entry.get("doc_id", "")] += 1

        chars.append(len(texto))
        words.append(contar_palavras(texto))
        exact_text_counter[texto.strip()] += 1

        for field in REQUIRED_FIELDS:
            if field not in entry or entry.get(field) in ("", None):
                missing_fields[field] += 1

        if len(samples_by_window[ws]) < SAMPLES_PER_WINDOW_SIZE:
            samples_by_window[ws].append(entry)

    duplicated_texts = sum(1 for _, count in exact_text_counter.items() if count > 1)
    duplicated_instances = sum(count for _, count in exact_text_counter.items() if count > 1)

    longest = sorted(entries, key=lambda e: len(e.get("texto", "")), reverse=True)[:N_EXTREMES]
    shortest = sorted(entries, key=lambda e: len(e.get("texto", "")))[:N_EXTREMES]

    random_samples_by_window = defaultdict(list)
    entries_by_window = defaultdict(list)

    for entry in entries:
        entries_by_window[entry.get("window_size")].append(entry)

    for ws, ws_entries in entries_by_window.items():
        random_samples_by_window[ws] = random.sample(
            ws_entries,
            min(SAMPLES_PER_WINDOW_SIZE, len(ws_entries))
        )

    report = []

    report.append("RELATÓRIO DE SONDAGEM DO CORPUS DE JANELAS\n")
    report.append("=" * 80 + "\n\n")

    report.append(f"Ficheiro analisado: {INPUT_JSONL}\n")
    report.append(f"Total de janelas: {total}\n")
    report.append(f"Linhas JSON inválidas: {linhas_invalidas}\n")
    report.append(f"Documentos únicos: {len(doc_counter)}\n")
    report.append(f"Ficheiros únicos: {len(ficheiro_counter)}\n\n")

    report.append("CONTAGEM POR WINDOW_SIZE\n")
    report.append("-" * 80 + "\n")
    for ws, count in sorted(window_counter.items(), key=lambda x: str(x[0])):
        report.append(f"window_size {ws}: {count}\n")
    report.append("\n")

    report.append("ESTATÍSTICAS DE TAMANHO\n")
    report.append("-" * 80 + "\n")
    if chars:
        report.append(f"Caracteres — mínimo: {min(chars)} | média: {mean(chars):.1f} | mediana: {median(chars):.1f} | máximo: {max(chars)}\n")
        report.append(f"Palavras — mínimo: {min(words)} | média: {mean(words):.1f} | mediana: {median(words):.1f} | máximo: {max(words)}\n")
    report.append("\n")

    report.append("CAMPOS EM FALTA\n")
    report.append("-" * 80 + "\n")
    if missing_fields:
        for field, count in missing_fields.items():
            report.append(f"{field}: {count}\n")
    else:
        report.append("Nenhum campo obrigatório em falta.\n")
    report.append("\n")

    report.append("DUPLICADOS EXATOS DE TEXTO\n")
    report.append("-" * 80 + "\n")
    report.append(f"Textos distintos duplicados: {duplicated_texts}\n")
    report.append(f"Instâncias envolvidas em duplicados: {duplicated_instances}\n\n")

    report.append("15 JANELAS MAIS LONGAS\n")
    report.append("=" * 80 + "\n\n")
    for entry in longest:
        report.append(resumo_janela(entry))
        report.append("-" * 80 + "\n\n")

    report.append("15 JANELAS MAIS CURTAS\n")
    report.append("=" * 80 + "\n\n")
    for entry in shortest:
        report.append(resumo_janela(entry))
        report.append("-" * 80 + "\n\n")

    report.append("AMOSTRAS ALEATÓRIAS POR WINDOW_SIZE\n")
    report.append("=" * 80 + "\n\n")
    for ws in sorted(random_samples_by_window.keys(), key=lambda x: str(x)):
        report.append(f"WINDOW_SIZE {ws}\n")
        report.append("-" * 80 + "\n\n")

        for entry in random_samples_by_window[ws]:
            report.append(resumo_janela(entry))
            report.append("-" * 80 + "\n\n")

    OUTPUT_REPORT.write_text("".join(report), encoding="utf-8")

    print("Sondagem concluída.")
    print(f"Relatório criado: {OUTPUT_REPORT}")
    print(f"Total de janelas: {total}")
    print("Contagem por window_size:")
    for ws, count in sorted(window_counter.items(), key=lambda x: str(x[0])):
        print(f"  {ws}: {count}")

    if missing_fields:
        print("Campos em falta detetados:")
        for field, count in missing_fields.items():
            print(f"  {field}: {count}")
    else:
        print("Campos obrigatórios: OK")


if __name__ == "__main__":
    main()