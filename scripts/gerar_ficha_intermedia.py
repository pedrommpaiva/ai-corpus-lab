import os
from pathlib import Path
import anthropic


OUTPUT = Path("ficha_intermedia_salazar.txt")

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


PROMPT_SISTEMA = """
Recebes uma pergunta destinada a interrogar um corpus textual de António de Oliveira Salazar.

Não respondas à pergunta.
Não simules Salazar.
Apenas traduz a pergunta para uma forma pesquisável no corpus.

Produz apenas:

Definição do objeto independente do corpus:
[definição factual]

Conceitos/tensões traduzidos:
[lista curta de conceitos e tensões fundamentais]

Queries para Chroma:
[6 a 12 consultas curtas, em vocabulário próximo do corpus]
""".strip()


def chamar_claude(pergunta: str) -> str:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    mensagem = client.messages.create(
        model=MODEL,
        max_tokens=800,
        temperature=0.2,
        system=PROMPT_SISTEMA,
        messages=[
            {
                "role": "user",
                "content": pergunta
            }
        ],
    )

    partes = []
    for bloco in mensagem.content:
        if getattr(bloco, "type", None) == "text":
            partes.append(bloco.text)

    return "\n".join(partes).strip()


def main():
    pergunta = input("\nPergunta: ").strip()

    if not pergunta:
        print("Pergunta vazia.")
        return

    ficha = chamar_claude(pergunta)

    OUTPUT.write_text(ficha, encoding="utf-8")

    print("\nFicha intermédia criada:")
    print(OUTPUT)
    print("\n" + ficha)


if __name__ == "__main__":
    main()