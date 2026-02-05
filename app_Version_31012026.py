def render_premium_navbar():
    """
    Renders the unified top navigation bar with dropdowns. (Restored and White-compatible)
    """
    query_params = st.query_params
    current_nav = query_params.get("nav", "Dashboard")
    current_sub = query_params.get("subtab", "")
    
    if current_nav not in SUBMENU_CONFIG:
        current_nav = "Dashboard"

    nav_html = ""
    for module_name, subitems in SUBMENU_CONFIG.items():
        is_active = "active" if module_name == current_nav else ""
        
        dropdown_html = ""
        if subitems:
            dropdown_html += '<div class="dropdown-content">'
            for item in subitems:
                sub_active = "active" if (is_active and item['key'] == current_sub) else ""
                raw_key = f"nav_{module_name}_{item['key']}" 
                button_key = raw_key.replace(" ", "_").lower()
                dropdown_html += f'<div class="dropdown-item {sub_active}" data-button-key="{button_key}"><span class="dropdown-label">{item["label"]}</span></div>'
            dropdown_html += '</div>'
            
        default_sub = subitems[0]['key'] if subitems else ""
        arrow_html = '<span class="dropdown-arrow">▼</span>' if subitems else ''
        
        raw_main_key = f"nav_{module_name}_{default_sub}" if subitems else f"nav_{module_name}_main"
        button_key = raw_main_key.replace(" ", "_").lower()
        
        nav_html += f'<div class="nav-item-wrapper {is_active}"><div class="nav-item" data-button-key="{button_key}"><span class="nav-label">{module_name}</span>{arrow_html}</div>{dropdown_html}</div>'

    navbar_css = textwrap.dedent(f"""
    <style>
    .premium-navbar {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 70px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 40px;
        z-index: 999999;
        font-family: 'Inter', sans-serif;
    }}

    .navbar-brand {{
        font-size: 20px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 1px;
    }}

    .navbar-menu {{
        display: flex;
        gap: 10px;
        height: 100%;
        align-items: center;
    }}

    .nav-item-wrapper {{
        position: relative;
        height: 100%;
        display: flex;
        align-items: center;
    }}

    .nav-item {{
        padding: 8px 16px;
        border-radius: 8px;
        color: rgba(255,255,255,0.85);
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
    }}

    .nav-item:hover {{
        background: rgba(255,255,255,0.15);
        color: #FFFFFF;
    }}

    .nav-item-wrapper.active .nav-item {{
        background: rgba(255,255,255,0.25);
        color: #FFFFFF;
    }}

    .dropdown-content {{
        display: none;
        position: absolute;
        top: 60px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px;
        padding: 8px;
        min-width: 220px;
        z-index: 1000000;
    }}

    .nav-item-wrapper:hover .dropdown-content {{
        display: block;
    }}

    .dropdown-item {{
        padding: 10px 14px;
        border-radius: 8px;
        color: #E2E8F0;
        font-size: 13px;
        cursor: pointer;
    }}

    .dropdown-item:hover {{
        background: rgba(255,255,255,0.1);
        color: #FFFFFF;
    }}
    </style>

    <div class="premium-navbar">
        <div class="navbar-brand">KONIA</div>
        <div class="navbar-menu">{nav_html}</div>
    </div>
    """)
    st.markdown(navbar_css, unsafe_allow_html=True)
    
    js_bridge = """
    <script>
    (function() {
        const doc = window.parent.document;
        function findButtonByText(text) {
            const buttons = Array.from(doc.querySelectorAll('button[kind="secondary"] p'));
            const target = buttons.find(el => el.innerText.trim() === text);
            return target ? target.closest('button') : null;
        }
        const observer = new MutationObserver(() => {
            const items = doc.querySelectorAll('.nav-item, .dropdown-item');
            if (items.length > 0) {
                items.forEach(el => {
                    el.onclick = function(e) {
                        e.stopPropagation();
                        const key = this.getAttribute('data-button-key');
                        if (key) {
                            const btn = findButtonByText(key);
                            if (btn) btn.click();
                        }
                    };
                });
            }
        });
        observer.observe(doc.body, { childList: true, subtree: true });
    })();
    </script>
    """
    components.html(js_bridge, height=0, width=0)

    clicked_nav = None
    clicked_sub = None
    with st.sidebar:
        for module_name, subitems in SUBMENU_CONFIG.items():
            if subitems:
                for item in subitems:
                    raw_key = f"nav_{module_name}_{item['key']}"
                    btn_key = raw_key.replace(" ", "_").lower()
                    if st.button(btn_key, key=btn_key, type="secondary"):
                        clicked_nav = module_name
                        clicked_sub = item['key']
            else:
                raw_key = f"nav_{module_name}_main"
                btn_key = raw_key.replace(" ", "_").lower()
                if st.button(btn_key, key=btn_key, type="secondary"):
                    clicked_nav = module_name
                    clicked_sub = ""

    if clicked_nav:
        st.query_params["nav"] = clicked_nav
        if clicked_sub:
            st.query_params["subtab"] = clicked_sub
        else:
            if "subtab" in st.query_params:
                del st.query_params["subtab"]
        st.rerun()

    return current_nav, current_sub
