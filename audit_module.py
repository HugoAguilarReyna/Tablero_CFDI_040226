import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render_invoice_module(data_lake):
    """
    Renders the Invoice Audit Module with Forensic Health Checks.
    """
    st.markdown('<div class="section-header">AUDITORÍA FORENSE 2026: VALIDACIÓN DE DOCUMENTOS</div>', unsafe_allow_html=True)

    # --- 1. Data Engineering (Merge Logic) ---
    required_keys = ['cfdis', 'cfdi_emisors', 'cfdi_receptors', 'cfdi_conceptos']
    if not all(k in data_lake for k in required_keys):
        st.error("Error: Data Lake incomplete. Missing required DataFrames.")
        return

    try:
        # Unir CFDI con Emisor y Receptor (Capa Gold) utilizando los nombres de columna actualizados
        # Nota: Ajustado a emisor_rfc / receptor_rfc según estructura de app.py
        df_master = data_lake['cfdis'].copy()
        df_conceptos = data_lake['cfdi_conceptos']
    except Exception as e:
        st.error(f"Error processing data: {e}")
        return

    # --- 2. Command Center (Search & Filter) ---
    with st.container():
        col_search, col_chips = st.columns([2, 3])
        
        with col_search:
            search_term = st.text_input("🔍 FILTRO GLOBAL FORENSE", placeholder="RFC, Nombre, Folio o UUID...")
            
        with col_chips:
            st.write("CRITERIOS DE RIESGO:")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                filter_cancel = st.checkbox("🚨 Canceladas")
            with col_c2:
                filter_high_val = st.checkbox("💰 Alta Materialidad")
            with col_c3:
                filter_current_month = st.checkbox("📅 Mes Actual")

    # Apply Filters
    mask = pd.Series(True, index=df_master.index)
    
    if search_term:
        term = search_term.lower()
        search_mask = (
            df_master['emisor_rfc'].astype(str).str.lower().str.contains(term) |
            df_master['emisor_nombre'].astype(str).str.lower().str.contains(term) |
            df_master['receptor_rfc'].astype(str).str.lower().str.contains(term) |
            df_master['receptor_nombre'].astype(str).str.lower().str.contains(term) |
            df_master['folio'].astype(str).str.lower().str.contains(term) |
            df_master['uuid'].astype(str).str.lower().str.contains(term)
        )
        mask = mask & search_mask

    if filter_cancel and 'estatus' in df_master.columns:
        mask = mask & (df_master['estatus'].astype(str).str.lower() == 'cancelado')
    
    if filter_high_val:
        mask = mask & (df_master['total'] > 50000)
        
    if filter_current_month and 'fecha_emision' in df_master.columns:
        now = pd.Timestamp.now()
        mask = mask & (
            (df_master['fecha_emision'].dt.month == now.month) & 
            (df_master['fecha_emision'].dt.year == now.year)
        )

    df_filtered = df_master.loc[mask].copy()

    # Results Table
    if not df_filtered.empty:
        disp_cols = ['fecha_emision', 'emisor_rfc', 'emisor_nombre', 'receptor_nombre', 'total', 'estatus']
        final_disp_cols = [c for c in disp_cols if c in df_filtered.columns]
        
        # Prepare Sorted DF for display
        df_display = df_filtered[final_disp_cols].sort_values('fecha_emision', ascending=False)
        
        # Initialize session state for selection if not present
        if "selected_invoice_idx" not in st.session_state:
            st.session_state.selected_invoice_idx = df_filtered.index[0] if not df_filtered.empty else None

        # --- CSS INJECTION FOR LIGHT THEME OVERRIDE ---
        st.markdown("""
            <style>
            /* Force Light Theme for Dataframe Container by overriding CSS Vars */
            [data-testid="stDataFrame"] { 
                background-color: #ffffff !important;
                /* These variables control the underlying component colors */
                --st-color-background-secondary: #f8f9fa !important;
                --st-color-border-table: #e5e7eb !important;
                --st-color-text: #000000 !important;
            }
            
            /* Target Table Header specific cells (if rendered as DOM elements) */
            [data-testid="stDataFrame"] th { 
                background-color: #f8f9fa !important; 
                color: #000000 !important; 
                border-bottom: 2px solid #e5e7eb !important; 
            }
            
            /* Target Index/Selection Column specific cells */
            [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] tbody th { 
                background-color: #ffffff !important; 
                color: #000000 !important; 
                border-bottom: 1px solid #f3f4f6 !important; 
            }
            
            /* Fix Input Contrast in this Module */
            div[data-testid="stTextInput"] input { 
                background-color: #ffffff !important; 
                color: #000000 !important; 
                border: 1px solid #cbd5e1 !important; 
                caret-color: #000000 !important;
            }
            div[data-testid="stTextInput"] label { 
                color: #334155 !important; 
            }
            
            /* Ensure checkboxes are visible */
            [data-testid="stCheckbox"] label { 
                color: #334155 !important; 
            }
            </style>
        """, unsafe_allow_html=True)

        # --- INTERACTIVE DATAFRAME ---
        # User requested selection capability + White Background / Black Text
        
        # 1. Pandas Styler for Formatting & Colors
        def highlight_status(val):
            color = '#059669' if str(val).lower() == 'vigente' else '#dc2626'
            return f'color: {color}; font-weight: bold;'

        styled_df = df_display.style.format({
            'fecha_emision': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else '',
            'total': "${:,.2f}"
        }).map(highlight_status, subset=['estatus']).set_properties(**{
            'background-color': '#ffffff',
            'color': '#000000',
            'border-color': '#e5e7eb'
        }).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f8f9fa'), ('color', '#000000'), ('font-weight', 'bold')]},
            {'selector': 'thead th', 'props': [('background-color', '#f8f9fa'), ('color', '#000000'), ('border-bottom', '2px solid #e5e7eb')]}
        ])
        
        # 2. Render Interactive Table
        event = st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=500
        )

        # 3. Handle Selection Event
        if event and len(event.selection["rows"]) > 0:
            # Get the index from the displayed dataframe using the row number
            selected_row_idx = event.selection["rows"][0]
            real_index = df_display.index[selected_row_idx]
            st.session_state.selected_invoice_idx = real_index
            # Sync drop-down
            st.session_state.audit_selectbox_key = real_index

        st.markdown("---")
        
        # --- SELECTOR DE DOCUMENTO ---
        # Ensure the selected index is valid in the current filtered dataset
        current_options = df_filtered.index.tolist()
        if st.session_state.selected_invoice_idx not in current_options and current_options:
             st.session_state.selected_invoice_idx = current_options[0]
             st.session_state['audit_selectbox_key'] = current_options[0]
        
        invoice_options = df_filtered.apply(
            lambda x: f"{x.get('fecha_emision', 'N/A')} | {x.get('emisor_nombre', 'N/A')} | ${x.get('total', 0):,.2f}", 
            axis=1
        )
        
        # Find the index position for the Selectbox
        try:
            sb_index = current_options.index(st.session_state.selected_invoice_idx)
        except:
            sb_index = 0

        # Callback to update state when selectbox changes manually
        def on_selectbox_change():
            st.session_state.selected_invoice_idx = st.session_state.audit_selectbox_key

        selected_invoice_idx = st.selectbox(
            "Seleccione factura para análisis profundo:", 
            options=current_options, 
            format_func=lambda i: invoice_options[i],
            index=sb_index,
            key="audit_selectbox_key",
            on_change=on_selectbox_change
        )
        
        if selected_invoice_idx is not None:
             row = df_filtered.loc[selected_invoice_idx]
             
             col_health, col_invoice = st.columns([1, 2])
             
             with col_health:
                 st.markdown('<div class="section-header">FORENSIC HEALTH CHECK</div>', unsafe_allow_html=True)
                 render_forensic_alerts(row, df_master)
                 
             with col_invoice:
                 render_invoice_html(row, df_conceptos)
                 with st.expander("🔍 DATA ESTRUCTURADA (JSON)"):
                    st.json(row.to_dict())

    else:
        st.info("Sin registros coincidentes.")


def render_forensic_alerts(row, df_master):
    """Calculates and displays forensic risk indicators including Issuer Risk Score."""
    total = row.get('total', 0)
    fecha = row.get('fecha_emision')
    emisor = row.get('emisor_rfc', '')
    emisor_nombre = row.get('emisor_nombre', '')
    
    # 1. Round Number Check
    is_round = (total > 0) and (total % 100 == 0 or total % 1000 == 0)
    
    # 2. Unusual Hour Check (10 PM - 6 AM)
    is_atypical_hour = fecha.hour >= 22 or fecha.hour <= 6 if pd.notnull(fecha) else False
    
    # 3. Weekend Check
    is_weekend = fecha.dayofweek >= 5 if pd.notnull(fecha) else False
    
    # 4. Statistical Deviation (vs Emisor Mean)
    emisor_avg = df_master[df_master['emisor_rfc'] == emisor]['total'].mean() if emisor else 0
    is_anomaly = total > (emisor_avg * 2.5) if emisor_avg > 0 else False

    # 5. Calculate Issuer Risk Score (Global context)
    risk_df = df_master[df_master['emisor_rfc'] == emisor].copy()
    if not risk_df.empty:
        total_count = len(risk_df)
        round_pct = (risk_df['total'].apply(lambda x: x > 0 and x % 100 == 0).sum() / total_count) * 100
        atypical_pct = (risk_df['fecha_emision'].dt.hour >= 22).sum() / total_count * 100
        weekend_pct = (risk_df['fecha_emision'].dt.dayofweek >= 5).sum() / total_count * 100
        issuer_score = (round_pct * 0.4 + atypical_pct * 0.3 + weekend_pct * 0.3)
    else:
        issuer_score = 0

    # Render indicators
    def alert_box(label, status, icon="✅"):
        # Darker semantic colors for readability on white
        color = "#059669" if status == "NORMAL" else "#dc2626" 
        bg = "rgba(0, 230, 118, 0.12)" if status == "NORMAL" else "rgba(255, 23, 68, 0.12)"
        border_color = "rgba(0, 230, 118, 0.3)" if status == "NORMAL" else "rgba(255, 23, 68, 0.3)"
        
        st.markdown(f"""
            <div style="padding: 15px; border-radius: var(--radius-md); background: {bg}; border: 1.5px solid {border_color}; margin-bottom: 12px; backdrop-filter: blur(10px);">
                <span style="font-size: 18px;">{icon}</span>
                <b style="color: {color}; margin-left: 10px; font-family: var(--font-sans);">{label}</b><br>
                <small style="color: var(--text-secondary); margin-left: 30px; font-family: var(--font-sans);">Estado: {status}</small>
            </div>
        """, unsafe_allow_html=True)

    # Score Gauge
    # Semantic colors for light mode contrast
    score_color = "#059669" if issuer_score < 30 else ("#d97706" if issuer_score < 70 else "#dc2626")
    st.markdown(f"""
        <div style="text-align: center; padding: 25px; background: var(--bg-card); backdrop-filter: blur(15px); border-radius: var(--radius-xl); border: 1.5px solid var(--glass-border); margin-bottom: 25px; box-shadow: var(--glass-shadow);">
            <div style="font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 2px; font-family: 'JetBrains Mono';">Índice de Riesgo Emisor</div>
            <div style="font-size: 42px; font-weight: 800; color: {score_color}; font-family: var(--font-sans); text-shadow: 0 0 10px {score_color}22;">{issuer_score:.1f}%</div>
        </div>
    """, unsafe_allow_html=True)

    alert_box("MONTO REDONDO", "ALERTA" if is_round else "NORMAL", "🎯" if is_round else "✅")
    alert_box("HORARIO OPERATIVO", "ATÍPICO" if is_atypical_hour else "NORMAL", "🌙" if is_atypical_hour else "✅")
    alert_box("DÍA NO LABORAL", "RIESGO" if is_weekend else "NORMAL", "📅" if is_weekend else "✅")
    alert_box("DESVIACIÓN MEDIA", "ANOMALÍA" if is_anomaly else "NORMAL", "📈" if is_anomaly else "✅")

    # 6. Export Action
    st.markdown("---")
    report_data = {
        "UUID": [row.get('uuid', 'N/A')],
        "Emisor": [emisor_nombre],
        "RFC": [emisor],
        "Monto": [total],
        "Risk_Score": [f"{issuer_score:.1f}%"],
        "Round_Number": ["YES" if is_round else "NO"],
        "Atypical_Hour": ["YES" if is_atypical_hour else "NO"],
        "Weekend_Billing": ["YES" if is_weekend else "NO"],
        "Mean_Deviation": ["YES" if is_anomaly else "NO"]
    }
    df_report = pd.DataFrame(report_data)
    csv = df_report.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 EXPORTAR REPORTE FORENSE (CSV)",
        data=csv,
        file_name=f"forensic_report_{row.get('uuid', 'unknown')[:8]}.csv",
        mime='text/csv',
        help="Descargar análisis técnico para materialidad"
    )

    if is_round or is_atypical_hour or is_weekend or is_anomaly:
        st.warning("⚠️ Se recomienda revisión de materialidad para este documento.")
    else:
        st.success("🟢 No se detectaron anomalías estructurales inmediatas.")


def render_invoice_html(row, df_conceptos):
    """Generates the Corporate HTML Invoice with comma31.2 formatting."""
    
    # Formatting helper for comma31.2
    def fmt(val):
        return f"{val:,.2f}"

    concepts_subset = pd.DataFrame()
    invoice_uuid = row.get('uuid')
    if pd.notnull(invoice_uuid) and 'uuid' in df_conceptos.columns:
        concepts_subset = df_conceptos[df_conceptos['uuid'] == invoice_uuid]
             
    rows_html = ""
    if not concepts_subset.empty:
        for _, c in concepts_subset.iterrows():
            rows_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{c.get('cantidad', 1)}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{c.get('clave_unidad', 'H87')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{c.get('descripcion', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${fmt(c.get('valor_unitario', 0))}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${fmt(c.get('importe', 0))}</td>
            </tr>
            """
    else:
        rows_html = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #999;"><i>Sin conceptos detallados disponibles</i></td></tr>'

    html_template = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 900px; margin: 0 auto; background: #ffffff; color: var(--text-primary); box-shadow: var(--glass-shadow); border: 1.5px solid var(--glass-border); border-radius: var(--radius-xl); overflow: hidden;">
        <div style="background-color: #f1f5f9; color: var(--color-primary); padding: 30px; display: flex; justify-content: space-between; border-bottom: 4px solid var(--color-primary); backdrop-filter: blur(10px);">
            <div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px;">ANÁLISIS DE CFDI</h1>
                <p style="margin: 5px 0 0; color: var(--text-secondary); font-size: 12px; font-family: 'JetBrains Mono';">{row.get('uuid', 'N/A')}</p>
            </div>
            <div style="text-align: right;">
                <h3 style="margin: 0; color: var(--text-primary); font-weight: 700;">{row.get('emisor_nombre', 'N/A')}</h3>
                <p style="margin: 2px 0; font-size: 12px; color: var(--text-secondary);">RFC: {row.get('emisor_rfc', 'N/A')}</p>
                <p style="margin: 0; font-size: 12px; color: var(--text-muted);">Fecha: {row.get('fecha_emision', 'N/A')}</p>
            </div>
        </div>
        
        <div style="padding: 25px; background-color: #f8fafc; border-bottom: 1.5px solid var(--glass-border);">
            <p style="margin: 0; color: #1e40af; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 1px;">Receptor</p>
            <h2 style="margin: 5px 0 0; font-size: 18px; color: var(--text-primary);">{row.get('receptor_nombre', 'N/A')}</h2>
            <p style="margin: 2px 0; font-size: 12px; color: var(--text-secondary);">RFC: {row.get('receptor_rfc', 'N/A')}</p>
        </div>

        <div style="padding: 20px;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: var(--text-primary);">
                <thead>
                    <tr style="color: var(--text-primary); background: #f1f5f9;">
                        <th style="padding: 12px; border-bottom: 2px solid var(--glass-border); text-align: left;">CANT</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--glass-border); text-align: left;">UNIDAD</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--glass-border); text-align: left;">DESCRIPCIÓN</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--glass-border); text-align: right;">P. UNITARIO</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--glass-border); text-align: right;">IMPORTE</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>

        <div style="padding: 0 20px 30px; display: flex; justify-content: flex-end;">
            <table style="width: 280px; font-size: 14px; border-collapse: collapse; color: var(--text-primary);">
                <tr><td style="padding: 8px; text-align: right; color: var(--text-secondary);">Subtotal:</td><td style="padding: 8px; text-align: right; font-weight: 600;">${fmt(row.get('subtotal', 0))}</td></tr>
                <tr><td style="padding: 8px; text-align: right; color: var(--text-secondary);">IVA:</td><td style="padding: 8px; text-align: right; font-weight: 600;">${fmt(row.get('calc_iva', 0))}</td></tr>
                <tr style="border-top: 2.5px solid var(--color-primary);"><td style="padding: 12px; text-align: right; font-weight: 800; color: #1e40af; font-size: 16px;">TOTAL CFDI:</td><td style="padding: 12px; text-align: right; font-weight: 800; color: #1e40af; font-size: 16px;">${fmt(row.get('total', 0))}</td></tr>
            </table>
        </div>
    </div>
    """
    components.html(html_template, height=600, scrolling=True)
