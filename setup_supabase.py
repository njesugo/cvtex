#!/usr/bin/env python3
"""
Script pour initialiser les tables Supabase.
Exécute: python setup_supabase.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Variables SUPABASE_URL et SUPABASE_KEY non trouvées dans .env")
    exit(1)

print(f"🔗 Connexion à Supabase: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL pour créer les tables
SQL_SCHEMA = """
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
"""

print("\n📋 Instructions pour créer les tables :")
print("=" * 50)
print("1. Ouvre https://app.supabase.com")
print("2. Sélectionne ton projet")
print("3. Va dans 'SQL Editor' (menu gauche)")
print("4. Clique sur 'New Query'")
print("5. Copie et exécute ce SQL :\n")
print("-" * 50)
print(SQL_SCHEMA)
print("-" * 50)

print("\n📦 Création du bucket Storage...")
try:
    # Vérifier si le bucket existe déjà
    buckets = supabase.storage.list_buckets()
    bucket_names = [b.name for b in buckets]
    
    if "documents" in bucket_names:
        print("✅ Bucket 'documents' existe déjà")
    else:
        # Créer le bucket
        result = supabase.storage.create_bucket(
            "documents",
            options={"public": True}
        )
        print("✅ Bucket 'documents' créé avec succès")
except Exception as e:
    print(f"⚠️  Erreur création bucket: {e}")
    print("   Tu peux le créer manuellement dans Storage > New Bucket")

print("\n🧪 Test de connexion aux tables...")
try:
    result = supabase.table("applications").select("*").limit(1).execute()
    print("✅ Table 'applications' accessible")
except Exception as e:
    print(f"❌ Table 'applications' non trouvée - exécute le SQL ci-dessus")

try:
    result = supabase.table("temp_analysis").select("*").limit(1).execute()
    print("✅ Table 'temp_analysis' accessible")
except Exception as e:
    print(f"❌ Table 'temp_analysis' non trouvée - exécute le SQL ci-dessus")

print("\n✨ Configuration terminée !")
print("Tu peux maintenant lancer l'API : python api.py")
