import os
import json
import requests
from mistralai import Mistral
from groq import Groq
from markdown2 import Markdown
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

markdowner = Markdown()

# === MISTRAL API ===
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in .env")

mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# === GROQ API ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found. Groq functions will fail.")
else:
    groq_client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# ===================================================================
# MISTRAL: CAREER COACH (LEO)
# ===================================================================

def get_mistral_response(prompt, tokens=300):
    """
    Get response from Mistral (NO BLOCKS, NO 429)
    """
    try:
        response = mistral_client.chat.complete(
            model="open-mistral-nemo",  # ← FREE & UNLIMITED
            messages=[
                {
                    "role": "system",
                    "content": "You are Leo, a friendly career coach. Be concise, warm, and give 1 actionable tip."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Mistral] Error: {e}")
        # Fallback response
        return "Hi there! With your skills, next: build a small project this week. I’ll help you plan it!"


def generate_prompt(user_data, user_query, chat_history):
    """
    Safe prompt with PII — Mistral doesn't care
    """
    first_name = user_data.get("first_name", "User").split()[0]
    address_name = first_name if first_name != "User" else "there"

    headline = user_data.get("position", "Student")
    skills = user_data.get("skills", [])
    skills_str = ', '.join(skills) if skills else 'None'

    experience = user_data.get("experience", [])[:2]
    exp_str = ', '.join([
        f"{e.get('title','Role')} at {e.get('company','Company')}"
        for e in experience
    ]) if experience else 'None'

    # Chat history (last 2 turns)
    recent = chat_history[-2:]
    history_str = "\n".join([
        f"User: {m.get('prompt','')}\nLeo: {m.get('raw_response','')}"
        for m in recent if isinstance(m, dict)
    ]) or "First message."

    return f"""
You are Leo, a friendly career coach.

User: {first_name}
Role: {headline}
Skills: {skills_str}
Experience: {exp_str}

Recent Chat:
{history_str}

Question: "{user_query}"

Respond:
- Address as "{address_name}"
- 1 actionable tip
- 2 short paragraphs max
""".strip()


# ===================================================================
# GITHUB
# ===================================================================

def extract_github_username(github_input):
    """
    Extract GitHub username from a profile URL or return as-is if already a username.
    
    Handles:
    - https://github.com/username
    - http://github.com/username
    - github.com/username
    - username (returns as-is)
    """
    if not github_input:
        return None
    
    github_input = github_input.strip().rstrip('/')
    
    # Check if it's a URL
    if 'github.com' in github_input:
        # Extract the username from the URL path
        parts = github_input.split('github.com/')
        if len(parts) > 1:
            # Get the first path segment (username)
            username = parts[1].split('/')[0]
            return username if username else None
    
    # Already a username
    return github_input


def fetch_github_projects(github_input):
    """
    Fetch GitHub repositories for a user.
    
    Args:
        github_input: GitHub profile URL (https://github.com/username) or just username
    
    Returns:
        List of repo dicts with title, description, language, stars
        OR string error message if fetch fails
    """
    username = extract_github_username(github_input)
    
    if not username:
        return "No valid GitHub username provided"
    
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    try:
        response = requests.get(url, headers={"User-Agent": "CatalystAI-CareerCoach"})
        response.raise_for_status()
        repos = response.json()
        
        # Return richer data
        return [
            {
                "title": r["name"],
                "description": r["description"] or "No description",
                "language": r["language"] or "Not specified",
                "stars": r.get("stargazers_count", 0)
            }
            for r in repos
        ]
    except Exception as e:
        print(f"[GitHub] Fetch failed for '{username}': {e}")
        return f"GitHub fetch failed: {e}"


# ===================================================================
# GROQ: LEARNING PLANS & TUTOR (FULLY WORKING)
# ===================================================================

def get_roadmap_from_groq(topic, duration=None, duration_unit="months"):
    """
    Generate a 4-phase learning roadmap using Groq.
    Optionally accepts a duration to customize phase timelines.
    Returns valid JSON with 'resources' in every phase — NO TEMPLATE CRASHES.
    """
    if not GROQ_API_KEY:
        return {
            "phases": [
                {
                    "name": "Setup Required",
                    "duration": "N/A",
                    "description": "GROQ_API_KEY is missing in .env",
                    "skills": ["Fix environment"],
                    "resources": {
                        "Documentation": ["Add GROQ_API_KEY to .env"],
                        "Support": ["https://console.groq.com"]
                    }
                }
            ] * 4
        }

    # Build duration context for the prompt
    duration_context = ""
    if duration:
        total_time = f"{duration} {duration_unit}"
        duration_context = f"\nIMPORTANT: The learner has {total_time} to complete this roadmap. Distribute the 4 phases accordingly within this timeframe. Make phase durations realistic and add up to approximately {total_time}."
    else:
        duration_context = "\nAssume a standard 6-12 month learning timeline."

    prompt = f'''Create a structured learning roadmap for "{topic}" in this EXACT JSON format:
{{
    "phases": [
        {{
            "name": "Phase Name",
            "duration": "X-Y months",
            "description": "Brief description of phase",
            "skills": ["skill1", "skill2"],
            "resources": {{
                "Courses": ["Course name"],
                "Books": ["Book title"],
                "Projects": ["Project idea"]
            }}
        }}
    ]
}}
{duration_context}
Include exactly 4 phases. Return ONLY valid JSON. No markdown, no explanations.'''

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON expert. Return ONLY valid JSON. No ```json blocks. No extra text."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()

        # Remove code blocks if present
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]).strip()

        roadmap = json.loads(content)

        # === VALIDATE & ENFORCE STRUCTURE ===
        if not isinstance(roadmap.get("phases"), list) or len(roadmap["phases"]) == 0:
            raise ValueError("No phases in response")

        # Ensure exactly 4 phases
        phases = roadmap["phases"][:4]
        if len(phases) < 4:
            last = phases[-1] if phases else None
            while len(phases) < 4 and last:
                phases.append({**last, "name": f"{last['name']} (Extended)"})
        
        # Fix each phase
        for i, phase in enumerate(phases):
            phase.setdefault("name", f"Phase {i+1}: {topic} Learning")
            phase.setdefault("duration", "1-2 months")
            phase.setdefault("description", f"Focus on core concepts of {topic}")
            phase.setdefault("skills", [f"Skill {i+1}"])

            # === GUARANTEE 'resources' EXISTS ===
            if not isinstance(phase.get("resources"), dict):
                phase["resources"] = {}

            res = phase["resources"]
            res.setdefault("Courses", [f"Search '{topic}' on Coursera/Udemy"])
            res.setdefault("Books", ["Beginner guide"])
            res.setdefault("Projects", ["Build a small project"])

        return {"phases": phases}

    except Exception as e:
        print(f"[Groq] Roadmap generation failed: {e}")
        # === BULLETPROOF FALLBACK ===
        fallback_phase = {
            "name": f"{topic} Basics",
            "duration": "1-2 months",
            "description": f"Learn the fundamentals of {topic}",
            "skills": ["Core concepts", "Basic tools"],
            "resources": {
                "Courses": ["YouTube tutorials", "Official docs"],
                "Books": ["Beginner guide"],
                "Projects": ["Hello World project"]
            }
        }
        return {"phases": [fallback_phase] * 4}


def generate_learning_plan(phase_name, skills):
    """
    Generate a detailed weekly learning plan using Groq.
    Returns valid JSON with 'weekly_schedule' — NEVER EMPTY.
    """
    if not GROQ_API_KEY:
        return {
            "weekly_schedule": [
                {
                    "week": 1,
                    "learning_objectives": ["Setup your environment"],
                    "daily_tasks": [
                        {
                            "day": 1,
                            "tasks": ["Read introduction", "Install tools"],
                            "resources": ["Official docs"],
                            "duration_hours": 2
                        }
                    ],
                    "assessment": "Complete setup checklist"
                }
            ]
        }

    skills_str = ', '.join(skills) if skills else 'core concepts'
    
    prompt = f'''Generate a detailed 4-week learning plan for the phase "{phase_name}" 
    focusing on skills: {skills_str}.

    Return ONLY valid JSON in this EXACT format:
    {{
        "weekly_schedule": [
            {{
                "week": 1,
                "learning_objectives": ["Objective 1", "Objective 2"],
                "daily_tasks": [
                    {{
                        "day": 1,
                        "tasks": ["Task 1", "Task 2"],
                        "resources": ["Resource 1"],
                        "duration_hours": 2
                    }}
                ],
                "assessment": "Short quiz or project"
            }}
        ]
    }}

    Include exactly 4 weeks. Return ONLY JSON. No markdown. No explanations.'''

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON expert. Return ONLY valid JSON. No code blocks."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=1500
        )

        content = response.choices[0].message.content.strip()

        # Remove code blocks
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]).strip()

        plan = json.loads(content)

        # === VALIDATE & ENFORCE STRUCTURE ===
        if "weekly_schedule" not in plan or not isinstance(plan["weekly_schedule"], list):
            raise ValueError("Missing weekly_schedule")

        weeks = plan["weekly_schedule"][:4]
        if len(weeks) == 0:
            raise ValueError("No weeks generated")

        # Ensure each week has required keys
        for i, week in enumerate(weeks):
            week.setdefault("week", i + 1)
            week.setdefault("learning_objectives", [f"Learn core concepts of week {i+1}"])
            week.setdefault("assessment", "Complete daily tasks")

            # Fix daily_tasks
            daily = week.get("daily_tasks", [])
            if not isinstance(daily, list) or len(daily) == 0:
                daily = [{
                    "day": 1,
                    "tasks": [f"Study {phase_name} fundamentals"],
                    "resources": ["Online tutorial"],
                    "duration_hours": 2
                }]
            week["daily_tasks"] = daily[:5]  # Limit to 5 days

        # Pad to 4 weeks if needed
        while len(weeks) < 4:
            last = weeks[-1]
            weeks.append({
                "week": len(weeks) + 1,
                "learning_objectives": last["learning_objectives"],
                "daily_tasks": last["daily_tasks"],
                "assessment": last["assessment"]
            })

        return {"weekly_schedule": weeks}

    except Exception as e:
        print(f"[Groq] Learning plan failed: {e}")
        # === SAFE FALLBACK ===
        fallback_week = {
            "week": 1,
            "learning_objectives": [f"Master basics of {phase_name}"],
            "daily_tasks": [
                {
                    "day": 1,
                    "tasks": ["Read introduction", "Watch tutorial"],
                    "resources": ["YouTube", "Official docs"],
                    "duration_hours": 2
                }
            ],
            "assessment": "Complete setup and notes"
        }
        return {"weekly_schedule": [fallback_week] * 4}


def get_groq_response(message, topic, objectives, skills, resources, conversation_context=[]):
    """
    AI Tutor response (non-streaming)
    """
    if not GROQ_API_KEY:
        return "Tutor unavailable: GROQ_API_KEY missing"

    resources_str = "\n".join([f"{k}: {', '.join(v)}" for k, v in resources.items()])

    system_prompt = f"""You are an AI tutor for {topic}.
Objectives: {', '.join(objectives)}
Skills: {', '.join(skills)}
Resources:
{resources_str}
Be concise, educational, and encouraging."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_context)
    messages.append({"role": "user", "content": message})

    try:
        response = groq_client.chat.completions.create(
            messages=messages,
            model=GROQ_MODEL,
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq] Response error: {e}")
        return "Sorry, I couldn't respond. Try again!"


def get_groq_response_stream(message, topic, objectives, skills, resources, conversation_context=[]):
    """
    Streaming tutor response
    """
    if not GROQ_API_KEY:
        yield "Tutor unavailable"
        return

    resources_str = "\n".join([f"{k}: {', '.join(v)}" for k, v in resources.items()])

    system_prompt = f"""You are an AI tutor for {topic}.
Objectives: {', '.join(objectives)}
Skills: {', '.join(skills)}
Resources:
{resources_str}
Be concise and educational."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_context)
    messages.append({"role": "user", "content": message})

    try:
        stream = groq_client.chat.completions.create(
            messages=messages,
            model=GROQ_MODEL,
            temperature=0.5,
            max_tokens=1000,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[Groq] Stream error: {e}")
        yield "Error in stream"