import pandas as pd
import os
import pymongo
from dotenv import load_dotenv
import smtplib
from email.mime.image import MIMEImage
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # non-interactive backend

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Environment Variables
load_dotenv()

# Configuration
DATA_DIR = os.getenv("DATA_DIR", "./data")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "cfdi_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "gold_cfdi")

# SMTP Config
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_RECEIVER = os.getenv("ALERT_RECEIVER")

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logging.error(f"File not found: {path}")
        return None
    try:
        # Try UTF-8 first, then Latin-1
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='latin-1')

def clean_money_column(series):
    """Cleans money columns potentially having currency symbols."""
    # If already numeric, return
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    return series.astype(str).str.replace(r'[$,]', '', regex=True).astype(float)

def send_alert(subject, body, image_path=None):
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD, ALERT_RECEIVER]):
        logging.warning("SMTP credentials missing. Skipping email alert.")
        print(f"--- FAKE EMAIL ALERT ---\nSubject: {subject}\nBody: {body}\nChart Attached: {image_path}\n------------------------")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_RECEIVER
        msg['Subject'] = subject
        
        # Attach HTML body to support inline images if needed, but for now just plain text + attachment
        msg.attach(MIMEText(body, 'plain'))

        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data, name=os.path.basename(image_path))
                msg.attach(image)
            logging.info(f"Image attached: {image_path}")

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logging.info(f"Alert sent: {subject}")
    except Exception as e:
        logging.error(f"Failed to send alert: {e}")

def create_trend_chart(series, title, filename):
    try:
        plt.figure(figsize=(10, 6))
        series.plot(kind='bar', color='#00f2ff', edgecolor='black')
        plt.title(title, fontsize=14, fontweight='bold', color='black')
        plt.ylabel('Volumen', fontsize=12)
        plt.xlabel('Periodo (Mes)', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        chart_path = os.path.join(os.getcwd(), filename)
        plt.savefig(chart_path)
        plt.close()
        return chart_path
    except Exception as e:
        logging.error(f"Failed to create chart: {e}")
        return None

def main():
    logging.info("Starting Migration Pipeline...")

    # 1. Load Data
    cfdis = load_csv("cfdis.csv")
    impuestos = load_csv("cfdi_comprobante_impuestos.csv")
    traslados = load_csv("cfdi_comprobante_traslados.csv")
    retenciones = load_csv("cfdi_comprobante_retenciones.csv")
    receptors = load_csv("cfdi_receptors.csv")
    emisors = load_csv("cfdi_emisors.csv")

    if cfdis is None: 
        logging.critical("CRITICAL: cfdis.csv missing. Aborting.")
        return

    # 2. Data Cleaning & Pre-processing
    logging.info("Cleaning Data...")
    
    # Normalize text columns
    text_cols = ['tipo', 'moneda', 'forma_pago', 'metodo_pago', 'estatus']
    for col in text_cols:
        if col in cfdis.columns:
            cfdis[col] = cfdis[col].astype(str).str.lower().str.strip()

    # Cast Money Columns
    money_cols = ['subtotal', 'descuento', 'total']
    for col in money_cols:
        if col in cfdis.columns:
            cfdis[col] = clean_money_column(cfdis[col])
            
    # Clean Taxes Money Columns
    if traslados is not None:
        traslados['importe'] = clean_money_column(traslados['importe'])
    if retenciones is not None:
        retenciones['importe'] = clean_money_column(retenciones['importe'])

    # 3. Calculate Taxes Aggregates per CFDI
    # Logic: cfdis.id -> impuestos.cfdi_id (impuestos.id) -> traslados/retenciones.cfdi_comprobante_impuestos_id
    
    cfdi_taxes = pd.DataFrame({'cfdi_id': cfdis['id'].unique()})
    
    if impuestos is not None and traslados is not None:
        # Traslados Aggregate
        # Join traslados with impuestos to get cfdi_id
        traslados_merged = traslados.merge(
            impuestos[['id', 'cfdi_id']], 
            left_on='cfdi_comprobante_impuestos_id', 
            right_on='id', 
            suffixes=('_tras', '_imp')
        )
        
        # Calculate Total Traslados per CFDI
        total_traslados = traslados_merged.groupby('cfdi_id')['importe'].sum().reset_index().rename(columns={'importe': 'calc_traslados'})
        cfdis = cfdis.merge(total_traslados, left_on='id', right_on='cfdi_id', how='left').drop(columns=['cfdi_id']).fillna({'calc_traslados': 0})
        
        # Calculate IVA vs IEPS
        iva_tras = traslados_merged[traslados_merged['impuesto'].astype(str).str.contains('002', na=False)].groupby('cfdi_id')['importe'].sum().reset_index().rename(columns={'importe': 'calc_iva'})
        ieps_tras = traslados_merged[traslados_merged['impuesto'].astype(str).str.contains('003', na=False)].groupby('cfdi_id')['importe'].sum().reset_index().rename(columns={'importe': 'calc_ieps'})
        
        cfdis = cfdis.merge(iva_tras, left_on='id', right_on='cfdi_id', how='left').drop(columns=['cfdi_id']).fillna({'calc_iva': 0})
        cfdis = cfdis.merge(ieps_tras, left_on='id', right_on='cfdi_id', how='left').drop(columns=['cfdi_id']).fillna({'calc_ieps': 0})

    else:
        cfdis['calc_traslados'] = 0
        cfdis['calc_iva'] = 0
        cfdis['calc_ieps'] = 0

    if impuestos is not None and retenciones is not None:
        # Retenciones Aggregate
        retenciones_merged = retenciones.merge(
            impuestos[['id', 'cfdi_id']],
            left_on='cfdi_comprobante_impuestos_id',
            right_on='id',
            suffixes=('_ret', '_imp')
        )
        
        total_retenciones = retenciones_merged.groupby('cfdi_id')['importe'].sum().reset_index().rename(columns={'importe': 'calc_retenciones'})
        cfdis = cfdis.merge(total_retenciones, left_on='id', right_on='cfdi_id', how='left').drop(columns=['cfdi_id']).fillna({'calc_retenciones': 0})
        
        # ISR vs IVA Ret
        isr_ret = retenciones_merged[retenciones_merged['impuesto'].astype(str).str.contains('001', na=False)].groupby('cfdi_id')['importe'].sum().reset_index().rename(columns={'importe': 'calc_ret_isr'})
        iva_ret = retenciones_merged[retenciones_merged['impuesto'].astype(str).str.contains('002', na=False)].groupby('cfdi_id')['importe'].sum().reset_index().rename(columns={'importe': 'calc_ret_iva'})
        
        cfdis = cfdis.merge(isr_ret, left_on='id', right_on='cfdi_id', how='left').drop(columns=['cfdi_id']).fillna({'calc_ret_isr': 0})
        cfdis = cfdis.merge(iva_ret, left_on='id', right_on='cfdi_id', how='left').drop(columns=['cfdi_id']).fillna({'calc_ret_iva': 0})

    else:
        cfdis['calc_retenciones'] = 0
        cfdis['calc_ret_isr'] = 0
        cfdis['calc_ret_iva'] = 0

    # --- NEW: Inject Company ID for Multi-tenancy ---
    # Default to a value from ENV or argument
    COMPANY_ID = os.getenv("COMPANY_ID", "DEFAULT_TENANT")
    cfdis['company_id'] = COMPANY_ID
    logging.info(f"Targeting Company ID: {COMPANY_ID}")

    # 4. Enrich with Names
    if receptors is not None:
        # Assuming 'receptor_id' in cfdis maps to 'id' in receptors
        # Check column names in receptors. usually id, nombre/razon_social
        # For robustness, we select the string column that looks like a name
        name_col = next((c for c in receptors.columns if 'nombre' in c.lower() or 'razon' in c.lower()), None)
        if name_col:
            receptors = receptors[['id', name_col]].rename(columns={name_col: 'receptor_nombre'})
            cfdis = cfdis.merge(receptors, left_on='receptor_id', right_on='id', how='left', suffixes=('', '_rec'))
    
    if emisors is not None:
        name_col = next((c for c in emisors.columns if 'nombre' in c.lower() or 'razon' in c.lower()), None)
        rfc_col = next((c for c in emisors.columns if 'rfc' in c.lower()), None)
        cols_to_keep = ['id']
        if name_col: cols_to_keep.append(name_col)
        if rfc_col: cols_to_keep.append(rfc_col)
        
        emisors_clean = emisors[cols_to_keep].rename(columns={name_col: 'emisor_nombre', rfc_col: 'emisor_rfc'})
        cfdis = cfdis.merge(emisors_clean, left_on='emisor_id', right_on='id', how='left', suffixes=('', '_emi'))

    # 5. Financial Calculations
    # Formula: $Neto = [Subtotal + Traslados] - [Retenciones + Descuentos]$
    cfdis['ventas_brutas'] = cfdis['subtotal']
    cfdis['ventas_netas'] = (cfdis['subtotal'] + cfdis['calc_traslados']) - (cfdis['calc_retenciones'] + cfdis['descuento'])
    
    logging.info(f"Processed {len(cfdis)} records.")
    
    # 6. Forensics & Alerts
    alerts = []
    
    # Check for Duplicates (Tríada: RFC + Monto + Fecha)
    # Using 'emisor_id' (proxy for RFC if RFC missing) or 'emisor_rfc'
    group_cols = ['total', 'fecha_emision']
    if 'emisor_rfc' in cfdis.columns:
        group_cols.append('emisor_rfc')
    else:
        group_cols.append('emisor_id')
        
    duplicates = cfdis[cfdis.duplicated(subset=group_cols, keep=False)]
    if not duplicates.empty:
        alert_msg = f"Posibles Duplicados Detectados:\n{duplicates[group_cols].head(10).to_string()}"
        alerts.append(alert_msg)
        cfdis['is_duplicate'] = cfdis.duplicated(subset=group_cols, keep=False)
    else:
        cfdis['is_duplicate'] = False

    # Check Retention Spike > 20% vs previous month
    # Convert date
    cfdis['fecha_dt'] = pd.to_datetime(cfdis['fecha_emision'], errors='coerce')
    cfdis['month_year'] = cfdis['fecha_dt'].dt.to_period('M')
    
    monthly_ret = cfdis.groupby('month_year')['calc_retenciones'].sum().sort_index()
    monthly_pct_change = monthly_ret.pct_change()
    
    # Check latest month
    if not monthly_pct_change.empty:
        latest_change = monthly_pct_change.iloc[-1]
        if latest_change > 0.20:
            alerts.append(f"Incremento Atípico de Retenciones: {latest_change:.1%} de aumento en {monthly_ret.index[-1]}")

    # --- NEW: Check Cancelled CFDI Spike > 20% vs previous month ---
    chart_to_send = None
    if 'estatus' in cfdis.columns:
        cancelled_mask = cfdis['estatus'].astype(str).str.lower().str.contains('cancel', na=False)
        monthly_cancelled = cfdis[cancelled_mask].groupby('month_year').size().sort_index()
        
        if not monthly_cancelled.empty:
            cancelled_pct_change = monthly_cancelled.pct_change()
            if not cancelled_pct_change.empty:
                latest_cancel_change = cancelled_pct_change.iloc[-1]
                if latest_cancel_change > 0.20:
                    alerts.append(f"Incremento Atípico de Cancelaciones: {latest_cancel_change:.1%} de aumento en {monthly_cancelled.index[-1]}")
                    # Create chart for cancellation trend
                    chart_to_send = create_trend_chart(monthly_cancelled, "Tendencia de Facturas Canceladas", "alerta_cancelaciones.png")

    # Send Alerts
    if alerts:
        send_alert("Alertas Forenses CFDI", "\n\n".join(alerts), image_path=chart_to_send)
        if chart_to_send and os.path.exists(chart_to_send):
            try:
                os.remove(chart_to_send)
            except:
                pass

    # 7. MongoDB Load
    if not MONGO_URI:
        logging.warning("No MongoDB URI provided. Skipping DB upload.")
        # Save to JSON locally for verification/demo purposes
        output_file = os.path.join(DATA_DIR, "gold_cfdi_processed.json")
        # Convert period to string for JSON serialization
        if 'month_year' in cfdis.columns:
            cfdis['month_year'] = cfdis['month_year'].astype(str)
        cfdis.to_json(output_file, orient='records', date_format='iso')
        logging.info(f"Data saved locally to {output_file}")
    else:
        try:
            client = pymongo.MongoClient(MONGO_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            
            # Convert to dict
            records = cfdis.to_dict(orient='records')
            
            # Batch Insert/Upsert
            # For simplicity, we define 'uuid' as unique index if it exists, else 'id'
            unique_field = 'uuid' if 'uuid' in cfdis.columns else 'id'
            
            # Create Unique Index to prevent duplicates
            collection.create_index([(unique_field, pymongo.ASCENDING)], unique=True)
            
            operations = []
            for record in records:
                # Filter out NaN values for Mongo
                clean_record = {k: v for k, v in record.items() if pd.notnull(v)}
                operations.append(
                    pymongo.UpdateOne(
                        {unique_field: clean_record[unique_field]},
                        {'$set': clean_record},
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logging.info(f"MongoDB Write: {result.upserted_count} upserted, {result.modified_count} modified.")
                
        except Exception as e:
            logging.error(f"MongoDB Error: {e}")

if __name__ == "__main__":
    main()
