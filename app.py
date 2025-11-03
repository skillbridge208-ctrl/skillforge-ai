# app.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from google import generativeai as genai

# ---------- INITIAL SETUP ----------
load_dotenv()

FIREBASE_CONFIG_PATH = os.getenv("FIREBASE_CONFIG_PATH", "firebase_config.json")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# ---------- MENU ----------
def main_menu():
    print("\nSkillForge AI – Intelligent Career Path Builder")
    print("1. Create new profile")
    print("2. Load existing profile")
    print("3. Generate roadmap")
    print("4. Mark skill as completed")
    print("5. View profile")
    print("6. Exit")
    return input("Choose an option: ").strip()

# ---------- FIREBASE HELPERS ----------
def save_profile_to_db(profile):
    """Save or update user profile in Firestore"""
    doc_ref = db.collection("users").document(profile["name"])
    doc_ref.set(profile)
    print(f"✅ Profile for {profile['name']} saved to Firestore.\n")

def load_profile_from_db(name):
    """Load a user profile by name"""
    doc_ref = db.collection("users").document(name)
    doc = doc_ref.get()
    if doc.exists:
        profile = doc.to_dict()
        print(f"\n✅ Loaded profile for {name}.")
        print("📋 Profile Details:")
        print(f"   Name: {profile.get('name')}")
        print(f"   Current Role: {profile.get('current_role')}")
        print(f"   Skills: {', '.join(profile.get('skills', []))}")
        print(f"   Goal: {profile.get('goal')}")
        completed = ', '.join(profile.get('completed', [])) or "None"
        print(f"   Completed: {completed}\n")
        return profile
    else:
        print("❌ Profile not found.\n")
        return None

# ---------- PROFILE OPERATIONS ----------
def create_profile():
    name = input("Name: ").strip()
    current_role = input("Current role: ").strip()
    skills = [s.strip() for s in input("Skills (comma separated): ").split(",") if s.strip()]
    goal = input("Career goal: ").strip()
    profile = {
        "name": name,
        "current_role": current_role,
        "skills": skills,
        "goal": goal,
        "completed": []
    }
    save_profile_to_db(profile)
    print("✅ Profile created successfully!\n")
    return profile

def mark_completed(profile):
    skill = input("Enter completed skill: ").strip()
    if skill:
        profile.setdefault("completed", []).append(skill)
        print(f"{skill} marked as completed.\n")
        save_profile_to_db(profile)

def view_profile(profile):
    print("\n📘 Profile Summary:")
    for k, v in profile.items():
        if isinstance(v, list):
            print(f"{k.capitalize()}: {', '.join(v) if v else 'None'}")
        else:
            print(f"{k.capitalize()}: {v}")

# ---------- AI ROADMAP GENERATION ----------
def generate_roadmap(profile):
    print(f"\n🧠 Generating updated AI Career Roadmap for {profile['name']}...")

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")

        completed_skills = profile.get("completed", [])
        completed_text = (
            f"The user has already completed these skills: {', '.join(completed_skills)}. "
            if completed_skills else ""
        )

        prompt = (
            f"You are an AI career mentor. {completed_text}"
            f"Create a personalized, step-by-step *updated* career roadmap for someone who is currently "
            f"working as a {profile['current_role']} with skills in {', '.join(profile['skills'])}, "
            f"aiming to become a {profile['goal']}. "
            f"Consider their completed skills and recommend the *next logical learning steps*, "
            f"including courses, certifications, projects, and soft skills to develop. "
            f"Only show what comes *after* the completed skills. Format it as clear bullet points or stages."
        )

        response = model.generate_content(prompt)

        print("\n🎯 Updated Personalized Career Roadmap:\n")
        print(response.text.strip())
        print("\n✨ Roadmap updated successfully based on user progress!\n")

    except Exception as e:
        print("⚠️ Error generating roadmap:", e)

# ---------- MAIN LOOP ----------
def main():
    profile = None
    while True:
        choice = main_menu()
        if choice == "1":
            profile = create_profile()
        elif choice == "2":
            name = input("Enter your name to load profile: ").strip()
            profile = load_profile_from_db(name)
        elif choice == "3":
            if profile:
                generate_roadmap(profile)
            else:
                print("Please create or load a profile first.")
        elif choice == "4":
            if profile:
                mark_completed(profile)
            else:
                print("Please create or load a profile first.")
        elif choice == "5":
            if profile:
                view_profile(profile)
            else:
                print("No profile available.")
        elif choice == "6":
            print("👋 Goodbye! Thank you for using SkillForge AI.")
            break
        else:
            print("❌ Invalid option. Try again.")

if __name__ == "__main__":
    main()
