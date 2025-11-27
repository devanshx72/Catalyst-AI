import os
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlparse
from app.utils.db_utils import get_db

# Configuration
API_ENDPOINT = "https://gw.magicalapi.com/profile-data"
CACHE_HOURS = 24

def extract_username(url):
    """
    Extracts the username from a LinkedIn URL.
    e.g. https://www.linkedin.com/in/williamhgates/ -> williamhgates
    """
    try:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # Usually it's /in/username
        if 'in' in path_parts:
            idx = path_parts.index('in')
            if idx + 1 < len(path_parts):
                return path_parts[idx + 1]
        
        # Fallback: take the last part if 'in' isn't found
        return path_parts[-1] if path_parts else None
    except:
        return None

def format_duration(date_obj):
    """Formats the date object from API to a string."""
    if not date_obj: return ""
    start = date_obj.get("start_date", "")
    end = date_obj.get("end_date", "Present")
    return f"{start} - {end}"

def fetch_linkedin_profile_brightdata(linkedin_url: str, user_id: str, force_refresh: bool = False) -> dict:
    """
    Fetches LinkedIn profile data using Magical API.
    Function name kept for compatibility.
    """
    db = get_db()
    coll = db.linkedin_data

    # === 1. Check Cache ===
    cached = coll.find_one({"user_id": user_id})
    if cached and not force_refresh:
        last_updated = cached.get("last_updated")
        if last_updated:
            if isinstance(last_updated, str):
                try: last_updated = datetime.fromisoformat(last_updated)
                except: last_updated = datetime.utcnow()
            
            age_hours = (datetime.utcnow() - last_updated).total_seconds() / 3600
            if age_hours < CACHE_HOURS:
                print(f"[LinkedIn] CACHE HIT: Using cached data (age: {age_hours:.1f}h)")
                return {"status": "success", "message": "From cache"}

    # === 2. Setup API ===
    api_key = os.getenv("LINKEDIN_API_KEY")
    if not api_key:
        print("[LinkedIn] Error: LINKEDIN_API_KEY missing in .env")
        return {"status": "error", "message": "Server config error: Missing API Key"}

    username = extract_username(linkedin_url)
    if not username:
        return {"status": "error", "message": "Invalid LinkedIn URL"}

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    try:
        print(f"[LinkedIn] Requesting data for: {username}")
        
        # === 3. Send Initial Request ===
        init_payload = {"profile_name": username}
        response = requests.post(API_ENDPOINT, json=init_payload, headers=headers)
        resp_json = response.json()

        request_id = resp_json.get("data", {}).get("request_id")
        
        if not request_id:
            # Sometimes data comes back immediately, or it's an error
            if "name" in resp_json.get("data", {}):
                raw_data = resp_json["data"]
            else:
                print(f"[LinkedIn] API Init Failed: {resp_json}")
                return {"status": "error", "message": "Failed to initiate scrape"}
        else:
            # === 4. Poll for Results ===
            print(f"[LinkedIn] Polling for Request ID: {request_id}")
            raw_data = None
            
            # Poll up to 10 times (approx 30 seconds)
            for i in range(10):
                time.sleep(3) # Wait 3s between checks
                
                poll_payload = {"request_id": request_id}
                poll_resp = requests.post(API_ENDPOINT, json=poll_payload, headers=headers)
                poll_json = poll_resp.json()
                
                data_obj = poll_json.get("data", {})
                
                # Check if we have the profile data (look for 'name' or 'profile')
                if data_obj and "name" in data_obj:
                    raw_data = data_obj
                    print("[LinkedIn] Data received successfully.")
                    break
                
                status = data_obj.get("status", "processing")
                print(f"[LinkedIn] Status: {status}...")

            if not raw_data:
                return {"status": "error", "message": "Scrape timed out. Please try again."}

        # === 5. Map API Data to DB Schema ===
        
        # Experiences
        experiences = []
        for exp in raw_data.get("experience", []):
            experiences.append({
                "title": exp.get("title", ""),
                "company": exp.get("company_name", ""),
                "location": exp.get("location", ""),
                "description": exp.get("description", ""),
                "duration": format_duration(exp.get("date", {}))
            })

        # Education
        education = []
        for edu in raw_data.get("education", []):
            education.append({
                "institution": edu.get("university_name", ""),
                "degree": edu.get("degree", ""),
                "description": edu.get("major", ""),
                "from_date": edu.get("date", {}).get("start_date", ""),
                "to_date": edu.get("date", {}).get("end_date", "")
            })

        # Gather other lists for "Accomplishments" or "Interests"
        accomplishments = []
        # Add Certifications
        for cert in raw_data.get("certifications", []):
            accomplishments.append(f"Certification: {cert.get('title')} from {cert.get('issuer')}")
        # Add Projects
        for proj in raw_data.get("projects", []):
            accomplishments.append(f"Project: {proj.get('name')}")
        # Add Awards
        for award in raw_data.get("honors_and_awards", []):
            accomplishments.append(f"Award: {award.get('title')}")

        # Languages (Mapping to Interests/Skills mostly)
        languages = [lang.get("name") for lang in raw_data.get("languages", [])]

        # Final Profile Object
        profile_data = {
            "user_id": user_id,
            "input_url": linkedin_url,
            "name": raw_data.get("name", ""),
            "about": raw_data.get("description", ""),
            # Use Headline or first job title as position
            "position": raw_data.get("headline") or (experiences[0]["title"] if experiences else ""),
            "company": experiences[0]["company"] if experiences else "",
            "location": raw_data.get("location", ""),
            "experiences": experiences,
            "education": education,
            "interests": languages, # Mapping languages here as skills/interests
            "accomplishments": accomplishments,
            "last_updated": datetime.utcnow()
        }

        # === 6. Save to DB ===
        coll.update_one({"user_id": user_id}, {"$set": profile_data}, upsert=True)
        print(f"[LinkedIn] SUCCESS: Saved {profile_data['name']} to DB")
        
        return {"status": "success", "message": "Fetched & cached"}

    except Exception as e:
        print(f"[LinkedIn] UNEXPECTED ERROR: {str(e)}")
        # Fallback to cache if available
        if cached:
            return {"status": "success", "message": "Scrape failed, using cached data"}
        return {"status": "error", "message": str(e)}