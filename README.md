# 🎓 CampusMind — AI-Powered Academic Assistant

CampusMind is an AI-powered academic assistant that helps students learn from their own study materials. Students can upload academic documents such as PDFs and DOCX files and interact with them through an intelligent RAG-based chatbot.

The system processes uploaded documents, extracts and chunks their content, stores embeddings in a vector database, retrieves relevant information for each question, and generates grounded answers using an LLM.

## 🚀 Live Demo

- **Frontend:** https://campusmind-golkftvzamrybbzjekwazj.streamlit.app/
- **Backend API:** https://campusmind.fastapicloud.dev/
- **API Documentation:** https://campusmind.fastapicloud.dev/docs

## ✨ Features

- 🔐 User registration and authentication
- 📚 Upload and manage academic documents
- 📄 PDF and DOCX document support
- 🖼️ OCR support for scanned/image-based PDFs
- ✂️ Intelligent document chunking
- 🧠 Retrieval-Augmented Generation (RAG)
- 💬 AI-powered academic chatbot
- 📑 Source-aware answers from uploaded documents
- 🗂️ Multiple document support
- 🧹 Document deletion
- 💾 Chat history and conversations
- 🌙 Dark mode
- ☀️ Light mode
- ⚡ FastAPI backend
- 🎨 Streamlit frontend
- 🔑 Secure environment-variable based API configuration
- ☁️ Cloud deployment

## 🧠 How CampusMind Works

```text
                Student
                   │
                   ▼
          Streamlit Frontend
                   │
                   │ HTTPS API
                   ▼
            FastAPI Backend
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Authentication Documents  Chat
                   │
                   ▼
            Document Loader
                   │
                   ▼
        PDF / DOCX Text Extraction
                   │
                   ▼
             OCR Fallback
                   │
                   ▼
           Text Chunking
                   │
                   ▼
             Embeddings
                   │
                   ▼
              ChromaDB
                   │
             User Question
                   │
                   ▼
         Relevant Context Retrieval
                   │
                   ▼
              Groq LLM
                   │
                   ▼
        Grounded AI Response
                   │
                   ▼
          Answer + Sources
