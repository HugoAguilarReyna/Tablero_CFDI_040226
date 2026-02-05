import pandas as pd
import numpy as np
import logging
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_RECEIVER = os.getenv("ALERT_RECEIVER")

def send_alert(subject, body, image_path=None):
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD, ALERT_RECEIVER]):
        logging.warning("SMTP credentials missing. Showing console output only.")
        print(f"\n--- [SIMULATED ALERT] ---")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print(f"Chart: {image_path}")
        print(f"-------------------------\n")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_RECEIVER
        msg['Subject'] = subject
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
        logging.info(f"REAL Email Alert sent to {ALERT_RECEIVER}")
    except Exception as e:
        logging.error(f"Failed to send real alert: {e}")

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

def run_test():
    logging.info("Starting Cancellation Spike Test...")
    
    # Create mock data for two months
    # Dec 2025: 10 cancellations
    # Jan 2026: 20 cancellations (100% increase, >20% threshold)
    
    dates = (
        [pd.Timestamp('2025-12-01')] * 10 + 
        [pd.Timestamp('2026-01-01')] * 20
    )
    
    df = pd.DataFrame({
        'fecha_emision': dates,
        'estatus': ['cancelado'] * 30
    })
    
    df['fecha_dt'] = pd.to_datetime(df['fecha_emision'])
    df['month_year'] = df['fecha_dt'].dt.to_period('M')
    
    alerts = []
    
    # Logic from migration.py
    chart_to_send = None
    if 'estatus' in df.columns:
        cancelled_mask = df['estatus'].astype(str).str.lower().str.contains('cancel', na=False)
        monthly_cancelled = df[cancelled_mask].groupby('month_year').size().sort_index()
        
        logging.info(f"Monthly cancellations found:\n{monthly_cancelled}")
        
        if not monthly_cancelled.empty:
            cancelled_pct_change = monthly_cancelled.pct_change()
            if not cancelled_pct_change.empty:
                latest_cancel_change = cancelled_pct_change.iloc[-1]
                logging.info(f"Latest change: {latest_cancel_change:.1%}")
                
                if latest_cancel_change > 0.20:
                    alert_msg = f"Incremento Atípico de Cancelaciones Detectado: {latest_cancel_change:.1%} de aumento supera el límite del 20%."
                    alerts.append(alert_msg)
                    # Create chart for cancellation trend
                    chart_to_send = create_trend_chart(monthly_cancelled, "Tendencia de Facturas Canceladas (PRUEBA)", "test_alerta_cancelaciones.png")

    if alerts:
        send_alert("PRUEBA: Alerta Forense CFDI - Pico de Cancelaciones", "\n\n".join(alerts), image_path=chart_to_send)
        if chart_to_send and os.path.exists(chart_to_send):
            try:
                os.remove(chart_to_send)
                logging.info("Cleaned up test chart file.")
            except:
                pass
    else:
        logging.warning("La prueba falló: No se detectó el pico. Revisa la lógica de los datos.")

if __name__ == "__main__":
    run_test()
