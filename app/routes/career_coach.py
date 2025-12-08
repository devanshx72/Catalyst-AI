from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from markdown2 import Markdown
from app.utils.llm_utils import get_mistral_response, fetch_github_projects
from app.utils.db_utils import get_db, get_user_by_id
from app.utils.linkedin import fetch_linkedin_profile_brightdata

# Initialize markdown converter
markdowner = Markdown()

# Career coach blueprint
career_coach_bp = Blueprint('career_coach_bp', __name__)

def generate_prompt(user_data, user_query, chat_history, github_projects=None, user_profile=None):
    """
    Generates a context-aware prompt for the LLM using LinkedIn data, GitHub projects, and career goals.
    
    Args:
        user_data: LinkedIn/rich profile data (experiences, education, etc.)
        user_query: The user's current question
        chat_history: Previous conversation messages
        github_projects: List of GitHub repositories
        user_profile: Basic user profile with career goal, dream company, etc.
    """
    # === 1. Personal Info ===
    # Fallback to "User" if name is missing
    full_name = user_data.get("name", "User")
    first_name = full_name.split()[0] if full_name else "User"
    headline = user_data.get("position", "Student")
    about_summary = user_data.get("about", "No summary provided.")
    
    # === 1b. Career Aspirations (from user profile) ===
    profile = user_profile or {}
    career_goal = profile.get("career_goal", "Not specified")
    dream_company = profile.get("dream_company", "Not specified")
    company_preference = profile.get("company_preference", "Not specified")
    personal_statement = profile.get("personal_statement", "Not provided")
    industries = profile.get("interested_industries") or profile.get("key_interests", [])
    industries_str = ', '.join(industries[:5]) if isinstance(industries, list) else str(industries) if industries else "Not specified"

    # === 2. Skills / Interests ===
    # In our DB schema, 'interests' holds the skills/languages from LinkedIn
    skills = user_data.get("interests", [])
    if not skills:
        # Fallback to manual key_interests if LinkedIn skills are empty
        skills = user_data.get("key_interests", [])
    
    skills_str = ', '.join(skills[:15]) if skills else 'None listed'

    # === 3. Experience ===
    # Format the first 3 experiences
    experiences = user_data.get("experiences", [])
    experience_list = []
    for exp in experiences[:3]:
        title = exp.get('title', 'Role')
        company = exp.get('company', 'Company')
        duration = exp.get('duration', '')
        # Add to list string
        experience_list.append(f"- {title} at {company} ({duration})")
    
    exp_str = "\n".join(experience_list) if experience_list else "No experience listed."

    # === 4. Education ===
    # Format the first 2 education entries
    educations = user_data.get("education", [])
    education_list = []
    for edu in educations[:2]:
        school = edu.get('institution', 'University')
        degree = edu.get('degree', 'Degree')
        major = edu.get('description', '')
        education_list.append(f"- {degree} in {major} from {school}")
    
    edu_str = "\n".join(education_list) if education_list else "No education listed."

    # GitHub Projects
    github_str = "No GitHub projects available."
    if github_projects and isinstance(github_projects, list) and len(github_projects) > 0:
        project_lines = []
        for repo in github_projects:
            name = repo.get('title', 'Project')
            desc = repo.get('description', 'No description')
            lang = repo.get('language', 'Unknown')
            stars = repo.get('stars', 0)
            project_lines.append(f"- {name} ({lang}, {stars}★): {desc[:80]}")
        github_str = "\n".join(project_lines)

    # === 6. Chat History (Last 3 interactions for context) ===
    recent_history = chat_history[-3:]
    history_str = ""
    for msg in recent_history:
        if isinstance(msg, dict):
            history_str += f"User: {msg.get('prompt', '')}\nLeo: {msg.get('raw_response', '')}\n"

    if not history_str:
        history_str = "No previous conversation."

    # === FINAL PROMPT CONSTRUCTION ===
    return f"""
        You are Leo, a professional and encouraging Career Coach AI.
        
        === USER PROFILE ===
        Name: {full_name}
        Headline: {headline}
        Summary: {about_summary}
        
        === CAREER ASPIRATIONS ===
        Career Goal: {career_goal}
        Dream Company: {dream_company}
        Company Preference: {company_preference}
        Industries of Interest: {industries_str}
        Personal Statement: {personal_statement[:200] if personal_statement else 'Not provided'}
        
        TOP SKILLS:
        {skills_str}
        
        EXPERIENCE:
        {exp_str}
        
        EDUCATION:
        {edu_str}
        
        GITHUB PROJECTS:
        {github_str}
        
        === CONVERSATION HISTORY (Memory) ===
        {history_str}
        
        === USER QUESTION ===
        "{user_query}"
        
        === INSTRUCTIONS ===
        1. Address the user as "{first_name}".
        2. Answer the user's question based on their FULL profile above, including their career aspirations.
        3. If they ask about jobs, suggest roles that align with their Career Goal ({career_goal}) and Dream Company ({dream_company}).
        4. Reference their GitHub projects when discussing their portfolio or technical skills.
        5. Remember the conversation history to provide contextual, coherent responses.
        6. Be concise (max 3 short paragraphs).
        7. Use a warm, professional, and motivating tone.
        8. Use formatting (bullet points, bold text) where helpful.
        """.strip()

@career_coach_bp.route('/your-career_coach-leo011', methods=['POST', 'GET'])
def career_coach():
    if "user_id" not in session:
        return redirect(url_for("auth_bp.sign_in"))

    db = get_db()
    leo_chat_history = db.career_coach
    linkedin_coll = db.linkedin_data

    if request.method == 'POST':
        user_id = session['user_id']
        user_query = request.form['userQuery']

        # --------------------------------------------------------------
        # 1. Get Basic User Record (for fallback)
        # --------------------------------------------------------------
        user_record = get_user_by_id(user_id)
        linkedin_url = user_record.get('linkedinProfile')
        
        # --------------------------------------------------------------
        # 2. Trigger Scrape if LinkedIn URL exists (Lazy Update)
        # --------------------------------------------------------------
        if linkedin_url:
            try:
                # This checks cache age internally, so it's safe to call every time
                fetch_linkedin_profile_brightdata(linkedin_url, user_id)
            except Exception as e:
                print(f"[Leo] LinkedIn fetch warning: {e}")

        # --------------------------------------------------------------
        # 3. Load Rich Data from DB
        # --------------------------------------------------------------
        # Try to get the rich scraped data first
        rich_user_data = linkedin_coll.find_one({"user_id": user_id})
        
        # If no scraped data, fall back to basic sign-up data
        if not rich_user_data:
            rich_user_data = user_record or {}
            # Normalize keys to match generate_prompt expectations
            rich_user_data["experiences"] = []
            rich_user_data["education"] = []
            rich_user_data["interests"] = rich_user_data.get("key_interests", [])

        # --------------------------------------------------------------
        # 4. Fetch GitHub Projects
        # --------------------------------------------------------------
        github_projects = None
        github_url = user_record.get('github_profile') or user_record.get('githubProfile')
        if github_url:
            try:
                github_projects = fetch_github_projects(github_url)
                if isinstance(github_projects, str):
                    # It's an error message, log it
                    print(f"[Leo] GitHub fetch warning: {github_projects}")
                    github_projects = None
            except Exception as e:
                print(f"[Leo] GitHub fetch error: {e}")
                github_projects = None

        # --------------------------------------------------------------
        # 5. Get Chat History
        # --------------------------------------------------------------
        conv = leo_chat_history.find_one({"user_id": user_id})
        chat_history = conv.get("messages", []) if conv else []

        # --------------------------------------------------------------
        # 6. Generate AI Response
        # --------------------------------------------------------------
        try:
            prompt = generate_prompt(rich_user_data, user_query, chat_history, github_projects, user_record)
            raw_resp = get_mistral_response(prompt, tokens=400)

            # Convert Markdown to HTML for display
            html_resp = markdowner.convert(raw_resp)
        except Exception as e:
            print(f"[Leo] LLM Error: {e}")
            first_name = rich_user_data.get("name", "there").split()[0]
            raw_resp = f"I'm sorry {first_name}, I'm having trouble thinking right now. Could you ask that again?"
            html_resp = markdowner.convert(raw_resp)

        # --------------------------------------------------------------
        # 6. Save Conversation
        # --------------------------------------------------------------
        new_msg = {
            "prompt": user_query,
            "response": html_resp,
            "raw_response": raw_resp,
            "time": datetime.utcnow(),
        }

        if not conv:
            conv_id = f"conv_{int(datetime.now().timestamp())}"
            leo_chat_history.insert_one({
                "user_id": user_id,
                "conversation_id": conv_id,
                "messages": [new_msg],
            })
            messages = [new_msg]
        else:
            # Append new message
            leo_chat_history.update_one(
                {"user_id": user_id},
                {"$push": {"messages": new_msg}}
            )
            # Fetch updated list for rendering
            updated_conv = leo_chat_history.find_one({"user_id": user_id})
            messages = updated_conv.get("messages", [])

        return render_template("career_coach.html", messages=messages)

    # GET route - Display history
    conv = leo_chat_history.find_one({"user_id": session["user_id"]})
    messages = conv.get("messages", []) if conv else []

    return render_template("career_coach.html", messages=messages)


@career_coach_bp.route('/your-career_coach-leo011/clear', methods=['POST'])
def clear_chat():
    """
    Clears the user's saved Leo chat history.
    """
    if "user_id" not in session:
        return redirect(url_for("auth_bp.sign_in"))

    db = get_db()
    leo_chat_history = db.career_coach
    user_id = session['user_id']

    try:
        # Remove the conversation document for this user (clean slate).
        leo_chat_history.delete_one({"user_id": user_id})
    except Exception as e:
        # Log but continue — do not reveal internal error to user
        print(f"[Leo] Error clearing chat for user {user_id}: {e}")

    # Redirect back to the main career coach page which will render empty history
    return redirect(url_for('career_coach_bp.career_coach'))
