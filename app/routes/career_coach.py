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

def generate_prompt(user_data, user_query, chat_history):
    """
    Generates a context-aware prompt for the LLM using LinkedIn data.
    """
    # === 1. Personal Info ===
    # Fallback to "User" if name is missing
    full_name = user_data.get("name", "User")
    first_name = full_name.split()[0] if full_name else "User"
    headline = user_data.get("position", "Student")
    about_summary = user_data.get("about", "No summary provided.")

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

    # === 5. Chat History (Last 3 interactions for context) ===
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
        
        TOP SKILLS:
        {skills_str}
        
        EXPERIENCE:
        {exp_str}
        
        EDUCATION:
        {edu_str}
        
        === CONVERSATION HISTORY ===
        {history_str}
        
        === USER QUESTION ===
        "{user_query}"
        
        === INSTRUCTIONS ===
        1. Address the user as "{first_name}".
        2. Answer the user's question specifically based on their profile data above.
        3. If they ask about jobs, suggest roles that fit their Experience and Skills.
        4. Be concise (max 3 short paragraphs).
        5. Use a warm, professional, and motivating tone.
        6. Use formatting (bullet points, bold text) where helpful.
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
        # 4. Get Chat History
        # --------------------------------------------------------------
        conv = leo_chat_history.find_one({"user_id": user_id})
        chat_history = conv.get("messages", []) if conv else []

        # --------------------------------------------------------------
        # 5. Generate AI Response
        # --------------------------------------------------------------
        try:
            prompt = generate_prompt(rich_user_data, user_query, chat_history)
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
