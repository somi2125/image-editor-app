# 🖼️ Image Editor App

## 📌 Introduction
Pro Image Editor is a powerful and user-friendly image editing web application built using Python and Streamlit.  
It allows users to upload images in multiple formats and apply real-time editing operations with a live preview feature.

---

## 🎯 Objective
The main goal of this project is to provide an easy-to-use image editing tool with multiple features like brightness adjustment, contrast control, filters, and resizing.

---

## 🔄 SDLC (Software Development Life Cycle)

### 🔹 1. Planning
- Build a simple yet powerful image editor
- Target users: Students, beginners, and developers
- Platform: Web-based using Streamlit

---

### 🔹 2. Requirement Analysis

#### ✅ Functional Requirements
- Upload image (JPG, PNG, TIFF, PDF)
- Apply grayscale
- Adjust brightness and contrast
- Apply blur and sharpening
- Resize image
- Live preview before applying changes

#### ✅ Non-Functional Requirements
- Fast processing
- Easy UI/UX
- Support multiple file formats

---

### 🔹 3. Design
- Frontend: Streamlit UI
- Backend: Python
- Libraries Used:
  - OpenCV
  - NumPy
  - PIL
  - pdf2image
  - rasterio

---

### 🔹 4. Development
Implemented features:
- Multi-format file upload (including PDF & TIFF)
- Real-time sidebar preview
- Image processing pipeline system
- Reset and apply changes functionality

---

### 🔹 5. Testing
- Tested with:
  - JPG, PNG, TIFF, PDF files
- Verified:
  - Image processing accuracy
  - UI responsiveness
- Handled errors:
  - Invalid file format
  - Large image handling

---

### 🔹 6. Deployment
Run locally using:

```bash
streamlit run app.py


