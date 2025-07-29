import firebase_admin
from firebase_admin import credentials, firestore, storage

# Init Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': '<your-bucket-name>.appspot.com'  # e.g., maata-app.appspot.com
    })

db = firestore.client()
bucket = storage.bucket()
# Our brand new app
import streamlit as st
import os
from auth import login_signup
from utils import load_posts, save_post, display_posts

# Set page settings
st.set_page_config(page_title="Maata", layout="centered")

# ✅ Create folders and initialize CSV with headers
os.makedirs("storage/uploads", exist_ok=True)
if not os.path.exists("storage/posts.csv") or os.path.getsize("storage/posts.csv") == 0:
    with open("storage/posts.csv", "w") as f:
        f.write("timestamp,username,caption,media_path\n")

# ✅ Manage session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ✅ App header
  
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Baloo+Tammudu+2&display=swap" rel="stylesheet">
<style>
body, h1, h2, input, .stButton {
    font-family: 'Baloo Tammudu 2', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='
    text-align: center;
    color: #0077cc;
     font-family: "Noto Sans Telugu", "Segoe UI", "sans-serif";
    font-size: 48px;
    margin-bottom: 10px;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
'>మాట 📰</h1>
""", unsafe_allow_html=True)

 
st.markdown("""<h1 style=' text-align: center;
                           font-size: 28px;
                           font-family: "Noto Sans Telugu", "Segoe UI", "sans-serif";'>
                           స్థానిక వార్తలు మరియు కథలు</h1>""", unsafe_allow_html=True)

# ✅ Authentication
if not st.session_state.logged_in:
    login_signup()
    st.stop()

# ✅ Sidebar navigation
page = st.sidebar.radio("Navigation", ["🏠 Home", "➕ Post", "👤 Profile"])

# ✅ Routing pages
if page == "🏠 Home":
    st.subheader("📢 Community Posts")
    display_posts()

elif page == "➕ Post":
    st.subheader("📝 Create a Post")
    
    with st.form("new_post"):
        caption = st.text_area("What's happening?")
        media_file = st.file_uploader("Upload image/video", type=["png", "jpg", "jpeg", "mp4"])
        submitted = st.form_submit_button("Post")

        if submitted:
            if not caption.strip():
                st.warning("⚠️ Please enter a caption.")
            elif not media_file:
                st.warning("⚠️ Please upload an image or video.")
            else:
                save_post(st.session_state.username, caption, media_file)
                st.success("✅ Posted successfully!")


elif page == "🧑‍💼 Profile":
    st.subheader(f"👋 Hello, {st.session_state.username}")

    user_doc = db.collection("users").document(st.session_state.username)

    # Load previous data
    user_data = user_doc.get().to_dict() if user_doc.get().exists else {}

    # Show current photo
    if "photo_url" in user_data:
        st.image(user_data["photo_url"], width=150)

    # Upload photo
    uploaded_file = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        blob = bucket.blob(f"profile_pics/{st.session_state.username}.jpg")
        blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.type)
        blob.make_public()
        photo_url = blob.public_url
    else:
        photo_url = user_data.get("photo_url", "")

    # About
    about = st.text_area("About you", user_data.get("about", ""))

    # DOB
    dob = st.date_input("Date of Birth", user_data.get("dob"))

    if st.button("Save Profile"):
        user_doc.set({
            "about": about,
            "dob": str(dob),
            "photo_url": photo_url
        })
        st.success("✅ Profile saved successfully!")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

