from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
import os
import json
import uuid
import tempfile
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import functions from generate.py
from generate import (
    fetch_job_offer,
    adapt_profile,
    generate_cv,
    generate_cover_letter,
    compile_latex,
    translate_profile_to_english,
    load_profile as load_profile_from_file,
    generate_cover_with_mistral
)

# Supabase setup
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == "your_supabase_project_url":
    print("⚠️  Supabase non configuré - Mode fichiers locaux activé")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connecté")

app = FastAPI(title="CVTeX API", version="2.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "https://cvtex.vercel.app",
        "https://cvtex-jjrs-projects-0dc738ef.vercel.app",
        "https://cvtex-git-main-jjrs-projects-0dc738ef.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local fallback storage
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
APPLICATIONS_FILE = DATA_DIR / "applications.json"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============= Storage Functions =============

def load_applications_local():
    if APPLICATIONS_FILE.exists():
        with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_applications_local(applications):
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(applications, f, ensure_ascii=False, indent=2)

def get_applications():
    """Get all applications from Supabase or local file"""
    if supabase:
        result = supabase.table("applications").select("*").order("created_at", desc=True).execute()
        return result.data
    return load_applications_local()

def save_application(application: dict):
    """Save an application to Supabase or local file"""
    if supabase:
        # Map camelCase to snake_case for Supabase
        db_record = {
            "id": application["id"],
            "company": application["company"],
            "position": application["position"],
            "location": application.get("location"),
            "salary": application.get("salary"),
            "contract_type": application.get("type"),
            "status": application.get("status", "submitted"),
            "match_score": application.get("matchScore"),
            "description": application.get("description"),
            "url": application.get("url"),
            "cv_path": application.get("cvPath"),
            "cover_path": application.get("coverPath"),
            "logo_url": application.get("logoUrl"),
            "language": application.get("language", "fr"),
            "cv_data": application.get("cvData"),
            "cover_data": application.get("coverData")
        }
        supabase.table("applications").insert(db_record).execute()
    else:
        applications = load_applications_local()
        applications.insert(0, application)
        save_applications_local(applications)

def update_application(app_id: str, updates: dict):
    """Update an existing application"""
    if supabase:
        supabase.table("applications").update(updates).eq("id", app_id).execute()
    else:
        applications = load_applications_local()
        for app in applications:
            if app["id"] == app_id:
                app.update(updates)
                break
        save_applications_local(applications)

def get_application_by_id(app_id: str) -> dict:
    """Get a single application by ID"""
    if supabase:
        result = supabase.table("applications").select("*").eq("id", app_id).execute()
        if result.data:
            return result.data[0]
        return None
    else:
        applications = load_applications_local()
        for app in applications:
            if app["id"] == app_id:
                return app
        return None

def save_temp_analysis(temp_data: dict):
    """Save temporary analysis data"""
    if supabase:
        db_record = {
            "id": temp_data["id"],
            "url": temp_data["url"],
            "job_data": temp_data["job_data"],
            "language": temp_data.get("language"),
            "logo_url": temp_data.get("logo_url"),
            "primary_color": temp_data.get("primary_color"),
            "match_score": temp_data.get("match_score")
        }
        supabase.table("temp_analysis").insert(db_record).execute()
    else:
        temp_file = DATA_DIR / f"temp_{temp_data['id']}.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(temp_data, f, ensure_ascii=False, indent=2)

def get_temp_analysis(app_id: str) -> dict:
    """Get temporary analysis data"""
    if supabase:
        result = supabase.table("temp_analysis").select("*").eq("id", app_id).execute()
        if result.data:
            return result.data[0]
        return None
    else:
        temp_file = DATA_DIR / f"temp_{app_id}.json"
        if temp_file.exists():
            with open(temp_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

def delete_temp_analysis(app_id: str):
    """Delete temporary analysis data"""
    if supabase:
        supabase.table("temp_analysis").delete().eq("id", app_id).execute()
    else:
        temp_file = DATA_DIR / f"temp_{app_id}.json"
        if temp_file.exists():
            temp_file.unlink()

def upload_pdf(file_path: Path, storage_name: str) -> str:
    """Upload PDF to Supabase Storage and return public URL"""
    if supabase:
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Upload to Supabase Storage
        result = supabase.storage.from_("documents").upload(
            storage_name,
            pdf_content,
            {"content-type": "application/pdf"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_("documents").get_public_url(storage_name)
        return public_url
    else:
        # Local: copy to output dir and return local path
        import shutil
        dest = OUTPUT_DIR / storage_name
        shutil.copy(file_path, dest)
        return f"/api/download/{storage_name}"

def get_pdf_content(storage_name: str) -> bytes:
    """Get PDF content from Supabase Storage or local file"""
    if supabase:
        result = supabase.storage.from_("documents").download(storage_name)
        return result
    else:
        file_path = OUTPUT_DIR / storage_name
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
        return None

# ============= API Models =============

class JobUrlRequest(BaseModel):
    url: str

class GenerateRequest(BaseModel):
    id: str

class StatusUpdateRequest(BaseModel):
    status: str

class CoverLetterData(BaseModel):
    accroche: str
    entreprise: str
    moi: str
    nous: str
    conclusion: str

class SkillItem(BaseModel):
    label: str
    items: List[str]

class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: str

class CVData(BaseModel):
    summary: str
    display_title: str
    skills: List[SkillItem]
    projects: List[ProjectItem]

class FinalizeRequest(BaseModel):
    id: str
    cv: CVData
    coverLetter: CoverLetterData

# ============= API Endpoints =============

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "storage": "supabase" if supabase else "local",
        "version": "2.0.0"
    }

@app.get("/api/applications")
def list_applications():
    """Get all applications"""
    apps = get_applications()
    
    # Convert snake_case to camelCase for frontend compatibility
    # Also convert storage URLs to backend download URLs for reliable access
    def get_download_path(path):
        """Extract filename from storage URL or return as-is"""
        if path and 'supabase.co' in path:
            # Extract just the filename from the full URL
            filename = path.split('/')[-1]
            return f"/api/download/{filename}"
        return path
    
    if supabase:
        return [{
            "id": app["id"],
            "company": app["company"],
            "position": app["position"],
            "location": app.get("location"),
            "salary": app.get("salary"),
            "type": app.get("contract_type"),
            "status": app.get("status", "submitted"),
            "appliedDate": app.get("created_at", "")[:10] if app.get("created_at") else "",
            "matchScore": app.get("match_score"),
            "description": app.get("description"),
            "url": app.get("url"),
            "cvPath": get_download_path(app.get("cv_path")),
            "coverPath": get_download_path(app.get("cover_path")),
            "logoUrl": app.get("logo_url"),
            "language": app.get("language", "fr")
        } for app in apps]
    
    return apps

@app.post("/api/analyze")
def analyze_job(request: JobUrlRequest):
    """Analyze a job offer URL"""
    try:
        # Fetch the job offer using generate.py function
        job_data = fetch_job_offer(request.url)
        
        if not job_data or not job_data.get('title'):
            raise HTTPException(status_code=400, detail="Could not scrape job offer")
        
        # Language is already detected by fetch_job_offer
        language = job_data.get('language', 'fr')
        
        # Logo URL is extracted by fetch_job_offer
        logo_url = job_data.get('logo_url')
        primary_color = job_data.get('primary_color', '#10b981')
        
        # Calculate match score
        profile = load_profile_from_file()
        description = job_data.get('description', '').lower()
        skills = profile.get('skills', [])
        matched = sum(1 for skill in skills if skill.lower() in description)
        match_score = min(95, 60 + (matched * 5))
        
        # Generate unique ID for this application
        app_id = str(uuid.uuid4())[:8]
        
        # Store temporary data for generation
        temp_data = {
            "id": app_id,
            "url": request.url,
            "job_data": job_data,
            "language": language,
            "logo_url": logo_url,
            "primary_color": primary_color,
            "match_score": match_score,
            "created_at": datetime.now().isoformat()
        }
        
        save_temp_analysis(temp_data)
        
        return {
            "id": app_id,
            "title": job_data.get('title', 'Unknown Position'),
            "company": job_data.get('company', 'Unknown Company'),
            "location": job_data.get('location', 'Remote'),
            "type": job_data.get('contract_type', 'Full-time'),
            "salary": job_data.get('salary', 'Non spécifié'),
            "description": job_data.get('description', '')[:300] + '...' if job_data.get('description') else '',
            "language": "Français" if language == "fr" else "English",
            "matchScore": match_score,
            "logoUrl": logo_url,
            "primaryColor": primary_color
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preview")
def preview_documents(request: GenerateRequest):
    """Generate preview data for editing before final generation"""
    try:
        # Load temp data
        temp_data = get_temp_analysis(request.id)
        if not temp_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        job_data = temp_data['job_data']
        language = job_data.get('language', 'fr')
        
        # Load profile
        profile = load_profile_from_file()
        
        # Translate profile if English
        if language == "en":
            profile = translate_profile_to_english(profile)
        
        # Adapt profile to job
        adapted = adapt_profile(profile, job_data)
        
        # Generate cover letter content with Mistral
        cover_letter = generate_cover_with_mistral(profile, job_data, adapted.get("job_context", {}))
        
        # If Mistral failed, create default structure
        if not cover_letter:
            company = job_data.get("company", "l'entreprise")
            position = job_data.get("title", "le poste")
            cover_letter = {
                "accroche": f"Fort de mon expérience en data engineering et développement, je suis particulièrement intéressé par le poste de {position} chez {company}.",
                "entreprise": f"{company} est reconnue pour son expertise et son innovation. Votre vision et vos projets correspondent parfaitement à mes aspirations professionnelles.",
                "moi": "Mon parcours m'a permis de développer des compétences solides en conception de pipelines de données, orchestration et déploiement cloud. J'ai notamment travaillé sur des projets d'envergure impliquant le traitement de données massives.",
                "nous": "Ensemble, nous pourrions relever les défis de modernisation de vos infrastructures data et contribuer à la création de valeur à partir de vos données.",
                "conclusion": "Je serais ravi d'échanger avec vous lors d'un entretien pour discuter de cette opportunité. Dans l'attente de votre retour, je vous prie d'agréer mes salutations distinguées."
            }
        
        # Extract editable CV data
        cv_data = {
            "summary": adapted.get("summary", ""),
            "display_title": adapted.get("display_title", ""),
            "skills": [
                {
                    "label": skill.get("label", ""),
                    "items": skill.get("items", [])[:8]
                }
                for skill in adapted.get("skills", [])[:6]
            ],
            "projects": [
                {
                    "name": "DataFlow Pipeline",
                    "description": "Pipeline de données temps réel avec Apache Kafka et Spark pour le traitement de millions d'événements par jour",
                    "technologies": "Python, Kafka, Spark, Docker, AWS"
                },
                {
                    "name": "ML Model Serving Platform",
                    "description": "Plateforme de déploiement de modèles ML avec API REST, monitoring et auto-scaling",
                    "technologies": "FastAPI, MLflow, Kubernetes, PostgreSQL"
                }
            ]
        }
        
        return {
            "id": request.id,
            "cv": cv_data,
            "coverLetter": cover_letter,
            "jobInfo": {
                "title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", ""),
                "language": language
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
def generate_documents(request: GenerateRequest):
    """Generate CV and cover letter"""
    try:
        # Load temp data
        temp_data = get_temp_analysis(request.id)
        if not temp_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        job_data = temp_data['job_data']
        language = job_data.get('language', 'fr')
        logo_url = temp_data.get('logo_url')
        
        # Load profile
        profile = load_profile_from_file()
        
        # Translate profile if English
        if language == "en":
            profile = translate_profile_to_english(profile)
        
        # Adapt profile to job (signature: profile, job_data)
        adapted = adapt_profile(profile, job_data)
        
        # Use temp directory for serverless compatibility
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate CV - writes to file
            cv_filename = f"cv_{request.id}.pdf"
            cv_tex_path = tmp_path / f"cv_{request.id}.tex"
            generate_cv(adapted, cv_tex_path)
            
            # Compile CV to PDF
            compile_latex(cv_tex_path)
            cv_pdf_path = tmp_path / cv_filename
            
            # Generate cover letter - writes to file
            cover_filename = f"cover_{request.id}.pdf"
            cover_tex_path = tmp_path / f"cover_{request.id}.tex"
            generate_cover_letter(adapted, cover_tex_path, profile=profile)
            
            # Compile cover letter to PDF
            compile_latex(cover_tex_path)
            cover_pdf_path = tmp_path / cover_filename
            
            # Upload PDFs to storage
            cv_url = upload_pdf(cv_pdf_path, cv_filename)
            cover_url = upload_pdf(cover_pdf_path, cover_filename)
        
        # Create application record
        company_name = job_data.get('company', 'Unknown')
        application = {
            "id": request.id,
            "company": company_name,
            "position": job_data.get('title', 'Unknown Position'),
            "location": job_data.get('location', 'Remote'),
            "salary": job_data.get('salary', 'Non spécifié'),
            "type": job_data.get('contract_type', 'Full-time'),
            "status": "submitted",
            "appliedDate": datetime.now().strftime("%d %b %Y"),
            "matchScore": temp_data['match_score'],
            "description": job_data.get('description', '')[:300] if job_data.get('description') else '',
            "url": temp_data['url'],
            "cvPath": cv_url if supabase else cv_filename,
            "coverPath": cover_url if supabase else cover_filename,
            "logoUrl": logo_url,
            "language": language
        }
        
        # Save application
        save_application(application)
        
        # Clean temp analysis data
        delete_temp_analysis(request.id)
        
        # Return paths via backend download endpoint (not direct Supabase URLs)
        cv_download_path = f"/api/download/{cv_filename}"
        cover_download_path = f"/api/download/{cover_filename}"
        
        return {
            "success": True,
            "cvPath": cv_download_path,
            "coverPath": cover_download_path,
            "application": application
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/finalize")
def finalize_documents(request: FinalizeRequest):
    """Generate final PDFs with edited content"""
    try:
        # Load temp data
        temp_data = get_temp_analysis(request.id)
        if not temp_data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        job_data = temp_data['job_data']
        language = job_data.get('language', 'fr')
        logo_url = temp_data.get('logo_url')
        
        # Load profile
        profile = load_profile_from_file()
        
        # Translate profile if English
        if language == "en":
            profile = translate_profile_to_english(profile)
        
        # Adapt profile to job
        adapted = adapt_profile(profile, job_data)
        
        # Apply user edits to CV
        adapted["summary"] = request.cv.summary
        adapted["display_title"] = request.cv.display_title
        
        # Apply user edits to skills
        adapted["skills"] = [
            {"label": skill.label, "items": skill.items}
            for skill in request.cv.skills
        ]
        
        # Apply user edits to projects
        adapted["projects"] = [
            {"name": proj.name, "description": proj.description, "technologies": proj.technologies}
            for proj in request.cv.projects
        ]
        
        # Apply user edits to cover letter
        cover_letter_content = {
            "accroche": request.coverLetter.accroche,
            "entreprise": request.coverLetter.entreprise,
            "moi": request.coverLetter.moi,
            "nous": request.coverLetter.nous,
            "conclusion": request.coverLetter.conclusion
        }
        adapted["cover_letter"] = cover_letter_content
        
        # Use temp directory for serverless compatibility
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate CV - writes to file
            cv_filename = f"cv_{request.id}.pdf"
            cv_tex_path = tmp_path / f"cv_{request.id}.tex"
            generate_cv(adapted, cv_tex_path)
            
            # Compile CV to PDF
            compile_latex(cv_tex_path)
            cv_pdf_path = tmp_path / cv_filename
            
            # Generate cover letter with edited content
            cover_filename = f"cover_{request.id}.pdf"
            cover_tex_path = tmp_path / f"cover_{request.id}.tex"
            generate_cover_letter(adapted, cover_tex_path, profile=profile)
            
            # Compile cover letter to PDF
            compile_latex(cover_tex_path)
            cover_pdf_path = tmp_path / cover_filename
            
            # Upload PDFs to storage
            cv_url = upload_pdf(cv_pdf_path, cv_filename)
            cover_url = upload_pdf(cover_pdf_path, cover_filename)
        
        # Store CV and cover letter data for future editing
        cv_data_to_store = {
            "summary": request.cv.summary,
            "display_title": request.cv.display_title,
            "skills": [{"label": s.label, "items": s.items} for s in request.cv.skills],
            "projects": [{"name": p.name, "description": p.description, "technologies": p.technologies} for p in request.cv.projects]
        }
        cover_data_to_store = {
            "accroche": request.coverLetter.accroche,
            "entreprise": request.coverLetter.entreprise,
            "moi": request.coverLetter.moi,
            "nous": request.coverLetter.nous,
            "conclusion": request.coverLetter.conclusion
        }
        
        # Create application record with editable data
        company_name = job_data.get('company', 'Unknown')
        application = {
            "id": request.id,
            "company": company_name,
            "position": job_data.get('title', 'Unknown Position'),
            "location": job_data.get('location', 'Remote'),
            "salary": job_data.get('salary', 'Non spécifié'),
            "type": job_data.get('contract_type', 'Full-time'),
            "status": "submitted",
            "appliedDate": datetime.now().strftime("%d %b %Y"),
            "matchScore": temp_data['match_score'],
            "description": job_data.get('description', '')[:300] if job_data.get('description') else '',
            "url": temp_data['url'],
            "cvPath": cv_url if supabase else cv_filename,
            "coverPath": cover_url if supabase else cover_filename,
            "logoUrl": logo_url,
            "language": language,
            "cvData": cv_data_to_store,
            "coverData": cover_data_to_store
        }
        
        # Save application
        save_application(application)
        
        # Clean temp analysis data
        delete_temp_analysis(request.id)
        
        # Return paths via backend download endpoint
        cv_download_path = f"/api/download/{cv_filename}"
        cover_download_path = f"/api/download/{cover_filename}"
        
        return {
            "success": True,
            "cvPath": cv_download_path,
            "coverPath": cover_download_path,
            "application": application
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
def download_file(filename: str):
    """Download a generated PDF"""
    content = get_pdf_content(filename)
    if not content:
        raise HTTPException(status_code=404, detail="File not found")
    
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.delete("/api/applications/{app_id}")
def delete_application(app_id: str):
    """Delete an application"""
    if supabase:
        # Delete from Supabase
        supabase.table("applications").delete().eq("id", app_id).execute()
        
        # Also delete associated PDFs from storage
        try:
            supabase.storage.from_("documents").remove([f"cv_{app_id}.pdf", f"cover_{app_id}.pdf"])
        except:
            pass
    else:
        applications = load_applications_local()
        applications = [a for a in applications if a['id'] != app_id]
        save_applications_local(applications)
    
    return {"success": True}

@app.patch("/api/applications/{app_id}/status")
def update_application_status(app_id: str, body: StatusUpdateRequest):
    """Update application status"""
    if supabase:
        supabase.table("applications").update({"status": body.status}).eq("id", app_id).execute()
    else:
        applications = load_applications_local()
        for app in applications:
            if app['id'] == app_id:
                app['status'] = body.status
                break
        save_applications_local(applications)
    
    return {"success": True}

@app.get("/api/applications/{app_id}/edit")
def get_application_for_edit(app_id: str):
    """Get application data for editing"""
    app = get_application_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get stored CV and cover letter data
    cv_data = app.get("cv_data") or app.get("cvData")
    cover_data = app.get("cover_data") or app.get("coverData")
    
    # If no stored data, create defaults from profile
    if not cv_data:
        profile = load_profile_from_file()
        language = app.get("language", "fr")
        if language == "en":
            profile = translate_profile_to_english(profile)
        
        cv_data = {
            "summary": profile.get("summary", ""),
            "display_title": app.get("position", ""),
            "skills": profile.get("skills", []),
            "projects": [
                {
                    "name": "DataFlow Pipeline",
                    "description": "Pipeline de données temps réel avec Apache Kafka et Spark",
                    "technologies": "Python, Kafka, Spark, Docker, AWS"
                },
                {
                    "name": "ML Model Serving Platform",
                    "description": "Plateforme de déploiement de modèles ML avec API REST",
                    "technologies": "FastAPI, MLflow, Kubernetes, PostgreSQL"
                }
            ]
        }
    
    if not cover_data:
        company = app.get("company", "l'entreprise")
        position = app.get("position", "le poste")
        cover_data = {
            "accroche": f"Fort de mon expérience, je suis particulièrement intéressé par le poste de {position} chez {company}.",
            "entreprise": f"{company} est reconnue pour son expertise et son innovation.",
            "moi": "Mon parcours m'a permis de développer des compétences solides en conception et développement.",
            "nous": "Ensemble, nous pourrions relever les défis techniques et contribuer à la création de valeur.",
            "conclusion": "Je serais ravi d'échanger avec vous lors d'un entretien. Dans l'attente de votre retour, je vous prie d'agréer mes salutations distinguées."
        }
    
    return {
        "id": app_id,
        "cv": cv_data,
        "coverLetter": cover_data,
        "jobInfo": {
            "title": app.get("position", ""),
            "company": app.get("company", ""),
            "location": app.get("location", ""),
            "language": app.get("language", "fr")
        }
    }

@app.post("/api/applications/{app_id}/regenerate")
def regenerate_documents(app_id: str, request: FinalizeRequest):
    """Regenerate documents for an existing application"""
    try:
        app = get_application_by_id(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        
        language = app.get("language", "fr")
        
        # Load profile
        profile = load_profile_from_file()
        
        # Translate profile if English
        if language == "en":
            profile = translate_profile_to_english(profile)
        
        # Create adapted data from request
        adapted = {
            "personal": profile.get("personal", {}),
            "summary": request.cv.summary,
            "display_title": request.cv.display_title,
            "experiences": profile.get("experiences", []),
            "education": profile.get("education", []),
            "skills": [{"label": s.label, "items": s.items} for s in request.cv.skills],
            "projects": [{"name": p.name, "description": p.description, "technologies": p.technologies} for p in request.cv.projects],
            "certifications": profile.get("certifications", []),
            "languages": profile.get("languages", []),
            "interests": profile.get("interests", []),
            "language": language,
            "cover_letter": {
                "accroche": request.coverLetter.accroche,
                "entreprise": request.coverLetter.entreprise,
                "moi": request.coverLetter.moi,
                "nous": request.coverLetter.nous,
                "conclusion": request.coverLetter.conclusion
            }
        }
        
        # Select bullets for experiences (use first 4 bullets per experience)
        for exp in adapted["experiences"]:
            exp["selected_bullets"] = exp.get("bullets", [])[:4]
        
        # Use temp directory for serverless compatibility
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate CV
            cv_filename = f"cv_{app_id}.pdf"
            cv_tex_path = tmp_path / f"cv_{app_id}.tex"
            generate_cv(adapted, cv_tex_path)
            
            # Compile CV to PDF
            compile_latex(cv_tex_path)
            cv_pdf_path = tmp_path / cv_filename
            
            # Generate cover letter
            cover_filename = f"cover_{app_id}.pdf"
            cover_tex_path = tmp_path / f"cover_{app_id}.tex"
            generate_cover_letter(adapted, cover_tex_path, profile=profile)
            
            # Compile cover letter to PDF
            compile_latex(cover_tex_path)
            cover_pdf_path = tmp_path / cover_filename
            
            # Upload PDFs to storage (overwrite existing)
            cv_url = upload_pdf(cv_pdf_path, cv_filename)
            cover_url = upload_pdf(cover_pdf_path, cover_filename)
        
        # Store updated CV and cover letter data
        cv_data_to_store = {
            "summary": request.cv.summary,
            "display_title": request.cv.display_title,
            "skills": [{"label": s.label, "items": s.items} for s in request.cv.skills],
            "projects": [{"name": p.name, "description": p.description, "technologies": p.technologies} for p in request.cv.projects]
        }
        cover_data_to_store = {
            "accroche": request.coverLetter.accroche,
            "entreprise": request.coverLetter.entreprise,
            "moi": request.coverLetter.moi,
            "nous": request.coverLetter.nous,
            "conclusion": request.coverLetter.conclusion
        }
        
        # Update application in database
        update_data = {
            "cv_path": cv_url if supabase else cv_filename,
            "cover_path": cover_url if supabase else cover_filename,
            "cv_data": cv_data_to_store,
            "cover_data": cover_data_to_store
        }
        update_application(app_id, update_data)
        
        # Return paths via backend download endpoint
        cv_download_path = f"/api/download/{cv_filename}"
        cover_download_path = f"/api/download/{cover_filename}"
        
        return {
            "success": True,
            "cvPath": cv_download_path,
            "coverPath": cover_download_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
