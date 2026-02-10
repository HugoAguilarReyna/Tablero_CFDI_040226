import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pymongo
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import json
import numpy as np
import hashlib
from streamlit_option_menu import option_menu # Import Option Menu
import textwrap # For dedenting HTML strings
import audit_module # Moved to top

# ============================================================================
# CONFIGURACIÓN DE SUBMENÚS PREMIUM
# ============================================================================
SUBMENU_CONFIG = {
    "Cuenta T": [
        {"label": "KPIs Operativos", "key": "kpis"},
        {"label": "Análisis Estructural", "key": "estructural"},
        {"label": "Tendencias", "key": "tendencias"}
    ],
    "Materialidad / REPSE": [
        {"label": "Normativa", "key": "normativa"},
        {"label": "Documentos", "key": "documentos"},
        {"label": "Seguimiento", "key": "seguimiento"}
    ],
    "Riesgos": [
        {"label": "Detección de Anomalías", "key": "anomalias"},
        {"label": "Ranking de Riesgo", "key": "ranking"}
    ],
    "Compliance": [
        {"label": "Auditoría de Tasas", "key": "tasas"},
        {"label": "Integridad de Flujo", "key": "flujo"},
        {"label": "Saldos IVA", "key": "saldos_iva"},
        {"label": "Pagos Provisionales", "key": "pagos_provisionales"}
    ],
    "Configuración": [
        {"label": "General", "key": "general"},
        {"label": "Modelos AI", "key": "ai"}
    ]
}

# ... [imports and setup remain] ...

# --- Setup & Config (MUST BE FIRST) ---
st.set_page_config(
    page_title="INTELIGENCIA FORENSE CFDI",
    layout="wide",
    initial_sidebar_state="expanded" # Force expanded to ensure DOM presence for stealth buttons
)

# --- GLOBAL SETTINGS ---
st.markdown("""
<style>
    /* Global Settings - Sidebar handled by v10 Engine */
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'active_modules' not in st.session_state:
    st.session_state.active_modules = []
if 'company_id' not in st.session_state:
    st.session_state.company_id = "comp_default" 






# --- PhD / Cyberpunk UI Utilities ---
def render_futuristic_header():
    # Load theme variables
    theme_css = ""
    theme_path = os.path.join(os.path.dirname(__file__), "theme-variables.css")
    if os.path.exists(theme_path):
        with open(theme_path, "r") as f:
            theme_css = f.read()

    # Inject Theme Variables First
    if theme_css:
        st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

    # Inject Static CSS & JS (No f-string, so no double braces needed)
    st.markdown("""
    <style>
    /* 1. Global Reset & Theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-primary);
        font-family: var(--font-sans);
    }

    /* 4. Hide Native Streamlit Elements */
    header, [data-testid="stHeader"], [data-testid="stDecoration"] {
        display: none !important;
    }
    
    /* Hide the native sidebar completely */
    /* Hide the native sidebar safely (Strategy A) */
    [data-testid="stSidebar"] {
        opacity: 0 !important;
        z-index: -1000 !important;
        pointer-events: none !important;
    }
    
    /* Strategy C: Hide Native Footer */
    footer {
        visibility: hidden !important;
        height: 0px !important;
    }

    /* 5. Cyber-Grid Background */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    /* 6. Section Headers */
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        color: var(--color-primary);
        border-left: 4px solid var(--color-primary);
        padding-left: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
        letter-spacing: 1px;
        text-transform: uppercase;
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), transparent);
        padding-top: 5px;
        padding-bottom: 5px;
    }
    
    /* 7. Neon Title */
    .neon-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 5px;
        text-align: center;
        background: linear-gradient(90deg, var(--color-primary), var(--color-info), var(--color-primary));
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
        text-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
        margin-bottom: 25px;
    }
    
    @keyframes shine {
        to { background-position: 200% center; }
    }

    /* 8. Stat Elements */
    .stat-container {
        background: var(--glass-bg);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-xl);
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: var(--glass-shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stat-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--neon-glow);
        border-color: var(--color-primary);
    }
    .stat-label {
        font-family: var(--font-sans);
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 5px;
        font-weight: 500;
    }
    .stat-value {
        font-family: var(--font-sans);
        font-size: 26px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
        color: var(--text-primary);
    }
    .stat-delta {
        font-family: var(--font-sans);
        font-size: 12px;
        color: var(--color-success);
        font-weight: 600;
    }

    /* 9. Sticky Header Logic */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important;
        overflow: visible !important;
        transition: margin-left 0.3s ease; /* Smooth transition for content push */
    }

    div[data-testid="stVerticalBlock"]:has(#sticky-header-anchor) {
        position: static !important;
        overflow: visible !important;
        display: block !important;
    }

    div[data-testid="stVerticalBlock"] > div:has(#sticky-header-anchor) {
        position: sticky !important;
        top: 0px !important;
        z-index: 10000; /* Lower z-index than sidebar */
        background-color: #ffffff !important;
        padding-top: 15px;
        padding-bottom: 0px;
        border-bottom: 2px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        display: block !important;
        backdrop-filter: none !important;
    }
    
    iframe {
        z-index: 100001 !important;
        background: transparent !important;
    }
    
    /* Remove gaps between menu and content */
    hr {
        margin-top: 0px !important;
        border-color: var(--glass-border) !important;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--bg-hover);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--color-primary);
    }

    /* --- CUSTOM SIDEBAR CSS --- */
    /* Target the container we will use as sidebar */
    /* We use :not(:has(...)) to ensure we select the LEAF container (the sidebar itself) 
       and NOT the parent main container which also "has" the marker recursively. */
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) {
        position: fixed;
        top: 0;
        left: -320px; /* Hidden by default */
        width: 320px;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* PREMIUM PURPLE GRADIENT */
        border-right: 1px solid rgba(255,255,255,0.1);
        box-shadow: 4px 0 15px rgba(0,0,0,0.2);
        z-index: 999999;
        transition: left 0.3s ease;
        padding: 20px;
        padding-top: 60px; /* Space for top */
        overflow-y: visible !important; /* Forces clip fix for children */
        color: #FFFFFF !important; /* Force white text */
    }

    /* Force all text elements inside sidebar to be white */
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) p,
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) span,
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) label,
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) h1,
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) h2,
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) h3,
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])) div {
        color: #FFFFFF !important;
    }

    /* Open State Class (toggled via JS) */
    div[data-testid="stVerticalBlock"]:has(#filter-sidebar-marker):not(:has([data-testid="stVerticalBlock"])).sidebar-open {
        left: 0;
    }
    </style>

    """, unsafe_allow_html=True)

    # --- BOTÓN PREMIUM DE ÚLTIMA GENERACIÓN ---
    components.html("""
    <script>
        (function() {
            const doc = window.parent.document;
            const BTN_ID = 'sidebar-premium-btn';
            
            // 1. INYECTAR ESTILOS PARA ANIMACIONES Y ESTADOS
            if (!doc.getElementById('premium-btn-styles')) {
                const style = doc.createElement('style');
                style.id = 'premium-btn-styles';
                style.innerHTML = `
                    @keyframes premium-shine {
                        from { transform: translateX(-100%); }
                        to { transform: translateX(300%); }
                    }
                    .sidebar-premium-btn-active-state {
                        transform: scale(0.98) !important;
                    }
                    .ripple {
                        position: absolute;
                        border-radius: 50%;
                        background: rgba(255, 255, 255, 0.5);
                        transform: scale(0);
                        animation: ripple-animation 0.6s linear;
                        pointer-events: none;
                    }
                    @keyframes ripple-animation {
                        to { transform: scale(4); opacity: 0; }
                    }
                    .sidebar-premium-btn::after {
                        content: '';
                        position: absolute;
                        top: 0; left: 0; width: 60px; height: 2px;
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
                        animation: premium-shine 3s ease-in-out infinite;
                        pointer-events: none;
                    }
                    /* Rotación suave del icono en hover (manejado por JS para fallback) */
                `;
                doc.head.appendChild(style);
            }

            function createBtn() {
                if (doc.getElementById(BTN_ID)) return;

                // Limpieza de versiones anteriores para asegurar unicidad
                ['floating-toggle-btn', 'sidebar-rescue-btn', 'sidebar-tab'].forEach(id => {
                    const el = doc.getElementById(id);
                    if (el) el.remove();
                });

                const btn = doc.createElement('div');
                btn.id = BTN_ID;
                btn.className = 'sidebar-premium-btn';
                
                // Estructura Interna (SVG + Label)
                btn.innerHTML = `
                    <div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; pointer-events:none;">
                        <svg class="icon-svg" viewBox="0 0 24 24" style="width:24px; height:24px; fill:none; stroke:white; stroke-width:2.5; stroke-linecap:round; margin-bottom:12px; transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
                            <line x1="3" y1="6" x2="21" y2="6"/>
                            <line x1="3" y1="12" x2="21" y2="12"/>
                            <line x1="3" y1="18" x2="21" y2="18"/>
                        </svg>
                        <span class="btn-label" style="font-family:'Inter', sans-serif; font-weight:700; font-size:11px; color:white; writing-mode:vertical-rl; text-transform:uppercase; letter-spacing:2px; text-shadow: 0 2px 8px rgba(0,0,0,0.3); transition: letter-spacing 0.3s ease;">FILTROS</span>
                    </div>
                `;

                // ESTILOS BASE (Glassmorphism & Gradients)
                Object.assign(btn.style, {
                    position: 'fixed',
                    top: '140px',
                    left: '0px',
                    width: '50px',
                    height: '140px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '0 16px 16px 0',
                    backdropFilter: 'blur(10px)',
                    WebkitBackdropFilter: 'blur(10px)',
                    boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4), 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                    zIndex: '9999999',
                    cursor: 'pointer',
                    transition: 'left 0.45s cubic-bezier(0.34, 1.56, 0.64, 1), width 0.3s ease, box-shadow 0.3s ease, transform 0.1s ease',
                    userSelect: 'none',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                });

                // MICROINTERACCIONES (Hover States)
                btn.onmouseenter = () => {
                    btn.style.width = '55px';
                    btn.style.boxShadow = '0 12px 48px rgba(102, 126, 234, 0.6), 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)';
                    const icon = btn.querySelector('.icon-svg');
                    const label = btn.querySelector('.btn-label');
                    if(icon) icon.style.transform = 'rotate(180deg) scale(1.1)';
                    if(label) label.style.letterSpacing = '3px';
                };
                
                btn.onmouseleave = () => {
                    btn.style.width = '50px';
                    btn.style.boxShadow = '0 8px 32px rgba(102, 126, 234, 0.4), 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.2)';
                    const icon = btn.querySelector('.icon-svg');
                    const label = btn.querySelector('.btn-label');
                    if(icon) icon.style.transform = 'rotate(0deg) scale(1)';
                    if(label) label.style.letterSpacing = '2px';
                };

                // LÓGICA DE CLIC (Ripple + Toggle + Vibrate)
                btn.onclick = function(e) {
                    // Feedback Háptico
                    if (navigator.vibrate) navigator.vibrate(10);

                    // Efecto Ripple
                    const ripple = doc.createElement('span');
                    ripple.className = 'ripple';
                    btn.appendChild(ripple);
                    const rect = btn.getBoundingClientRect();
                    const size = Math.max(rect.width, rect.height);
                    ripple.style.width = ripple.style.height = `${size}px`;
                    ripple.style.left = `${e.clientX - rect.left - size/2}px`;
                    ripple.style.top = `${e.clientY - rect.top - size/2}px`;
                    setTimeout(() => ripple.remove(), 600);

                    // Toggle del Sidebar
                    const marker = doc.getElementById('filter-sidebar-marker');
                    if (marker) {
                        const sidebar = marker.closest('[data-testid="stVerticalBlock"]');
                        const mainContent = doc.querySelector('.block-container');
                        if (sidebar) {
                            sidebar.classList.toggle('sidebar-open');
                            const isOpen = sidebar.classList.contains('sidebar-open');
                            btn.style.left = isOpen ? '320px' : '0px';
                            if (mainContent) {
                                mainContent.style.marginLeft = isOpen ? '320px' : '0';
                                mainContent.style.width = isOpen ? 'calc(100% - 320px)' : '100%';
                                mainContent.style.transition = 'margin-left 0.45s cubic-bezier(0.34, 1.56, 0.64, 1), width 0.45s cubic-bezier(0.34, 1.56, 0.64, 1)';
                            }
                        }
                    }
                };
                
                doc.body.appendChild(btn);
            }

            // MANTENIMIENTO DEL BOTÓN (Teleport Pattern)
            createBtn();
            setInterval(createBtn, 1000);
        })();
    </script>
    """, height=0, width=0)


# ... [Rest of Styles and Login Logic] ...

# --- Main App Logic (After Login) ---

# --- Data Visualization Functions ---
def plot_dark_histogram(df, x_col, y_col, color_col, title):
    fig = px.bar(df, x=x_col, y=y_col, color=color_col, 
                 color_discrete_sequence=['#7551FF', '#C084FC', '#667eea', '#764ba2', '#4318FF'], # Purple/Violet Palette
                 title=title)
    fig.update_layout(
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif', 'color': '#000000'}, # Black text
        xaxis=dict(showgrid=False, tickfont=dict(color='#000000')),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='#000000')),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(font=dict(color='#000000'))
    )
    return fig

# --- Data Loading ---
@st.cache_data(ttl=600)
def load_data(company_id):
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "cfdi_db")
    collection_name = os.getenv("COLLECTION_NAME", "gold_cfdi")
    
    df = pd.DataFrame()
    
    # Try MongoDB
    if mongo_uri:
        try:
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            db = client[db_name]
            collection = db[collection_name]
            # --- MANDATORY FILTER BY COMPANY ---
            data = list(collection.find({"company_id": company_id}))
            if data:
                df = pd.DataFrame(data)
                if '_id' in df.columns:
                    df = df.drop(columns=['_id'])
        except Exception as e:
            pass
    
    # Fallback to local JSON
    if df.empty:
        local_path = os.path.join(os.getenv("DATA_DIR", "./data"), "gold_cfdi_processed.json")
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:
            return None

    # Post-processing
    if not df.empty:
        # 1. Enforce Datetime
        if 'fecha_emision' in df.columns:
            # Bug Fix: Do NOT force numeric first, as it destroys ISO date strings.
            # 1. Try direct conversion (handles strings like "2026-01-15" and mixed types)
            df['fecha_emision_dt'] = pd.to_datetime(df['fecha_emision'], errors='coerce')
            
            # 2. If we have NaNs, they might be numeric timestamps (e.g. from Mongo export)
            if df['fecha_emision_dt'].isna().any():
                 # Try converting the original column to numeric, then to datetime
                 numeric_dates = pd.to_numeric(df['fecha_emision'], errors='coerce')
                 # Fill NaNs in the datetime column with the converted numeric timestamps
                 df['fecha_emision_dt'] = df['fecha_emision_dt'].fillna(pd.to_datetime(numeric_dates, unit='ms', errors='coerce'))
            
            df['fecha_emision'] = df['fecha_emision_dt']
            df = df.drop(columns=['fecha_emision_dt'])
            df = df.dropna(subset=['fecha_emision']) # Drop invalid dates
            
            df['month'] = df['fecha_emision'].dt.to_period('M').astype(str)
            df['year'] = df['fecha_emision'].dt.year
            df['week'] = df['fecha_emision'].dt.to_period('W').astype(str)
            df['ventas_netas_calc'] = (df['subtotal'] + df['calc_iva']) - (df['calc_retenciones'] + df['descuento'])

        # 2. Enforce Numeric Columns (Critical for Calculations)
        numeric_cols = ['subtotal', 'total', 'descuento', 'calc_iva', 'calc_ieps', 'calc_ret_isr', 'calc_ret_iva', 'calc_retenciones', 'calc_traslados']
        for col in numeric_cols:
            if col in df.columns:
                # Remove currency symbols if present
                if df[col].dtype == object:
                     df[col] = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0

        # 3. Data Integrity & Normalization (RFCs)
        # Ensure we have standard 'emisor_rfc' and 'receptor_rfc' columns
        
        # Check for common variations
        if 'rfc_emisor' in df.columns and 'emisor_rfc' not in df.columns:
            df['emisor_rfc'] = df['rfc_emisor']
        elif 'emisor' in df.columns and 'emisor_rfc' not in df.columns: # Sometimes 'emisor' holds the RFC
             df['emisor_rfc'] = df['emisor']

        if 'rfc_receptor' in df.columns and 'receptor_rfc' not in df.columns:
            df['receptor_rfc'] = df['rfc_receptor']
        elif 'receptor' in df.columns and 'receptor_rfc' not in df.columns:
             df['receptor_rfc'] = df['receptor']
             
        # Fill N/A for safety in str operations
        if 'emisor_rfc' not in df.columns: df['emisor_rfc'] = 'XAXX010101000'
        if 'receptor_rfc' not in df.columns: df['receptor_rfc'] = 'XAXX010101000'
        if 'emisor_nombre' not in df.columns: df['emisor_nombre'] = 'DESCONOCIDO'
        if 'receptor_nombre' not in df.columns: df['receptor_nombre'] = 'DESCONOCIDO'


    return df


@st.cache_data(ttl=600)
def load_conceptos():
    """Loads the concepts catalog for detailed invoice visualization."""
    path = os.path.join(os.getenv("DATA_DIR", "./data"), "cfdi_conceptos.csv")
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding='utf-8')
        except:
             try:
                 return pd.read_csv(path, encoding='latin-1')
             except:
                 return pd.DataFrame()
    return pd.DataFrame()

# --- Load Catalogs (Moved here for logic continuity) ---
@st.cache_data(ttl=600)
def load_catalogs():
    """Loads Emisors and Receptors for the Audit Module."""
    data_dir = os.getenv("DATA_DIR", "./data")
    
    def load_safe(filename):
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            try: return pd.read_csv(path, encoding='utf-8')
            except: 
                try: return pd.read_csv(path, encoding='latin-1')
                except: return pd.DataFrame()
        return pd.DataFrame()

    df_emisors = load_safe("cfdi_emisors.csv")
    df_receptors = load_safe("cfdi_receptors.csv")
    return df_emisors, df_receptors

# --- SECURITY UTILS ---
SECRET_KEY = os.getenv("SECRET_KEY", "default-salt")

def hash_password(password):
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()

def check_login(cid, user, password):
    # --- MOCK CREDENTIALS FOR TESTING ---
    if cid == "TENANT_001":
        if user == "admin" and password == "admin123":
            return {
                "username": "admin", 
                "role": "admin", 
                "active_modules": ["kpis", "tendencias", "riesgos", "auditoria", "config"], 
                "company_id": "TENANT_001",
                "password_hash": "mock"
            }
        if user == "user01" and password == "user123":
             return {
                "username": "user01", 
                "role": "user", 
                "active_modules": ["kpis", "riesgos"], 
                "company_id": "TENANT_001",
                "password_hash": "mock"
            }

    client = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "cfdi_db")]
    users_col = db["users"]
    user_doc = users_col.find_one({"company_id": cid, "username": user})
    if user_doc and user_doc["password_hash"] == hash_password(password):
        user_doc["active_modules"] = user_doc.get("active_modules", [])
        return user_doc
    return None

# --- AUTHENTICATION FLOW ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Futuristic PhD Header
    st.markdown("""
        <div style="text-align: center; margin-top: 100px;">
            <h1 style="font-family: 'JetBrains Mono'; font-size: 50px; color: var(--color-primary); text-shadow: var(--neon-glow);">SECURE ACCESS</h1>
            <p style="color: var(--text-secondary);">RESTRICTED AREA // FORENSIC SYSTEM</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("login_form"):
            cid_input = st.text_input("ID EMPRESA")
            user_input = st.text_input("USUARIO")
            pass_input = st.text_input("CONTRASEÑA", type="password")
            submit = st.form_submit_button("INGRESAR AL SISTEMA")
            
            if submit:
                user_data = check_login(cid_input, user_input, pass_input)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.company_id = cid_input
                    st.session_state.username = user_input
                    st.session_state.active_modules = user_data.get("active_modules", [])
                    st.session_state.role = user_data.get("role", "user")
                    st.rerun()
                else:
                    st.error("Credenciales Inválidas o Error de Acceso.")
    st.stop() # Stop execution here if not authenticated

df_emisors, df_receptors = load_catalogs()

if st.session_state.authenticated:
    
    # --- INJECT CSS & ASSETS ---
    render_futuristic_header()

    # --- LOAD DATA ---
    df = load_data(st.session_state.company_id)
    df_conceptos = load_conceptos()

    if df is not None and not df.empty:
        # --- ENRICHMENT: JOIN WITH CATALOGS ---
        # Fix missing Receptor RFC by joining with catalog
        if 'receptor_id' in df.columns and not df_receptors.empty:
            # Prepare receptor catalog for merge
            cat_rec = df_receptors[['id', 'rfc']].rename(columns={'id': 'receptor_id', 'rfc': 'catalog_receptor_rfc'})
            # Merge
            df = df.merge(cat_rec, on='receptor_id', how='left')
            # Fill receptor_rfc if it was missing or generic
            if 'receptor_rfc' in df.columns:
                 df['receptor_rfc'] = df['catalog_receptor_rfc'].fillna(df['receptor_rfc'])
            else:
                 df['receptor_rfc'] = df['catalog_receptor_rfc']
            
            # Clean up temporary column
            df = df.drop(columns=['catalog_receptor_rfc'], errors='ignore')
            
            # Ensure no NaNs remain after merge (fallback to generic if catalog also fails)
            df['receptor_rfc'] = df['receptor_rfc'].fillna(df['receptor'].fillna('XAXX010101000') if 'receptor' in df.columns else 'XAXX010101000')

        # --- ENRICHMENT: MAP CONCEPTS TO UUID ---
        # The concepts loaded from CSV use 'cfdi_id' which links to 'id' in gold_cfdi.
        # But audit_module expects 'uuid' in concepts. We must map it.
        if not df_conceptos.empty and 'cfdi_id' in df_conceptos.columns and 'id' in df.columns:
            # Create mapping: id -> uuid
            mapping = df[['id', 'uuid']].drop_duplicates().astype(str) # Ensure string types for matching
            
            # Ensure proper types for merge keys
            df_conceptos['cfdi_id'] = df_conceptos['cfdi_id'].astype(str)
            
            # Merge to add uuid to concepts
            df_conceptos = df_conceptos.merge(
                mapping, 
                left_on='cfdi_id', 
                right_on='id', 
                how='left'
            )
            # Cleanup
            df_conceptos = df_conceptos.drop(columns=['id'], errors='ignore')


    if df is None:
        st.error("SISTEMA OFFLINE: FUENTE DE DATOS INACCESIBLE.")
        st.stop()

    # --- CUSTOM FILTER SIDEBAR ---
    # This container is targeted by CSS to become the sidebar
    with st.container():
        st.markdown('<div id="filter-sidebar-marker"></div>', unsafe_allow_html=True)
        # Tab removed - handled by JS Teleport Pattern
        
        st.markdown("### FILTROS")
        st.markdown("---")
        
        # --- FILTERS CONTENT ---
        if 'tipo' in df.columns:
            tipo_opts = df['tipo'].unique()
            selected_tipo = st.multiselect("Tipo Comprobante", tipo_opts, default=tipo_opts)
        else:
            selected_tipo = []

        st.markdown("---")
        
        time_agg_map = {"DIARIO": "D", "SEMANAL": "W", "MENSUAL": "M"}
        time_agg_label = st.radio("Agrupación Temporal", options=list(time_agg_map.keys()), index=0) 
        time_agg_code = time_agg_map[time_agg_label]
        
        st.markdown("---")
        
        # Date Range Filter
        if not df.empty and 'fecha_emision' in df.columns:
            min_date = df['fecha_emision'].min().date()
            max_date = df['fecha_emision'].max().date()
            date_range = st.date_input("Rango de Fechas", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        else:
            date_range = []

    # --- APPLY FILTERS ---
    # Default mask (all true)
    mask = pd.Series([True] * len(df))
    
    if selected_tipo:
        mask = mask & (df['tipo'].isin(selected_tipo))
        
    # Apply Date Filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = mask & (df['fecha_emision'].dt.date >= start_date) & (df['fecha_emision'].dt.date <= end_date)
        
    df_filtered = df.loc[mask]


    # --- FIXED HEADER WRAPPER ---
    # Container for sticky header
    # --- FIXED HEADER WRAPPER (Now handled by render_premium_navbar) ---
    with st.container():
        st.markdown('<span id="sticky-header-anchor"></span>', unsafe_allow_html=True)
        # Title and Menu superseded by Unified Navbar
        pass



# ============================================================================
# FUNCIÓN DE RENDERIZADO PREMIUM
# ============================================================================

# ============================================================================
# FUNCIÓN DE RENDERIZADO PREMIUM V2 (FIXED: st.markdown Injection)
# ============================================================================
# ============================================================================
# UNIFIED PREMIUM NAVBAR (Mega-Menu Style)
def render_premium_navbar():
    """
    Linear-Inspired Premium Navbar (v7.5 - Offscreen Interactive Sidebar)
    - Navegación estable sin recargas (Preserva st.session_state)
    - Portal de botones en st.sidebar para proteger el layout principal (evita el "white box")
    - CSS Offscreen (position: fixed; left: -100vw; opacity: 0) en lugar de display: none
    - Fix definitivo para "Blank Screen" y botones no clickeables
    """
    import urllib.parse
    import unicodedata
    import textwrap

    # Helper para normalizar acentos y strings
    def clean_str(val):
        if not val: return ""
        if isinstance(val, list): val = val[0]
        s = urllib.parse.unquote(str(val)).strip().lower()
        return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

    # Get state
    params = st.query_params
    current_nav_norm = clean_str(params.get("nav", "Cuenta T"))
    current_sub_norm = clean_str(params.get("subtab", ""))

    # ============================================================================
    # V9.0 SESSION SAFE NAVIGATION (STEALTH FOOTER STRATEGY)
    # ============================================================================
    # 1. CSS: HIDE SIDEBAR WITHOUT DESTROYING IT
    # We use visibility: hidden so buttons exist in DOM but are invisible.
    st.markdown("""
    <style>
        /* v9.2 FIX: NUCLEAR SIDEBAR COLLAPSE */
        
        /* 1. OFFSCREEN & INVISIBLE */
        section[data-testid="stSidebar"], 
        div[data-testid="stSidebarNav"] {
            position: fixed !important;
            left: -100vw !important;
            top: 0 !important;
            height: 100vh !important;
            width: 300px !important; 
            visibility: visible !important; 
            opacity: 0 !important;
            z-index: -9999 !important;
            pointer-events: none !important;
            transition: none !important;
            transform: translateX(-100%);
        }
        
        /* 2. ENABLE CLICKS ON INTERNAL BUTTONS */
        section[data-testid="stSidebar"] button,
        section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            pointer-events: auto !important;
            cursor: pointer !important;
            position: relative !important;
            z-index: 10000 !important; /* Attempt to surface clicks? No, parent is offscreen */
        }

        /* 3. HIDE CONTROL ELEMENTS */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarUserContent"] {
            display: none !important;
        }
        
        /* 4. FORCE MAIN CONTENT TO IGNORE SIDEBAR */
        div[data-testid="stAppViewContainer"] {
            margin-left: 0 !important;
            width: 100vw !important;
        }
        
        .main .block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 2. RENDER ACTIVE KEYS LOGIC
    active_module_key = "Cuenta T"
    for k in SUBMENU_CONFIG.keys():
        if clean_str(k) == current_nav_norm:
            active_module_key = k
            break
            
    active_sub_key = ""
    if active_module_key in SUBMENU_CONFIG:
        subitems = SUBMENU_CONFIG[active_module_key]
        if subitems:
            active_sub_key = subitems[0]['key']
            for sit in subitems:
                if clean_str(sit['key']) == current_sub_norm:
                    active_sub_key = sit['key']
                    break

    # 3. BUILD HTML (VISUAL NAVBAR)
    nav_items_html = ""
    for module_name, subitems in SUBMENU_CONFIG.items():
        is_mod_active = (module_name == active_module_key)
        mod_class = "active" if is_mod_active else ""
        
        dropdown_html = ""
        if subitems:
            dropdown_html = '<div class="linear-dropdown">'
            for item in subitems:
                is_s_active = (is_mod_active and item['key'] == active_sub_key)
                s_class = "active" if is_s_active else ""
                
                # V9.0: Target Key for JS Bridge
                raw_key = f"nav_{module_name}_{item['key']}"
                
                # HTML attributes
                dropdown_html += f'<div class="linear-dropdown-item dropdown-item {s_class}" data-button-key="{raw_key}">{item["label"]}</div>'
            dropdown_html += '</div>'
        
        # Main item data attributes
        raw_main_key = f"nav_{module_name}_main"
        
        # HTML Item
        item_html = textwrap.dedent(f"""
        <div class="linear-nav-item-wrapper {mod_class}">
            <div class="linear-nav-item nav-item" data-button-key="{raw_main_key}">{module_name}</div>
            {dropdown_html}
        </div>
        """)
        nav_items_html += item_html


    # 4. CSS FOR NAVBAR (UNCHANGED)
    navbar_style = textwrap.dedent(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* HIDE NATIVE ELEMENTS */
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {{
        display: none !important;
    }}
    
    /* CONTENT ADJUST - FORCE FULL WIDTH */
    div[data-testid="stAppViewContainer"] > .main > .block-container {{
        padding-top: 80px !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
    }}

    /* NAVBAR STYLES (v15.1 FIXED & FLATTENED) */
    .linear-navbar {{
        position: fixed !important;
        top: 0 !important; bottom: auto !important; left: 0 !important; right: 0 !important;
        height: 60px !important; /* Standard Height */
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 4px 30px rgba(0,0,0,0.3) !important; /* Shadow Down */
        border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-top: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important; /* RIGHT ALIGNMENT (Logo Left, Menu Right) */
        padding: 0 20px !important; /* Standard Padding */
        z-index: 999999999 !important;
        font-family: 'Inter', sans-serif !important;
        overflow: visible !important;
    }}

    .linear-logo {{
        font-size: 20px;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: 1px;
        margin-right: 16px; /* Tight Gap */
        cursor: pointer;
    }}
    .linear-nav-menu {{
        display: flex;
        align-items: center;
        gap: 8px;
        height: 100%;
        overflow: visible !important;
    }}

    .linear-nav-item-wrapper {{
        position: relative;
        height: 100%;
        display: flex;
        align-items: center;
        overflow: visible !important;
    }}

    .linear-nav-item {{
        padding: 0 16px;
        height: 40px;
        display: flex;
        align-items: center;
        color: rgba(255, 255, 255, 0.82) !important;
        font-size: 14px;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .linear-nav-item:hover, .linear-nav-item-wrapper.active .linear-nav-item {{
        background: rgba(255, 255, 255, 0.12) !important;
        color: #FFFFFF !important;
    }}

    .linear-dropdown {{
        display: none;
        position: absolute;
        top: 60px; /* Open Downwards */
        bottom: auto; 
        left: 0;
        min-width: 220px;
        background: linear-gradient(160deg, rgba(102, 126, 234, 0.98), rgba(118, 75, 162, 0.98)) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px;
        padding: 8px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        z-index: 999999999 !important;
    }}

    .linear-nav-item-wrapper:hover .linear-dropdown {{
        display: block !important;
    }}

    .linear-dropdown-item {{
        padding: 12px 16px;
        color: rgba(255, 255, 255, 0.75) !important;
        font-size: 13px;
        font-weight: 500;
        border-radius: 6px;
        cursor: pointer;
    }}

    .linear-dropdown-item:hover, .linear-dropdown-item.active {{
        background: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
    }}
    </style>
    """)

    # 5. RENDER HTML (FLATTENED TO AVOID MARKDOWN CODE BLOCK ARTIFACTS)
    navbar_html = f'<div class="linear-navbar"><div class="linear-logo" data-button-key="nav_Cuenta T_main">KONIA</div><div class="linear-nav-menu">{nav_items_html}</div></div>'
    
    st.markdown(navbar_style, unsafe_allow_html=True)
    st.markdown(navbar_html, unsafe_allow_html=True)

    # 6. INJECT JS BRIDGE
    # Note: The JS Bridge is now injected via components.html in the Footer Function
    # to ensure it loads AFTER the ghost buttons are ready.
    
    return active_module_key, active_sub_key

# ============================================================================
# 3. FUNCIÓN DE BOTONES FANTASMA (SOLUCIÓN v10: OFF-SCREEN SIDEBAR)
# ============================================================================
def render_footer_ghost_buttons(active_mod, active_sub):
    """
    Renders the ACTUAL Streamlit buttons inside the sidebar.
    Estrategia v10: 'Off-Screen Persistence'.
    En lugar de 'display: none' (que mata el evento clic), movemos el sidebar
    a coordenadas negativas (-9999px). Esto mantiene los botones interactivos
    para el JS pero visualmente inexistentes para el usuario.
    """
    import streamlit.components.v1 as components
    
    # 1. CSS BLINDADO (Transform + Recursive Transp + Min-Width)
    st.markdown("""
    <style>
        /* 1. OFF-SCREEN & TRANSFORM */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
            position: fixed !important;
            left: -5000px !important;
            transform: translateX(-5000px) !important; /* Doble seguridad */
            
            width: 1px !important;
            min-width: 0px !important;
            max-width: 1px !important;
            height: 100vh !important;
            
            z-index: -9999 !important;
            opacity: 0 !important;
            transition: none !important;
            
            background-color: transparent !important;
            background: transparent !important;
            pointer-events: none !important; /* Contenedor ignora mouse */
        }

        /* 2. REGLA MAESTRA (Vantablack): Todo invisible dentro */
        [data-testid="stSidebar"] * {
             color: transparent !important;
             background-color: transparent !important;
             background: transparent !important;
             border-color: transparent !important;
             opacity: 0 !important;
             box-shadow: none !important;
             text-shadow: none !important;
        }
        
        /* 3. LAYOUT FIX: Main content full width & TOP PADDING RESTORED */
        [data-testid="stSidebar"] + section.main, 
        div[data-testid="stAppViewContainer"] {
            margin-left: 0px !important;
            width: 100vw !important;
        }
        
        [data-testid="block-container"], .block-container {
            padding-top: 90px !important; /* RESTORED TOP PADDING */
            padding-bottom: 0px !important;
            max-width: 100% !important;
            background-color: transparent !important; /* USER REQUESTED TRANSPARENCY */
            background: transparent !important;
        }
        
        /* 4. BOTONES RESPONSIVOS (Estrategia v10.7: Zero-G Absolute Stack) */
        /* 4. BOTONES RESPONSIVOS (Estrategia v10.8: Nuclear Specificity) */
        section[data-testid="stSidebar"] button, 
        section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            pointer-events: auto !important;
            display: block !important;
            
            /* FORCED 0x0 LAYOUT */
            position: absolute !important;
            top: 0px !important;
            left: 0px !important;
            transform: translate(0,0) !important;
            margin: 0px !important;
            padding: 0px !important;
            
            width: 1px !important;
            height: 1px !important;
            
            /* INVISIBILITY */
            opacity: 0 !important;
            color: transparent !important;
            background: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            z-index: 99999 !important;
        }
        
        /* 5. UI CLEANUP */
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # 2. RENDERIZADO DE BOTONES (Dentro del sidebar técnico)
    with st.sidebar:
        # Helper para normalizar llaves
        def normalize_key(k):
             return k.replace(" ", "_").lower()

        for module_name, subitems in SUBMENU_CONFIG.items():
            # 2A. Generar Botón Padre (Main) - FIX v11
            # Incluso si tiene hijos, el padre necesita un botón fantasma para redirigir
            # Logica: Si hago clic en "Dashboard", me lleva a "Dashboard > KPIs"
            
            main_raw_key = f"nav_{module_name}_main"
            main_btn_key = normalize_key(main_raw_key)
            
            if st.button(main_raw_key, key=f"footer_{main_btn_key}"):
                st.query_params["nav"] = module_name
                # Si tiene subitems, default al primero. Si no, limpia subtab.
                if subitems:
                     st.query_params["subtab"] = subitems[0]['key']
                else:
                     if "subtab" in st.query_params: del st.query_params["subtab"]
                st.rerun()

            # 2B. Generar Botones Hijos (Submenús)
            if subitems:
                for item in subitems:
                    raw_key = f"nav_{module_name}_{item['key']}"
                    button_key = normalize_key(raw_key) 
                    
                    if st.button(raw_key, key=f"footer_{button_key}"):
                        st.query_params["nav"] = module_name
                        st.query_params["subtab"] = item['key']
                        st.rerun()
    
    # 3. PUENTE JAVASCRIPT (CLICKER v11 - REGEX FIXED)
    components.html("""
    <script>
    (function() {
        const doc = window.parent.document;
        const SCRIPT_ID = 'nav-engine-v11-0';
        
        if (doc.getElementById(SCRIPT_ID)) return;
        
        const script = doc.createElement('script');
        script.id = SCRIPT_ID;
        script.textContent = `
            (function() {
                console.log("🚀 Nav Engine v11.0: Regex Fixed & Parent Links");
                const parentDoc = document;

                // A. THE ENFORCER: Vigilancia constante
                setInterval(() => {
                    const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
                    if (sidebar) {
                         // 1. SIDEBAR BULK HIDE
                         sidebar.style.setProperty('position', 'fixed', 'important');
                         sidebar.style.setProperty('left', '-9999px', 'important'); 
                         sidebar.style.setProperty('width', '0px', 'important');
                         sidebar.style.setProperty('opacity', '0', 'important');
                         sidebar.style.setProperty('z-index', '-9999', 'important');
                         sidebar.style.setProperty('pointer-events', 'none', 'important');

                         // 2. BUTTON BULLY (Force 0x0 absolute on children)
                         const buttons = sidebar.querySelectorAll('button');
                         buttons.forEach(btn => {
                             btn.style.setProperty('position', 'absolute', 'important');
                             btn.style.setProperty('top', '0px', 'important');
                             btn.style.setProperty('left', '0px', 'important');
                             btn.style.setProperty('width', '0px', 'important');
                             btn.style.setProperty('height', '0px', 'important');
                             btn.style.setProperty('margin', '0px', 'important');
                             btn.style.setProperty('padding', '0px', 'important');
                             btn.style.setProperty('opacity', '0', 'important');
                             btn.style.setProperty('pointer-events', 'auto', 'important'); // Keep Clickable
                         });
                    }
                    
                    const main = parentDoc.querySelector('.main .block-container');
                    if(main) {
                        main.style.setProperty('max-width', '100%', 'important');
                        main.style.setProperty('margin-left', '0px', 'important');
                    }
                }, 500);

                function cleanText(str) {
                    // FIX v11: Quadruple backslash for literal whitespace matching
                    return str.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "")
                              .toLowerCase().replace(/\\\\s+/g, "_").trim();
                }

                function handleNavClick(e) {
                    // Detectar clic en el menú visual (HTML)
                    const target = e.target.closest('[data-button-key]');
                    if (target) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        const rawKey = target.getAttribute('data-button-key');
                        const searchKey = cleanText(rawKey);
                        console.log("🎯 Targets:", searchKey);

                        // Buscar el botón en el DOM (incluso si está fuera de pantalla)
                        const allButtons = Array.from(document.querySelectorAll('button'));
                        const ghostBtn = allButtons.find(btn => {
                            const btnText = cleanText(btn.innerText || btn.textContent);
                            return btnText.includes(searchKey);
                        });

                        if (ghostBtn) {
                            // Disparar clic nativo
                            console.log("✅ Click Sent");
                            ghostBtn.style.setProperty('pointer-events', 'auto', 'important');
                            ghostBtn.click();
                        } else {
                            console.error("❌ Sync Error: Button not found for", searchKey);
                        }
                    }
                }

                document.body.removeEventListener('click', handleNavClick, true);
                document.body.addEventListener('click', handleNavClick, true);
            })();
        `;
        doc.body.appendChild(script);
    })();
    </script>
    """, height=0)

# --- EXECUTE NAVIGATION ---
selected_module, selected_subtab = render_premium_navbar()



# Validar cambio de módulo para resetear subtab si fuera necesario
if selected_module in SUBMENU_CONFIG and not selected_subtab:
    selected_subtab = SUBMENU_CONFIG[selected_module][0]["key"]

st.markdown("---")



# --- METRIC HELPER ---
# --- NEW METRIC HELPER (PhD Style) ---
# --- NEW METRIC HELPER (Clean Design) ---



def render_stat_element(label, value, sub_label, color="var(--text-primary)"):
    st.markdown(f"""
        <div class="stat-container">
            <div class="stat-label">{label}</div>
            <div class="stat-value" style="color: {color};">{value}</div>
            <div class="stat-delta">↑ {sub_label}</div>
        </div>
    """, unsafe_allow_html=True)

def render_quantum_kpis(q1, q2, q3, q4, q5):
    """
    Renders the Quantum KPI Strip (Q1-Q5) with Crystal Prism aesthetics.
    """
    st.markdown("""
        <style>
        .quantum-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 30px;
            width: 100%;
        }
        .quantum-card {
            flex: 1;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px 15px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 120px;
        }
        .quantum-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 30px rgba(118, 75, 162, 0.25);
            border-color: #764ba2;
        }
        .quantum-card::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: height 0.3s ease;
        }
        .quantum-card:hover::after {
            height: 6px;
        }
        .quantum-label {
            text-transform: uppercase;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1.2px;
            color: #A3AED0;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
        }
        .quantum-value {
            color: #2B3674;
            font-family: 'DM Sans', sans-serif;
            font-size: 24px;
            font-weight: 700;
            line-height: 1.2;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="quantum-container">
            <div class="quantum-card">
                <div class="quantum-label">Q1 (UMBRAL 20%)</div>
                <div class="quantum-value">${q1:,.2f}</div>
            </div>
            <div class="quantum-card">
                <div class="quantum-label">Q2 (UMBRAL 40%)</div>
                <div class="quantum-value">${q2:,.2f}</div>
            </div>
            <div class="quantum-card">
                <div class="quantum-label">Q3 (UMBRAL 60%)</div>
                <div class="quantum-value">${q3:,.2f}</div>
            </div>
            <div class="quantum-card">
                <div class="quantum-label">Q4 (UMBRAL 80%)</div>
                <div class="quantum-value">${q4:,.2f}</div>
            </div>
            <div class="quantum-card" style="border-color: #2b367422;">
                <div class="quantum-label" style="color: #7551FF;">Q5 (UMBRAL 100%)</div>
                <div class="quantum-value" style="color: #7551FF;">${q5:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- METRIC HELPER (Legacy) ---
def render_custom_metric(label, value, prefix="", suffix="", delta="", delta_color="normal"):
    color = "#00f2ff" if delta_color == "normal" else "#ff4b4b"
    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <div style="font-size: 12px; color: #888; margin-bottom: 5px;">{label}</div>
        <div style="font-size: 36px; font-weight: bold; color: white;">
            {prefix}{value}{suffix}
        </div>
        <div style="font-size: 12px; color: {color};">
            {'↑' if delta_color == 'normal' else '↓'} {delta}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- INVOICE RENDER GENERATOR (HTML) ---
def render_invoice_html(row, conceptos_df):
    """Generates a Corporate/PhD style HTML invoice."""
    
    # Safe getters
    def get_val(r, col, default=""): return r[col] if col in r else default
    
    uuid = get_val(row, 'uuid', 'N/A')
    folio = get_val(row, 'folio', 'N/A')
    fecha = get_val(row, 'fecha_emision', pd.Timestamp.now()).strftime('%Y-%m-%d %H:%M:%S')
    emisor = get_val(row, 'emisor_nombre', 'EMISOR DESCONOCIDO')
    rfc_emisor = get_val(row, 'emisor_rfc', 'N/A')
    receptor = get_val(row, 'receptor_nombre', 'RECEPTOR DESCONOCIDO')
    rfc_receptor = get_val(row, 'receptor_rfc', 'N/A')
    
    total = f"${row.get('total', 0):,.2f}"
    subtotal = f"${row.get('subtotal', 0):,.2f}"
    iva = f"${row.get('calc_iva', 0):,.2f}"
    ret = f"${row.get('calc_retenciones', 0):,.2f}"
    desc = f"${row.get('descuento', 0):,.2f}"
    
    # Generate Rows
    rows_html = ""
    if not conceptos_df.empty:
        for _, c_row in conceptos_df.iterrows():
            desc_item = c_row.get('descripcion', 'Item')
            cant = c_row.get('cantidad', 1)
            unidad = c_row.get('clave_unidad', 'H87')
            pu = f"${c_row.get('valor_unitario', 0):,.2f}"
            imp = f"${c_row.get('importe', 0):,.2f}"
            
            rows_html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">{cant}</td>
                <td style="padding: 10px;">{unidad}</td>
                <td style="padding: 10px;">{desc_item}</td>
                <td style="padding: 10px; text-align: right;">{pu}</td>
                <td style="padding: 10px; text-align: right;">{imp}</td>
            </tr>
            """
    else:
        rows_html = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #888;">DETALLE DE CONCEPTOS NO DISPONIBLE</td></tr>'

    html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; background: white; color: #333; padding: 40px; border: 1px solid #e0e0e0; box-shadow: 0 0 20px rgba(0,0,0,0.1);">
        <!-- HEADER -->
        <table style="width: 100%; margin-bottom: 30px;">
            <tr>
                <td style="vertical-align: top; width: 50%;">
                    <h1 style="margin: 0; color: #002e6e; font-size: 24px; text-transform: uppercase; letter-spacing: 1px;">FACTURA</h1>
                    <p style="margin: 5px 0 0; color: #666; font-size: 12px;">UUID: {uuid}</p>
                    <p style="margin: 0; color: #666; font-size: 12px;">FOLIO INTERNO: {folio}</p>
                </td>
                <td style="vertical-align: top; text-align: right;">
                    <h3 style="margin: 0; color: #333;">{emisor}</h3>
                    <p style="margin: 2px 0; color: #555; font-size: 12px;">RFC: {rfc_emisor}</p>
                    <p style="margin: 2px 0; color: #888; font-size: 12px;">{fecha}</p>
                </td>
            </tr>
        </table>
        
        <hr style="border: 0; border-top: 2px solid #002e6e; margin-bottom: 30px;">
        
        <!-- INFO CLIENTE -->
        <div style="margin-bottom: 30px; background: #f9f9f9; padding: 15px; border-left: 4px solid #002e6e;">
            <p style="margin: 0 0 5px; font-weight: bold; font-size: 12px; color: #002e6e;">CLIENTE / RECEPTOR</p>
            <h4 style="margin: 0; font-size: 16px;">{receptor}</h4>
            <p style="margin: 2px 0 0; color: #555; font-size: 13px;">RFC: {rfc_receptor}</p>
        </div>
        
        <!-- TABLA CONCEPTOS -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px;">
            <thead style="background: #002e6e; color: white;">
                <tr>
                    <th style="padding: 12px; text-align: left;">CANT</th>
                    <th style="padding: 12px; text-align: left;">UNIDAD</th>
                    <th style="padding: 12px; text-align: left;">DESCRIPCIÓN</th>
                    <th style="padding: 12px; text-align: right;">P. UNITARIO</th>
                    <th style="padding: 12px; text-align: right;">IMPORTE</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        
        <!-- TOTALES -->
        <div style="display: flex; justify-content: flex-end;">
            <table style="width: 250px; border-collapse: collapse; font-size: 14px;">
                <tr>
                    <td style="padding: 8px; color: #666; text-align: right;">SUBTOTAL</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold;">{subtotal}</td>
                </tr>
                 <tr>
                    <td style="padding: 8px; color: #666; text-align: right;">DESCUENTO</td>
                    <td style="padding: 8px; text-align: right;">{desc}</td>
                </tr>
                 <tr>
                    <td style="padding: 8px; color: #666; text-align: right;">TRASLADOS (IVA)</td>
                    <td style="padding: 8px; text-align: right;">{iva}</td>
                </tr>
                 <tr>
                    <td style="padding: 8px; color: #666; text-align: right;">RETENCIONES</td>
                    <td style="padding: 8px; text-align: right; color: #ff0055;">{ret}</td>
                </tr>
                <tr style="border-top: 2px solid #333;">
                    <td style="padding: 12px; color: #002e6e; text-align: right; font-weight: bold; font-size: 16px;">TOTAL</td>
                    <td style="padding: 12px; text-align: right; font-weight: bold; font-size: 16px; color: #002e6e;">{total}</td>
                </tr>
            </table>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #888; font-size: 10px;">
            <p>Este documento es una representación impresa de un CFDI generada por Inteligencia Estratégica.</p>
        </div>
    </div>
    """
    return html

# --- Navigation Logic (Cleaned up redundant block) ---
# Previous mapping removed to avoid conflict
# tab_kpi is already defined above


# --- VIEW CONTROLLER ---
render_futuristic_header()
selected_module, selected_subtab = render_premium_navbar()

if selected_module == "Configuración":
    st.markdown('<div class="section-header">PERFIL DE USUARIO</div>', unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns([3, 1])
    with col_c1:
        st.success(f"🟢 SESIÓN ACTIVA: {st.session_state.username} | {st.session_state.company_id}")
        st.caption("Permisos: " + str(st.session_state.active_modules))
    
    with col_c2:
        if st.button("🔴 CERRAR SESIÓN", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
            
    st.divider()
    st.info("Configuración del sistema - Módulo en desarrollo")

elif selected_module == "Cuenta T":
    
    if selected_subtab == "kpis":
        # --- SECCIÓN 1: VOLUMETRÍA...



        # --- SECCIÓN 1: VOLUMETRÍA Y SECCIÓN 2: ESTADÍSTICA (MISMO NIVEL VISUAL) ---
        st.markdown("<div class='section-header'>Volumetría y Control Operativo</div>", unsafe_allow_html=True)

        # Robust filtering for 'Ingreso', 'I', 'egreso', 'E', etc.
        ing_mask = df_filtered['tipo'].astype(str).str.upper().str.startswith('I')
        egr_mask = df_filtered['tipo'].astype(str).str.upper().str.startswith('E')
        ing = df_filtered.loc[ing_mask, 'total'].sum()
        egr = df_filtered.loc[egr_mask, 'total'].sum()
        vol = len(df_filtered)
        avg = df_filtered['total'].mean() if vol > 0 else 0

        v1, v2, v3, v4 = st.columns(4)
        with v1: render_stat_element("Volumen CFDI", f"{vol:,}", "Total Transacciones", "var(--color-primary)")
        with v2: render_stat_element("Ingresos", f"${ing:,.2f}", "Net Inflow", "#059669")
        with v3: render_stat_element("Egresos", f"${egr:,.2f}", "Net Outflow", "#dc2626")
        with v4: render_stat_element("Balance", f"${ing - egr:,.2f}", "Net Liquidity", "var(--text-primary)")

        # LÍNEA DIVISORIA
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>Inteligencia Estadística y Distribución</div>", unsafe_allow_html=True)

        s1, s2, s3, s4 = st.columns(4)
        with s1: render_stat_element("Monto Máximo", f"${df_filtered['total'].max():,.2f}", "Peak Value")
        with s2: render_stat_element("Desviación Est.", f"${df_filtered['total'].std():,.2f}", "Sigma Variance")
        with s3: render_stat_element("Rango Operativo", f"${df_filtered['total'].max() - df_filtered['total'].min():,.2f}", "Full Spread")
        with s4: render_stat_element("Promedio", f"${avg:,.2f}", "Mean Density")

        # LÍNEA DIVISORIA
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

        # --- SECCIÓN: ANÁLISIS DE SEGMENTACIÓN POR QUINTILES (VERSIÓN ULTRA-IMPACT) ---
        st.markdown("<div class='section-header'>Segmentación y Concentración de Capital</div>", unsafe_allow_html=True)

        with st.container():
            if not df_filtered.empty:
                # 1. Cálculo de Quintiles
                q_vals = df_filtered['total'].quantile([0.2, 0.4, 0.6, 0.8, 1.0]).values
                
                # Renderizado de Tarjetas Quantum
                render_quantum_kpis(q_vals[0], q_vals[1], q_vals[2], q_vals[3], q_vals[4])

                # 3. Gráfico de Concentración
                df_q = df_filtered.copy() # Avoid modifying main df view
                df_q['quintil'] = pd.qcut(df_q['total'], 5, labels=['Q1 (Bajo)', 'Q2', 'Q3', 'Q4', 'Q5 (Alto)'], duplicates='drop')
                q_dist = df_q.groupby('quintil', observed=False)['total'].agg(['sum']).reset_index()
                
                if q_dist['sum'].sum() > 0:
                   q_dist['porcentaje'] = (q_dist['sum'] / q_dist['sum'].sum()) * 100
                else:
                   q_dist['porcentaje'] = 0

                fig_q = px.bar(
                    q_dist, x='quintil', y='sum',
                    text=q_dist['porcentaje'].apply(lambda x: f'{x:.1f}%'),
                    color='sum', template="plotly_white",
                    color_continuous_scale='Blues'
                )
                fig_q.update_layout(
                    height=400, 
                    showlegend=False, 
                    coloraxis_showscale=False,
                    title=dict(text="Distribución de Masa Monetaria por Quintil", font=dict(color="black")),
                    margin=dict(l=0, r=0, t=50, b=0), 
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(tickfont=dict(color='black')),
                    yaxis=dict(tickfont=dict(color='black')),
                    font=dict(color="black")
                )
                st.plotly_chart(fig_q, use_container_width=True)
                
            else:
                st.info("Sin datos suficientes para segmentación.")




    # --- SUB-TAB: STRUCTURAL ANALYSIS ---
    elif selected_subtab == "estructural":

        st.markdown('<div class="section-header">Desglose Categórico</div>', unsafe_allow_html=True)
        
        c_cat1, c_cat2 = st.columns(2)
        
        with c_cat1:
            if 'tipo' in df_filtered.columns:
                df_tipo = df_filtered.groupby('tipo', observed=False)['total'].sum().reset_index()
                # Updated N/P to dark grey for visibility on light background
                color_map = {'I': '#39d353', 'E': '#f85149', 'N': '#57606a', 'P': '#57606a'}
                fig_tipo = px.bar(
                    df_tipo, x='tipo', y='total', 
                    title="Ingresos vs Egresos",
                    text_auto='.2s',
                    color='tipo', 
                    color_discrete_map=color_map,
                    template="plotly_white"
                )
                fig_tipo.update_layout(
                    title=dict(font=dict(color='black')),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'family': 'JetBrains Mono', 'color': 'black'},
                    showlegend=False,
                    xaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
                    yaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black'))
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            else:
                st.warning("Campo 'tipo' no encontrado.")

        with c_cat2:
            cat_col = None
            title = ""
            if 'metodo_pago' in df_filtered.columns:
                cat_col = 'metodo_pago'
                title = "Método de Pago"
            elif 'uso_cfdi' in df_filtered.columns:
                cat_col = 'uso_cfdi'
                title = "Uso de CFDI"
            
            if cat_col:
                df_cat = df_filtered.groupby(cat_col, observed=False)['total'].sum().reset_index()
                fig_cat = px.pie(
                    df_cat, values='total', names=cat_col, 
                    title=title,
                    hole=0.4,
                    template="plotly_white",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_cat.update_layout(
                    title=dict(font=dict(color='black')),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'family': 'JetBrains Mono', 'color': 'black'},
                    legend=dict(font=dict(color='black'))
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("Detalle de Método de Pago no disponible en los datos.")

    # --- SUB-TAB: TRENDS ---
    elif selected_subtab == "tendencias":


        # --- DETAILED EXPLORER REMOVED (As requested) ---

        
        # --- SECCIÓN: ANÁLISIS DE CONCENTRACIÓN (TOP 10) ---
        st.markdown("<div class='section-header'>Análisis de Concentración: Top 10 Clientes</div>", unsafe_allow_html=True)

        entity_col = 'receptor_nombre' if 'receptor_nombre' in df_filtered.columns else 'receptor_id'
        if not df_filtered.empty:
            top10 = df_filtered.groupby(entity_col)['total'].sum().nlargest(10).reset_index()
            top10 = top10.sort_values('total', ascending=True) 

            # --- REEMPLAZO PREMIUM: TABLA INTELIGENTE EN LUGAR DE GRÁFICO BÁSICO ---
            # --- REEMPLAZO PREMIUM: TABLA HTML PERSONALIZADA (FONDO BLANCO, LETRAS NEGRAS) ---
            # Solicitud Usuario: "Cambiar color negro por blanco y letras en negro" para la "gráfica" (tabla con barras)
            
            html_rows = ""
            max_val = top10['total'].max()
            
            for _, row in top10.iterrows():
                name = row[entity_col]
                val = row['total']
                pct = (val / max_val) * 100 if max_val > 0 else 0
                
                # Removed indentation to prevent Markdown code block rendering
                html_rows += f"""<div style="display: flex; align-items: center; padding: 12px 15px; border-bottom: 1px solid #f0f0f0;">
    <div style="flex: 0 0 40%; font-weight: 600; font-size: 13px; color: #1a1a1a; padding-right: 20px; text-transform: uppercase;">{name}</div>
    <div style="flex: 1; display: flex; align-items: center;">
         <div style="flex-grow: 1; background-color: #f5f5f7; height: 8px; border-radius: 4px; overflow: hidden; margin-right: 15px;">
             <div style="width: {pct}%; background-color: #ff4b4b; height: 100%; border-radius: 4px;"></div>
         </div>
         <div style="min-width: 80px; text-align: right; font-weight: 700; font-size: 13px; color: #1a1a1a; font-family: 'JetBrains Mono', monospace;">${val:,.0f}</div>
    </div>
</div>"""
            
            st.markdown(f"""
<div style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; overflow: hidden; margin-top: 10px; margin-bottom: 30px;">
    <div style="background-color: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e1e4e8; display: flex; justify-content: space-between; align-items: center;">
        <div style="color: #1a1a1a; font-weight: 700; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">CLIENTE / RECEPTOR</div>
        <div style="color: #1a1a1a; font-weight: 700; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">VOLUMEN OPERADO</div>
    </div>
    {html_rows}
</div>
""", unsafe_allow_html=True)

        # --- MOVING TRENDS HERE AS REQUESTED (Area Chart + Waterfall) ---
        st.markdown("---")
        st.markdown('<div class="section-header">EVOLUCIÓN TEMPORAL</div>', unsafe_allow_html=True)
        
        # --- Gráfico 1: Dinámica Temporal OPTIMIZADO (¡Impactante!) ---
        if not df_filtered.empty:
            # Preparamos los datos semanalmente (o según filtro)
            time_agg_p = time_agg_code if 'time_agg_code' in locals() else 'W'
            df_w = df_filtered.set_index('fecha_emision').resample(time_agg_p)['total'].sum().reset_index()

            # Creamos la gráfica de área con mejoras visuales
            fig_area = px.area(
                df_w, 
                x='fecha_emision', 
                y='total', 
                template="plotly_white",
                title="Análisis del Capital Operado",
                labels={'fecha_emision': 'Periodo', 'total': 'Monto Total ($)'}
            )

            # Refinamiento visual avanzado
            fig_area.update_traces(
                mode='lines+markers+text',  # Líneas, marcadores y TEXTO en cada punto
                line_color='#58a6ff',      # Color de la línea (azul de la marca PhD)
                fillcolor='rgba(88, 166, 255, 0.15)', # Relleno con más opacidad
                marker=dict(size=8, color='#58a6ff', line=dict(width=2, color='#ffffff')), # Marcadores claros
                text=df_w['total'].apply(lambda x: f'${x/1000:,.0f}k'), # Texto con formato monetario sin decimales
                textposition="top center", # Posición del texto encima de los puntos
                textfont=dict(size=12, color='black') # Estilo del texto
            )

            fig_area.update_layout(
                height=550, # Aumentamos un poco más la altura para mayor impacto
                margin=dict(l=0, r=0, t=50, b=0), # Ajustamos márgenes
                hovermode="x unified", # Hover que unifica información en el eje X
                xaxis_title=None, # Quitamos título del eje X, ya está en el subtítulo
                yaxis_title=None, # Quitamos título del eje Y, ya está en el subtítulo
                xaxis=dict(
                    showgrid=False, # Eliminamos cuadrícula para un look más limpio
                    tickfont=dict(size=10, color='black'),
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(0,0,0,0.1)', # Color de la cuadrícula más tenue
                    tickfont=dict(size=10, color='black')
                ),
                plot_bgcolor='rgba(0,0,0,0)', # Fondo transparente
                paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente del papel
                title=dict(
                    font=dict(size=24, color='black', family='Inter, sans-serif'), # Título más grande
                    x=0.01 # Posición del título
                )
            )

            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.info("Sin datos temporales.")
        
        st.markdown('<div class="section-header">CASCADA FINANCIERA</div>', unsafe_allow_html=True)
        
        sums = df_filtered[['ventas_brutas', 'calc_traslados', 'calc_retenciones', 'descuento', 'ventas_netas_calc']].sum()
        
        fig_water = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "total"],
            x = ["BRUTO", "+ IMPUESTOS", "- RETENCIONES", "- DESCUENTOS", "NETO"],
            textposition = "outside",
            # Use safe access to sums
            text = [f"${x/1000:.1f}k" for x in [sums.get('ventas_brutas',0), sums.get('calc_traslados',0), -sums.get('calc_retenciones',0), -sums.get('descuento',0), sums.get('ventas_netas_calc',0)]],
            y = [sums.get('ventas_brutas',0), sums.get('calc_traslados',0), -sums.get('calc_retenciones',0), -sums.get('descuento',0), sums.get('ventas_netas_calc',0)],
            connector = {"line":{"color":"#333"}},
            decreasing = {"marker":{"color":"#ff4b4b"}},
            increasing = {"marker":{"color":"#00f2ff"}},
            totals = {"marker":{"color":"#0047ab"}}
        ))
        fig_water.update_layout(
            title=dict(text="DESGLOSE DE FLUJO DE EFECTIVO", font=dict(color="black")),
            template='plotly_white', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
            font={'family': 'JetBrains Mono', 'color': 'black'}, showlegend=False,
            xaxis=dict(tickfont=dict(color='black')),
            yaxis=dict(tickfont=dict(color='black'))
        )
        st.plotly_chart(fig_water, use_container_width=True)




# --- VIEW: RISK CENTER ---
elif selected_module == "Riesgos":
    st.markdown('<div class="section-header">INTELIGENCIA FISCAL 2026: ESTRATEGIA FISCAL PRESCRIPTIVA</div>', unsafe_allow_html=True)
    
    if df_filtered.empty:
        st.warning("SISTEMA SIN DATOS: No hay registros disponibles para el análisis de riesgos con los filtros actuales.")
    else:
        # --- PHASE 2: RISK SCORING LOGIC ---
        def calculate_risk_scores(df_raw):
            # Group by Supplier
            risk_df = df_raw.copy()
            risk_df['is_round'] = (risk_df['total'] > 0) & (risk_df['total'] % 100 == 0)
            risk_df['is_atypical'] = risk_df['fecha_emision'].dt.hour >= 22
            risk_df['is_weekend'] = risk_df['fecha_emision'].dt.dayofweek >= 5
            
            agg = risk_df.groupby('emisor_nombre').agg({
                'total': ['count', 'sum', 'std', 'mean'],
                'is_round': 'sum',
                'is_atypical': 'sum',
                'is_weekend': 'sum'
            })
            agg.columns = ['count', 'total_sum', 'std', 'mean', 'round_count', 'atypical_count', 'weekend_count']
            
            # Risk Penalties
            agg['pct_round'] = (agg['round_count'] / agg['count']) * 100
            agg['pct_atypical'] = (agg['atypical_count'] / agg['count']) * 100
            agg['pct_weekend'] = (agg['weekend_count'] / agg['count']) * 100
            agg['cv'] = (agg['std'] / agg['mean']).fillna(0) # Coeff variation
            
            # Score (0-100)
            agg['risk_score'] = (agg['pct_round'] * 0.4 + agg['pct_atypical'] * 0.2 + agg['pct_weekend'] * 0.2 + (agg['cv'] > 1.5).astype(int) * 20)
            return agg.sort_values('risk_score', ascending=False)

        if selected_subtab == "anomalias":

            # 1. TRACEABILITY SANKEY DIAGRAM (MATERIALITY)
            st.markdown('<div class="section-header">DIAGRAMA DE TRAZABILIDAD (MATERIALIDAD)</div>', unsafe_allow_html=True)
            st.caption("Detecta la materialidad de la operación mediante el flujo de capital desde los Top 15 Proveedores hacia su destino fiscal. Crucial para la reforma 2026.")
            
            sankey_cols = ['emisor_nombre', 'total']
            target_col = 'uso_cfdi' if 'uso_cfdi' in df_filtered.columns else ('tipo' if 'tipo' in df_filtered.columns else None)
            
            if all(col in df_filtered.columns for col in sankey_cols) and target_col:
                top_15_names = df_filtered.groupby('emisor_nombre')['total'].sum().nlargest(15).index.tolist()
                df_sankey_data = df_filtered[df_filtered['emisor_nombre'].isin(top_15_names)].copy()
                links = df_sankey_data.groupby(['emisor_nombre', target_col])['total'].sum().reset_index()
                nodes = list(set(links['emisor_nombre'].unique()) | set(links[target_col].unique()))
                node_idx = {name: i for i, name in enumerate(nodes)}
                
                fig_sankey = go.Figure(data=[go.Sankey(
                    node = dict(pad = 20, thickness = 15, line = dict(color = "#58a6ff", width = 0.5), label = nodes, color = "#58a6ff"),
                    link = dict(source = links['emisor_nombre'].map(node_idx), target = links[target_col].map(node_idx), value = links['total'], color = 'rgba(88, 166, 255, 0.2)')
                )])
                fig_sankey.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="JetBrains Mono", size=10, color="black"), height=500)
                st.plotly_chart(fig_sankey, use_container_width=True)
            else:
                st.warning("Faltan columnas críticas para el Diagrama de Sankey")

            st.markdown("---")
            col_box, col_heat = st.columns(2)
            
            with col_box:
                st.markdown('<div class="section-header">DETECCIÓN DE OUTLIERS ESTADÍSTICOS</div>', unsafe_allow_html=True)
                st.caption("Identifica anomalías fiscales mediante la detección automática de outliers en los montos totales.")
                box_x = 'metodo_pago' if 'metodo_pago' in df_filtered.columns else ('tipo' if 'tipo' in df_filtered.columns else None)
                if 'total' in df_filtered.columns and box_x:
                    fig_box = px.box(df_filtered, x=box_x, y='total', points="outliers", template="plotly_white", color_discrete_sequence=['#58a6ff'])
                    fig_box.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="JetBrains Mono", color="black"), showlegend=False, xaxis=dict(tickfont=dict(color='black')), yaxis=dict(tickfont=dict(color='black')))
                    st.plotly_chart(fig_box, use_container_width=True)

            with col_heat:
                st.markdown('<div class="section-header">MAPA DE CALOR TEMPORAL (RISK PATTERNS)</div>', unsafe_allow_html=True)
                st.caption("Detecta patrones de 'facturación de pánico' o anomalías de cierre de mes. Rojo indica zonas de alta densidad.")
                if 'fecha_emision' in df_filtered.columns:
                    df_h = df_filtered.copy()
                    df_h['dia_mes'] = df_h['fecha_emision'].dt.day
                    df_h['mes_ano'] = df_h['fecha_emision'].dt.to_period('M').astype(str)
                    fig_heat = px.density_heatmap(df_h, x='dia_mes', y='mes_ano', z='total', histfunc="count", color_continuous_scale="Reds", template="plotly_white")
                    fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="JetBrains Mono", color="black"), xaxis=dict(tickfont=dict(color='black')), yaxis=dict(tickfont=dict(color='black')))
                    st.plotly_chart(fig_heat, use_container_width=True)

        elif selected_subtab == "ranking":

            st.markdown('<div class="section-header">MATRIZ DE RIESGO POR PROVEEDOR</div>', unsafe_allow_html=True)
            st.caption("Ranking prescriptivo basado en comportamientos atípicos. Puntuación alta = Prioridad de Auditoría Directa.")
            
            risk_summary = calculate_risk_scores(df_filtered)
            
            # Display high-risk suppliers
            c1, c2 = st.columns([2, 1])
            with c1:
                risk_display = risk_summary[['risk_score', 'count', 'total_sum', 'pct_round', 'pct_atypical']].head(20).copy()
                risk_display['total_sum'] = pd.to_numeric(risk_display['total_sum'], errors='coerce')
                
                st.dataframe(
                    risk_display,
                    use_container_width=True,
                    column_config={
                        "risk_score": st.column_config.BarChartColumn(  # <--- CAMBIO AQUÍ
                            "Risk Index", 
                            y_min=0,      # Nota: BarChart usa y_min, no min_value
                            y_max=100,    # Nota: BarChart usa y_max, no max_value
                            color="#f85149" 
                        ),
                        "total_sum": st.column_config.NumberColumn("Total Operado", format="$%,.2f")
                    }
                )
            with c2:
                # Risk Distribution Chart
                fig_risk_dist = px.histogram(risk_summary, x='risk_score', nbins=10, title="Distribución de Riesgo", template="plotly_white", color_discrete_sequence=['#f85149'])
                fig_risk_dist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="JetBrains Mono", color="black"), xaxis=dict(tickfont=dict(color='black')), yaxis=dict(tickfont=dict(color='black')))
                st.plotly_chart(fig_risk_dist, use_container_width=True)

            # --- CYBER-ALERT BANNER FOR EXTREME RISK ---
            extreme_risk = risk_summary[risk_summary['risk_score'] > 80]
            if not extreme_risk.empty:
                st.markdown(f"""
                <div style="background: rgba(248, 81, 73, 0.1); border: 2px solid #f85149; padding: 15px; border-radius: 10px; margin-top: 20px;">
                    <h4 style="color: #f85149; margin-top: 0;">⚠️ ALERTA DE CRITICALIDAD FISCAL</h4>
                    <p style="color: #ffffff; font-size: 14px;">Se han detectado {len(extreme_risk)} emisores con un Score de Riesgo superior al 80%. 
                    Estos proveedores presentan una combinación de facturación en números redondos y horarios atípicos.</p>
                </div>
                """, unsafe_allow_html=True)



# --- VIEW: FORENSIC AUDIT ---
elif selected_module == "Materialidad / REPSE":
    if selected_subtab == "normativa":
        st.markdown('<div class="section-header">NORMATIVA SAT 2026</div>', unsafe_allow_html=True)
        st.info("📖 Módulo de Normativa - En desarrollo")
        
    elif selected_subtab == "documentos":
        st.markdown('<div class="section-header">GESTIÓN DOCUMENTAL</div>', unsafe_allow_html=True)
        st.info("📋 Módulo de Documentos - En desarrollo")
        
    elif selected_subtab == "seguimiento":
        st.markdown('<div class="section-header">SEGUIMIENTO DE AUDITORÍAS</div>', unsafe_allow_html=True)
        
        # Construct Data Lake
        data_lake = {
            'cfdis': df, 
            'cfdi_emisors': df_emisors,
            'cfdi_receptors': df_receptors,
            'cfdi_conceptos': df_conceptos
        }
        
        audit_module.render_invoice_module(data_lake)


# --- VIEW: COMPLIANCE ---
elif selected_module == "Compliance":
     st.markdown('<div class="neon-title">AUDITORÍA DE CUMPLIMIENTO (SAT 2026)</div>', unsafe_allow_html=True)
     
     if selected_subtab == "tasas":
         st.markdown("<div class='section-header'>VERIFICACIÓN DE TASA EFECTIVA</div>", unsafe_allow_html=True)
         st.caption("Ejecuta una validación algorítmica de la Tasa Efectiva por factura. Detecta discrepancias matemáticas entre la Base y el Impuesto Trasladado que los modelos automatizados del SAT marcan inmediatamente como 'inconsistencia de cálculo' o riesgo de evasión.")
         
         if 'subtotal' in df_filtered.columns and 'calc_iva' in df_filtered.columns:
             # Logic: Tasa = IVA / Subtotal
             # Handle 0 division
             df_tabs = df_filtered.copy()
             df_tabs['tasa_calculada'] = df_tabs.apply(lambda x: x['calc_iva'] / x['subtotal'] if x['subtotal'] > 0 else 0, axis=1)
             
             # Identify specific tax rates + tolerance
             # 16% (0.16), 8% (0.08), 0% (0.0)
             tolerance = 0.01
             mask_16 = (df_tabs['tasa_calculada'] - 0.16).abs() < tolerance
             mask_08 = (df_tabs['tasa_calculada'] - 0.08).abs() < tolerance
             mask_00 = (df_tabs['tasa_calculada'] - 0.0).abs() < tolerance
             
             df_tabs['es_anomalo'] = ~(mask_16 | mask_08 | mask_00)
             
             anomalias = df_tabs[df_tabs['es_anomalo']]
             num_anomalias = len(anomalias)
             
             m1, m2 = st.columns(2)
             m1.metric("Facturas Analizadas", f"{len(df_tabs):,}")
             m2.metric("Facturas con Tasa Atípica", f"{num_anomalias:,}", delta="-Riesgo SAT" if num_anomalias > 0 else "OK", delta_color="inverse")
             
             st.markdown("---")
             
             # Chart
             c1, c2 = st.columns([2, 1])
             with c1:
                 fig_tasa = px.scatter(
                     df_tabs, 
                     x='subtotal', 
                     y='calc_iva', 
                     color='es_anomalo',
                     color_discrete_map={True: '#f85149', False: '#2ea043'},
                     title="Dispersión de Tasas: Base vs Impuesto (Rojo = Atípico)",
                     template="plotly_white",
                     hover_data=['uuid', 'tasa_calculada']
                 )
                 fig_tasa.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="black"), xaxis=dict(tickfont=dict(color='black')), yaxis=dict(tickfont=dict(color='black')))
                 st.plotly_chart(fig_tasa, use_container_width=True)
             
             with c2:
                 st.markdown("#### Detalle de Anomalías")
                 if not anomalias.empty:
                     st.dataframe(
                         anomalias[['uuid', 'subtotal', 'calc_iva', 'tasa_calculada']],
                         use_container_width=True,
                         column_config={
                             "tasa_calculada": st.column_config.NumberColumn("Tasa Calc.", format="%.4f")
                         }
                     )
                 else:
                     st.success("No se detectaron tasas fuera de norma (16%, 8%, 0%). integridad Aritmética Verificada.")
         else:
             st.warning("Faltan columnas requeridas (subtotal, calc_iva) para este análisis.")

     # --- TAB 2: FLOW INTEGRITY ---
     elif selected_subtab == "flujo":
         st.markdown("<div class='section-header'>COBERTURA DE PAGOS (PPD vs REP)</div>", unsafe_allow_html=True)
         st.caption("Monitor de Materialidad de Flujo. Bajo la reforma 2026, el acreditamiento del IVA está estrictamente condicionado a la existencia del Complemento de Pago (REP). Esta vista cuantifica el monto en riesgo de NO ser deducible por falta de timbrado del cobro.")
         
         if 'metodo_pago' in df_filtered.columns:
             # Calculate metrics
             # PPD Total
             mask_ppd = df_filtered['metodo_pago'].astype(str).str.upper() == 'PPD'
             if 'tipo' in df_filtered.columns:
                mask_rep = df_filtered['tipo'].astype(str).str.upper() == 'P'
             else:
                mask_rep = pd.Series([False]*len(df_filtered))
             
             monto_ppd = df_filtered.loc[mask_ppd, 'total'].sum()
             monto_rep = df_filtered.loc[mask_rep, 'total'].sum()
             
             gap = monto_ppd - monto_rep
             # Avoid div by zero
             if monto_ppd > 0:
                 cobertura = (monto_rep / monto_ppd) * 100
             else:
                 cobertura = 100.0 if monto_rep >= 0 else 0.0
             
             col1, col2, col3 = st.columns(3)
             col1.metric("Facturado PPD (Obligación)", f"${monto_ppd:,.2f}")
             col2.metric("Pagos Timbrados (REP)", f"${monto_rep:,.2f}")
             col3.metric("Brecha Fiscal (Riesgo)", f"${gap:,.2f}", delta=f"{100-cobertura:.1f}% Sin Cobertura", delta_color="inverse")
             
             st.markdown("---")
             
             # Gauge Chart
             fig_gauge = go.Figure(go.Indicator(
                 mode = "gauge+number+delta",
                 value = cobertura,
                 domain = {'x': [0, 1], 'y': [0, 1]},
                 title = {'text': "Cobertura de Flujo (Integridad REP)", 'font': {'size': 24, 'color': "white"}},
                 delta = {'reference': 100, 'increasing': {'color': "green"}, 'decreasing': {'color': "#f85149"}},
                 gauge = {
                     'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                     'bar': {'color': "#58a6ff"},
                     'bgcolor': "rgba(0,0,0,0)",
                     'borderwidth': 2,
                     'bordercolor': "#333",
                     'steps': [
                         {'range': [0, 80], 'color': 'rgba(248, 81, 73, 0.3)'},
                         {'range': [80, 95], 'color': 'rgba(255, 166, 0, 0.3)'},
                         {'range': [95, 100], 'color': 'rgba(57, 211, 83, 0.3)'}],
                     'threshold': {
                         'line': {'color': "white", 'width': 4},
                         'thickness': 0.75,
                         'value': 100}}))
             
             fig_gauge.update_layout(paper_bgcolor = "rgba(0,0,0,0)", font = {'color': "black", 'family': "JetBrains Mono"})
             st.plotly_chart(fig_gauge, use_container_width=True)
             
             if gap > 0:
                 st.error(f"⚠️ RIESGO CRÍTICO DE DEDUCIBILIDAD: Existe una brecha de ${gap:,.2f} en facturas PPD sin complemento de pago asociado. Esto podría resultar en el rechazo del acreditamiento de IVA.")
             elif gap < 0:
                 st.info("Nota: El monto de pagos excede lo facturado en PPD. Verifique posibles anticipos o pagos de periodos anteriores.")
             else:
                 st.success("Integridad de Flujo Perfecta. Todo lo facturado PPD tiene su complemento de pago.")
                 
         else:
             st.warning("La columna 'metodo_pago' no está disponible para este análisis.")

     elif selected_subtab == "saldos_iva":
         st.markdown("<div class='section-header'>SALDOS IVA</div>", unsafe_allow_html=True)
         st.info("💰 Módulo de Saldos IVA - En desarrollo")

     elif selected_subtab == "pagos_provisionales":
         st.markdown("<div class='section-header'>PAGOS PROVISIONALES</div>", unsafe_allow_html=True)
         st.info("📅 Módulo de Pagos Provisionales - En desarrollo")


# --- VIEW: SETTINGS (CONFIGURACIÓN) ---
elif selected_module == "Configuración":
    st.markdown('<div class="neon-title">CONFIGURACIÓN DE SISTEMA</div>', unsafe_allow_html=True)
    
    if selected_subtab == "general":
        st.subheader("Parámetros de Visualización")
        st.toggle("Modo Oscuro Forzado (Cyberpunk)", value=True, disabled=True)
        st.toggle("Animaciones de Interfaz", value=True)
        
    elif selected_subtab == "ai":
        st.info("Módulo de Reentrenamiento de Modelos de Riesgo: PRÓXIMAMENTE")



# --- EXECUTE FOOTER (GHOST BUTTONS) ---
# This must run LAST to ensure buttons are generated after the main content logic
if st.session_state.authenticated:
    render_footer_ghost_buttons(selected_module, selected_subtab)
