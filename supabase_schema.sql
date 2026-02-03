-- Schema SQL pour Supabase
-- Exécuter dans l'éditeur SQL de Supabase (https://app.supabase.com)

-- Table des candidatures
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    position TEXT NOT NULL,
    location TEXT,
    salary TEXT,
    contract_type TEXT,
    status TEXT DEFAULT 'submitted',
    applied_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    match_score INTEGER,
    description TEXT,
    url TEXT,
    cv_path TEXT,
    cover_path TEXT,
    logo_url TEXT,
    language TEXT DEFAULT 'fr',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les recherches
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company);
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);

-- Table pour les données temporaires d'analyse
CREATE TABLE IF NOT EXISTS temp_analysis (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    job_data JSONB,
    language TEXT,
    logo_url TEXT,
    primary_color TEXT,
    match_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour mettre à jour updated_at
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Activer RLS (Row Level Security) - optionnel pour l'instant
-- ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE temp_analysis ENABLE ROW LEVEL SECURITY;

-- Créer un bucket pour stocker les PDFs
-- Note: Ceci doit être fait via l'interface Supabase Storage ou l'API
-- Nom du bucket: "documents"
