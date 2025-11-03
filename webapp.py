import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import google.generativeai as genai

st.set_page_config(
    page_title="SkillForge AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ STYLING ------------------
st.markdown("""
<style>
/* Main container styling */
.stApp {
    background-color: #f8faf8;
}

/* Main title */
.main-title {
    text-align: center;
    font-size: 2em;
    color: #065f46;
    margin-bottom: 20px;
    font-weight: bold;
}

/* Card style for data boxes */
.profile-box {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    background-color: #ffffff;
    box-shadow: 0px 1px 6px rgba(0,0,0,0.08);
}

/* Titles */
.profile-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #800000; /* maroon */
}

/* Labels and values */
.profile-label {
    font-weight: 500;
    color: #333;
}

.profile-value {
    color: #555;
}

/* Buttons */
div.stButton > button {
    background-color: #800000 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    font-weight: 500 !important;
}

div.stButton > button:hover {
    background-color: #a52a2a !important;
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

# ------------------ HELPER FUNCTIONS ------------------
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

def show_profile_card(profile):
    st.markdown("<div class='profile-box'>", unsafe_allow_html=True)
    st.markdown(f"<div class='profile-title'>👤 Name</div><div class='profile-value'>{profile.get('name','')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='profile-title'>💼 Current Role</div><div class='profile-value'>{profile.get('current_role','')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='profile-title'>🧠 Skills</div><div class='profile-value'>{', '.join(profile.get('skills',[]))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='profile-title'>🎯 Career Goal</div><div class='profile-value'>{profile.get('goal','')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='profile-title'>✅ Completed Skills</div><div class='profile-value'>{', '.join(profile.get('completed',[]))}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ APP LOGIC ------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧍 Create Profile", 
    "🔍 Load Profile", 
    "🧩 Generate Roadmap", 
    "📊 View Profile", 
    "✅ Mark Completed"
])

profile = st.session_state.get("profile", None)

# ----- CREATE PROFILE -----
with tab1:
    st.markdown("### Create New Profile")
    with st.form("create_profile_form"):
        name = st.text_input("👤 Name", key="create_name")
        current_role = st.text_input("💼 Current Role", key="create_role")
        skills = st.text_input("🧠 Skills (comma separated)", key="create_skills")
        goal = st.text_area("🎯 Career Goal", key="create_goal")
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

# ----- LOAD PROFILE -----
with tab2:
    st.markdown("### Load Existing Profile")
    load_name = st.text_input("Enter your name to load profile", key="load_name")
    if st.button("Load Profile", key="load_btn"):
        loaded = load_profile_from_db(load_name)
        if loaded:
            profile = loaded
            st.session_state["profile"] = profile
            show_profile_card(profile)  # ✅ Styled display

# ----- GENERATE ROADMAP -----
with tab3:
    st.markdown("### Generate Personalized Roadmap")
    if profile:
        if st.button("Generate Roadmap 🚀", key="gen_roadmap_btn"):
            with st.spinner("⏳ Generating your personalized roadmap... please wait."):
                roadmap = generate_roadmap(profile)
                if roadmap:
                    st.success("✅ Roadmap generated successfully!")
                    st.markdown("### 📘 Your Career Roadmap:")
                    st.markdown(roadmap)
    else:
        st.info("Load or create a profile first.")

# ----- VIEW PROFILE -----
with tab4:
    st.markdown("### View Profile Details")
    if profile:
        show_profile_card(profile)  # ✅ Styled display
    else:
        st.info("No profile loaded yet.")

# ----- MARK COMPLETED -----
with tab5:
    st.markdown("### Mark Skill as Completed")
    if profile:
        skill = st.text_input("Enter skill to mark completed", key="mark_skill")
        if st.button("Mark Completed", key="mark_btn"):
            if skill:
                profile.setdefault("completed", []).append(skill)
                save_profile_to_db(profile)
                st.success(f"{skill} marked as completed!")
                st.session_state["profile"] = profile
    else:
        st.info("Load a profile first.")
