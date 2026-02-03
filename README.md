# CV & Cover Letter Generator

Système d'adaptation automatique de CV et lettre de motivation basé sur l'analyse d'offres d'emploi.

## 📦 Installation

```bash
pip install requests beautifulsoup4
```

## 🚀 Utilisation

### Générer CV + Lettre adaptés à une offre

```bash
python generate.py "https://www.welcometothejungle.com/fr/companies/xxx/jobs/yyy"
```

### Options

| Option | Description |
|--------|-------------|
| `--output, -o` | Dossier de sortie personnalisé |
| `--compile, -c` | Compiler automatiquement en PDF |
| `--cv-only` | Générer uniquement le CV |
| `--cover-only` | Générer uniquement la lettre |

### Exemples

```bash
# Avec compilation PDF
python generate.py "https://example.com/job" --compile

# Sortie dans un dossier spécifique
python generate.py "https://example.com/job" -o ./candidature_sopra

# CV uniquement
python generate.py "https://example.com/job" --cv-only
```

## 📁 Structure

```
cvtex/
├── generate.py          # Script principal
├── profile.json         # Ton profil (expériences, compétences, etc.)
├── cv.tex              # CV actuel
├── cover.tex           # Lettre actuelle
└── output/             # Dossiers de sortie générés
    └── 20260203_143022/
        ├── cv.tex
        ├── cv.pdf
        ├── cover.tex
        ├── cover.pdf
        └── job_data.json
```

## ✏️ Personnalisation

### Modifier ton profil

Édite `profile.json` pour :
- Ajouter/modifier des expériences
- Mettre à jour tes compétences
- Ajouter des certifications
- Modifier les templates de résumé

### Mots-clés

Le système analyse l'offre et détecte automatiquement les mots-clés techniques pour :
- Réorganiser les expériences par pertinence
- Sélectionner les compétences les plus adaptées
- Choisir le bon template de résumé
- Filtrer les certifications pertinentes

## 🎯 Sites supportés

Le scraper fonctionne avec la plupart des sites d'emploi :
- Welcome to the Jungle
- LinkedIn
- Indeed
- Glassdoor
- Sites carrières d'entreprises
