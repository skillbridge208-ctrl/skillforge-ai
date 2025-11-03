import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------- SETUP --------------------
st.set_page_config(page_title="SkillForge AI – Intelligent Career Path Builder", page_icon="🧠", layout="centered")

load_dotenv()
FIREBASE_CONFIG_PATH = os.getenv("FIREBASE_CONFIG_PATH", "firebase_config.json")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
MODEL = "models/gemini-2.5-flash"

st.markdown("""
    <style>
        .stApp {
            background-color: #f8faf8;
        }
        .main-title {
            text-align: center;
            font-size: 2em;
            color: #065f46;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🧠 SkillForge AI – Intelligent Career Path Builder</h1>", unsafe_allow_html=True)


# -------------------- FIREBASE HELPERS --------------------
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


# -------------------- GEMINI ROADMAP --------------------
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


# -------------------- APP LOGIC --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧍 Create Profile", "🔍 Load Profile", "🧩 Generate Roadmap", "📊 View Profile", "✅ Mark Completed"])

profile = st.session_state.get("profile", None)

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

with tab2:
    st.markdown("### Load Existing Profile")
    name = st.text_input("Enter your name to load profile")
    if st.button("Load Profile"):
        loaded = load_profile_from_db(name)
        if loaded:
            st.session_state["profile"] = loaded
            profile = loaded
            st.json(loaded)

with tab3:
    st.markdown("### Generate Personalized Roadmap")
    if profile:
        if st.button("Generate Roadmap 🚀"):
            with st.spinner("⏳ Generating your personalized roadmap... please wait."):
                roadmap = generate_roadmap(profile)
                if roadmap:
                    st.success("✅ Roadmap generated successfully!")
                    st.markdown("### 📘 Your Career Roadmap:")
                    st.markdown(roadmap)
    else:
        st.info("Load or create a profile first.")


with tab4:
    st.markdown("### View Profile Details")
    if profile:
        st.json(profile)
    else:
        st.info("No profile loaded yet.")

with tab5:
    st.markdown("### Mark Skill as Completed")
    if profile:
        skill = st.text_input("Enter skill to mark completed")
        if st.button("Mark Completed"):
            if skill:
                profile.setdefault("completed", []).append(skill)
                save_profile_to_db(profile)
                st.success(f"{skill} marked as completed!")
                st.session_state["profile"] = profile
    else:
        st.info("Load a profile first.")
