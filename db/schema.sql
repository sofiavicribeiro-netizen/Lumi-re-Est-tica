-- db/schema.sql
-- Cria extensão e as tabelas básicas + políticas RLS recomendadas para Supabase

-- Extensão para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabela de procedimentos (leitura pública)
CREATE TABLE IF NOT EXISTS procedures (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE,
  summary text,
  details text,
  created_at timestamptz DEFAULT now()
);

-- Tabela de contatos (mensagens do site)
CREATE TABLE IF NOT EXISTS contacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  email text NOT NULL,
  message text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Tabela de perfis (opcional - vinculada ao auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  full_name text,
  role text DEFAULT 'client', -- client | staff | admin
  phone text,
  created_at timestamptz DEFAULT now()
);

-- Tabela de agendamentos (opcional)
CREATE TABLE IF NOT EXISTS appointments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users,
  procedure_id uuid REFERENCES procedures,
  scheduled_at timestamptz NOT NULL,
  status text DEFAULT 'pending',
  notes text,
  created_at timestamptz DEFAULT now()
);

-- Ativa Row Level Security (RLS) para controle fino
ALTER TABLE procedures ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- POLÍTICAS

-- procedures: leitura pública (todos podem SELECT)
CREATE POLICY "Public read on procedures" ON procedures
  FOR SELECT USING (true);

-- procedures: bloqueia escrita pública (somente service_role / admin via backend)
CREATE POLICY "No client write procedures" ON procedures
  FOR INSERT, UPDATE, DELETE USING (false);

-- contacts: permitir INSERT público (formulário do site pode enviar)
CREATE POLICY "Allow insert contacts" ON contacts
  FOR INSERT WITH CHECK (true);

-- contacts: bloquear leitura pública; leitura via service_role/back-end
CREATE POLICY "Deny select public contacts" ON contacts
  FOR SELECT USING (false);

-- profiles: usuário vê/edita seu próprio profile
CREATE POLICY "Profiles: select own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Profiles: update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- appointments: permitir INSERT apenas para usuários autenticados
CREATE POLICY "Appointments: insert authenticated" ON appointments
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Appointments: select own" ON appointments
  FOR SELECT USING (auth.uid() = user_id);
