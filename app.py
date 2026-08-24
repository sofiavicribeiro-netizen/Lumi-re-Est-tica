import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

# Carrega variáveis do .env na raiz do projeto
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service_role (use somente no backend)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

# Inicializa Supabase (se disponível)
supabase = None
try:
    from supabase import create_client
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None

# Inicializa OpenAI (opcional)
openai = None
if OPENAI_API_KEY:
    try:
        import openai as _openai
        openai = _openai
        openai.api_key = OPENAI_API_KEY
    except Exception:
        openai = None

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app, resources={r"/*": {"origins": "*"}})


def _extract_data(res):
    """
    Compatibilidade com várias versões do supabase-py:
    - nova API pode retornar um objeto com .data
    - versões antigas podem retornar dict com key 'data'
    - ou já retornar a lista direta
    """
    try:
        return getattr(res, "data", None) or (res.get("data") if isinstance(res, dict) else None) or res
    except Exception:
        return res


@app.route("/")
def index():
    # Renderiza o template principal (templates/index.html)
    return render_template("index.html")


@app.route("/procedures", methods=["GET"])
def get_procedures():
    """
    Retorna lista de procedimentos.
    Prefere buscar no Supabase; se não configurado, retorna fallback local.
    """
    if supabase:
        try:
            res = supabase.table("procedures").select("*").order("name", {"ascending": True}).execute()
            data = _extract_data(res) or []
            return jsonify(data), 200
        except Exception as e:
            app.logger.error("Erro ao buscar procedures no Supabase: %s", e)

    # fallback
    fallback = [
        {"id": "p1", "name": "Preenchimento facial", "summary": "Correção de volumes e harmonização facial.", "details": "Utilizamos ácido hialurônico para repor volumes com segurança. Sessões de avaliação e resultados temporários."},
        {"id": "p2", "name": "Toxina botulínica (Botox)", "summary": "Redução de linhas de expressão.", "details": "Toxina botulínica para suavizar rugas dinâmicas. Procedimento rápido, com efeito em dias."},
        {"id": "p3", "name": "Peeling químico", "summary": "Renovação da pele.", "details": "Peelings para clareamento, textura e rejuvenescimento. Vários níveis: superficial, médio."},
    ]
    return jsonify(fallback), 200


@app.route("/contact", methods=["POST"])
def contact():
    """
    Recebe contato do frontend e grava em Supabase (recomendado) ou retorna OK.
    Usa a service_role key do Supabase (SUPABASE_KEY) — mantenha-a apenas no backend.
    """
    payload = request.get_json() or {}
    name = payload.get("name")
    email = payload.get("email")
    message = payload.get("message")

    if not name or not email or not message:
        return jsonify({"error": "Campos inválidos"}), 400

    record = {
        "name": name,
        "email": email,
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    }

    if supabase:
        try:
            res = supabase.table("contacts").insert(record).execute()
            data = _extract_data(res)
            return jsonify({"ok": True, "result": data}), 201
        except Exception as e:
            app.logger.error("Erro ao inserir contact no Supabase: %s", e)
            return jsonify({"ok": False, "error": "Falha ao salvar no banco"}), 500

    # Se não houver Supabase configurado, apenas retorna sucesso (ou implemente envio de e-mail)
    return jsonify({"ok": True, "note": "Supabase não configurado; mensagem não persistida."}), 201


@app.route("/assistant", methods=["POST"])
def assistant():
    """
    Assistente virtual:
    - Se OPENAI_API_KEY estiver configurada, encaminha para a API OpenAI (ChatCompletion).
    - Caso contrário, usa um fallback simples que responde perguntas sobre procedimentos e agendamento.
    """
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"reply": "Envie uma pergunta para o assistente."}), 400

    # Tenta usar OpenAI (se disponível)
    if openai:
        try:
            system_prompt = (
                "Você é o assistente virtual da clínica Lumière Estética. "
                "Responda em português de forma profissional, amigável e concisa. "
                "Forneça informações sobre procedimentos, agendamento e cuidados. "
                "Se o usuário pedir para agendar, solicite nome e telefone ou explique como entrar em contato."
            )
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.2,
            )
            reply = resp["choices"][0]["message"]["content"].strip()
            return jsonify({"reply": reply}), 200
        except Exception as e:
            app.logger.error("OpenAI error: %s", e)
            # cai para fallback

    # Fallback local: tenta relacionar por nome de procedimento ou palavras-chave de agendamento
    try:
        procedures = []
        if supabase:
            try:
                r = supabase.table("procedures").select("*").execute()
                procedures = _extract_data(r) or []
            except Exception as e:
                app.logger.error("Erro ao ler procedures no assistant fallback: %s", e)

        if not procedures:
            procedures = [
                {"id": "p1", "name": "Preenchimento facial", "summary": "Correção de volumes e harmonização facial.", "details": "Utilizamos ácido hialurônico para repor volumes com segurança."},
                {"id": "p2", "name": "Toxina botulínica (Botox)", "summary": "Redução de linhas de expressão.", "details": "Aplicação de toxina botulínica para suavizar rugas dinâmicas."},
                {"id": "p3", "name": "Peeling químico", "summary": "Renovação da pele.", "details": "Peelings para clareamento, textura e rejuvenescimento."},
            ]

        msg_lower = message.lower()

        # Se mencionar um procedimento pelo nome, retorna detalhes
        for p in procedures:
            name = (p.get("name") or "").lower()
            if name and name in msg_lower:
                reply = f"{p.get('name')}: {p.get('summary','')}\n\nDetalhes: {p.get('details','')}"
                return jsonify({"reply": reply}), 200

        # Perguntas sobre agendamento/contato
        if any(term in msg_lower for term in ["agendar", "marcar", "consulta", "horário", "horarios", "horários", "telefone", "contato"]):
            reply = (
                "Para agendar uma avaliação, por favor envie seu nome e telefone aqui ou entre em contato pelo e-mail/telefone da clínica. "
                "Também podemos marcar por mensagem; informe uma janela de horário preferida."
            )
            return jsonify({"reply": reply}), 200

        # Resposta genérica
        reply = (
            "Olá! Sou o assistente da Lumière Estética. Posso informar sobre nossos procedimentos (preenchimento, botox, peelings, tratamentos corporais) "
            "ou ajudar com agendamentos. Pergunte sobre um procedimento específico ou diga que quer agendar."
        )
        return jsonify({"reply": reply}), 200

    except Exception as e:
        app.logger.error("Assistant fallback error: %s", e)
        return jsonify({"reply": "Desculpe, ocorreu um erro ao consultar o assistente."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=FLASK_DEBUG)
