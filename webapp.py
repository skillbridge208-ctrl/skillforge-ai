import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import google.generativeai as genai

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="SkillForge AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ CUSTOM STYLING ------------------
st.markdown("""
    <style>
    /* App background */
    .stApp {
        background-color: #008080;  /* Teal */
        color: #000000;
        font-family: 'Inter', sans-serif;
    }

    /* Main title */
    .main-title {
        text-align: center;
        font-size: 2em;
        color: #ffffff;
        margin-bottom: 20px;
        font-weight: bold;
    }

    /* Card style for profile and roadmap boxes */
    .card {
        background-color: #ffffff;  /* white cards */
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        color: #000000;
        margin-bottom: 20px;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #800000 !important;  /* maroon */
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }

    div.stButton > button:hover {
        background-color: #a52a2a !important;
    }

    /* Input fields */
    input, textarea {
        color: #000 !important;
    }

    /* Ensure text inside cards is visible */
    .card p, .card li {
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🧠 SkillForge AI – Intelligent Career Path Builder</h1>", unsafe_allow_html=True)

# ------------------ FIREBASE + GEMINI SETUP ------------------
firebase_config = json.loads(st.secrets["FIREBASE_CONFIG"])
gemini_api_key = st.secrets["GEMINI_API_KEY"]

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()
genai.configure(api_key=gemini_api_key)
MODEL = "models/gemini-2.5-flash"

# ------------------ FIREBASE HELPERS ------------------
def save_profile_to_db(profile):
    doc_ref = db.collection("users").document(profile["name"])
    doc_ref.set(profile)
    st.success(f"✅ Profile for {profile['name']} saved successfully!")

def load_profile_from_db(name):
    doc_ref = db.collection("users").document(name)
    doc = doc_ref.get()
    if doc.exists:
        st.success(f"✅ Loaded profile for {name}")
        return doc.to_dict()
    else:
        st.error("❌ Profile not found.")
        return None

# ------------------ GENERATE ROADMAP ------------------
def generate_roadmap(profile):
    prompt = f"""
    You are an AI career mentor. Create a clear, step-by-step learning roadmap 
    for this user based on their details:

    Name: {profile['name']}
    Current Role: {profile['current_role']}
    Existing Skills: {', '.join(profile['skills'])}
    Career Goal: {profile['goal']}

    Provide:
    - Learning stages (Beginner, Intermediate, Advanced)
    - Specific skill recommendations
    - Suggested courses or certifications
    - Final project ideas

    Format neatly with bullet points.
    """
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"⚠️ Error generating roadmap: {e}")
        return None

# ------------------ DISPLAY PROFILE CARD ------------------
def show_profile_card(profile):
    st.markdown(f"""
        <div class="card">
            <p><strong>Name:</strong> {profile.get("name","")}</p>
            <p><strong>Current Role:</strong> {profile.get("current_role","")}</p>
            <p><strong>Skills:</strong> {', '.join(profile.get("skills",[]))}</p>
            <p><strong>Completed:</strong> {', '.join(profile.get("completed",[]))}</p>
            <p><strong>Goal:</strong> {profile.get("goal","")}</p>
        </div>
    """, unsafe_allow_html=True)

# ------------------ APP LOGIC ------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧍 Create Profile", 
    "🔍 Load Profile", 
    "🧩 Generate Roadmap", 
    "📊 View Profile", 
    "✅ Mark Completed"
])

profile = st.session_state.get("profile", None)

# --- Tab 1: Create Profile ---
with tab1:
    st.markdown("### Create New Profile")
    with st.form("create_profile_form"):
        name = st.text_input("👤 Name")
        current_role = st.text_input("💼 Current Role")
        skills = st.text_input("🧠 Skills (comma separated)")
        goal = st.text_area("🎯 Career Goal")
        submitted = st.form_submit_button("Save Profile")

        if submitted:
            if name and current_role and goal:
                profile = {
                    "name": name.strip(),
                    "current_role": current_role.strip(),
                    "skills": [s.strip() for s in skills.split(",") if s.strip()],
                    "goal": goal.strip(),
                    "completed": []
                }
                save_profile_to_db(profile)
                st.session_state["profile"] = profile
            else:
                st.warning("Please fill in all required fields.")

# --- Tab 2: Load Profile ---
with tab2:
    st.markdown("### Load Existing Profile")
    name = st.text_input("Enter your name to load profile", key="load_name")
    if st.button("Load Profile"):
        loaded = load_profile_from_db(name)
        if loaded:
            st.session_state["profile"] = loaded
            profile = loaded
            show_profile_card(profile)

# --- Tab 3: Generate Roadmap ---
with tab3:
    st.markdown("### Generate Personalized Roadmap")
    if profile:
        if st.button("Generate Roadmap 🚀"):
            with st.spinner("⏳ Generating your personalized roadmap... please wait."):
                roadmap = generate_roadmap(profile)
                if roadmap:
                    st.success("✅ Roadmap generated successfully!")
                    st.markdown(f'<div class="card"><pre>{roadmap}</pre></div>', unsafe_allow_html=True)
    else:
        st.info("Load or create a profile first.")

# --- Tab 4: View Profile ---
with tab4:
    st.markdown("### View Profile Details")
    if profile:
        show_profile_card(profile)
    else:
        st.info("No profile loaded yet.")

# --- Tab 5: Mark Completed ---
with tab5:
    st.markdown("### Mark Skill as Completed")
    if profile:
        skill = st.text_input("Enter skill to mark completed", key="completed_skill")
        if st.button("Mark Completed"):
            if skill:
                profile.setdefault("completed", []).append(skill)
                save_profile_to_db(profile)
                st.success(f"{skill} marked as completed!")
                st.session_state["profile"] = profile
    else:
        st.info("Load a profile first.")
