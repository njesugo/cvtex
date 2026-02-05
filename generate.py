#!/usr/bin/env python3
"""
CV & Cover Letter Generator - Adapte automatiquement ton CV et ta lettre de motivation
à une offre d'emploi en analysant son contenu.

Usage:
    python generate.py <url_offre> [--output <dossier>] [--compile]
    
Exemple:
    python generate.py "https://www.welcometothejungle.com/fr/companies/xxx/jobs/yyy"
"""

import json
import os
import re
import subprocess
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

# Charger les variables d'environnement depuis .env
def load_dotenv():
    """Charge les variables depuis le fichier .env"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value:  # Ne pas écraser avec une valeur vide
                        os.environ.setdefault(key, value)

load_dotenv()

# Mistral AI
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

# ColorThief pour extraction de couleurs
try:
    from colorthief import ColorThief
    COLORTHIEF_AVAILABLE = True
except ImportError:
    COLORTHIEF_AVAILABLE = False

# Détection de langue
try:
    from langdetect import detect as detect_language
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# Configuration
PROFILE_PATH = Path(__file__).parent / "profile.json"
CV_TEMPLATE_PATH = Path(__file__).parent / "templates" / "cv_template.tex"
COVER_TEMPLATE_PATH = Path(__file__).parent / "templates" / "cover_template.tex"
OUTPUT_DIR = Path(__file__).parent / "output"
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")


def detect_offer_language(text: str) -> str:
    """Détecte la langue de l'offre d'emploi (fr ou en)"""
    if not text:
        return "fr"
    
    text_lower = text.lower()
    
    # D'abord, vérifier les indicateurs forts de langue française
    # Ces mots n'existent pas en anglais et sont très courants dans les offres françaises
    strong_french_indicators = ["vous", "nous", "votre", "notre", "être", "avoir", 
                                 "poste", "rejoindre", "rejoignez", "postuler", 
                                 "télétravail", "salaire", "candidature", "contrat",
                                 "équipe", "entreprise", "missions", "avantages",
                                 "profil recherché", "ce que nous offrons", "vos missions"]
    
    # Compter les indicateurs français forts
    french_strong = sum(1 for w in strong_french_indicators if w in text_lower)
    
    # Si on trouve plusieurs indicateurs français forts, c'est du français
    if french_strong >= 3:
        return "fr"
    
    # Indicateurs forts anglais
    strong_english_indicators = ["you will", "we are", "you are", "your role", 
                                  "responsibilities", "requirements", "about us",
                                  "what we offer", "who you are", "what you'll do"]
    
    english_strong = sum(1 for w in strong_english_indicators if w in text_lower)
    
    if english_strong >= 2:
        return "en"
    
    # Fallback sur langdetect si disponible
    if LANGDETECT_AVAILABLE:
        try:
            lang = detect_language(text[:3000])
            if lang == "fr":
                return "fr"
            elif lang == "en":
                # Double vérification pour l'anglais car langdetect confond souvent
                # les offres françaises avec termes techniques anglais
                if french_strong >= 2:
                    return "fr"
                return "en"
            return "fr"  # Défaut français pour autres langues
        except:
            pass
    
    # Fallback final: détection par mots-clés
    french_words = ["poste", "vous", "nous", "équipe", "entreprise", "rejoindre", 
                    "candidature", "profil", "missions", "avantages", "salaire",
                    "expérience", "compétences", "formation", "télétravail",
                    "votre", "notre", "être", "avoir", "pour", "dans", "avec"]
    
    english_words = ["you", "we", "team", "company", "join", "application", 
                     "profile", "responsibilities", "benefits", "salary",
                     "experience", "skills", "education", "remote", "role",
                     "your", "our", "about", "will", "with"]
    
    french_count = sum(1 for w in french_words if f" {w} " in f" {text_lower} ")
    english_count = sum(1 for w in english_words if f" {w} " in f" {text_lower} ")
    
    return "en" if english_count > french_count + 3 else "fr"


def rgb_to_latex(rgb: Tuple[int, int, int]) -> str:
    """Convertit RGB en définition de couleur LaTeX"""
    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"


def extract_logo_url(soup: BeautifulSoup, url: str, company_name: str = "") -> Optional[str]:
    """Extrait l'URL du logo de l'entreprise depuis la page"""
    logo_url = None
    
    # Pour WTTJ, chercher spécifiquement le logo de l'entreprise
    if "welcometothejungle" in url:
        # Sur WTTJ, le logo est souvent dans une balise avec "logo" dans la classe
        # ou c'est une petite image carrée (pas une photo d'équipe rectangulaire)
        
        # 1. Chercher d'abord les éléments avec "logo" explicitement
        for img in soup.find_all("img"):
            parent_classes = " ".join(img.parent.get("class", [])) if img.parent else ""
            img_classes = " ".join(img.get("class", []))
            all_classes = (parent_classes + " " + img_classes).lower()
            
            src = img.get("src", "")
            
            # Chercher les images avec "logo" dans les classes
            if "logo" in all_classes and src:
                # Exclure les logos WTTJ génériques
                if "wttj" not in src.lower() and "welcometothejungle" not in src.lower():
                    if "cdn-images.welcometothejungle.com" in src:
                        logo_url = src
                        break
        
        # 2. Chercher dans les liens vers le profil entreprise (sidebar)
        if not logo_url:
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if "/companies/" in href and "/jobs" not in href:
                    img = a.find("img")
                    if img and img.get("src"):
                        src = img.get("src")
                        # Exclure les images WTTJ génériques
                        if "wttj" not in src.lower() and "cdn-images.welcometothejungle.com" in src:
                            logo_url = src
                            break
        
        # 3. Chercher par le nom de l'entreprise dans l'attribut alt
        if not logo_url and company_name:
            company_lower = company_name.lower()
            for img in soup.find_all("img"):
                alt = img.get("alt", "").lower()
                src = img.get("src", "")
                
                # Si l'alt contient exactement le nom de l'entreprise (logo)
                # et c'est une image du CDN (pas une photo d'équipe large)
                if alt == company_lower or f"{company_lower} logo" in alt:
                    if "cdn-images.welcometothejungle.com" in src:
                        logo_url = src
                        break
        
        # 4. NOUVEAU: Si pas de logo trouvé, aller chercher sur la page profil de l'entreprise
        if not logo_url:
            import re
            match = re.search(r'/companies/([^/]+)', url)
            if match:
                company_slug = match.group(1)
                lang = "en" if "/en/" in url else "fr"
                profile_url = f"https://www.welcometothejungle.com/{lang}/companies/{company_slug}"
                
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                    response = requests.get(profile_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        profile_soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Chercher le logo dans la page profil
                        # Le logo est généralement une image avec "logo" dans l'URL ou avec alt vide (petite taille)
                        for img in profile_soup.find_all("img"):
                            src = img.get("src", "")
                            alt = img.get("alt", "")
                            
                            # Le logo est souvent une image du CDN avec "logo" dans le path base64 ou petite dimension
                            if "cdn-images.welcometothejungle.com" in src:
                                # Exclure les grandes images (cover, photos d'équipe)
                                # Les logos ont généralement :auto:400:: ou moins
                                if "rs:auto:400:" in src or "rs:auto:200:" in src or "rs:auto:100:" in src:
                                    # Exclure les images avec "Meet" (photos de personnes)
                                    if "Meet" not in alt and "video" not in src.lower():
                                        logo_url = src
                                        print(f"🖼️  Logo trouvé sur la page profil")
                                        break
                except Exception as e:
                    pass  # Silently fail, continue without logo
    
    # Fallback: chercher le logo de manière générique (hors WTTJ)
    if not logo_url and "welcometothejungle" not in url:
        logo_selectors = [
            "img[alt*='logo']",
            "img[class*='logo']",
            "img[src*='logo']",
        ]
        
        for selector in logo_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get("src"):
                logo_url = elem.get("src")
                break
    
    return logo_url


def extract_colors_from_logo(logo_url: str) -> dict:
    """Extrait les couleurs dominantes du logo"""
    colors = {
        "primary": (41, 98, 255),      # Bleu par défaut
        "secondary": (255, 193, 7),     # Jaune par défaut
        "text": (33, 37, 41),           # Gris foncé
        "background": (255, 255, 255)   # Blanc
    }
    
    if not COLORTHIEF_AVAILABLE or not logo_url:
        return colors
    
    try:
        # Télécharger l'image
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
        }
        response = requests.get(logo_url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # Vérifier que c'est bien une image
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"⚠️  Le logo n'est pas une image: {content_type}")
            return colors
        
        # Charger l'image avec PIL d'abord pour conversion
        from PIL import Image
        img_data = io.BytesIO(response.content)
        
        # Convertir en RGB si nécessaire (pour les PNG avec transparence)
        pil_img = Image.open(img_data)
        if pil_img.mode in ('RGBA', 'LA', 'P'):
            # Créer un fond blanc et fusionner
            background = Image.new('RGB', pil_img.size, (255, 255, 255))
            if pil_img.mode == 'P':
                pil_img = pil_img.convert('RGBA')
            background.paste(pil_img, mask=pil_img.split()[-1] if len(pil_img.split()) == 4 else None)
            pil_img = background
        elif pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Sauvegarder en mémoire pour ColorThief
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Utiliser ColorThief pour extraire les couleurs
        color_thief = ColorThief(img_buffer)
        
        # Couleur dominante
        dominant = color_thief.get_color(quality=1)
        colors["primary"] = dominant
        
        # Palette de couleurs (5 couleurs)
        try:
            palette = color_thief.get_palette(color_count=5, quality=1)
            if len(palette) >= 2:
                colors["secondary"] = palette[1]
            if len(palette) >= 3:
                # Trouver une couleur sombre pour le texte
                for color in palette:
                    brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000
                    if brightness < 128:
                        colors["text"] = color
                        break
        except Exception:
            pass
        
        print(f"🎨 Couleurs extraites: Primary={colors['primary']}, Secondary={colors['secondary']}")
        
    except Exception as e:
        print(f"⚠️  Impossible d'extraire les couleurs du logo: {e}")
    
    return colors


def translate_profile_to_english(profile: dict) -> dict:
    """Traduit le profil en anglais via Mistral AI"""
    
    if not MISTRAL_AVAILABLE or not MISTRAL_API_KEY:
        print("⚠️  Mistral non disponible, profil non traduit")
        return profile
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    # Collecter tous les textes à traduire
    texts_to_translate = {
        "introduction": profile.get("introduction", ""),
    }
    
    # Summary templates
    for key, value in profile.get("summary_templates", {}).items():
        texts_to_translate[f"summary_{key}"] = value
    
    # Expériences
    for i, exp in enumerate(profile.get("experiences", [])):
        texts_to_translate[f"exp_{i}_title"] = exp.get("title", "")
        texts_to_translate[f"exp_{i}_bullets"] = " ||| ".join(exp.get("bullets", []))
    
    # Formations
    for i, edu in enumerate(profile.get("education", [])):
        texts_to_translate[f"edu_{i}_title"] = edu.get("title", "")
        texts_to_translate[f"edu_{i}_school"] = edu.get("school", "")
    
    # Compétences (catégories seulement, pas les items techniques)
    for skill_id, skill_data in profile.get("skills", {}).items():
        texts_to_translate[f"skill_{skill_id}_name"] = skill_data.get("name", "")
    
    # Certifications (ce sont des dicts avec 'name')
    certs = profile.get("certifications", [])
    if certs:
        cert_names = [c.get("name", "") if isinstance(c, dict) else str(c) for c in certs]
        texts_to_translate["certifications"] = " ||| ".join(cert_names)
    
    # Langues
    for i, lang in enumerate(profile.get("languages", [])):
        texts_to_translate[f"lang_{i}"] = f"{lang.get('name', '')} - {lang.get('level', '')}"
    
    # Centres d'intérêt
    interests = profile.get("interests", [])
    if interests:
        interest_names = [i if isinstance(i, str) else str(i) for i in interests]
        texts_to_translate["interests"] = " ||| ".join(interest_names)
    
    # Créer le prompt de traduction
    texts_json = json.dumps(texts_to_translate, ensure_ascii=False)
    
    prompt = f"""Translate the following French texts to English. Keep the same JSON structure.
For items separated by " ||| ", keep the separator in the translation.
Keep technical terms (BigQuery, Terraform, GCP, Python, etc.) unchanged.
Keep company names and proper nouns unchanged.

JSON to translate:
{texts_json}

Return ONLY the translated JSON, no explanation."""

    try:
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Nettoyer si nécessaire
        if content.startswith("```"):
            content = re.sub(r'^```json?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        
        translated = json.loads(content)
        
        # Reconstruire le profil traduit
        translated_profile = json.loads(json.dumps(profile))  # Deep copy
        
        if "introduction" in translated:
            translated_profile["introduction"] = translated["introduction"]
        
        # Summary templates
        for key in translated_profile.get("summary_templates", {}).keys():
            if f"summary_{key}" in translated:
                translated_profile["summary_templates"][key] = translated[f"summary_{key}"]
        
        # Expériences
        for i, exp in enumerate(translated_profile.get("experiences", [])):
            if f"exp_{i}_title" in translated:
                exp["title"] = translated[f"exp_{i}_title"]
            if f"exp_{i}_bullets" in translated:
                exp["bullets"] = translated[f"exp_{i}_bullets"].split(" ||| ")
        
        # Formations
        for i, edu in enumerate(translated_profile.get("education", [])):
            if f"edu_{i}_title" in translated:
                edu["title"] = translated[f"edu_{i}_title"]
            if f"edu_{i}_school" in translated:
                edu["school"] = translated[f"edu_{i}_school"]
        
        # Compétences
        for skill_id, skill_data in translated_profile.get("skills", {}).items():
            if f"skill_{skill_id}_name" in translated:
                skill_data["name"] = translated[f"skill_{skill_id}_name"]
        
        # Certifications (mettre à jour le 'name' de chaque dict)
        if "certifications" in translated:
            translated_names = translated["certifications"].split(" ||| ")
            for i, cert in enumerate(translated_profile.get("certifications", [])):
                if i < len(translated_names) and isinstance(cert, dict):
                    cert["name"] = translated_names[i]
        
        # Langues
        for i, lang in enumerate(translated_profile.get("languages", [])):
            if f"lang_{i}" in translated:
                parts = translated[f"lang_{i}"].split(" - ")
                if len(parts) == 2:
                    lang["name"] = parts[0]
                    lang["level"] = parts[1]
        
        # Centres d'intérêt
        if "interests" in translated:
            translated_profile["interests"] = translated["interests"].split(" ||| ")
        
        print("🌐 Profil traduit en anglais")
        return translated_profile
        
    except Exception as e:
        print(f"⚠️  Erreur traduction profil: {e}")
        return profile


def generate_cover_with_mistral(profile: dict, job_data: dict, job_context: dict) -> dict:
    """Utilise Mistral AI pour générer une lettre de motivation personnalisée"""
    
    if not MISTRAL_AVAILABLE or not MISTRAL_API_KEY:
        print("⚠️  Mistral non disponible, utilisation du template par défaut")
        return None
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    # Langue de l'offre
    lang = job_data.get("language", "fr")
    lang_instruction = {
        'fr': "Rédige TOUT le contenu en FRANÇAIS.",
        'en': "Write ALL the content in ENGLISH."
    }.get(lang, "Rédige TOUT le contenu en FRANÇAIS.")
    
    # Construire le prompt
    company = job_data.get("company", "l'entreprise")
    job_title = job_data.get("title", "Data Engineer")
    description = job_data.get("description", "")[:2000]  # Limiter la taille
    job_keywords = job_data.get("keywords", [])
    
    # Extraire les infos du profil
    name = profile["personal"]["name"]
    experiences = profile.get("experiences", [])[:3]
    exp_text = ""
    for exp in experiences:
        exp_text += f"- {exp['title']} chez {exp['company']} ({exp['period']}): {'; '.join(exp['bullets'][:2])}\n"
    
    # Compétences PERTINENTES pour l'offre (pas toutes les compétences)
    job_text = job_data.get("raw_text", "").lower()
    relevant_skills = []
    for skill_id, skill_data in profile.get("skills", {}).items():
        for item in skill_data.get("items", []):
            item_lower = item.lower()
            # L'item matche un mot-clé de l'offre
            if item_lower in [kw.lower() for kw in job_keywords]:
                relevant_skills.append(item)
            # L'item est mentionné dans le texte de l'offre
            elif item_lower in job_text:
                relevant_skills.append(item)
    
    # Dédupliquer
    relevant_skills = list(dict.fromkeys(relevant_skills))[:12]
    
    # Si pas assez, ajouter les top compétences
    if len(relevant_skills) < 5:
        for skill_id, skill_data in profile.get("skills", {}).items():
            for item in skill_data.get("items", [])[:2]:
                if item not in relevant_skills:
                    relevant_skills.append(item)
                    if len(relevant_skills) >= 10:
                        break
    
    skills_text = ", ".join(relevant_skills)
    
    # Mots-clés importants de l'offre
    key_requirements = ", ".join(job_keywords[:10])
    
    # Projets marquants
    projects = profile.get("notable_projects", [])
    projects_text = "\n".join([f"- {p['name']}: {p['description']}" for p in projects[:2]]) if projects else "Pas de projets spécifiques mentionnés"
    
    prompt = f"""Tu es un expert en rédaction de lettres de motivation pour des postes Data/Tech.

LANGUE: {lang_instruction}

CONTEXTE DE L'OFFRE:
- Entreprise: {company}
- Poste: {job_title}
- Mots-clés requis: {key_requirements}
- Description: {description[:1500]}

PROFIL DU CANDIDAT:
- Nom: {name}
- Expériences:
{exp_text}
- Compétences PERTINENTES pour cette offre: {skills_text}
- Projets marquants:
{projects_text}

CONSIGNES:
Génère une lettre de motivation en suivant EXACTEMENT cette structure (5 parties distinctes):

1. ACCROCHE (2-3 phrases max): Commence par une réalisation marquante ou une compétence clé qui capte l'attention. Fais un lien direct avec le poste. Ne commence PAS par "Je vous écris pour..." / "I am writing to...".

2. ENTREPRISE (1 paragraphe): Montre que tu connais l'entreprise. Mentionne ses valeurs, son actualité, ce qui t'attire. Explique pourquoi tu veux les rejoindre EUX spécifiquement.

3. MOI (1 paragraphe): Parle de tes compétences et expériences en lien avec le poste. Donne des exemples concrets. UTILISE les compétences pertinentes listées ci-dessus qui correspondent aux mots-clés requis.

4. NOUS (1 paragraphe): Projette une collaboration réussie. Comment tu vas contribuer à leurs objectifs ? Mentionne les compétences techniques pertinentes pour ce poste (parmi: {skills_text}).

5. CONCLUSION (2 phrases): Formule de politesse professionnelle avec demande d'entretien.

IMPORTANT: 
- Utilise UNIQUEMENT les compétences pertinentes listées ci-dessus. Ne mentionne pas de technologies que le candidat ne maîtrise pas.
- {lang_instruction}

FORMAT DE RÉPONSE (JSON):
{{
    "accroche": "...",
    "entreprise": "...",
    "moi": "...",
    "nous": "...",
    "conclusion": "..."
}}

Réponds UNIQUEMENT avec le JSON, sans markdown ni explication."""

    try:
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parser le JSON
        # Nettoyer si nécessaire (enlever les backticks markdown)
        if content.startswith("```"):
            content = re.sub(r'^```json?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        
        result = json.loads(content)
        print("✨ Lettre générée par Mistral AI")
        return result
        
    except Exception as e:
        print(f"⚠️  Erreur Mistral: {e}")
        return None


def load_profile() -> dict:
    """Charge le profil personnel depuis profile.json"""
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_job_offer(url: str) -> dict:
    """Récupère et parse l'offre d'emploi depuis l'URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Erreur lors de la récupération de l'offre: {e}")
        sys.exit(1)
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extraction générique - fonctionne pour la plupart des sites
    job_data = {
        "url": url,
        "title": "",
        "company": "",
        "location": "",
        "description": "",
        "requirements": [],
        "keywords": [],
        "raw_text": ""
    }
    
    # Détection spéciale Welcome to the Jungle
    if "welcometothejungle" in url:
        import re
        import json as json_module
        
        # Extraire depuis l'URL: /companies/{company}/jobs/{job-title}_{city}_{COMPANY}_{id}
        match = re.search(r'/companies/([^/]+)/jobs/([^/?]+)', url)
        if match:
            job_data["company"] = match.group(1).replace('-', ' ').title()
            raw_slug = match.group(2)
            
            # Enlever le suffixe ID (format: _COMPANY_RandomId comme _THALE_DxLJy4A)
            raw_slug = re.sub(r'_[A-Z]{2,}_[A-Za-z0-9]+$', '', raw_slug)
            
            # Séparer par underscore : format typique {job-title}_{city}
            parts = raw_slug.split('_')
            
            if len(parts) >= 2:
                # La dernière partie est probablement la ville
                potential_city = parts[-1].replace('-', ' ')
                job_data["location"] = potential_city.title()
        
        # Extraire les données JSON de window.__INITIAL_DATA__ (WTTJ utilise du JS)
        json_match = re.search(r'window\.__INITIAL_DATA__\s*=\s*"(.+?)"(?:\s|;)', response.text)
        if json_match:
            try:
                escaped_json = json_match.group(1)
                # Decode the escaped JSON string
                decoded = json_module.loads('"' + escaped_json + '"')
                parsed_data = json_module.loads(decoded)
                
                # Chercher les données du job dans queries
                for query in parsed_data.get('queries', []):
                    state = query.get('state', {})
                    data = state.get('data', {})
                    if 'name' in data:
                        # Titre du poste
                        raw_title = data.get('name', '')
                        # Nettoyer le titre
                        raw_title = re.sub(r'\s*[-–—]\s+.*$', '', raw_title)
                        raw_title = re.sub(r'\s*[\(\[]\s*[xXhHfFmM]\s*/?\s*[xXhHfFmM]\s*/?\s*[xXhHfFmM]?\s*[\)\]]?\s*$', '', raw_title)
                        raw_title = re.sub(r'\s+[HhFf]\s*/?\s*[HhFf]\s*$', '', raw_title)
                        job_data["title"] = raw_title.strip()
                        
                        # Description (enlever HTML)
                        description = data.get('description', '')
                        if description:
                            desc_soup = BeautifulSoup(description, 'html.parser')
                            job_data["description"] = desc_soup.get_text(separator='\n', strip=True)
                        
                        # Profil recherché
                        profile = data.get('profile', '')
                        if profile:
                            profile_soup = BeautifulSoup(profile, 'html.parser')
                            job_data["requirements"] = [li.get_text(strip=True) for li in profile_soup.find_all('li')]
                        
                        # Location depuis offices
                        offices = data.get('offices', [])
                        if offices and not job_data["location"]:
                            job_data["location"] = offices[0].get('city', '')
                        
                        # Logo de l'organisation
                        organization = data.get('organization', {})
                        if organization:
                            job_data["company"] = organization.get('name', job_data["company"])
                            logo = organization.get('logo', {})
                            if logo:
                                job_data["logo_url"] = logo.get('url', '')
                        
                        break
            except Exception as e:
                print(f"⚠️ Erreur parsing JSON WTTJ: {e}")
        
        # Fallback: essayer le HTML si pas de données JSON
        if not job_data["title"]:
            title_elem = soup.select_one("h1")
            if title_elem:
                html_title = title_elem.get_text(strip=True)
                html_title = re.sub(r'\s*[-–—]\s+.*$', '', html_title)
                html_title = re.sub(r'\s*[\(\[]\s*[xXhHfFmM]\s*/?\s*[xXhHfFmM]\s*/?\s*[xXhHfFmM]?\s*[\)\]]?\s*$', '', html_title)
                html_title = re.sub(r'\s+[HhFf]\s*/?\s*[HhFf]\s*$', '', html_title)
                job_data["title"] = html_title.strip()
    
    # Titre du poste (si pas déjà trouvé)
    if not job_data["title"]:
        title_selectors = [
            "h1", 
            "[data-testid='job-title']",
            ".job-title",
            ".offer-title",
            "[class*='title']"
        ]
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                job_data["title"] = elem.get_text(strip=True)
                break
    
    # Nom de l'entreprise (si pas déjà trouvé)
    if not job_data["company"]:
        company_selectors = [
            "[data-testid='company-name']",
            ".company-name",
            "[class*='company']",
            "meta[property='og:site_name']"
        ]
        for selector in company_selectors:
            elem = soup.select_one(selector)
            if elem:
                job_data["company"] = elem.get("content") if elem.name == "meta" else elem.get_text(strip=True)
                if job_data["company"]:
                    break
    
    # Description complète
    content_selectors = [
        "[data-testid='job-section-description']",
        ".job-description",
        ".offer-description",
        "article",
        "main",
        "[class*='description']"
    ]
    for selector in content_selectors:
        elem = soup.select_one(selector)
        if elem:
            job_data["description"] = elem.get_text(separator="\n", strip=True)
            break
    
    # Texte brut de toute la page pour l'analyse
    job_data["raw_text"] = soup.get_text(separator=" ", strip=True).lower()
    
    # Extraction des mots-clés techniques
    job_data["keywords"] = extract_keywords(job_data["raw_text"])
    
    # Extraction du logo de l'entreprise
    job_data["logo_url"] = extract_logo_url(soup, url, job_data.get("company", ""))
    if job_data["logo_url"]:
        print(f"🖼️  Logo trouvé: {job_data['logo_url'][:80]}...")
    
    # Extraction des couleurs du logo
    job_data["colors"] = extract_colors_from_logo(job_data["logo_url"])
    
    # Détection de la langue de l'offre
    job_data["language"] = detect_offer_language(job_data.get("description", "") or job_data.get("raw_text", ""))
    lang_emoji = "🇬🇧" if job_data["language"] == "en" else "🇫🇷"
    print(f"{lang_emoji} Langue détectée: {'Anglais' if job_data['language'] == 'en' else 'Français'}")
    
    return job_data


def extract_keywords(text: str) -> list:
    """Extrait les mots-clés techniques du texte de l'offre"""
    text_lower = text.lower()
    
    # Liste de mots-clés techniques à détecter
    tech_keywords = {
        # Cloud
        "gcp", "google cloud", "aws", "azure", "cloud", "kubernetes", "docker", "terraform",
        # Data Engineering
        "bigquery", "big query", "airflow", "kafka", "spark", "hadoop", "dataflow", "pub/sub",
        "etl", "elt", "pipeline", "data pipeline", "dbt", "fivetran", "airbyte",
        # Databases
        "sql", "nosql", "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
        "snowflake", "redshift", "databricks",
        # Programming
        "python", "java", "scala", "go", "golang", "bash", "shell", "r",
        # ML/AI
        "machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn",
        "hugging face", "bert", "llm", "ia", "ai", "vertex ai", "mlops",
        # BI/Viz
        "power bi", "tableau", "looker", "lookml", "metabase", "data visualization", "dashboard",
        "semantic layer", "bi", "reporting",
        # Methodologies
        "agile", "scrum", "devops", "ci/cd", "git",
        # Data Governance
        "data quality", "data governance", "gouvernance", "qualité des données", "rgpd", "gdpr",
        "data catalog", "metadata", "lineage",
        # Soft skills
        "anglais", "english", "communication", "équipe", "team"
    }
    
    found = []
    for kw in tech_keywords:
        if kw in text_lower:
            found.append(kw)
    
    return list(set(found))


def match_score(item_keywords: list, job_keywords: list) -> int:
    """Calcule un score de correspondance entre deux listes de mots-clés"""
    item_set = set(k.lower() for k in item_keywords)
    job_set = set(k.lower() for k in job_keywords)
    return len(item_set & job_set)


def adapt_profile(profile: dict, job_data: dict) -> dict:
    """Adapte le profil en fonction de l'offre d'emploi"""
    job_keywords = job_data["keywords"]
    job_text = job_data["raw_text"]
    
    adapted = {
        "personal": profile["personal"].copy(),
        "job_title": job_data["title"] or "Data Engineer",
        "company": job_data["company"] or "Entreprise",
        "job_url": job_data["url"]
    }
    
    # Déterminer le meilleur titre/résumé
    title_scores = {
        "data_engineer": sum(1 for kw in ["etl", "elt", "pipeline", "airflow", "gcp", "bigquery", "data engineer", 
                                          "dbt", "terraform", "kafka", "spark", "dataflow", "orchestration",
                                          "cloud", "aws", "azure", "infrastructure"] if kw in job_text),
        "data_scientist": sum(1 for kw in ["machine learning", "ml", "model", "nlp", "deep learning", "data scientist",
                                           "tensorflow", "pytorch", "scikit", "prediction", "classification"] if kw in job_text),
        "data_steward": sum(1 for kw in ["governance", "gouvernance", "quality", "qualité", "steward", "catalog",
                                         "metadata", "lineage", "compliance"] if kw in job_text),
        "data_analyst": sum(1 for kw in ["analyst", "bi", "power bi", "tableau", "dashboard", "reporting",
                                         "excel", "business intelligence"] if kw in job_text)
    }
    best_profile = max(title_scores, key=title_scores.get)
    
    # Phrase de base personnelle (toujours présente) - versions FR et EN
    base_intro_fr = profile.get("personal_intro", 
        "Avec un parcours riche en programmation/développement et spécialisé en data, "
        "notamment en data gouvernance et en data engineering, je cherche une nouvelle "
        "opportunité pour mettre en pratique mes expériences et connaissances acquises, "
        "afin de relever de nouveaux défis.")
    
    base_intro_en = profile.get("personal_intro_en",
        "With a rich background in programming/development and specialized in data, "
        "particularly in data governance and data engineering, I am seeking a new "
        "opportunity to apply my acquired experiences and knowledge, in order to take on new challenges.")
    
    # Phrase de spécialisation selon le profil détecté - versions FR et EN
    specialization_phrases_fr = {
        "data_engineer": "Passionné par l'industrialisation des flux de données, l'optimisation des pipelines et l'infrastructure cloud.",
        "data_scientist": "Passionné par le Machine Learning et l'IA, avec une expertise en déploiement de modèles et analyse prédictive.",
        "data_steward": "Expert en gouvernance des données, catalogage et qualité des données, avec une forte capacité de collaboration transverse.",
        "data_analyst": "Passionné par la visualisation de données et le reporting, avec une maîtrise des outils BI modernes.",
        "default": ""
    }
    
    specialization_phrases_en = {
        "data_engineer": "Passionate about industrializing data flows, optimizing pipelines, and cloud infrastructure.",
        "data_scientist": "Passionate about Machine Learning and AI, with expertise in model deployment and predictive analytics.",
        "data_steward": "Expert in data governance, cataloging, and data quality, with strong cross-functional collaboration skills.",
        "data_analyst": "Passionate about data visualization and reporting, with mastery of modern BI tools.",
        "default": ""
    }
    
    # Choisir la langue selon l'offre
    lang = job_data.get("language", "fr")
    if lang == "en":
        base_intro = base_intro_en
        specialization = specialization_phrases_en.get(best_profile, "")
    else:
        base_intro = base_intro_fr
        specialization = specialization_phrases_fr.get(best_profile, "")
    
    # Construire le résumé complet
    if specialization:
        adapted["summary"] = f"{base_intro} {specialization}"
    else:
        adapted["summary"] = base_intro
    
    # Adapter le titre si on a un titre d'offre
    if job_data["title"]:
        # Nettoyer et utiliser le titre de l'offre si c'est un titre data
        title_lower = job_data["title"].lower()
        if any(kw in title_lower for kw in ["data", "engineer", "scientist", "analyst", "bi", "ml"]):
            adapted["display_title"] = job_data["title"].split(" - ")[0].split(" (")[0].strip()
        else:
            adapted["display_title"] = profile["titles"][0]
    else:
        adapted["display_title"] = profile["titles"][0]
    
    # Trier les expériences par pertinence
    experiences = []
    for exp in profile["experiences"]:
        score = match_score(exp["keywords"], job_keywords)
        # Sélectionner les bullets les plus pertinentes (max 4)
        selected_bullets = exp["bullets"][:4]
        experiences.append({
            **exp,
            "score": score,
            "selected_bullets": selected_bullets
        })
    experiences.sort(key=lambda x: (-x["score"], x["priority"]))
    adapted["experiences"] = experiences
    
    # Trier les compétences par pertinence
    skills = []
    for skill_id, skill_data in profile["skills"].items():
        score = match_score(skill_data["keywords"], job_keywords)
        # Filtrer les items pertinents - matching amélioré
        # Priorité 1: items qui matchent exactement un mot-clé de l'offre
        exact_match = []
        # Priorité 2: items présents dans le texte de l'offre
        text_match = []
        # Priorité 3: autres items
        other_items = []
        
        for item in skill_data["items"]:
            item_lower = item.lower()
            item_clean = item_lower.replace(" ", "").replace("-", "")
            
            # Vérifier si c'est un match exact avec un mot-clé détecté
            if item_lower in job_keywords or item_clean in [k.replace(" ", "").replace("-", "") for k in job_keywords]:
                exact_match.append(item)
            # Vérifier si l'item est mentionné dans le texte de l'offre
            elif item_lower in job_text or item_clean in job_text.replace(" ", ""):
                text_match.append(item)
            # Vérifier si un mot-clé est contenu dans l'item
            elif any(kw.lower() in item_lower for kw in job_keywords):
                text_match.append(item)
            else:
                other_items.append(item)
        
        # Combiner: exact matches en premier, puis text matches, puis autres
        all_items = exact_match + text_match + other_items
        if not exact_match and not text_match:
            all_items = skill_data["items"][:5]
        
        # Score: bonus très important pour les exact matches
        item_score = len(exact_match) * 5 + len(text_match) * 2
        skills.append({
            "id": skill_id,
            "label": skill_data["label"],
            "items": all_items[:6],
            "score": score + item_score,
            "exact_count": len(exact_match)
        })
    skills.sort(key=lambda x: (-x["score"], -x["exact_count"]))
    adapted["skills"] = skills[:7]  # Top 7 catégories
    
    # Filtrer les certifications pertinentes
    certifications = []
    for cert in profile["certifications"]:
        score = match_score(cert["keywords"], job_keywords)
        certifications.append({**cert, "score": score})
    certifications.sort(key=lambda x: -x["score"])
    adapted["certifications"] = certifications[:5]  # Top 5
    
    # Education, langues et intérêts restent identiques
    adapted["education"] = profile["education"]
    adapted["languages"] = profile["languages"]
    adapted["interests"] = profile["interests"]
    
    # Mots-clés de l'offre pour la lettre de motivation
    adapted["job_keywords"] = job_keywords
    
    # Localisation de l'offre
    adapted["job_location"] = job_data.get("location", "")
    
    # Analyser le contexte de l'offre pour la lettre
    adapted["job_context"] = analyze_job_context(job_data)
    adapted["job_description"] = job_data.get("description", "")
    
    # Logo et couleurs de l'entreprise
    adapted["logo_url"] = job_data.get("logo_url", "")
    adapted["colors"] = job_data.get("colors", {})
    
    # Langue de l'offre
    adapted["language"] = job_data.get("language", "fr")
    
    return adapted


def escape_latex(text: str) -> str:
    """Échappe les caractères spéciaux LaTeX"""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def generate_cv(adapted: dict, output_path: Path) -> None:
    """Génère le CV LaTeX adapté"""
    
    # Langue de l'offre
    lang = adapted.get("language", "fr")
    
    # Traductions des sections
    translations = {
        "fr": {
            "experiences": "EXPÉRIENCES",
            "education": "FORMATIONS",
            "skills": "COMPÉTENCES",
            "projects": "PROJETS PERSONNELS",
            "certifications": "CERTIFICATIONS",
            "languages": "LANGUES",
            "interests": "CENTRES D'INTÉRÊT",
            "babel": "french"
        },
        "en": {
            "experiences": "EXPERIENCE",
            "education": "EDUCATION",
            "skills": "SKILLS",
            "projects": "PERSONAL PROJECTS",
            "certifications": "CERTIFICATIONS",
            "languages": "LANGUAGES",
            "interests": "INTERESTS",
            "babel": "english"
        }
    }
    t = translations.get(lang, translations["fr"])
    
    # Générer les sections
    experiences_tex = ""
    for exp in adapted["experiences"]:
        bullets = "\n".join(f"    \\item {escape_latex(b)}" for b in exp["selected_bullets"])
        if bullets:
            experiences_tex += f"""\\cventry{{{escape_latex(exp['title'])}}}
{{{escape_latex(exp['company'])}}}
{{{exp['period']}}}
{{%
\\begin{{itemize}}[leftmargin=*, noitemsep, topsep=0pt]
{bullets}
\\end{{itemize}}
}}

"""
        else:
            experiences_tex += f"""\\cventry{{{escape_latex(exp['title'])}}}
{{{escape_latex(exp['company'])}}}
{{{exp['period']}}}
{{}}

"""
    
    education_tex = ""
    for edu in adapted["education"]:
        education_tex += f"""\\cventry{{{escape_latex(edu['title'])}}}
{{{escape_latex(edu['school'])}}}
{{{edu['period']}}}
{{}}

"""
    
    skills_tex = ""
    for skill in adapted["skills"]:
        items = ", ".join(skill["items"])
        skills_tex += f"\\competence{{{escape_latex(skill['label'])}}}{{{escape_latex(items)}}}\n"
    
    certifications_tex = ""
    for cert in adapted["certifications"]:
        certifications_tex += f"\\certification{{{escape_latex(cert['name'])} ({cert['date']})}}\n"
    
    languages_tex = ""
    for lang in adapted["languages"]:
        languages_tex += f"\\certification{{\\small {escape_latex(lang['name'])} - {escape_latex(lang['level'])}}}\n"
    
    interests_tex = ""
    for interest in adapted["interests"]:
        interests_tex += f"\\certification{{\\small {interest}}}\n"
    
    # Projects section
    projects_tex = ""
    for proj in adapted.get("projects", []):
        projects_tex += f"""\\noindent\\textbf{{{escape_latex(proj['name'])}}} \\hfill \\textcolor{{textgray}}{{\\small {escape_latex(proj.get('technologies', ''))}}}\\\\
{{\\small {escape_latex(proj['description'])}}}\\\\[4pt]
"""
    
    # Template CV
    cv_content = f"""\\documentclass[a4paper,10pt]{{article}}

% Packages
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage[{t['babel']}]{{babel}}
\\usepackage{{lmodern}}
\\usepackage[sfdefault]{{roboto}}
\\usepackage{{geometry}}
\\usepackage{{xcolor}}
\\usepackage{{tikz}}
\\usepackage{{fontawesome5}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage{{hyperref}}
\\usepackage{{parskip}}

% Page geometry
\\geometry{{left=0.5cm, right=0.8cm, top=0.4cm, bottom=0.4cm}}

% Colors
\\definecolor{{maingreen}}{{RGB}}{{76, 175, 130}}
\\definecolor{{darkgreen}}{{RGB}}{{60, 140, 105}}
\\definecolor{{lightgray}}{{RGB}}{{245, 245, 245}}
\\definecolor{{textgray}}{{RGB}}{{80, 80, 80}}

% Remove page numbers
\\pagestyle{{empty}}

% Hyperref setup
\\hypersetup{{
    colorlinks=true,
    linkcolor=maingreen,
    urlcolor=maingreen
}}

% Custom section command
\\newcommand{{\\cvsection}}[1]{{%
    \\vspace{{5pt}}
    \\noindent\\colorbox{{maingreen}}{{%
        \\parbox{{\\dimexpr\\linewidth-2\\fboxsep}}{{%
            \\textcolor{{white}}{{\\textbf{{\\normalsize #1}}}}%
        }}%
    }}%
    \\vspace{{4pt}}
}}

% Custom subsection for experiences
\\newcommand{{\\cventry}}[4]{{%
    \\noindent\\textbf{{#1}}\\\\
    \\textit{{\\small\\textcolor{{textgray}}{{#2}}}} \\hfill \\textcolor{{textgray}}{{\\small #3}}\\\\
    #4
    \\vspace{{2pt}}
}}

% Competence line
\\newcommand{{\\competence}}[2]{{%
    \\noindent\\textbf{{\\small #1:}} {{\\small #2}}\\\\[1pt]
}}

% Certification item
\\newcommand{{\\certification}}[1]{{%
    \\textcolor{{maingreen}}{{\\textbullet}} {{\\small #1}}\\\\[1pt]
}}

\\begin{{document}}

% Left green bar
\\begin{{tikzpicture}}[remember picture, overlay]
    \\fill[maingreen] (current page.north west) rectangle ([xshift=0.3cm]current page.south west);
\\end{{tikzpicture}}

% Header
\\begin{{center}}
    {{\\LARGE\\textbf{{{adapted['personal']['name']}}}}}\\\\[3pt]
    {{\\normalsize\\textcolor{{maingreen}}{{{escape_latex(adapted['display_title'])}}}}}\\\\[4pt]
    {{\\small\\textcolor{{textgray}}{{%
        \\faEnvelope\\ {adapted['personal']['email']} \\quad
        \\faPhone\\ {adapted['personal']['phone']} \\quad
        \\faMapMarker\\ {adapted['personal']['location']}
    }}}}
\\end{{center}}

\\vspace{{4pt}}

% Introduction
{{\\small\\noindent\\textcolor{{textgray}}{{%
{escape_latex(adapted['summary'])}
}}}}

% EXPERIENCES
\\cvsection{{{t['experiences']}}}
{experiences_tex}

% FORMATIONS
\\cvsection{{{t['education']}}}
{education_tex}

% COMPETENCES
\\cvsection{{{t['skills']}}}
{skills_tex}

% PROJETS PERSONNELS
{f"\\cvsection{{{t['projects']}}}" if projects_tex else ""}
{projects_tex}

% CERTIFICATIONS
\\cvsection{{{t['certifications']}}}
{certifications_tex}

% LANGUES et CENTRES D'INTERET - 2 colonnes
\\noindent
\\begin{{minipage}}[t]{{0.48\\linewidth}}
\\cvsection{{{t['languages']}}}
\\vspace{{-2pt}}
{languages_tex}\\end{{minipage}}%
\\hfill
\\begin{{minipage}}[t]{{0.48\\linewidth}}
\\cvsection{{{t['interests']}}}
\\vspace{{-2pt}}
{interests_tex}\\end{{minipage}}

\\end{{document}}
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cv_content)
    
    print(f"✅ CV généré: {output_path}")


def analyze_job_context(job_data: dict) -> dict:
    """Analyse le contexte de l'offre pour personnaliser la lettre"""
    description = job_data.get("description", "").lower()
    raw_text = job_data.get("raw_text", "").lower()
    
    context = {
        "company_type": "entreprise",  # startup, scale-up, grand groupe
        "tone": "professional",  # casual, professional, formal
        "team_size": "",
        "missions": [],
        "values": [],
        "tech_stack": [],
        "growth_stage": "",
        "remote_policy": "",
        "key_challenges": []
    }
    
    # Détecter le type d'entreprise
    if any(w in raw_text for w in ["startup", "early stage", "seed", "série a"]):
        context["company_type"] = "startup"
        context["tone"] = "casual"
    elif any(w in raw_text for w in ["scale-up", "scaleup", "série b", "série c", "hyper-croissance", "forte croissance"]):
        context["company_type"] = "scale-up"
        context["tone"] = "casual"
    elif any(w in raw_text for w in ["groupe", "filiale", "cac 40", "grand compte", "leader mondial"]):
        context["company_type"] = "grand groupe"
        context["tone"] = "formal"
    
    # Détecter French Tech
    if "french tech" in raw_text or "next 40" in raw_text or "next 120" in raw_text:
        context["growth_stage"] = "French Tech"
    
    # Détecter la taille de l'équipe data
    import re
    team_match = re.search(r'équipe\s+(?:data\s+)?(?:de\s+)?(\d+)', raw_text)
    if team_match:
        context["team_size"] = team_match.group(1)
    
    # Détecter le télétravail
    if any(w in raw_text for w in ["full remote", "100% remote", "télétravail total"]):
        context["remote_policy"] = "full remote"
    elif any(w in raw_text for w in ["télétravail", "remote", "hybride"]):
        context["remote_policy"] = "hybride"
    
    # Extraire la stack technique mentionnée
    tech_keywords = ["bigquery", "snowflake", "databricks", "airflow", "dbt", "spark", 
                     "kafka", "python", "sql", "terraform", "docker", "kubernetes",
                     "aws", "gcp", "azure", "looker", "tableau", "power bi", "dataflow"]
    context["tech_stack"] = [t for t in tech_keywords if t in raw_text]
    
    # Extraire les valeurs de l'entreprise
    value_keywords = {
        "innovation": ["innovation", "innover", "disruption", "révolutionne"],
        "collaboration": ["collaboration", "équipe", "ensemble", "collectif"],
        "excellence": ["excellence", "exigence", "qualité", "rigueur"],
        "impact": ["impact", "différence", "transformation", "changer"],
        "croissance": ["croissance", "ambition", "scale", "développement"],
        "bienveillance": ["bienveillance", "humain", "bien-être", "care"]
    }
    for value, keywords in value_keywords.items():
        if any(k in raw_text for k in keywords):
            context["values"].append(value)
    
    # Extraire les défis/challenges mentionnés
    if "challenge" in raw_text or "défi" in raw_text:
        context["key_challenges"].append("relever des défis ambitieux")
    if "croissance" in raw_text or "scale" in raw_text:
        context["key_challenges"].append("accompagner la croissance")
    if "industrialis" in raw_text:
        context["key_challenges"].append("industrialiser les pipelines")
    if "ia" in raw_text or "machine learning" in raw_text or "ml" in raw_text:
        context["key_challenges"].append("intégrer l'IA/ML")
    
    return context


def generate_cover_letter(adapted: dict, output_path: Path, profile: dict = None) -> None:
    """Génère la lettre de motivation LaTeX avec structure professionnelle
    
    Structure :
    1. Accroche percutante (réalisation marquante)
    2. Paragraphe Entreprise (pourquoi cette entreprise)
    3. Paragraphe Moi (compétences et expériences)
    4. Paragraphe Nous (projection dans la collaboration)
    5. Formule de politesse formelle
    
    Utilise Mistral AI pour générer le contenu si l'API est disponible.
    """
    
    company = adapted["company"]
    job_title = adapted["job_title"]
    name = adapted["personal"]["name"]
    email = adapted["personal"]["email"]
    phone = adapted["personal"]["phone"]
    personal_location = adapted["personal"]["location"]
    job_location = adapted.get("job_location", "") or personal_location
    job_keywords = adapted.get("job_keywords", [])
    job_context = adapted.get("job_context", {})
    job_description = adapted.get("job_description", "")
    
    # Détection de la langue
    lang = adapted.get("language", "fr")
    
    # Traductions pour la lettre de motivation
    t = {
        'fr': {
            'babel': 'french',
            'subject': 'Objet :',
            'application_for': 'Candidature au poste de',
            'greeting': 'Madame, Monsieur,',
            'today_intro': 'Aujourd\'hui, je souhaite mettre mes compétences au service de',
            'as_position': 'en tant que',
            'recruitment': 'Service Recrutement',
            'made_at': 'Fait à',
            'on_date': 'le',
            'accroche_default': "Passionné par la data et son potentiel de transformation, je souhaite aujourd'hui mettre mes compétences au service de votre entreprise.",
            'currently': 'Actuellement',
            'at': 'chez',
            'developed_expertise': "j'ai développé une expertise approfondie, notamment en",
            'previous_exp': "Mon expérience précédente en tant que",
            'allowed_develop': "m'a permis de développer une solide culture de la qualité des données et de la collaboration transverse",
            'education_complement': "Ma formation en",
            'at_school': "à",
            'completes_path': "complète ce parcours par une vision analytique rigoureuse",
            'joining_team': "Intégrer votre équipe en tant que",
            'represents_opportunity': "représente pour moi l'opportunité de mettre mes compétences techniques",
            'at_service': "au service de vos projets. Ma",
            'will_be_assets': "seront des atouts pour contribuer efficacement à la réussite de vos missions.",
            'formule_formal': "Dans l'attente de votre réponse, je me tiens à votre disposition pour un entretien. Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
            'formule_casual': "Je serais ravi d'échanger avec vous lors d'un entretien pour vous présenter plus en détail mon parcours et mes motivations. Dans cette attente, je vous adresse mes meilleures salutations.",
            'formule_default': "En espérant que ma candidature retiendra votre attention, je reste à votre disposition pour un entretien. Veuillez agréer, Madame, Monsieur, mes sincères salutations.",
            'qualites_default': "rigueur, esprit d'équipe et proactivité",
            'startup_intro': "En tant que startup innovante,",
            'offers_environment': "offre un environnement propice à la prise d'initiative et à l'impact direct",
            'scaleup_intro': ", en pleine phase de croissance, représente exactement le type d'environnement dynamique où je souhaite évoluer",
            'mission_caught': "La mission de",
            'caught_attention': "m'a particulièrement interpellé",
            'appreciate': "J'apprécie particulièrement",
            'values_of': "les valeurs d'",
            'animating_team': "qui animent votre équipe",
            'your_stack': "votre stack technique",
            'ambitious_challenges': "les défis ambitieux que vous proposez",
            'as_well_as': "ainsi que",
            'and': "et",
            'member_of': ", membre de la",
            'embodies_ambition': ", incarne l'ambition et l'innovation qui me motivent",
            'project_impact': "Cette réalisation illustre ma capacité à mener des projets data à fort impact.",
            'convinced_value': ", je suis convaincu de pouvoir apporter une réelle valeur ajoutée à votre équipe.",
            'strong_experience': "Fort de mon expérience en tant que",
        },
        'en': {
            'babel': 'english',
            'subject': 'Subject:',
            'application_for': 'Application for the position of',
            'greeting': 'Dear Hiring Manager,',
            'today_intro': 'Today, I would like to bring my skills to',
            'as_position': 'as a',
            'recruitment': 'Recruitment Department',
            'made_at': 'Written in',
            'on_date': 'on',
            'accroche_default': "Passionate about data and its transformative potential, I am eager to contribute my skills to your organization.",
            'currently': 'Currently',
            'at': 'at',
            'developed_expertise': "I have developed deep expertise, particularly in",
            'previous_exp': "My previous experience as",
            'allowed_develop': "enabled me to build a strong foundation in data quality and cross-functional collaboration",
            'education_complement': "My education in",
            'at_school': "at",
            'completes_path': "complements this path with a rigorous analytical perspective",
            'joining_team': "Joining your team as a",
            'represents_opportunity': "represents an opportunity for me to apply my technical skills",
            'at_service': "to support your projects. My",
            'will_be_assets': "will be valuable assets to contribute effectively to your mission's success.",
            'formule_formal': "I look forward to your response and remain at your disposal for an interview. Please accept my best regards.",
            'formule_casual': "I would be delighted to discuss my background and motivations with you in an interview. Looking forward to hearing from you. Best regards.",
            'formule_default': "I hope my application will be of interest to you, and I remain available for an interview at your convenience. Sincerely.",
            'qualites_default': "rigor, teamwork and proactivity",
            'startup_intro': "As an innovative startup,",
            'offers_environment': "offers an environment conducive to initiative and direct impact",
            'scaleup_intro': ", in full growth phase, represents exactly the kind of dynamic environment where I want to evolve",
            'mission_caught': "The mission of",
            'caught_attention': "particularly caught my attention",
            'appreciate': "I particularly appreciate",
            'values_of': "the values of",
            'animating_team': "that drive your team",
            'your_stack': "your tech stack",
            'ambitious_challenges': "the ambitious challenges you offer",
            'as_well_as': "as well as",
            'and': "and",
            'member_of': ", member of the",
            'embodies_ambition': ", embodies the ambition and innovation that motivate me",
            'project_impact': "This achievement illustrates my ability to lead high-impact data projects.",
            'convinced_value': ", I am confident I can bring real added value to your team.",
            'strong_experience': "With my experience as",
        }
    }[lang]
    
    # ============================================
    # TENTATIVE GÉNÉRATION MISTRAL
    # ============================================
    mistral_content = None
    if MISTRAL_API_KEY and profile:
        print("🤖 Génération Mistral AI en cours...")
        mistral_content = generate_cover_with_mistral(profile, adapted, job_context)
        if mistral_content:
            print("✨ Contenu généré par Mistral AI")
    
    # Récupérer les expériences pertinentes
    main_exp = adapted["experiences"][0] if adapted["experiences"] else None
    second_exp = adapted["experiences"][1] if len(adapted["experiences"]) > 1 else None
    
    # Récupérer les éléments du profil enrichi
    accroches = adapted.get("accroches", [])
    qualites = adapted.get("qualites", [])
    projets = adapted.get("projets_marquants", [])
    
    # Contexte de l'offre
    tone = job_context.get("tone", "professional")
    company_type = job_context.get("company_type", "entreprise")
    tech_stack = job_context.get("tech_stack", [])
    values = job_context.get("values", [])
    challenges = job_context.get("key_challenges", [])
    growth_stage = job_context.get("growth_stage", "")
    
    # ============================================
    # 1. ACCROCHE - Réalisation marquante
    # ============================================
    accroche = ""
    # Sélectionner l'accroche la plus pertinente selon les mots-clés
    best_accroche_score = -1
    for acc in accroches:
        score = sum(1 for kw in acc.get("keywords", []) if kw in job_keywords)
        if score > best_accroche_score:
            best_accroche_score = score
            accroche = acc["text"]
    
    if not accroche:
        # Accroche par défaut basée sur l'expérience principale
        if main_exp:
            accroche = f"{t['strong_experience']} {main_exp['title']} {t['at']} {main_exp['company']}{t['convinced_value']}"
        else:
            accroche = t['accroche_default']
    
    # Si on a des projets marquants, les utiliser dans l'accroche
    if projets and not best_accroche_score > 0:
        # Sélectionner le projet le plus pertinent
        best_proj = None
        best_proj_score = -1
        for proj in projets:
            score = sum(1 for kw in proj.get("keywords", []) if kw in job_keywords)
            if score > best_proj_score:
                best_proj_score = score
                best_proj = proj
        
        if best_proj:
            accroche = f"{best_proj['description']} : {best_proj['impact']}. {t['project_impact']}"
    
    # ============================================
    # 2. PARAGRAPHE ENTREPRISE - Pourquoi vous ?
    # ============================================
    
    # Construire un paragraphe fluide sur l'entreprise
    if growth_stage:
        intro_entreprise = f"{escape_latex(company)}{t['member_of']}{growth_stage}{t['embodies_ambition']}"
    elif company_type == "startup":
        intro_entreprise = f"{t['startup_intro']} {escape_latex(company)} {t['offers_environment']}"
    elif company_type == "scale-up":
        intro_entreprise = f"{escape_latex(company)}{t['scaleup_intro']}"
    else:
        intro_entreprise = f"{t['mission_caught']} {escape_latex(company)} {t['caught_attention']}"

    # Valeurs et stack
    complements = []
    if values:
        values_text = " {0} ".format(t['and']).join(values[:2])
        complements.append(f"{t['values_of']}{values_text} {t['animating_team']}")

    if tech_stack:
        stack_text = ", ".join(tech.upper() for tech in tech_stack[:4])
        complements.append(f"{t['your_stack']} ({stack_text})")

    if challenges:
        complements.append(t['ambitious_challenges'])

    # Joindre avec des connecteurs variés
    if len(complements) == 1:
        para_entreprise = f"{intro_entreprise}. {t['appreciate']} {complements[0]}."
    elif len(complements) == 2:
        para_entreprise = f"{intro_entreprise}. {t['appreciate']} {complements[0]}, {t['as_well_as']} {complements[1]}."
    elif len(complements) >= 3:
        para_entreprise = f"{intro_entreprise}. {t['appreciate']} {complements[0]}, {complements[1]}, {t['and']} {complements[2]}."
    
    # ============================================
    # 3. PARAGRAPHE MOI - Compétences et expériences
    # ============================================
    para_moi_parts = []
    
    # Expérience actuelle
    if main_exp and main_exp.get('selected_bullets'):
        # Sélectionner les bullets pertinentes
        relevant_bullets = [b for b in main_exp['selected_bullets'][:3] 
                          if any(kw in b.lower() for kw in job_keywords[:10])]
        if not relevant_bullets:
            relevant_bullets = main_exp['selected_bullets'][:2]
        
        # Reformuler le bullet pour l'intégrer proprement
        first_bullet = relevant_bullets[0] if relevant_bullets else ""
        # Enlever le point final si présent et mettre en minuscule
        if first_bullet.endswith('.'):
            first_bullet = first_bullet[:-1]
        first_bullet = first_bullet[0].lower() + first_bullet[1:] if first_bullet else ""
        
        para_moi_parts.append(f"{t['currently']} \\textbf{{{escape_latex(main_exp['title'])}}} {t['at']} \\textbf{{{escape_latex(main_exp['company'])}}}, {t['developed_expertise']} {escape_latex(first_bullet)}")

    # Expérience précédente si pertinente
    if second_exp:
        para_moi_parts.append(f"{t['previous_exp']} {escape_latex(second_exp['title'])} {t['at']} {escape_latex(second_exp['company'])} {t['allowed_develop']}")

    # Formation
    if adapted.get("education"):
        edu = adapted["education"][0]
        para_moi_parts.append(f"{t['education_complement']} {escape_latex(edu['title'])} {t['at_school']} {escape_latex(edu['school'])} {t['completes_path']}")
    
    para_moi = ". ".join(para_moi_parts) + "."
    para_moi = para_moi.replace("..", ".")
    
    # ============================================
    # 4. PARAGRAPHE NOUS - Projection
    # ============================================
    # Compétences techniques qui matchent exactement les mots-clés de l'offre
    matching_skills = []
    job_keywords_lower = [kw.lower() for kw in job_keywords]
    
    # Parcourir les compétences adaptées (déjà triées par pertinence)
    for skill in adapted["skills"]:
        for item in skill.get("items", []):
            item_lower = item.lower()
            # Match exact avec un mot-clé de l'offre
            if item_lower in job_keywords_lower:
                matching_skills.append(item)
            # Ou l'item est dans le texte de l'offre
            elif item_lower in job_description.lower():
                matching_skills.append(item)
            # Ou un mot-clé est contenu dans l'item
            elif any(kw in item_lower for kw in job_keywords_lower if len(kw) > 2):
                matching_skills.append(item)
    
    # Dédupliquer tout en gardant l'ordre
    seen = set()
    matching_skills = [x for x in matching_skills if not (x in seen or seen.add(x))]
    
    if matching_skills:
        skills_text = ", ".join(escape_latex(s) for s in matching_skills[:4])
    else:
        # Fallback: prendre les premiers items des catégories les plus pertinentes
        top_items = []
        for skill in adapted["skills"][:3]:
            top_items.extend(skill.get("items", [])[:2])
        skills_text = ", ".join(escape_latex(s) for s in top_items[:4])
    
    # Qualités
    if qualites:
        qualites_text = ", ".join(qualites[:3]).lower()
    else:
        qualites_text = t['qualites_default']

    para_nous = f"""{t['joining_team']} {escape_latex(job_title)} {t['represents_opportunity']} (\\textbf{{{skills_text}}}) {t['at_service']}{qualites_text} {t['will_be_assets']}"""
    
    # ============================================
    # 5. FORMULE DE POLITESSE
    # ============================================
    if tone == "formal":
        formule = t['formule_formal']
    elif tone == "casual":
        formule = t['formule_casual']
    else:
        formule = t['formule_default']
    
    # ============================================
    # UTILISER CONTENU ÉDITÉ OU MISTRAL SI DISPONIBLE
    # ============================================
    # Priorité 1: Contenu édité par l'utilisateur
    edited_content = adapted.get("cover_letter")
    if edited_content:
        accroche = edited_content.get("accroche", accroche)
        para_entreprise = edited_content.get("entreprise", para_entreprise)
        para_moi = edited_content.get("moi", para_moi)
        para_nous = edited_content.get("nous", para_nous)
        formule = edited_content.get("conclusion", formule)
    # Priorité 2: Contenu généré par Mistral
    elif mistral_content:
        accroche = mistral_content.get("accroche", accroche)
        para_entreprise = mistral_content.get("entreprise", para_entreprise)
        para_moi = mistral_content.get("moi", para_moi)
        para_nous = mistral_content.get("nous", para_nous)
        formule = mistral_content.get("conclusion", formule)
    
    # ============================================
    # COULEURS DE L'ENTREPRISE
    # ============================================
    colors = adapted.get('colors', {})
    primary_color = colors.get('primary', (30, 60, 114))
    secondary_color = colors.get('secondary', (212, 175, 55))
    primary_rgb = rgb_to_latex(primary_color)
    secondary_rgb = rgb_to_latex(secondary_color)
    
    # Logo de l'entreprise
    logo_url = adapted.get('logo_url', '')
    logo_path = ""
    if logo_url:
        try:
            # Télécharger le logo
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(logo_url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Sauvegarder le logo dans le dossier de sortie
            logo_ext = "png"
            content_type = response.headers.get('Content-Type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                logo_ext = "jpg"
            
            logo_file = output_path.parent / f"logo.{logo_ext}"
            with open(logo_file, "wb") as f:
                f.write(response.content)
            logo_path = str(logo_file)
            print(f"🖼️  Logo téléchargé: {logo_file.name}")
        except Exception as e:
            print(f"⚠️  Impossible de télécharger le logo: {e}")
    
    # Inclure le logo dans le template si disponible
    logo_line = ""
    if logo_path:
        logo_path_escaped = logo_path.replace("\\", "/")
        logo_line = f"\\includegraphics[height=1.2cm]{{{logo_path_escaped}}}\\\\[0.3cm]"
    
    # Signature
    signature_file = Path(__file__).parent / "sign.png"
    signature_path = str(signature_file).replace("\\", "/") if signature_file.exists() else ""
    
    # ============================================
    # TEMPLATE LATEX PROFESSIONNEL
    # ============================================
    cover_content = f"""\\documentclass[11pt,a4paper]{{article}}

\\usepackage[{t['babel']}]{{babel}}
\\usepackage[T1]{{fontenc}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[sfdefault]{{roboto}}
\\renewcommand{{\\familydefault}}{{\\sfdefault}}

\\usepackage{{geometry}}
\\usepackage{{parskip}}
\\usepackage{{microtype}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{xcolor}}
\\usepackage{{tikz}}
\\usepackage{{fontawesome5}}
\\usepackage{{graphicx}}

\\geometry{{top=2cm,bottom=2cm,left=2.5cm,right=2cm}}
\\pagestyle{{empty}}

% Couleurs
\\definecolor{{mainblue}}{{RGB}}{{{primary_rgb}}}
\\definecolor{{accentgold}}{{RGB}}{{{secondary_rgb}}}
\\definecolor{{textgray}}{{RGB}}{{80, 80, 80}}

\\begin{{document}}

% Barre latérale gauche
\\begin{{tikzpicture}}[remember picture, overlay]
    \\fill[mainblue] (current page.north west) rectangle ([xshift=0.5cm]current page.south west);
    \\fill[accentgold] ([yshift=-3cm]current page.north west) rectangle ([xshift=0.5cm, yshift=-3.3cm]current page.north west);
\\end{{tikzpicture}}

% En-tête expéditeur
\\noindent
\\begin{{minipage}}[t]{{0.5\\textwidth}}
\\textbf{{{name}}}\\\\
{escape_latex(personal_location)}\\\\
{escape_latex(phone)}\\\\
{escape_latex(email)}
\\end{{minipage}}%
\\hfill
\\begin{{minipage}}[t]{{0.45\\textwidth}}
\\raggedleft
{logo_line}
\\textbf{{{escape_latex(company)}}}\\\\
{t['recruitment']}\\\\
\\textit{{{t['made_at']} {escape_latex(job_location)}, {t['on_date']} \\today}}
\\end{{minipage}}

\\vspace{{1.5cm}}

% Objet
\\noindent\\textcolor{{mainblue}}{{\\textbf{{{t['subject']}}}}} {t['application_for']} {escape_latex(job_title)}

\\vspace{{0.8cm}}

% Salutation
\\noindent {t['greeting']}

\\vspace{{0.5cm}}

% ACCROCHE
\\noindent {escape_latex(accroche)} {t['today_intro']} \\textbf{{{escape_latex(company)}}} {t['as_position']} \\textbf{{{escape_latex(job_title)}}}.

\\vspace{{0.4cm}}

% PARAGRAPHE ENTREPRISE
\\noindent {para_entreprise}

\\vspace{{0.4cm}}

% PARAGRAPHE MOI
\\noindent {para_moi}

\\vspace{{0.4cm}}

% PARAGRAPHE NOUS
\\noindent {para_nous}

\\vspace{{0.4cm}}

% FORMULE DE POLITESSE
\\noindent {formule}

\\vspace{{0.5cm}}

% Signature
\\hfill \\begin{{minipage}}{{5cm}}
\\centering
\\includegraphics[height=2cm]{{{signature_path}}}\\\\
\\textbf{{{name}}}
\\end{{minipage}}

\\end{{document}}
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cover_content)
    
    print(f"✅ Lettre de motivation générée: {output_path}")


def compile_latex(tex_path: Path) -> bool:
    """Compile un fichier LaTeX en PDF avec tectonic ou pdflatex"""
    # Essayer d'abord tectonic, puis pdflatex
    compilers = [
        (["tectonic", "-o", str(tex_path.parent), str(tex_path)], "tectonic"),
        (["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tex_path.parent), str(tex_path)], "pdflatex")
    ]
    
    for cmd, name in compilers:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                pdf_path = tex_path.with_suffix(".pdf")
                print(f"📄 PDF compilé: {pdf_path}")
                return True
            else:
                # Si le compilateur existe mais échoue, afficher l'erreur
                if "not found" not in result.stderr.lower():
                    print(f"⚠️  Erreur de compilation avec {name}: {tex_path.name}")
                    # Afficher les dernières lignes d'erreur
                    error_lines = [l for l in result.stdout.split('\n') if 'error' in l.lower() or '!' in l]
                    if error_lines:
                        print(f"   {error_lines[0][:100]}")
                    continue
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout lors de la compilation avec {name}")
            continue
    
    print("⚠️  Aucun compilateur LaTeX trouvé. Installez tectonic ou texlive-latex-base.")
    return False


def format_filename(name: str, company: str) -> tuple:
    """Génère les noms de fichiers professionnels pour CV et lettre de motivation
    
    Format: CV_Prenom_Nom_Entreprise.pdf / LM_Prenom_Nom_Entreprise.pdf
    """
    import unicodedata
    import re
    
    def normalize(text: str) -> str:
        # Supprimer les accents
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        # Garder seulement les caractères alphanumériques et espaces
        text = re.sub(r'[^\w\s]', '', text)
        # Remplacer les espaces par des underscores
        text = text.replace(' ', '_')
        return text
    
    name_normalized = normalize(name)
    company_normalized = normalize(company)
    
    cv_name = f"CV_{name_normalized}_{company_normalized}"
    cover_name = f"LM_{name_normalized}_{company_normalized}"
    
    return cv_name, cover_name


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Génère un CV et une lettre de motivation adaptés à une offre d'emploi"
    )
    parser.add_argument("url", help="URL de l'offre d'emploi")
    parser.add_argument("--output", "-o", help="Dossier de sortie", default=None)
    parser.add_argument("--no-compile", action="store_true", help="Ne pas compiler en PDF (compilation automatique par défaut)")
    parser.add_argument("--cv-only", action="store_true", help="Générer uniquement le CV")
    parser.add_argument("--cover-only", action="store_true", help="Générer uniquement la lettre")
    
    args = parser.parse_args()
    
    # Créer le dossier de sortie
    if args.output:
        output_dir = Path(args.output)
    else:
        # Créer un dossier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = OUTPUT_DIR / timestamp
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Récupération de l'offre: {args.url}")
    job_data = fetch_job_offer(args.url)
    
    print(f"📋 Titre: {job_data['title'] or 'Non détecté'}")
    print(f"🏢 Entreprise: {job_data['company'] or 'Non détectée'}")
    print(f"🔑 Mots-clés détectés: {', '.join(job_data['keywords'][:10])}")
    
    print(f"\n📂 Chargement du profil...")
    profile = load_profile()
    
    # Traduire le profil en anglais si l'offre est en anglais
    if job_data.get("language") == "en":
        print("🌐 Traduction du profil en anglais...")
        profile = translate_profile_to_english(profile)
    
    print(f"🔄 Adaptation du profil...")
    adapted = adapt_profile(profile, job_data)
    
    # Sauvegarder les données de l'offre
    with open(output_dir / "job_data.json", "w", encoding="utf-8") as f:
        json.dump(job_data, f, ensure_ascii=False, indent=2)
    
    # Nommage professionnel des fichiers
    name = profile["personal"]["name"]
    company = job_data.get("company") or "Entreprise"
    cv_filename, cover_filename = format_filename(name, company)
    
    # Générer les documents
    if not args.cover_only:
        cv_path = output_dir / f"{cv_filename}.tex"
        generate_cv(adapted, cv_path)
        if not args.no_compile:
            compile_latex(cv_path)
            print(f"   📄 {cv_filename}.pdf")
    
    if not args.cv_only:
        cover_path = output_dir / f"{cover_filename}.tex"
        generate_cover_letter(adapted, cover_path, profile=profile)
        if not args.no_compile:
            compile_latex(cover_path)
            print(f"   📄 {cover_filename}.pdf")
    
    print(f"\n✨ Terminé! Fichiers dans: {output_dir}")
    
    # Ouvrir le dossier de sortie
    if not args.no_compile:
        import subprocess
        try:
            subprocess.run(["xdg-open", str(output_dir)], check=False, capture_output=True)
        except:
            pass


if __name__ == "__main__":
    main()
