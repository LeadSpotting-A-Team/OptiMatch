# Face Search Engine: End-to-End Facial Recognition Pipeline

A high-performance facial recognition and retrieval system designed to detect, index, and search millions of faces from raw image and video datasets in milliseconds.



## 🚀 Project Overview
This project is an automated pipeline that transforms raw scraped data into a searchable "Digital Identity" database. It utilizes state-of-the-art computer vision models for detection and embedding, coupled with high-speed vector indexing for real-time forensic analysis.

---

## 🏗️ System Architecture

### Phase 1: The "Face Harvester" (Detection & Extraction)
The entry point of the pipeline, responsible for isolating facial data from noise.
* **Input:** Raw images and video frames.
* **Technology:** MTCNN / MediaPipe.
* **Key Features:**
    * Automatic cropping of "Face Chips."
    * **Minimum Quality Filter:** Hard-coded threshold (e.g., 64x64 pixels) to ignore low-resolution background faces.
    * Metadata mapping (Original URL, timestamp, platform source).

### Phase 2: The "Digital Identity" (Embedding Generation)
Converting visual pixels into numerical biological signatures.
* **Input:** Cropped Face Chips.
* **Technology:** FaceNet / ArcFace.
* **Mathematical Optimization:**
    * **L2 Normalization:** Applied to all vectors to ensure search consistency across varying lighting, brightness, and contrast levels.
* **Output:** High-dimensional vector database (CSV/SQL).

### Phase 3: The "Brain" (Vector Indexing & Retrieval)
The core search engine designed for extreme scalability.
* **Input:** Face Embeddings.
* **Technology:** FAISS (Facebook AI Similarity Search) / ChromaDB.
* **Performance Tuning:**
    * **Flat Indexing:** For 100% accuracy on smaller datasets.
    * **IVF (Inverted File Index):** For approximate nearest neighbor (ANN) search on datasets exceeding millions of entries.



### Phase 4: The "Visual Investigator" (Search UI)
A specialized dashboard for analysts to perform visual queries.
* **Input:** User-uploaded query image.
* **Frontend:** React.js / Tailwind CSS.
* **Features:**
    * **Similarity Scoring:** Displays distance scores (e.g., "98% Match").
    * **Evidence Linking:** One-click navigation from a match back to the original source post.
    * **Split View:** Interactive "Query vs. Results" gallery.

---

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **CV Libraries:** OpenCV, MediaPipe, DeepFace
* **Vector Search:** FAISS
* **Database:** SQLite / PostgreSQL (for metadata)
* **Frontend:** React.js
* **Backend API:** FastAPI / Flask

---

## 🔧 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/ShlomiGanon/Face-Search-Engine.git](https://github.com/ShlomiGanon/Face-Search-Engine.git)
   cd Face-Search-Engine