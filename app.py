import os
import json
import streamlit as st # Streamlit library
from dotenv import load_dotenv # Environment variable management
from PIL import Image # Image handling
from google import genai # Google GenAI module
from google.genai import types # Content generation configuration
import time # For delays between API calls
import re # Regular expression for URL cleaning

# --- CONFIGURATION AND INITIALIZATION ---

# Load environment variables (API Key) from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize client to None. It will only be initialized if the API key is present.
client = None 
if not API_KEY:
    st.error("GEMINI_API_KEY not found. Please set it in the .env file.")
else:
    # Initialize the Gemini Client
    client = genai.Client(api_key=API_KEY)

# MUST set page config before any other Streamlit calls to avoid runtime errors
st.set_page_config(
    page_title="Gemini StudyPal",
    layout="wide"
)
st.title("Your Gemini StudyPal")
st.caption("Use Gemini StudyPal to create flashcards, quizzes, and explanations from your notes.")


def apply_light_theme_css():
    """
    Applies custom CSS for light theme compatibility, using borders and 
    subtle shadows for visual separation of containers and tabs.
    
    Colors used match your config.toml:
    Primary: #87b4f2ff (Light Blue)
    Secondary Background: #F0F2F6 (Light Gray)
    Text: #262627ff (Near-Black)
    """
    st.markdown(
        """
        <style>
        /* General text styling for better readability */
        p, .stMarkdown, .stText {
            font-size: 16px;
            line-height: 1.6;
            color: #262627ff; /* Ensure dark text */
        }

        /* Customize the primary button for a cleaner, defined look */
        .stButton button {
            border-radius: 12px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s ease-in-out;
            /* Using a box shadow for a 'lifted' effect on a light background */
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); 
        }
        
        /* Center the main app content */
        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Custom styling for the tabs to give them a modern, lifted look */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            border-bottom: 2px solid #E0E0E0; /* Light separator line */
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 8px 8px 0 0;
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0; /* Subtle border for inactive tabs */
            margin-bottom: -1px;
        }
        /* Style for the currently selected tab */
        .stTabs [aria-selected="true"] {
            font-weight: bold;
            color: #262627ff; /* Keep text readable */
            background-color: #FFFFFF;
            /* Use primary color for a strong, active bottom border */
            border-bottom: 4px solid #87b4f2ff; 
            border-top: 1px solid #87b4f2ff; /* Primary color border on active tab top */
            border-left: 1px solid #87b4f2ff;
            border-right: 1px solid #87b4f2ff;
            box-shadow: 0 -4px 6px rgba(0, 0, 0, 0.05); /* Shadow for active tab */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- CACHED API CALL FUNCTION (FIXED) ---

# Use st.cache_data to prevent redundant API calls when switching tabs
@st.cache_data(show_spinner=False)
def generate_content(_client, _images, system_instruction, prompt): # <--- FINAL FIX APPLIED HERE: _client AND _images
    """Generates content using the Gemini API with JSON enforcement."""
    
    if _client is None: # Use _client
        return None
        
    contents = list(_images) # Use _images
    contents.append(prompt) 
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json"
    )

    try:
        with st.spinner("Analyzing your notes and generating materials..."):
            response = _client.models.generate_content( # Use _client
                model='gemini-2.5-flash',
                contents=contents,
                config=config,
            )
            
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            st.error(f"Failed to decode JSON response from API. Expected JSON. Raw text received: {response.text[:200]}...")
            st.error(f"JSON Decoding Error: {e}")
            return None
        
    except Exception as e:
        st.error(f"An API error occurred during content generation: {e}")
        return None

# --- APPLY CSS AND INITIALIZE STATE ---

apply_light_theme_css()

# Initialize session state for generated content (to prevent re-triggering)
if 'ready' not in st.session_state:
    st.session_state.ready = False
if 'video_url' not in st.session_state:
    st.session_state.video_url = None
if 'video_search_query' not in st.session_state:
    st.session_state.video_search_query = None

# --- UI & LOGIC ---

# Sidebar for customization and upload
with st.sidebar:
    st.header("Upload Notes")
    
    # File uploader allows multiple files
    uploaded_files = st.file_uploader(
        "Upload photos of your notes or textbook pages (JPG/JPEG/PNG)", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True 
    )
    subject_input = st.text_input("Subject Context", "General Study")
    
    if uploaded_files:
        st.subheader("Notes Preview")
        # Display small previews of all uploaded files
        for file in uploaded_files:
            st.image(file, caption=file.name, use_container_width=True) 


if uploaded_files is None or len(uploaded_files) == 0: 
    st.info("Please upload one or more images of your notes or textbook to begin.")
elif client is None:
    pass 
else:
    # --- Generation Trigger Logic ---
    if st.button("Analyze and Generate Study Tools", type="primary"):
        
        # Clear cache and reset state for new notes
        st.cache_data.clear()
        st.session_state.video_url = None 
        st.session_state.video_search_query = None 
        
        try:
            image_list = [Image.open(file) for file in uploaded_files]
        except Exception as e:
            st.error(f"Error opening uploaded image files: {e}")
            image_list = []
            
        st.session_state.image_list = image_list 
        st.session_state.subject = subject_input
        st.session_state.ready = True
    
    # Only show the results tabs if generation has been triggered successfully
    if st.session_state.ready:
        images = st.session_state.image_list 
        subject = st.session_state.subject
        
        # --- TAB INTERFACE FOR FEATURES (4 tabs including Video Tutor) ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "Flashcards", 
            "Quiz", 
            "Explainer",
            "Video Tutor" # NEW TAB
        ])
        
        # --- 1. FLASHCARD TAB ---
        with tab1:
            st.header("Flashcard Set")
            
            fc_sys_instruction = (
                f"You are an expert study assistant for {subject}. Analyze the images and "
                "extract key terms or concepts. Generate a flashcard for each. "
                "Output must be a strict JSON array of objects with keys 'question' and 'answer'."
            )
            fc_prompt = "Generate a comprehensive set of flashcards based on the image content."
            
            # Function call remains (client, images, ...), but the function signature ignores them for caching
            flashcards = generate_content(client, images, fc_sys_instruction, fc_prompt) 
            
            if flashcards:
                for i, card in enumerate(flashcards):
                    with st.expander(f"Question {i+1}: {card['question']}", expanded=False):
                        st.markdown(f"Answer: {card['answer']}")
                st.success("Flashcards generated successfully.")
            else:
                st.warning("Could not generate flashcards.")

            time.sleep(1) 
        
        # --- 2. QUIZ TAB ---
        with tab2:
            st.header("Multiple-Choice Quiz")
            
            quiz_sys_instruction = (
                f"You are a quiz master for {subject}. Create a 10-question multiple-choice quiz "
                "based on the images. Each question must have 4 options (A, B, C, D) and a correct answer. "
                "Output must be a strict JSON array of objects with keys: 'question', 'options' (object mapping A-D to choices), 'correct_answer', and 'explanation'."
            )
            quiz_prompt = "Generate a challenging 10-question multiple-choice quiz."
            
            # Function call is correct
            quiz = generate_content(client, images, quiz_sys_instruction, quiz_prompt)
            
            if quiz:
                for i, q in enumerate(quiz):
                    st.subheader(f"Question {i+1}: {q['question']}")
                    
                    options_str = "\n".join([f"- **{key}**: {val}" for key, val in q['options'].items()])
                    st.markdown(options_str)
                    
                    with st.expander("Reveal Answer"):
                        st.success(f"Correct Answer: **{q['correct_answer']}**")
                        st.info(f"Explanation: {q['explanation']}")
                st.success("Quiz generated successfully.")
            else:
                st.warning("Could not generate the quiz.")
                
            time.sleep(1) 

        # --- 3. EXPLAINER TAB ---
        with tab3:
            st.header("Step-by-Step Problem Solver & Explainer")
            
            solver_sys_instruction = (
                f"You are a helpful tutor for {subject}. Analyze the images for any complex concepts or "
                "mathematical problems. If a problem is present, provide a clear, numbered step-by-step solution. "
                "If concepts are present, provide a clear, simple explanation for one of the core concepts. "
                "Output must be a strict JSON object with a single key: 'tutor_response', "
                "containing the full text of the solution or explanation, formatted in markdown (use **bold** and steps)."
            )
            solver_prompt = (
                "Analyze the images and either (1) pick a difficult concept and explain it simply and clearly, "
                "or (2) solve the most prominent problem shown, providing a clear, numbered, step-by-step solution."
            )

            # Function call is correct
            solver_data = generate_content(client, images, solver_sys_instruction, solver_prompt)

            if solver_data and 'tutor_response' in solver_data:
                st.info("Tutor's Analysis:")
                st.markdown(solver_data['tutor_response'])
                st.success("Explainer generated successfully.")
            else:
                st.warning("Could not generate the Explainer.")
            
            time.sleep(1) 

        # --- 4. VIDEO TUTOR TAB (NEW FEATURE) ---
        with tab4:
            st.header("Video Tutor")
            
            # Check if video URL is already in session state (to prevent re-running the API)
            if st.session_state.video_url:
                search_query = st.session_state.video_search_query
                st.subheader(f"Video suggested for: **{search_query}**")
                st.video(st.session_state.video_url)
                st.success("Video embedded from a previous analysis.")
            else:
                # 1. AI Analysis to get the best video URL directly
                video_sys_instruction = (
                    f"You are an expert video suggester for {subject}. Analyze the images and "
                    "identify the single most complex or interesting concept that would benefit from a video explanation. "
                    "Search YouTube and provide the URL for the best, most relevant educational video. "
                    "Output must be a strict JSON object with keys: 'video_search_query' (the topic you searched for) and 'video_url' (the full YouTube URL)."
                )
                video_prompt = "Identify the core concept and provide the best educational YouTube video URL for that concept."
                
                # Generate the search query and URL using Gemini
                # Function call is correct
                video_data = generate_content(client, images, video_sys_instruction, video_prompt)
                
                if video_data and 'video_url' in video_data and 'video_search_query' in video_data:
                    # Clean the URL (sometimes models wrap it in quotes or markdown)
                    raw_url = video_data['video_url']
                    clean_url = raw_url.strip()
                    clean_url = re.sub(r'(^"|"$)', '', clean_url)
                    
                    # Store in session state
                    st.session_state.video_url = clean_url
                    st.session_state.video_search_query = video_data['video_search_query']
                    
                    st.subheader(f"Video suggested for: **{video_data['video_search_query']}**")
                    
                    # Use st.video to embed the YouTube video player
                    st.video(clean_url)
                    st.success("Video embedded successfully.")
                    
                else:
                    st.warning("Could not identify a topic or find a video URL. Try again.")
                    
                time.sleep(1)