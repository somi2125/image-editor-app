import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_cropper import st_cropper 
from pdf2image import convert_from_bytes
import io
import pandas as pd

st.set_page_config(page_title="Pro Image Editor", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better UI
st.markdown("""
    <style>
    [data-testid="stImage"] img {
        max-height: 70vh;
        width: auto;
        margin: auto;
        display: block;
        object-fit: contain;
        border-radius: 10px;
    }
    .stDownloadButton button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

def init_session():
    if "img_cv" not in st.session_state: st.session_state.img_cv = None
    if "processed" not in st.session_state: st.session_state.processed = None

def load_file(file):
    name = file.name.lower()
    if name.endswith(".pdf"):
        images = convert_from_bytes(file.read())
        img = np.array(images[0])
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:
        image = Image.open(file)
        img = np.array(image)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

# --- Filter Functions ---

def to_grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

def adjust_brightness(img, val):
    if val == 0: return img
    matrix = np.ones(img.shape, dtype="uint8") * abs(val)
    return cv2.add(img, matrix) if val > 0 else cv2.subtract(img, matrix)

def adjust_contrast(img, alpha):
    return cv2.convertScaleAbs(img, alpha=alpha, beta=0)

def blur_image(img, k):
    if k % 2 == 0: k += 1
    return cv2.GaussianBlur(img, (k, k), 0)

def denoise_median(img, k):
    if k % 2 == 0: k += 1
    return cv2.medianBlur(img, k)

def sharpen(img):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)

def apply_sepia(img):
    # Sepia matrix (standard photo transformation)
    kernel = np.array([[0.272, 0.534, 0.131],
                       [0.349, 0.686, 0.168],
                       [0.393, 0.769, 0.189]])
    sepia = cv2.transform(img, kernel)
    sepia = np.clip(sepia, 0, 255) # Ensure values stay in valid range
    return sepia.astype(np.uint8)

def apply_edges(img, low, high):
    gray = to_grayscale(img)
    edges = cv2.Canny(gray, low, high)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

def get_image_bytes(img, format_choice):
    buf = io.BytesIO()
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
    pil_img = Image.fromarray(rgb_img)
    format_map = {"PNG": "PNG", "JPG": "JPEG", "TIFF": "TIFF", "PDF": "PDF"}
    if format_choice in ["JPG", "PDF"] and pil_img.mode == 'RGBA':
        pil_img = pil_img.convert('RGB')
    pil_img.save(buf, format=format_map[format_choice])
    return buf.getvalue()

def apply_pipeline(img, cfg):
    temp = img.copy()
    
    # 1. Cleaning / Denoising
    if cfg['denoise']: temp = denoise_median(temp, cfg['v_denoise'])
    
    # 2. Color Transformations
    if cfg['gray']: temp = to_grayscale(temp)
    if cfg['sepia']: temp = apply_sepia(temp)
    if cfg['bright']: temp = adjust_brightness(temp, cfg['v_bright'])
    if cfg['contrast']: temp = adjust_contrast(temp, cfg['v_contrast'])
    
    # 3. Artistic/Structural Filters
    if cfg['blur']: temp = blur_image(temp, cfg['v_blur'])
    if cfg['sharpen']: temp = sharpen(temp)
    if cfg['edges']: temp = apply_edges(temp, cfg['v_edge_low'], cfg['v_edge_high'])
    
    # 4. Final Sizing
    if cfg['resize']:
        h, w = temp.shape[:2]
        nw, nh = max(1, int(w * (cfg['scale']/100))), max(1, int(h * (cfg['scale']/100)))
        methods = {"Bilinear": cv2.INTER_LINEAR, "Bicubic": cv2.INTER_CUBIC, 
                   "Area": cv2.INTER_AREA, "Lanczos": cv2.INTER_LANCZOS4}
        interp = methods.get(cfg['resample_method'], cv2.INTER_LANCZOS4)
        temp = cv2.resize(temp, (nw, nh), interpolation=interp)
    return temp

init_session()
st.title("✨ Pro Image Dashboard")

file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg", "tif", "tiff", "pdf"])
if file:
    if 'last_filename' not in st.session_state or st.session_state.last_filename != file.name:
        st.session_state.img_cv = load_file(file)
        st.session_state.processed = st.session_state.img_cv.copy()
        st.session_state.last_filename = file.name

if st.session_state.processed is not None:
    col_tools, col_main, col_export = st.columns([0.9, 2, 0.9], gap="medium")

    with col_tools:
        st.subheader("🛠️ Tools")
        
        with st.expander("✂️ Crop Tool"):
            enable_crop = st.checkbox("Enable Interactive Crop", value=False)
            aspect_choice = st.selectbox("Aspect Ratio", ["Free", "1:1", "16:9", "4:3"])
            aspect_dict = {"Free": None, "1:1": (1, 1), "16:9": (16, 9), "4:3": (4, 3)}

        with st.expander("🎨 Color & Style"):
            c_gray, c_sepia = st.checkbox("Grayscale"), st.checkbox("Sepia Tone")
            c_bright = st.checkbox("Brightness")
            v_bright = st.slider("Level", -100, 100, 0)
            c_contrast = st.checkbox("Contrast")
            v_contrast = st.slider("Multiplier", 0.5, 3.0, 1.0, 0.1)

        with st.expander("🌫️ Filters & Noise"):
            c_denoise = st.checkbox("Median Denoise")
            v_denoise = st.slider("Denoise Strength", 1, 15, 3, 2)
            c_blur, c_sharpen = st.checkbox("Gaussian Blur"), st.checkbox("Sharpening")
            v_blur = st.slider("Blur Intensity", 1, 25, 3, 2)
            
        with st.expander("🖋️ Edge Detection"):
            c_edges = st.checkbox("Canny Edges")
            v_edge_low = st.slider("Low Threshold", 0, 255, 100)
            v_edge_high = st.slider("High Threshold", 0, 255, 200)

        with st.expander("📐 Size & Resampling"):
            c_resize = st.checkbox("Enable Resizing")
            v_scale = st.slider("Scale %", 10, 300, 100)
            v_resample = st.selectbox("Algorithm", ["Bilinear", "Bicubic", "Area", "Lanczos"], index=3)

        config = {
            'gray':c_gray, 'sepia':c_sepia, 'bright':c_bright, 'v_bright':v_bright, 
            'contrast':c_contrast, 'v_contrast':v_contrast, 'blur':c_blur, 
            'v_blur':v_blur, 'sharpen':c_sharpen, 'denoise': c_denoise, 
            'v_denoise': v_denoise, 'edges': c_edges, 'v_edge_low': v_edge_low,
            'v_edge_high': v_edge_high, 'resize':c_resize, 'scale':v_scale, 
            'resample_method': v_resample
        }

    with col_main:
        st.subheader("🖼️ Workspace")
        img_base = st.session_state.processed
        img_input_pil = Image.fromarray(cv2.cvtColor(img_base, cv2.COLOR_BGR2RGB))
        
        if enable_crop:
            cropped_pil = st_cropper(img_input_pil, realtime_update=True, box_color='#FF0000', 
                                    aspect_ratio=aspect_dict[aspect_choice])
            active_img = cv2.cvtColor(np.array(cropped_pil), cv2.COLOR_RGB2BGR)
        else:
            st.image(img_input_pil, use_container_width=True)
            active_img = img_base

        final_processed = apply_pipeline(active_img, config)

    with col_tools:
        st.markdown("---")
        st.markdown("**🔍 Live Tool Preview**")
        ph, pw = final_processed.shape[:2]
        side_w = 300
        side_h = int(ph * (side_w / pw))
        preview_small = cv2.resize(final_processed, (side_w, side_h), interpolation=cv2.INTER_AREA)
        st.image(cv2.cvtColor(preview_small, cv2.COLOR_BGR2RGB), use_container_width=True)

        if st.button("🚀 Commit Edits", type="primary", use_container_width=True):
            st.session_state.processed = final_processed
            st.rerun()
        
        if st.button("🔄 Reset Original", use_container_width=True):
            st.session_state.processed = st.session_state.img_cv.copy()
            st.rerun()

    with col_export:
        st.subheader("📊 Export")
        if len(final_processed.shape) == 3:
            b, g, r = cv2.split(final_processed)
            rh, gh, bh = [cv2.calcHist([c],[0],None,[256],[0,256]) for c in [r, g, b]]
            st.line_chart(pd.DataFrame({"Red": rh.flatten(), "Green": gh.flatten(), "Blue": bh.flatten()}), color=["#FF0000", "#00FF00", "#0000FF"])
        
        st.write("---")
        fmt = st.radio("Format", ["PNG", "JPG", "TIFF", "PDF"], horizontal=True)
        st.download_button("🏆 Download Final", get_image_bytes(final_processed, fmt), f"output.{fmt.lower()}", type="primary")
        st.caption(f"Res: {final_processed.shape[1]}x{final_processed.shape[0]}")

else:
    st.info("👈 Upload an image to start!")