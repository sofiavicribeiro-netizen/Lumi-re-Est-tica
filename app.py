import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, abort
from flask_cors import CORS

# Carrega .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service_role (somente backend)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")  # chave simples para proteger rotas admin
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
    """Compatibilidade com várias versões do supabase-py."""
    try:
        return getattr(res, "data", None) or (res.get("data") if isinstance(res, dict) else None) or res
    except Exception:
        return res


def _require_admin():
    """Verifica header X-ADMIN-KEY ou ENV ADMIN_API_KEY."""
    key = request.headers.get("X-ADMIN-KEY") or request.args.get("admin_key")
    if not ADMIN_API_KEY:
        # Se não definido, bloqueia ações admin por segurança
        abort(403, "Admin key not configured on server.")
    if key != ADMIN_API_KEY:
        abort(401, "Invalid admin key")


def _to_decimal(v):
    """Converte para Decimal com duas casas (currency)."""
    try:
        return (Decimal(str(v))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------
# Tax rules / fiscal endpoints
# ---------------------------

@app.route("/tax-rules", methods=["GET"])
def list_tax_rules():
    """
    Lista regras fiscais. Público para leitura.
    Campos esperados: id, name, country, state, city, rate (ex: 0.12)
    """
    if supabase:
        try:
            res = supabase.table("tax_rules").select("*").order("name", {"ascending": True}).execute()
            data = _extract_data(res) or []
            return jsonify(data), 200
        except Exception as e:
            app.logger.error("Erro ao buscar tax_rules no Supabase: %s", e)

    # fallback vazio
    return jsonify([]), 200


@app.route("/tax-rules", methods=["POST"])
def create_tax_rule():
    """Cria nova regra fiscal — protegido por ADMIN_API_KEY."""
    _require_admin()
    payload = request.get_json() or {}
    name = payload.get("name")
    rate = payload.get("rate")  # ex: 0.12
    country = payload.get("country")
    state = payload.get("state")
    city = payload.get("city")
    is_default = bool(payload.get("is_default", False))

    if name is None or rate is None:
        return jsonify({"error": "Campos 'name' e 'rate' são obrigatórios"}), 400

    record = {
        "name": name,
        "rate": float(rate),
        "country": country,
        "state": state,
        "city": city,
        "is_default": is_default,
        "created_at": datetime.utcnow().isoformat()
    }

    if supabase:
        try:
            res = supabase.table("tax_rules").insert(record).execute()
            data = _extract_data(res)
            return jsonify({"ok": True, "result": data}), 201
        except Exception as e:
            app.logger.error("Erro ao inserir tax_rule: %s", e)
            return jsonify({"ok": False, "error": "Falha ao salvar"}), 500

    return jsonify({"ok": False, "error": "Supabase não configurado"}), 500


@app.route("/tax-rules/<rule_id>", methods=["PUT"])
def update_tax_rule(rule_id):
    _require_admin()
    payload = request.get_json() or {}
    updates = {}
    for f in ("name", "rate", "country", "state", "city", "is_default"):
        if f in payload:
            updates[f] = payload[f]
    if not updates:
        return jsonify({"error": "Nada para atualizar"}), 400

    if supabase:
        try:
            res = supabase.table("tax_rules").update(updates).eq("id", rule_id).execute()
            data = _extract_data(res)
            return jsonify({"ok": True, "result": data}), 200
        except Exception as e:
            app.logger.error("Erro ao atualizar tax_rule: %s", e)
            return jsonify({"ok": False, "error": "Falha ao atualizar"}), 500

    return jsonify({"ok": False, "error": "Supabase não configurado"}), 500


@app.route("/tax-rules/<rule_id>", methods=["DELETE"])
def delete_tax_rule(rule_id):
    _require_admin()
    if supabase:
        try:
            res = supabase.table("tax_rules").delete().eq("id", rule_id).execute()
            return jsonify({"ok": True}), 200
        except Exception as e:
            app.logger.error("Erro ao deletar tax_rule: %s", e)
            return jsonify({"ok": False, "error": "Falha ao deletar"}), 500
    return jsonify({"ok": False, "error": "Supabase não configurado"}), 500


def _find_applicable_rule(country=None, state=None, city=None):
    """
    Lógica simples de prioridade:
    1) busca por city
    2) por state
    3) por country
    4) regra com is_default = true
    """
    if not supabase:
        return None
    try:
        res = supabase.table("tax_rules").select("*").execute()
        rules = _extract_data(res) or []
    except Exception as e:
        app.logger.error("Erro ao ler tax_rules: %s", e)
        return None

    # Normaliza e procura
    def matches(r, field, val):
        if not val:
            return False
        rf = (r.get(field) or "").lower()
        return rf == val.lower()

    # city
    for r in rules:
        if city and matches(r, "city", city):
            return r
    # state
    for r in rules:
        if state and matches(r, "state", state):
            return r
    # country
    for r in rules:
        if country and matches(r, "country", country):
            return r
    # default
    for r in rules:
        if r.get("is_default"):
            return r
    return None


@app.route("/tax-calculate", methods=["POST"])
def tax_calculate():
    """
    Calcula imposto e retorna breakdown.
    Body JSON esperado:
      { "amount": 250.00, "quantity":1, "procedure_id": "...", "country":"BR", "state":"SP", "city":"São Paulo" }
    Retorna:
      { amount, quantity, subtotal, tax_rate, tax_amount, total, tax_rule }
    """
    payload = request.get_json() or {}
    amount = payload.get("amount")
    quantity = int(payload.get("quantity", 1))
    country = payload.get("country")
    state = payload.get("state")
    city = payload.get("city")
    procedure_id = payload.get("procedure_id")

    if amount is None:
        return jsonify({"error": "Campo 'amount' é obrigatório"}), 400

    dec_amount = _to_decimal(amount)
    quantity = max(1, quantity)
    subtotal = (dec_amount * Decimal(quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # encontra regra
    rule = _find_applicable_rule(country=country, state=state, city=city)
    if not rule:
        # fallback: 0% tax
        tax_rate = Decimal("0.00")
    else:
        tax_rate = _to_decimal(rule.get("rate", 0))

    tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = (subtotal + tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    response = {
        "amount": str(dec_amount),
        "quantity": quantity,
        "subtotal": str(subtotal),
        "tax_rate": str(tax_rate),
        "tax_amount": str(tax_amount),
        "total": str(total),
        "tax_rule": rule or None,
        "procedure_id": procedure_id
    }
    return jsonify(response), 200


@app.route("/fiscal-records", methods=["POST"])
def create_fiscal_record():
    """
    Salva registro fiscal no banco. Protegido por ADMIN_API_KEY.
    Body esperado (exemplo):
      { "procedure_id": "...", "amount": 250.00, "quantity":1, "tax_rule_id": "...", "tax_amount": 12.50, "total": 262.50, "meta": {...} }
    """
    _require_admin()
    payload = request.get_json() or {}
    procedure_id = payload.get("procedure_id")
    amount = payload.get("amount")
    quantity = int(payload.get("quantity", 1))
    tax_rule_id = payload.get("tax_rule_id")
    tax_amount = payload.get("tax_amount")
    total = payload.get("total")
    meta = payload.get("meta", {})

    if amount is None or tax_amount is None or total is None:
        return jsonify({"error": "Campos amount, tax_amount e total são obrigatórios"}), 400

    record = {
        "procedure_id": procedure_id,
        "amount": float(amount),
        "quantity": quantity,
        "tax_amount": float(tax_amount),
        "total": float(total),
        "tax_rule_id": tax_rule_id,
        "meta": meta,
        "created_at": datetime.utcnow().isoformat()
    }

    if supabase:
        try:
            res = supabase.table("fiscal_records").insert(record).execute()
            data = _extract_data(res)
            return jsonify({"ok": True, "result": data}), 201
        except Exception as e:
            app.logger.error("Erro ao inserir fiscal_record: %s", e)
            return jsonify({"ok": False, "error": "Falha ao salvar"}), 500

    return jsonify({"ok": False, "error": "Supabase não configurado"}), 500


# ---------------------------
# Mantém endpoints anteriores (/procedures, /contact, /assistant)
# (Se já tiver estes endpoints no seu app, mantenha-os; a seguir está um resumo)
# ---------------------------

@app.route("/procedures", methods=["GET"])
def get_procedures():
    if supabase:
        try:
            res = supabase.table("procedures").select("*").order("name", {"ascending": True}).execute()
            data = _extract_data(res) or []
            return jsonify(data), 200
        except Exception as e:
            app.logger.error("Erro ao buscar procedures no Supabase: %s", e)

    fallback = [
        {"id": "p1", "name": "Preenchimento facial", "summary": "Correção de volumes e harmonização facial.", "details": "Utilizamos ácido hialurônico para repor volumes com segurança."},
        {"id": "p2", "name": "Toxina botulínica (Botox)", "summary": "Redução de linhas de expressão.", "details": "Toxina botulínica para suavizar rugas dinâmicas."},
    ]
    return jsonify(fallback), 200


@app.route("/contact", methods=["POST"])
def contact():
    payload = request.get_json() or {}
    name = payload.get("name")
    email = payload.get("email")
    message = payload.get("message")

    if not name or not email or not message:
        return jsonify({"error": "Campos inválidos"}), 400

    record = {"name": name, "email": email, "message": message, "created_at": datetime.utcnow().isoformat()}
    if supabase:
        try:
            res = supabase.table("contacts").insert(record).execute()
            data = _extract_data(res)
            return jsonify({"ok": True, "result": data}), 201
        except Exception as e:
            app.logger.error("Erro ao inserir contact: %s", e)
            return jsonify({"ok": False, "error": "Falha ao salvar"}), 500

    return jsonify({"ok": True, "note": "Supabase não configurado; mensagem não persistida."}), 201


@app.route("/assistant", methods=["POST"])
def assistant():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"reply": "Envie uma pergunta para o assistente."}), 400

    if openai:
        try:
            system_prompt = (
                "Você é o assistente virtual da clínica Lumière Estética. Responda em português de forma profissional."
            )
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
                max_tokens=500,
                temperature=0.2,
            )
            reply = resp["choices"][0]["message"]["content"].strip()
            return jsonify({"reply": reply}), 200
        except Exception as e:
            app.logger.error("OpenAI error: %s", e)

    # fallback simples
    return jsonify({"reply": "Olá! Posso ajudar com informações sobre procedimentos ou agendamento."}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=FLASK_DEBUG)
