import os
import time
import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
from dotenv import load_dotenv

# ✅ Load .env variables
load_dotenv()
# 🔐 API key from environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Use a lightweight, fast model for fewer quota issues
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

# 📄 Extract text from PDF
def extract_text_from_pdf(uploaded_file):
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# 🤖 Summarize with error handling + retry
def summarize_text(text):
    prompt = f"Summarize the following document:\n\n{text}"
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except ResourceExhausted as e:
            st.warning(f"⏱️ Quota exceeded. Retrying in 30 seconds... ({attempt + 1}/3)")
            time.sleep(30)
        except GoogleAPIError as e:
            st.error(f"❌ API error: {str(e)}")
            break
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            break
    return "⚠️ Unable to summarize due to repeated errors. Please try again later."

# 💬 Chat-style message display
def chat_bubble(message, role="bot"):
    with st.chat_message(role):
        st.markdown(message)

# 🚀 Streamlit UI setup
st.set_page_config(page_title="📄 PDF Summarizer Bot", layout="centered")
st.title("💬 Gemini PDF Chatbot Summarizer")
st.caption("Upload a PDF and chat with a smart summarizer bot powered by Gemini!")

uploaded_file = st.file_uploader("📎 Upload your PDF", type=["pdf"])

# 🧠 Summarization Flow
if uploaded_file:
    chat_bubble("✅ PDF Uploaded. Let me read it for you...", "bot")
    with st.spinner("🔍 Extracting content..."):
        pdf_text = extract_text_from_pdf(uploaded_file)

    if not pdf_text:
        chat_bubble("❌ I couldn't find any readable text in the PDF.", "bot")
    elif len(pdf_text) > 100_000:
        chat_bubble("⚠️ The PDF is too long for me to summarize at once. Try splitting it.", "bot")
    else:
        with st.spinner("✍️ Summarizing your document..."):
            summary = summarize_text(pdf_text)
        chat_bubble("Here’s the summary of your document:", "bot")
        chat_bubble(summary, "bot")
