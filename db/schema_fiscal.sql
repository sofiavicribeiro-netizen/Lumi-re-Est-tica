-- db/schema_fiscal.sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS tax_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  country text,
  state text,
  city text,
  rate numeric NOT NULL,       -- ex: 0.12 (12%)
  is_default boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fiscal_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  procedure_id uuid REFERENCES procedures,
  amount numeric NOT NULL,
  quantity integer DEFAULT 1,
  tax_amount numeric NOT NULL,
  total numeric NOT NULL,
  tax_rule_id uuid REFERENCES tax_rules,
  meta jsonb,
  created_at timestamptz DEFAULT now()
);

-- Recomendo habilitar RLS e criar políticas:
ALTER TABLE tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE fiscal_records ENABLE ROW LEVEL SECURITY;

-- policy: permitir SELECT em tax_rules (leitura pública)
CREATE POLICY "Public read on tax_rules" ON tax_rules
  FOR SELECT USING (true);

-- policy: bloquear escrita pública em tax_rules (só backend/admin)
CREATE POLICY "No public write tax_rules" ON tax_rules
  FOR INSERT, UPDATE, DELETE USING (false);

-- policy: permitir insert fiscal_records via service_role/backend (bloquear leitura pública)
CREATE POLICY "No public read fiscal_records" ON fiscal_records
  FOR SELECT USING (false);

CREATE POLICY "No public write fiscal_records" ON fiscal_records
  FOR INSERT USING (false);
-- Nota: se você vai inserir fiscal_records pelo backend com SERVICE_ROLE, a policy pode permanecer assim.
