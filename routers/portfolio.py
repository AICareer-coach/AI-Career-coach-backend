import uuid
import os
from fastapi import APIRouter, File, UploadFile, Request, Depends, HTTPException, Body
from core.ai_core import extract_text_auto, get_resume_structure
from core.portfolio_core import generate_portfolio_website
from dependencies import get_current_user

router = APIRouter()

@router.post("/generate-direct")
async def generate_direct(
    request: Request, 
    file: UploadFile = File(...), 
    template_id: str = "modern.html", # Added this parameter
    user: dict = Depends(get_current_user)
):
    # 1. Extract File
    file_bytes = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    
    # 2. Extract Data using your EXISTING ai_core function
    try:
        raw_text = extract_text_auto(file_bytes, ext)
        structured_data = get_resume_structure(raw_text)

        # If AI fails to produce structured data, create a safe fallback so we can still generate a portfolio.
        if not structured_data:
            print("⚠️ Warning: AI returned empty data — using fallback structured_data.")
            # Minimal fallback: put raw_text into summary and provide empty lists for sections
            fallback_summary = (raw_text or "").strip()[:800]
            structured_data = {
                "personal_info": {"name": "Candidate", "email": "", "phone": ""},
                "summary": fallback_summary or "",
                "work_experience": [],
                "internships": [],
                "projects": [],
                "education": []
            }

    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze resume structure.")

    # 3. Generate HTML with Template
    html_code = generate_portfolio_website(structured_data, template_id)
    
    if not html_code:
        raise HTTPException(status_code=500, detail="Could not generate portfolio HTML.")

    # 4. Save to Disk
    unique_id = uuid.uuid4().hex[:8]
    filename = f"portfolio_{unique_id}.html"
    os.makedirs("generated_portfolios", exist_ok=True)
    
    save_path = os.path.join("generated_portfolios", filename)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html_code)

    # 5. Return URL
    base_url = str(request.base_url).rstrip("/")
    return {"url": f"{base_url}/generated_portfolios/{filename}", "html": html_code}


@router.post("/save-edited")
async def save_edited(request: Request, payload: dict = Body(...), user: dict = Depends(get_current_user)):
    """Save edited HTML posted from the frontend editor and return a hosted URL."""
    html = payload.get("html") if isinstance(payload, dict) else None
    if not html or not isinstance(html, str):
        raise HTTPException(status_code=400, detail="Missing 'html' in request body")

    unique_id = uuid.uuid4().hex[:8]
    filename = f"portfolio_edited_{unique_id}.html"
    os.makedirs("generated_portfolios", exist_ok=True)
    save_path = os.path.join("generated_portfolios", filename)
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print("Failed to save edited HTML:", e)
        raise HTTPException(status_code=500, detail="Failed to save edited portfolio")

    base_url = str(request.base_url).rstrip("/")
    return {"url": f"{base_url}/generated_portfolios/{filename}", "html": html}