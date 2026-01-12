import os
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "portfolios")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_portfolio_website(structured_data, template_name="modern.html"):
    try:
        # 1. CLEANING & MERGING DATA
        # Ensure we capture experience even if the AI uses different key names
        work = structured_data.get("work_experience", []) or structured_data.get("experience", [])
        interns = structured_data.get("internships", [])
        
        # Combine them into one unified list for the "Path" section
        combined_exp = []
        if isinstance(work, list): combined_exp.extend(work)
        if isinstance(interns, list): combined_exp.extend(interns)
        
        # Ensure description is always a list for bullet points
        for item in combined_exp:
            if isinstance(item.get("description"), str):
                item["description"] = [item["description"]]

        # Clean up projects too
        projects = structured_data.get("projects", [])
        for p in projects:
            if isinstance(p.get("description"), str):
                p["description"] = [p["description"]]

        # Final context for the template
        context = {
            **structured_data,
            "full_experience": combined_exp,
            "projects": projects
        }

        template = jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        print(f"❌ Rendering Error: {e}")
        return None