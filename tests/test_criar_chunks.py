import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "criar_chunks.py"
SPEC = importlib.util.spec_from_file_location("criar_chunks", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CriarChunksTests(unittest.TestCase):
    def test_texto_vazio_nao_cria_chunks(self):
        self.assertEqual(MODULE.criar_chunks_texto(""), [])

    def test_parametros_invalidos_sao_rejeitados(self):
        with self.assertRaises(ValueError):
            MODULE.criar_chunks_texto("texto", chunk_size=0)
        with self.assertRaises(ValueError):
            MODULE.criar_chunks_texto("texto", chunk_size=10, overlap=10)

    def test_metadados_sao_preservados(self):
        corpus = [{"id": "doc-1", "titulo": "Exemplo", "texto": "Texto curto."}]
        with tempfile.TemporaryDirectory() as pasta:
            input_path = Path(pasta) / "input.json"
            output_path = Path(pasta) / "output.json"
            input_path.write_text(json.dumps(corpus), encoding="utf-8")
            chunks = MODULE.criar_corpus_chunks(input_path, output_path)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["doc_id"], "doc-1")
        self.assertEqual(chunks[0]["titulo"], "Exemplo")


if __name__ == "__main__":
    unittest.main()
