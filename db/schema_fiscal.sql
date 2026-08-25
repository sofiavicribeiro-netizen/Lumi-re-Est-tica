-- db/schema_fiscal.sql
-- Execute no SQL Editor do Supabase para criar as tabelas fiscais e políticas RLS.

-- Extensão para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabela de regras fiscais
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

-- Tabela de registros fiscais (fiscal records)
CREATE TABLE IF NOT EXISTS fiscal_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  procedure_id uuid REFERENCES procedures, -- se tabela procedures existir
  amount numeric NOT NULL,
  quantity integer DEFAULT 1,
  tax_amount numeric NOT NULL,
  total numeric NOT NULL,
  tax_rule_id uuid REFERENCES tax_rules,
  meta jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

-- Habilita Row Level Security (RLS)
ALTER TABLE tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE fiscal_records ENABLE ROW LEVEL SECURITY;

-- POLÍTICAS

-- tax_rules: leitura pública (qualquer um pode SELECT)
CREATE POLICY "Public read on tax_rules" ON tax_rules
  FOR SELECT USING (true);

-- tax_rules: bloqueia escrita pública (inserir/atualizar/deletar apenas via backend/service_role)
CREATE POLICY "No public write tax_rules" ON tax_rules
  FOR INSERT, UPDATE, DELETE USING (false);

-- fiscal_records: bloqueia leitura pública (somente backend/service_role deve ler)
CREATE POLICY "No public read fiscal_records" ON fiscal_records
  FOR SELECT USING (false);

-- fiscal_records: bloqueia escrita pública (inserção deve ser feita pelo backend com service_role)
CREATE POLICY "No public write fiscal_records" ON fiscal_records
  FOR INSERT USING (false);

-- Observações:
-- 1) A service_role key do Supabase IGNORA RLS; portanto o backend que usa a service_role pode inserir/ler sem restrição.
-- 2) Para permitir que usuários autenticados realizem operações específicas, crie políticas adicionais que usem auth.uid() ou claims custom.
-- 3) Se sua aplicação front-end precisa apenas ler tax_rules, use a chave ANON (public) e a política acima já permite SELECT.
