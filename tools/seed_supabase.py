# tools/seed_supabase.py
# Script Python para inserir/atualizar registros na tabela `procedures` via API do Supabase.
# Uso: python tools/seed_supabase.py
# Requer: pip install supabase python-dotenv

import os
from dotenv import load_dotenv

load_dotenv()  # carrega .env da raiz

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service_role para escrita segura

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("Defina SUPABASE_URL e SUPABASE_KEY no arquivo .env antes de rodar este script.")

try:
    from supabase import create_client
except Exception as e:
    raise SystemExit("Instale a dependência supabase: pip install supabase") from e

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

procedures = [
    {
        "name": "Preenchimento facial",
        "slug": "preenchimento-facial",
        "summary": "Correção de volumes e harmonização facial.",
        "details": "Utilizamos ácido hialurônico de alta qualidade para repor volumes, corrigir sulcos e harmonizar o rosto. Cada tratamento começa com avaliação detalhada e plano personalizado."
    },
    {
        "name": "Toxina botulínica (Botox)",
        "slug": "toxina-botulinica-botox",
        "summary": "Redução de linhas de expressão.",
        "details": "Aplicação de toxina botulínica para suavizar rugas dinâmicas. Procedimento rápido, com efeito em 2-7 dias e duração média de 3-6 meses."
    },
    {
        "name": "Peeling químico",
        "slug": "peeling-quimico",
        "summary": "Renovação da pele e melhora de textura.",
        "details": "Peelings químicos indicados para renovar a camada superficial da pele, melhorar manchas e estimular colágeno. Cuidados pós-peeling são essenciais."
    },
    {
        "name": "Microagulhamento",
        "slug": "microagulhamento",
        "summary": "Estimula produção de colágeno e melhora cicatrizes.",
        "details": "Técnica que usa microagulhas para induzir regeneração; indicada para cicatrizes de acne, poros dilatados e linhas finas."
    },
    {
        "name": "Criolipólise",
        "slug": "criolitpólise",
        "summary": "Redução localizada de gordura corporal.",
        "details": "Congelamento controlado de adipócitos para redução gradual de gordura em áreas específicas. Indicado para pacientes próximos ao peso ideal."
    },
    {
        "name": "Radiofrequência corporal",
        "slug": "radiofrequencia-corporal",
        "summary": "Melhora flacidez e contorno corporal.",
        "details": "Aquecimento por radiofrequência para estimular colágeno e melhorar a firmeza da pele, frequentemente combinado com outros tratamentos."
    }
]

def upsert_procedures(items):
    # Insere todos; se já existir slug único, faz update (via upsert)
    try:
        res = supabase.table("procedures").upsert(items, on_conflict="slug").execute()
        print("Resposta do Supabase:", getattr(res, "data", res))
    except Exception as e:
        print("Erro ao inserir/atualizar procedimentos:", e)

if __name__ == "__main__":
    upsert_procedures(procedures)
