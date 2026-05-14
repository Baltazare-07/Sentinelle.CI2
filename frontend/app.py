import os
import pandas as pd
import streamlit as st
import json
from web3 import Web3
import random
import uuid
from streamlit_folium import st_folium
import folium
from folium.plugins import LocateControl
import requests
import plotly.graph_objects as go
import hashlib
import time
import io
import xlsxwriter



# ==================== FONCTIONS D'IMPRESSION PDF ====================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import base64
from datetime import datetime, timedelta


def get_date_days_ago(days):
    """Retourne une date il y a X jours"""
    from datetime import datetime, timedelta
    return datetime.now() - timedelta(days=days)

def generate_report_pdf(signalement, photo_data=None):
    """
    Génère un PDF pour un signalement avec toutes les informations
    """
    # Créer un buffer en mémoire
    buffer = io.BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
        title=f"Signalement_{signalement.get('id', 'SIG')}.pdf"
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#FF7F00'),
        spaceAfter=30,
        alignment=1  # Centré
    )
    
    # Style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#00CD00'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Style pour le texte normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=6
    )
    
    # Style pour les informations importantes
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#FF7F00'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    # Liste des éléments du PDF
    elements = []
    
    # En-tête avec logo et titre
    header_text = f"""
    <para alignment="center">
        <font color="#FF7F00" size="20"><b>SENTINELLE.CI</b></font><br/>
        <font color="#00CD00" size="12">Plateforme citoyenne de signalement sur blockchain</font><br/>
        <font color="black" size="10">RAPPORT DE SIGNALEMENT</font>
    </para>
    """
    elements.append(Paragraph(header_text, title_style))
    elements.append(Spacer(1, 20))
    
    # Ligne de séparation
    elements.append(Paragraph("<hr color='#FF7F00'/>", normal_style))
    elements.append(Spacer(1, 20))
    
    # Informations générales
    elements.append(Paragraph("📋 INFORMATIONS GÉNÉRALES", subtitle_style))
    
    # Préparer les données pour le tableau
    data = [
        ["🆔 ID du signalement:", signalement.get('id', 'N/A')],
        ["📅 Date de création:", signalement.get('date', datetime.now()).strftime('%d/%m/%Y à %H:%M:%S') if isinstance(signalement.get('date'), datetime) else str(signalement.get('date', datetime.now()))],
        ["📍 Type de problème:", signalement.get('type', 'N/A')],
        ["🏙️ Quartier:", signalement.get('quartier', 'N/A')],
        ["📊 Statut:", get_status_fr(signalement.get('statut', 'en_attente'))],
        ["👤 Signalé par:", signalement.get('signale_par', 'Anonyme')],
    ]
    
    # Ajouter le hash blockchain si disponible
    tx_hash = signalement.get('tx_hash', '')
    if tx_hash and tx_hash != 'en_attente':
        data.append(["🔗 Transaction blockchain:", f"{tx_hash[:20]}..."])
        data.append(["🔍 Voir sur Etherscan:", f"https://sepolia.etherscan.io/tx/{tx_hash}"])
    else:
        data.append(["🔗 Transaction blockchain:", "En attente de confirmation"])
    
    # Ajouter les coordonnées GPS
    if signalement.get('lat') and signalement.get('lng'):
        data.append(["📍 Coordonnées GPS:", f"{signalement['lat']:.6f}, {signalement['lng']:.6f}"])
    
    # Créer le tableau
    table = Table(data, colWidths=[120, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF8F0')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#FF7F00')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 11),
        ('FONTSIZE', (1, 0), (1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FF7F00')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Description
    if signalement.get('description'):
        elements.append(Paragraph("📝 DESCRIPTION", subtitle_style))
        elements.append(Paragraph(f"<b>{signalement['description']}</b>", normal_style))
        elements.append(Spacer(1, 20))
    
    # Ajouter la photo si disponible
    if photo_data:
        elements.append(Paragraph("📸 PHOTO DU SIGNALEMENT", subtitle_style))
        
        try:
            # Convertir la photo pour PDF
            if isinstance(photo_data, bytes):
                img_data = photo_data
            elif hasattr(photo_data, 'getvalue'):
                img_data = photo_data.getvalue()
            else:
                img_data = photo_data.read() if hasattr(photo_data, 'read') else photo_data
            
            # Sauvegarder temporairement l'image
            temp_img = PILImage.open(io.BytesIO(img_data))
            
            # Redimensionner l'image si trop grande
            max_width = 400
            if temp_img.width > max_width:
                ratio = max_width / temp_img.width
                new_height = int(temp_img.height * ratio)
                temp_img = temp_img.resize((max_width, new_height), PILImage.Resampling.LANCZOS)
            
            # Convertir en RVB si nécessaire
            if temp_img.mode != 'RGB':
                temp_img = temp_img.convert('RGB')
            
            # Sauvegarder temporairement
            img_buffer = io.BytesIO()
            temp_img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            # Ajouter l'image au PDF
            img = Image(img_buffer, width=temp_img.width, height=temp_img.height)
            elements.append(img)
            elements.append(Spacer(1, 10))
            
            # Ajouter légende
            elements.append(Paragraph("<i>Photo prise lors du signalement</i>", normal_style))
            
        except Exception as e:
            elements.append(Paragraph(f"<i>Erreur lors du chargement de la photo: {str(e)}</i>", normal_style))
    
    elements.append(Spacer(1, 20))
    
    # Informations supplémentaires
    elements.append(Paragraph("🔒 INFORMATIONS BLOCKCHAIN", subtitle_style))
    blockchain_info = """
    <para>
        <b>✓ Plateforme:</b> Sentinelle.CI<br/>
        <b>✓ Réseau:</b> Ethereum Sepolia<br/>
        <b>✓ Contrat:</b> {contract}<br/>
        <b>✓ Horodatage:</b> {timestamp}<br/>
        <b>✓ Intégrité:</b> Données immuables sur la blockchain
    </para>
    """.format(
        contract=CONTRACT_ADDRESS[:15] + "..." if CONTRACT_ADDRESS else "N/A",
        timestamp=datetime.now().strftime('%d/%m/%Y à %H:%M:%S')
    )
    elements.append(Paragraph(blockchain_info, normal_style))
    
    elements.append(Spacer(1, 30))
    
    # Pied de page
    footer_text = f"""
    <para alignment="center">
        <font size="8" color="gray">
            Document généré par Sentinelle.CI le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}<br/>
            Ce document est la preuve du signalement sur la blockchain Ethereum Sepolia
        </font>
    </para>
    """
    elements.append(Paragraph(footer_text, normal_style))
    
    # Générer le PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer

def get_status_fr(status):
    """Convertit le statut en français"""
    status_map = {
        'en_attente': '⏳ En attente de traitement',
        'en_cours': '🔄 En cours de traitement',
        'resolu': '✅ Résolu'
    }
    return status_map.get(status, status)

def format_date_for_pdf(date_obj):
    """Formate la date pour le PDF"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y à %H:%M:%S')
    elif isinstance(date_obj, str):
        try:
            return datetime.fromisoformat(date_obj).strftime('%d/%m/%Y à %H:%M:%S')
        except:
            return date_obj
    return str(date_obj)


def export_signalements_to_excel(signalements, filter_status=None):
    """Exporte les signalements vers Excel"""
    output = io.BytesIO()
    
    # Filtrer si nécessaire
    data = []
    for s in signalements:
        if filter_status and s['statut'] != filter_status:
            continue
        
        # Formater la date
        if isinstance(s['date'], datetime):
            date_val = s['date']
        else:
            try:
                date_val = datetime.fromisoformat(str(s['date']))
            except:
                date_val = datetime.now()
        
        data.append({
            'ID': s['id'],
            'Type': s['type'],
            'Quartier': s['quartier'],
            'Statut': get_status_fr(s.get('statut', 'en_attente')),
            'Date': date_val.strftime('%d/%m/%Y %H:%M:%S'),
            'Latitude': s.get('lat', 'N/A'),
            'Longitude': s.get('lng', 'N/A'),
            'Signalé par': s.get('signale_par', 'Anonyme'),
            'Description': s.get('description', ''),
            'Agent assigné': s.get('agent', 'Non assigné'),
            'Hash TX': s.get('tx_hash', 'Non disponible')[:20] + '...' if s.get('tx_hash') else 'En attente'
        })
    
    # Créer le DataFrame
    df = pd.DataFrame(data)
    
    # Exporter vers Excel
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Signalements', index=False)
        
        # Ajuster les colonnes
        worksheet = writer.sheets['Signalements']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(column_width, 50))
    
    output.seek(0)
    return output

def create_detailed_map(signalements, center_lat=5.3415, center_lng=-4.0142, zoom_start=13):
    """Crée une carte détaillée avec tous les signalements et informations"""
    m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)
    
    # Couleurs par statut
    colors = {
        'en_attente': 'red',
        'en_cours': 'orange',
        'resolu': 'green'
    }
    
    # Groupes de calques
    fg_attente = folium.FeatureGroup(name="En attente", show=True)
    fg_cours = folium.FeatureGroup(name="En cours", show=True)
    fg_resolu = folium.FeatureGroup(name="Résolus", show=True)
    
    for s in signalements:
        if s.get('lat') and s.get('lng'):
            # Créer le contenu du popup
            popup_html = f"""
            <div style="min-width: 200px;">
                <h4 style="color: #FF7F00; margin: 0 0 5px 0;">{s['type']}</h4>
                <hr style="margin: 5px 0;">
                <b>ID:</b> {s['id']}<br>
                <b>Quartier:</b> {s['quartier']}<br>
                <b>Statut:</b> {get_status_fr(s['statut'])}<br>
                <b>Date:</b> {s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime) else str(s['date'])[:10]}<br>
            """
            
            if s.get('description'):
                popup_html += f"<b>Description:</b> {s['description'][:100]}...<br>"
            
            if s.get('agent'):
                popup_html += f"<b>Agent:</b> {s['agent']}<br>"
            
            popup_html += """
                <hr style="margin: 5px 0;">
                <a href="https://www.google.com/maps?q={lat},{lng}" target="_blank" style="color: #FF7F00;">
                    🗺️ Voir sur Google Maps
                </a>
            </div>
            """.format(lat=s['lat'], lng=s['lng'])
            
            # Créer le marqueur
            marker = folium.Marker(
                location=[s['lat'], s['lng']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=colors.get(s['statut'], 'gray'), 
                                icon='info-sign', 
                                icon_color='white')
            )
            
            # Ajouter au bon groupe
            if s['statut'] == 'en_attente':
                marker.add_to(fg_attente)
            elif s['statut'] == 'en_cours':
                marker.add_to(fg_cours)
            else:
                marker.add_to(fg_resolu)
    
    # Ajouter les groupes à la carte
    fg_attente.add_to(m)
    fg_cours.add_to(m)
    fg_resolu.add_to(m)
    
    # Ajouter le contrôle des calques
    folium.LayerControl().add_to(m)
    
    # Ajouter le contrôle de localisation
    LocateControl().add_to(m)
    
    return m

def generate_mairie_pdf(signalements):
    """Génère un rapport PDF pour la mairie avec tous les signalements"""
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#FF7F00'), alignment=1)
    
    elements = []
    
    # En-tête
    elements.append(Paragraph("MAIRIE DE YOPOUGON - RAPPORT DES SIGNALEMENTS", title_style))
    elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Statistiques
    stats_data = [
        ["📊 Statistiques", "Valeur"],
        ["Total signalements", len(signalements)],
        ["En attente", len([s for s in signalements if s['statut'] == 'en_attente'])],
        ["En cours", len([s for s in signalements if s['statut'] == 'en_cours'])],
        ["Résolus", len([s for s in signalements if s['statut'] == 'resolu'])]
    ]
    
    stats_table = Table(stats_data, colWidths=[200, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF7F00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(stats_table)
    elements.append(PageBreak())
    
    # Liste des signalements
    elements.append(Paragraph("DÉTAIL DES SIGNALEMENTS", title_style))
    elements.append(Spacer(1, 10))
    
    for s in signalements:
        date_str = s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime) else str(s['date'])[:10]
        
        report_html = f"""
        <b>ID:</b> {s['id']}<br/>
        <b>Type:</b> {s['type']}<br/>
        <b>Quartier:</b> {s['quartier']}<br/>
        <b>Date:</b> {date_str}<br/>
        <b>Statut:</b> {get_status_fr(s['statut'])}<br/>
        <b>Agent:</b> {s.get('agent', 'Non assigné')}<br/>
        """
        if s.get('description'):
            report_html += f"<b>Description:</b> {s['description']}<br/>"
        
        elements.append(Paragraph(report_html, styles['Normal']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<hr color='#FF7F00'/>", styles['Normal']))
        elements.append(Spacer(1, 10))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer



# ==================== CONFIGURATION DE LA PAGE ====================
st.set_page_config(
    page_title="SentinelleCI",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Ajoutez ce CSS à votre section de style (avant le st.markdown du header)
st.markdown("""
<style>
    /* Style pour le selectbox - Texte orange */
    .stSelectbox label {
        color: #FF7F00 !important;
        font-weight: 600 !important;
    }
    
    /* Style pour l'élément selectbox lui-même */
    .stSelectbox [data-baseweb="select"] {
        background-color: white !important;
        border-color: #FF7F00 !important;
    }
    
    /* Style pour le texte sélectionné */
    .stSelectbox [data-baseweb="select"] .st-bw {
        color: #FF7F00 !important;
        font-weight: 500 !important;
    }
    
    /* Style pour le placeholder */
    .stSelectbox [data-baseweb="select"] .st-bx {
        color: #FF7F00 !important;
        opacity: 0.7 !important;
    }
    
    /* Style pour les options du dropdown */
    div[data-baseweb="popover"] ul {
        background-color: white !important;
        border: 2px solid #FF7F00 !important;
    }
    
    div[data-baseweb="popover"] li {
        color: #FF7F00 !important;
        background-color: white !important;
    }
    
    div[data-baseweb="popover"] li:hover {
        background-color: #FFF8F0 !important;
        color: #FF7F00 !important;
    }
    
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #FF7F00 !important;
        color: white !important;
    }
    
    /* Style pour l'icône du selectbox */
    .stSelectbox svg {
        fill: #FF7F00 !important;
        stroke: #FF7F00 !important;
    }
    
    /* Style pour le texte dans le selectbox (option sélectionnée) */
    .stSelectbox [data-baseweb="select"] div[role="button"] span {
        color: #FF7F00 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* ========== STYLE POUR FILE UPLOADER ========== */
    .stFileUploader label {
        color: #FF7F00 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    
    /* Zone de drop */
    .stFileUploader div[data-testid="stFileUploaderDropzone"] {
        background: linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 100%) !important;
        border: 2px dashed #FF7F00 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #00CD00 !important;
        background-color: #F0FFF0 !important;
    }
    
    /* Texte dans la zone */
    .stFileUploader div[data-testid="stFileUploaderDropzone"] p {
        color: #FF7F00 !important;
        font-weight: 500 !important;
    }
    
    /* Petit texte informatif */
    .stFileUploader div[data-testid="stFileUploaderDropzone"] small {
        color: #FF7F00 !important;
        opacity: 0.7 !important;
    }
    
    /* Bouton parcourir */
    .stFileUploader button {
        background: linear-gradient(135deg, #FF7F00 0%, #FFA500 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(255, 127, 0, 0.3) !important;
        background: linear-gradient(135deg, #FFA500 0%, #FF7F00 100%) !important;
    }
    
    /* Message d'information */
    .stFileUploader .uploadedFileInfo, 
    .stFileUploader [data-testid="stUploadedFileIndicator"] + div {
        color: #FF7F00 !important;
    }
    
    /* ========== STYLE POUR CAMERA INPUT ========== */
    .stCameraInput label {
        color: #FF7F00 !important;
        font-weight: 600 !important;
    }
    
    .stCameraInput button {
        background-color: #FF7F00 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    .stCameraInput button:hover {
        background-color: #E67300 !important;
    }
    
    /* ========== STYLE POUR LES IMAGES UPLOADÉES ========== */
    .stImage {
        border: 2px solid #FF7F00 !important;
        border-radius: 10px !important;
        padding: 5px !important;
        background-color: white !important;
    }
    
    /* Bouton supprimer */
    button[kind="secondary"]:has(svg) {
        color: #FF4500 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CSS STYLE COULEURS DRAPEAU IVOIRIEN ====================
st.markdown("""
<style>
    /* Fond blanc global */
    .stApp {
        background-color: white !important;
    }
    
    /* Corps de la page */
    body, .main, .stApp > header, .stApp > div {
        background-color: white !important;
    }
    
    /* Sidebar avec dégradé orange-vert */
    .css-1d391kg, .css-1633bj2, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FF7F00 0%, #FFFFFF 50%, #00CD00 100%) !important;
    }
    
    /* Texte dans la sidebar */
    .css-1d391kg, .css-1633bj2, [data-testid="stSidebar"] {
        color: #1a1a1a !important;
    }
    
    /* Titres dans la sidebar */
    .sidebar .sidebar-content, [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown {
        color: #1a1a1a !important;
    }
    
    /* Boutons personnalisés - Orange */
    .stButton > button {
        background: linear-gradient(135deg, #FF7F00 0%, #FFA500 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(255, 127, 0, 0.4) !important;
        background: linear-gradient(135deg, #FFA500 0%, #FF7F00 100%) !important;
    }
    
    /* Bouton primaire - Vert */
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background: linear-gradient(135deg, #00CD00 0%, #009900 100%) !important;
    }
    
    /* Cartes de signalement */
    .signal-card {
        background: linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 100%) !important;
        border-left: 5px solid #FF7F00 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    /* Titres - Orange */
    h1, h2, h3, h4, h5, h6 {
        color: #FF7F00 !important;
        font-weight: 700 !important;
    }
    
    /* Texte normal */
    p, li, span, div, .stMarkdown, .stText {
        color: #1a1a1a !important;
    }
    
    /* Métriques - style orange */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 100%) !important;
        border-radius: 15px !important;
        padding: 15px !important;
        border: 2px solid #FF7F00 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    [data-testid="stMetric"] label, 
    [data-testid="stMetric"] .stMetricLabel,
    [data-testid="stMetric"] .stMetricValue {
        color: #FF7F00 !important;
    }
    
    /* Alertes et messages */
    .stAlert {
        border-radius: 10px !important;
        border-left: 5px solid #FF7F00 !important;
        background-color: #FFF8F0 !important;
        color: #1a1a1a !important;
    }
    
    .stAlert svg, .stAlert span {
        color: #1a1a1a !important;
    }
    
    /* Messages de succès - Vert */
    .stAlert[data-baseweb="notification"][kind="success"] {
        border-left-color: #00CD00 !important;
    }
    
    /* Messages d'erreur - Orange foncé */
    .stAlert[data-baseweb="notification"][kind="error"] {
        border-left-color: #FF4500 !important;
    }
    
    /* Champs de saisie */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        color: #1a1a1a !important;
        border-color: #FF7F00 !important;
        border-width: 2px !important;
    }
    
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: #00CD00 !important;
        box-shadow: 0 0 0 1px #00CD00 !important;
    }
    
    /* Checkbox */
    .stCheckbox {
        color: #1a1a1a !important;
    }
    
    .stCheckbox label {
        color: #1a1a1a !important;
    }
    
    /* Expandeur */
    .streamlit-expanderHeader {
        background-color: #FFF8F0 !important;
        border-radius: 10px !important;
        color: #FF7F00 !important;
        border: 1px solid #FF7F00 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #FFFFFF !important;
        border: 1px solid #FF7F00 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #F5F5F5 !important;
        border-radius: 8px 8px 0 0 !important;
        color: #1a1a1a !important;
        border: 1px solid #FF7F00 !important;
        border-bottom: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF7F00 !important;
        color: white !important;
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #FF7F00 0%, #FFFFFF 50%, #00CD00 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-top: 30px;
    }
    
    /* Code */
    code, pre {
        background-color: #FFF8F0 !important;
        color: #FF7F00 !important;
        border-radius: 5px !important;
    }
    
    /* Tableaux */
    table, th, td {
        border-color: #FF7F00 !important;
    }
    
    th {
        background-color: #FF7F00 !important;
        color: white !important;
    }
    
    td {
        color: #1a1a1a !important;
    }
    
    /* Barre de progression */
    .stProgress > div > div {
        background-color: #FF7F00 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #FF7F00 !important;
    }
    
    /* Information box */
    .stInfo {
        background-color: #FFF8F0 !important;
        border-left-color: #FF7F00 !important;
    }
    
    /* Warning box */
    .stWarning {
        background-color: #FFF3E0 !important;
        border-left-color: #FF9800 !important;
    }
    
    /* Success box */
    .stSuccess {
        background-color: #E8F5E9 !important;
        border-left-color: #00CD00 !important;
    }
    
    /* Error box */
    .stError {
        background-color: #FFEBEE !important;
        border-left-color: #FF4500 !important;
    }
    
    /* Selectbox items */
    .stSelectbox [data-baseweb="select"] {
        background-color: white !important;
    }
    
    /* MultiSelect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #FF7F00 !important;
        color: white !important;
    }
    
    /* Date input */
    .stDateInput input {
        background-color: white !important;
        border-color: #FF7F00 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== ENTÊTE COMPLÈTE SENTINELLE.CI (DRAPEAU IVOIRIEN) ====================
st.markdown("""
<div style="background: linear-gradient(135deg, #FF7F00 0%, #FFFFFF 50%, #00CD00 100%);
            padding: 20px 30px;
            border-radius: 0 0 20px 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="background: linear-gradient(135deg, #FF7F00 0%, #FFFFFF 50%, #00CD00 100%); 
                        border-radius: 50%; 
                        width: 55px; 
                        height: 55px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                <span style="font-size: 32px;">📍</span>
            </div>
            <div>
                <h1 style="margin: 0; color: #FF7F00; font-size: 28px; font-weight: 700;">Sentinelle.CI</h1>
                <p style="margin: 0; color: #1a1a1a; font-size: 12px;">↳ Signalements citoyens sur blockchain</p>
            </div>
        </div>
        <div style="background: rgba(255,127,0,0.2);
                    padding: 8px 15px;
                    border-radius: 20px;
                    border: 1px solid #FF7F00;">
            <span style="color: #1a1a1a; font-size: 12px;">✓ Blockchain active</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== CONFIGURATION BLOCKCHAIN ====================
# Liste des RPC Sepolia alternatifs
RPC_URLS = [
    "https://rpc.ankr.com/eth_sepolia",
    "https://ethereum-sepolia.publicnode.com",
    "https://sepolia.gateway.tenderly.co",
    "https://1rpc.io/sepolia",
]

# ADRESSE DU CONTRAT DÉPLOYÉ (À REMPLACER APRÈS DÉPLOIEMENT)
CONTRACT_ADDRESS = "0xd9145CCE52D386f254917e481eB44e9943F39138"  # À modifier après déploiement

# ABI DU CONTRAT (Version complète avec toutes les fonctionnalités)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_reportType", "type": "string"},
            {"internalType": "string", "name": "_description", "type": "string"},
            {"internalType": "string", "name": "_quartier", "type": "string"},
            {"internalType": "int256", "name": "_latitude", "type": "int256"},
            {"internalType": "int256", "name": "_longitude", "type": "int256"}
        ],
        "name": "createReport",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_reportId", "type": "uint256"}],
        "name": "resolveReport",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_reportId", "type": "uint256"},
            {"internalType": "bool", "name": "_isUpvote", "type": "bool"}
        ],
        "name": "vote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_reportId", "type": "uint256"}],
        "name": "getReport",
        "outputs": [
            {"internalType": "address", "name": "citizen", "type": "address"},
            {"internalType": "string", "name": "reportType", "type": "string"},
            {"internalType": "string", "name": "description", "type": "string"},
            {"internalType": "string", "name": "quartier", "type": "string"},
            {"internalType": "int256", "name": "latitude", "type": "int256"},
            {"internalType": "int256", "name": "longitude", "type": "int256"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "uint256", "name": "upvotes", "type": "uint256"},
            {"internalType": "uint256", "name": "downvotes", "type": "uint256"},
            {"internalType": "bool", "name": "isResolved", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReportCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "reportId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "citizen", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "reportType", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "ReportCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "reportId", "type": "uint256"}
        ],
        "name": "ReportResolved",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "reportId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "voter", "type": "address"},
            {"indexed": False, "internalType": "bool", "name": "isUpvote", "type": "bool"}
        ],
        "name": "Voted",
        "type": "event"
    }
]

# Adresse du contrat déployé (à remplacer par la vraie adresse)
CONTRACT_ADDRESS = "0xd9145CCE52D386f254917e481eB44e9943F39138"

class BlockchainManager:
    def __init__(self):
        self.w3 = None
        self.connected = False
        self.current_rpc = None
        self.contract = None
        self.connect()
    
    def connect(self):
        """Connexion automatique au premier RPC disponible"""
        for rpc_url in RPC_URLS:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
                if w3.is_connected():
                    self.w3 = w3
                    self.connected = True
                    self.current_rpc = rpc_url
                    
                    if CONTRACT_ADDRESS and CONTRACT_ADDRESS.startswith('0x'):
                        self.contract = self.w3.eth.contract(
                            address=CONTRACT_ADDRESS,
                            abi=CONTRACT_ABI
                        )
                    
                    print(f"✅ Connecté à Sepolia via {rpc_url.split('/')[2]}")
                    return True
            except Exception as e:
                continue
        
        self.connected = False
        return False
    
    def get_balance(self, address):
        if self.connected and address and self.w3:
            try:
                balance = self.w3.eth.get_balance(address)
                return self.w3.from_wei(balance, 'ether')
            except Exception as e:
                print(f"Erreur get_balance: {e}")
                return 0
        return 0
    
    def get_status(self):
        if self.connected:
            return f"✅ Connecté à {self.current_rpc.split('/')[2]}"
        return "❌ Non connecté - Vérifiez votre connexion internet"
    
    def create_report_transaction(self, report_type, description, quartier, latitude, longitude, from_address):
        if not self.connected or not self.contract:
            return None, "Blockchain non connectée"
        
        try:
            lat_int = int(float(latitude) * 10**6) if latitude else 0
            lng_int = int(float(longitude) * 10**6) if longitude else 0
            
            transaction = self.contract.functions.createReport(
                report_type,
                description,
                quartier,
                lat_int,
                lng_int
            ).build_transaction({
                'from': from_address,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })
            return transaction, None
        except Exception as e:
            return None, str(e)
    
    def get_report_from_blockchain(self, report_id):
        if not self.connected or not self.contract:
            return None
        
        try:
            result = self.contract.functions.getReport(report_id).call()
            return {
                'citizen': result[0],
                'reportType': result[1],
                'description': result[2],
                'quartier': result[3],
                'latitude': result[4] / 10**6,
                'longitude': result[5] / 10**6,
                'timestamp': result[6],
                'upvotes': result[7],
                'downvotes': result[8],
                'isResolved': result[9]
            }
        except Exception as e:
            print(f"Erreur get_report: {e}")
            return None
    
    def get_report_details(self, report_id):
        if self.connected and self.contract:
            try:
                report = self.contract.functions.getReport(report_id).call()
                return {
                    'citizen': report[0],
                    'type': report[1],
                    'description': report[2],
                    'quartier': report[3],
                    'lat': report[4] / 10**6,
                    'lng': report[5] / 10**6,
                    'timestamp': report[6],
                    'upvotes': report[7],
                    'downvotes': report[8],
                    'resolved': report[9]
                }
            except Exception as e:
                print(f"Erreur: {e}")
        return None
    
    def get_report_count(self):
        if not self.connected or not self.contract:
            return 0
        
        try:
            return self.contract.functions.getReportCount().call()
        except Exception as e:
            print(f"Erreur get_report_count: {e}")
            return 0

# Initialiser le gestionnaire blockchain
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = BlockchainManager()

# Initialiser la connexion wallet
if 'wallet_connected' not in st.session_state:
    st.session_state.wallet_connected = False
    st.session_state.wallet_address = None
    st.session_state.demo_mode = False

# Configuration du backend
if os.environ.get('RENDER') or os.environ.get('STREAMLIT_CLOUD'):
    # En production sur Render
    BACKEND_URL = os.environ.get('BACKEND_URL', 'https://sentinelle-backend.onrender.com')

# Ajoutez un test de connexion au backend
def check_backend_health():
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False
        
def load_signalements_from_backend():
    try:
        response = requests.get(f"{BACKEND_URL}/api/signalements", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                for s in data:
                    if 'date' in s and isinstance(s['date'], str):
                        s['date'] = datetime.fromisoformat(s['date'])
                st.session_state.signalements = data
                return True
    except Exception as e:
        print(f"⚠️ Impossible de charger depuis backend : {e}")
    return False

# ==================== INITIALISATION SESSION STATE ====================
if 'signalements' not in st.session_state:
    st.session_state.signalements = [
        {
            'id': 'SIG-001', 
            'type': 'Route', 
            'quartier': 'Azito', 
            'lat': 5.3415, 
            'lng': -4.0142, 
            'statut': 'en_attente', 
            'date': datetime.now() - timedelta(days=2), 
            'tx_hash': '0x7a3f8b2c1d4e9f3a8b2c1d4e9f3a8b2c1d4e9f3a', 
            'signale_par': 'A. KONE'
        },
        {
            'id': 'SIG-002', 
            'type': 'Éclairage', 
            'quartier': 'Maroc', 
            'lat': 5.3591, 
            'lng': -4.0195, 
            'statut': 'en_cours', 
            'date': datetime.now() - timedelta(days=5), 
            'tx_hash': '0x2b9e7a1d3f6c8a4b2e9d7f3a1c5b8e2a4d6f9c7a', 
            'signale_par': 'M. TRAORE'
        },
        {
            'id': 'SIG-003', 
            'type': 'Eau', 
            'quartier': 'Sicogi', 
            'lat': 5.3856, 
            'lng': -3.9974, 
            'statut': 'resolu', 
            'date': datetime.now() - timedelta(days=10), 
            'tx_hash': '0x8c4d2f1a7e9b3a6c8d4e2f1a7b9c3d5e8f2a4b6c', 
            'signale_par': 'S. COULIBALY'
        },
        {
            'id': 'SIG-004', 
            'type': 'Route', 
            'quartier': 'Yopougon', 
            'lat': 5.3225, 
            'lng': -4.0552, 
            'statut': 'en_attente', 
            'date': datetime.now() - timedelta(days=1), 
            'tx_hash': None, 
            'signale_par': 'F. KONAN'
        },
        {
            'id': 'SIG-005', 
            'type': 'École', 
            'quartier': 'Niagon', 
            'lat': 5.3591, 
            'lng': -4.0195, 
            'statut': 'en_cours', 
            'date': datetime.now() - timedelta(days=3), 
            'tx_hash': None, 
            'signale_par': 'L. DIAKITÉ'
        },
    ]

if 'page' not in st.session_state:
    st.session_state.page = 'accueil'
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = None
if 'show_prise_en_charge' not in st.session_state:
    st.session_state.show_prise_en_charge = False
if 'selected_lat' not in st.session_state:
    st.session_state.selected_lat = 5.3415
if 'selected_lng' not in st.session_state:
    st.session_state.selected_lng = -4.0142
if 'camera_enabled' not in st.session_state:
    st.session_state.camera_enabled = False
if 'photo_data' not in st.session_state:
    st.session_state.photo_data = None
if 'pending_transaction' not in st.session_state:
    st.session_state.pending_transaction = None


# ==================== FONCTIONS ====================

def create_map(zoom=11):
    """Crée une carte Folium avec les signalements"""
    m = folium.Map(location=[5.3415, -4.0142], zoom_start=zoom)
    colors = {'en_attente': 'orange', 'en_cours': 'lightblue', 'resolu': 'green'}
    
    for s in st.session_state.signalements:
        if s.get('lat') and s.get('lng'):
            # Correction ici : utilisez 'datetime' au lieu de 'datetime.datetime'
            if isinstance(s['date'], datetime):
                date_str = s['date'].strftime('%d/%m/%Y')
            else:
                date_str = str(s['date'])
            
            popup_text = f"<b>{s['type']}</b><br>📍 {s['quartier']}<br>📅 {date_str}"
            if s.get('tx_hash'):
                popup_text += f"<br>🔗 {s['tx_hash'][:15]}..."
            folium.Marker(
                location=[s['lat'], s['lng']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color=colors.get(s['statut'], 'gray'), icon_color='white')
            ).add_to(m)
    return m

def create_donut_chart():
    """Crée un graphique circulaire (donut) des statistiques"""
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    en_cours = len([s for s in st.session_state.signalements if s['statut'] == 'en_cours'])
    resolu = len([s for s in st.session_state.signalements if s['statut'] == 'resolu'])
    
    labels = ['En attente', 'En cours', 'Résolus']
    values = [en_attente, en_cours, resolu]
    colors = ['#FF7F00', '#00CD00', '#0050FF']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='auto',
        textfont=dict(color='#1a1a1a')
    )])
    
    fig.update_layout(
        title_text="Répartition des signalements",
        title_font_color="#FF7F00",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1a1a1a"),
        height=400
    )
    return fig


# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 📍 Sentinelle.CI")
    st.markdown("---")
    
    st.markdown("### 📱 Navigation")
    if st.button("🏠 Accueil", width='stretch', key="nav_accueil"):
        st.session_state.page = "accueil"
        st.rerun()
    
    if st.button("➕ Nouveau signalement", width='stretch', key="nav_nouveau"):
        st.session_state.page = "nouveau_signalement"
        st.rerun()
    
    if st.button("📋 Mes signalements", width='stretch', key="nav_mes"):
        st.session_state.page = "mes_signalements"
        st.rerun()
    
    if st.button("🗺️ Carte publique", width='stretch', key="nav_carte"):
        st.session_state.page = "carte_publique"
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 👑 Administration")
    if st.button("🏛️ Vue Mairie", width='stretch', type="primary", key="nav_mairie"):
        st.session_state.page = "mairie"
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 👤 Compte")
    if st.button("👤 Mon profil", width='stretch', key="nav_profil"):
        st.session_state.page = "profil"
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### ℹ️ À propos")
    st.info("""
    **Sentinelle.CI**  
    Plateforme citoyenne de signalement  
    des travaux publics
    
    Version 2.0 | Blockchain Réelle
    """)
    
    st.markdown("---")
    
    st.markdown("### 📊 Stats rapides")
    total = len(st.session_state.signalements)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    st.metric("Total signalements", total)
    st.metric("En attente", en_attente)
    
    # Blockchain Wallet dans la sidebar
    st.markdown("---")
    st.markdown("### 🦊 Portefeuille Blockchain")

# Suite du code pour la blockchain (identique à l'originale)
if st.session_state.blockchain.connected:
    st.success("✅ Réseau: Sepolia")
    if CONTRACT_ADDRESS and CONTRACT_ADDRESS.startswith('0x'):
        st.caption(f"📄 Contrat: {CONTRACT_ADDRESS[:10]}...")
else:
    st.error("❌ Réseau: Non connecté")

if not st.session_state.wallet_connected:
    st.markdown("**🔧 Options de connexion :**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 Mode démo", width='stretch', key="demo_mode_btn"):
            st.session_state.demo_mode = True
            st.session_state.wallet_connected = True
            st.session_state.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            st.rerun()
    
    with col2:
        use_real = st.checkbox("🔗 Mode réel", key="real_mode_checkbox")
    
    if use_real:
        st.markdown("---")
        st.markdown("**📌 Connexion MetaMask**")
        
        st.info("""
        **Étapes :**
        1. Ouvrez **http://localhost:8501** dans Chrome
        2. Cliquez sur l'icône 🦊 MetaMask
        3. Connectez-vous au réseau Sepolia
        4. Copiez votre adresse ci-dessous
        """)
        
        address_input = st.text_input(
            "Adresse MetaMask :",
            placeholder="0x...",
            key="real_wallet_input"
        )
        
        if address_input and len(address_input) > 30:
            if st.button("✅ Valider et connecter", width='stretch', key="connect_real_final"):
                st.session_state.wallet_connected = True
                st.session_state.wallet_address = address_input
                st.session_state.demo_mode = False
                st.rerun()
        
        st.markdown("""
        <div style="background: #FFF8F0; padding: 8px; border-radius: 6px; margin-top: 10px; border: 1px solid #FF7F00;">
            <span style="color: #FF7F00;">💡 Vous n'avez pas MetaMask ?</span><br>
            <a href="https://metamask.io/download/" target="_blank" style="color: #FF7F00;">Télécharger MetaMask</a>
        </div>
        """, unsafe_allow_html=True)

else:
    address = st.session_state.wallet_address
    if st.session_state.demo_mode:
        st.info("🔧 Mode démo actif")
        st.success(f"✅ Wallet: {address[:10]}...")
    else:
        st.success("✅ Wallet connecté")
        st.code(f"{address[:8]}...{address[-6:]}", language="text")
    
    balance = st.session_state.blockchain.get_balance(address)
    if balance > 0:
        st.metric("💰 Solde", f"{balance:.4f} ETH")
    else:
        st.warning("⚠️ Solde 0 ETH - Obtenez des SepoliaETH sur un faucet")
    
    if st.button("🔌 Déconnecter", width='stretch', key="disconnect_wallet_final"):
        st.session_state.wallet_connected = False
        st.session_state.wallet_address = None
        st.session_state.demo_mode = False
        st.rerun()


# ==================== PAGE ACCUEIL ====================
if st.session_state.page == 'accueil':
    st.markdown("## 🗺️ CARTE DES SIGNALEMENTS")
    m = create_map(zoom=11)
    st_folium(m, width=900, height=450, key="carte_accueil")
    
    # with st.expander("ℹ️ Debug signalements"):
    #     for s in st.session_state.signalements[-5:]:
    #         st.write(f"{s['id']} → hash: {s.get('tx_hash')}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚠️ Problèmes signalés", len([s for s in st.session_state.signalements if s['statut'] == 'en_attente']))
    with col2:
        st.metric("🔄 En cours", len([s for s in st.session_state.signalements if s['statut'] == 'en_cours']))
    with col3:
        st.metric("✅ Résolus", len([s for s in st.session_state.signalements if s['statut'] == 'resolu']))
    
    st.markdown("---")
    
    # Derniers signalements
    colA, colB = st.columns([2, 1])
    with colA:
        st.markdown("### 📋 Derniers signalements")
        for s in reversed(st.session_state.signalements[-5:]):
            # Correction : utilisez 'datetime' au lieu de 'datetime.datetime'
            if isinstance(s['date'], datetime):
                date_obj = s['date']
            else:
                # Correction : utilisez 'datetime' au lieu de 'datetime.datetime'
                date_obj = datetime.fromisoformat(str(s['date']))
            date_str = date_obj.strftime('%d/%m/%Y %H:%M:%S')

            tx = s.get('tx_hash', '')
            identifiant = s.get('id', 'ID inconnu')
        
            if tx and len(tx) == 66 and tx.startswith('0x'):
                etherscan_url = f"https://sepolia.etherscan.io/tx/{tx}"
                hash_display = tx[:20] + '...'
                right_content = f"<a href='{etherscan_url}' target='_blank' style='color:#FF7F00; text-decoration:none;'>🔗 {hash_display}</a>"
            else:
                right_content = "<span style='color:#FF7F00; font-weight:500;'>⏳ En attente</span>"
        
            st.markdown(f"""
            <div style="background:#FFF8F0; border-radius:12px; padding:16px; margin-bottom:12px; border-left:5px solid #FF7F00; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span style="font-size:16px; font-weight:700; color:#FF7F00;">🆔 {identifiant}</span>
                    <span>{right_content}</span>
                </div>
                <div style="font-size:15px; color:#1a1a1a; line-height:1.4;">
                    <span style="font-weight:600;">{s['type']}</span> – {s['quartier']}<br>
                    <span style="color:#666;">📅 {date_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with colB:
        st.markdown("### 📊 STATS EN DIRECT")
        st.metric("Problèmes résolus ce mois", "45", delta="+12")
        st.metric("Délai moyen de traitement", "12 jours", delta="Objectif <15j")
    
    st.markdown("---")
    
    if st.button("➕ NOUVEAU SIGNALEMENT", width='stretch', key="btn_nouveau_accueil"):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()

# ==================== PAGE NOUVEAU SIGNALEMENT ====================
elif st.session_state.page == 'nouveau_signalement':
    st.markdown("## 🆕 Nouveau signalement")
    if st.button("← Retour", key="retour_nv"):
        st.session_state.page = 'accueil'
        st.rerun()
    st.markdown("---")

    type_probleme = st.selectbox(
        "Type de problème",
        ["Route", "Eau", "École", "Éclairage"],
        index=None,
        placeholder="Sélectionnez...",
        key="type_nv"
    )
    if type_probleme:
        st.session_state.selected_type = type_probleme

    st.markdown("---")

    st.markdown("### 📍 GÉOLOCALISATION")
    st.info("💡 Cliquez sur la carte pour placer le signalement")

    m_location = folium.Map(
        location=[st.session_state.selected_lat, st.session_state.selected_lng],
        zoom_start=14
    )
    folium.Marker(
        location=[st.session_state.selected_lat, st.session_state.selected_lng],
        popup="📍 Position du signalement",
        draggable=True,
        icon=folium.Icon(color='orange', icon='info-sign', icon_color='white')
    ).add_to(m_location)
    LocateControl().add_to(m_location)

    map_data = st_folium(m_location, width=700, height=400, key="map_nv")

    if map_data and map_data.get('last_clicked'):
        st.session_state.selected_lat = map_data['last_clicked']['lat']
        st.session_state.selected_lng = map_data['last_clicked']['lng']
        st.success(f"📍 Position mise à jour: {st.session_state.selected_lat:.4f}, {st.session_state.selected_lng:.4f}")

    st.info(f"📍 **Position actuelle :** {st.session_state.selected_lat:.6f}, {st.session_state.selected_lng:.6f}")

    st.markdown("---")

    st.markdown("### 📸 PHOTO")
    photo_data = st.session_state.get('photo_data', None)

    col_btn_cam, _ = st.columns(2)
    with col_btn_cam:
        if st.button("📷 Activer la caméra", key="cam_nv", width='stretch'):
            st.session_state.camera_enabled = True
            st.rerun()

    if st.session_state.camera_enabled:
        camera_photo = st.camera_input("Prenez une photo", key="camera_nv")
        if camera_photo:
            st.session_state.photo_data = camera_photo
            # Stocker la photo pour le signalement (à sauvegarder plus tard)
            st.session_state[f'pending_photo'] = camera_photo
            photo_data = camera_photo
            st.success("✅ Photo prise avec succès !")
        if st.button("🔒 Désactiver la caméra", key="disable_cam_nv"):
            st.session_state.camera_enabled = False
            st.rerun()

    uploaded_file = st.file_uploader(
        "📁 Upload depuis galerie",
        type=['jpg', 'jpeg', 'png', 'webp'],
        key="upload_nv"
    )
    if uploaded_file:
        st.session_state.photo_data = uploaded_file
        st.session_state[f'pending_photo'] = uploaded_file
        photo_data = uploaded_file
        st.success("✅ Photo uploadée avec succès !")

    if photo_data:
        st.image(photo_data, width=300)
        if st.button("🗑️ Supprimer", key="delete_photo_nv"):
            st.session_state.photo_data = None
            st.rerun()

    st.markdown("---")

    quartier = st.text_input("Quartier", placeholder="Ex: Yopougon, Cocody, etc.", key="quartier_nv")
    description = st.text_area(
        "Description (optionnelle)",
        placeholder="Décrivez le problème...",
        height=100,
        key="desc_nv"
    )

    st.markdown("---")

    accept = st.checkbox("✅ J'accepte la publication sur blockchain (immuable)", key="accept_nv")

    with st.container():
        st.warning("🦊 **Une pop-up MetaMask doit apparaître pour confirmer la transaction.**")
        st.info("💡 Si elle ne s'affiche pas : vérifiez que les fenêtres pop-up sont autorisées pour ce site.", icon="🔧")
        submitted = st.button("🚀 SIGNALER SUR BLOCKCHAIN", type="primary", width='stretch', key="submit_nv")

    if submitted:
        if not accept:
            st.error("⚠️ Veuillez accepter la publication sur blockchain")
        elif not type_probleme:
            st.error("⚠️ Veuillez sélectionner un type de problème")
        elif not quartier:
            st.error("⚠️ Veuillez indiquer le quartier")
        elif not st.session_state.wallet_connected:
            st.error("⚠️ Veuillez connecter votre wallet dans la sidebar")
        else:
            new_id = f"SIG-{len(st.session_state.signalements)+1:03d}"
            nouvel_signalement = {
                'id': new_id,
                'type': type_probleme,
                'quartier': quartier,
                'date': datetime.now().isoformat(),
                'statut': 'en_attente',
                'lat': st.session_state.selected_lat,
                'lng': st.session_state.selected_lng,
                'description': description,
                'tx_hash': 'en_attente',
                'signale_par': st.session_state.wallet_address[:10]
            }
            st.session_state.signalements.append(nouvel_signalement)
            signalement_index = len(st.session_state.signalements) - 1
            if st.session_state.get('pending_photo'):
                st.session_state[f'photo_{new_id}'] = st.session_state.pending_photo
                st.session_state.pending_photo = None
            
            with st.spinner("📡 Envoi au backend sponsor..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/sponsor",
                        json={
                            'type': type_probleme,
                            'description': description,
                            'quartier': quartier,
                            'lat': st.session_state.selected_lat,
                            'lng': st.session_state.selected_lng,
                            'user_address': st.session_state.wallet_address
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        tx_hash = data.get('tx_hash')
                        if tx_hash:
                            st.session_state.signalements[signalement_index]['tx_hash'] = tx_hash
                            st.success(f"✅ Transaction envoyée ! Hash : {tx_hash[:10]}...")
                            st.session_state.page = 'accueil'
                            st.rerun()
                        else:
                            st.error("❌ Le backend n'a pas retourné de hash")
                    else:
                        st.error(f"❌ Erreur backend : {response.text}")
                except Exception as e:
                    st.error(f"❌ Échec de l'appel au sponsor : {e}")

# ==================== PAGE CONFIRMATION ====================
elif st.session_state.page == 'confirmation':
    report_id = st.session_state.get('pending_report_id')
    if not report_id:
        st.error("Erreur : aucun signalement en cours")
        st.stop()
    
    st.info("📤 Transaction en cours...")
    st.stop()

# ==================== PAGE MES SIGNALEMENTS ====================
elif st.session_state.page == 'mes_signalements':
    st.markdown("## 📋 Mes signalements")
    
    # Bouton de rafraîchissement
    col_refresh, col_spacer = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Rafraîchir", width='stretch'):
            st.rerun()
    
    st.markdown("---")

    if not st.session_state.signalements:
        st.info("📭 Aucun signalement trouvé")
    else:
        # Afficher la liste des signalements avec bouton d'impression
        for idx, s in enumerate(reversed(st.session_state.signalements)):
            # Date
            if isinstance(s['date'], datetime):
                date_obj = s['date']
            else:
                date_obj = datetime.fromisoformat(str(s['date']))
            date_str = date_obj.strftime('%d/%m/%Y %H:%M:%S')
            
            # Lien Etherscan
            tx_hash = s.get('tx_hash', '')
            if tx_hash and len(tx_hash) == 66 and tx_hash.startswith('0x'):
                lien = f'<a href="https://sepolia.etherscan.io/tx/{tx_hash}" target="_blank">🔍 Voir sur Etherscan</a>'
            else:
                lien = "⏳ En attente de confirmation"
            
            # Statut
            statut_map = {
                'en_attente': '⏳ En attente',
                'en_cours': '🔄 En cours',
                'resolu': '✅ Résolu'
            }
            statut_fr = statut_map.get(s['statut'], s['statut'])
            
            # Afficher la carte du signalement
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"""
                    <div style="background: #FFF8F0; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #FF7F00;">
                        <b style="color:#FF7F00;">#{s['id']}</b><br>
                        <b>Type:</b> {s['type']}<br>
                        <b>Quartier:</b> {s['quartier']}<br>
                        <b>Date:</b> {date_str}<br>
                        <b>Statut:</b> {statut_fr}<br>
                        <b>Hash/Lien:</b> {lien}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if s.get('description'):
                        st.markdown(f"""
                        <div style="background: #FFF8F0; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                            <b>📝 Description:</b><br>
                            <i>{s['description'][:100]}...</i>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col3:
                    # Bouton d'impression PDF
                    if st.button(f"🖨️ PDF", key=f"print_pdf_{s['id']}_{idx}", width='stretch'):
                        try:
                            # Récupérer la photo associée si disponible
                            photo = st.session_state.get(f'photo_{s["id"]}', None)
                            
                            # Générer le PDF
                            pdf_buffer = generate_report_pdf(s, photo)
                            
                            # Proposer le téléchargement
                            st.download_button(
                                label="📥 Télécharger le PDF",
                                data=pdf_buffer,
                                file_name=f"Signalement_{s['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                key=f"download_{s['id']}_{idx}"
                            )
                            st.success(f"✅ PDF généré pour le signalement {s['id']}")
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la génération du PDF: {str(e)}")
            
            st.markdown("---")
        
        # Version tableau (alternative)
        with st.expander("📊 Vue tableau des signalements"):
            data = []
            for s in reversed(st.session_state.signalements):
                if isinstance(s['date'], datetime):
                    date_obj = s['date']
                else:
                    date_obj = datetime.fromisoformat(str(s['date']))
                date_str = date_obj.strftime('%d/%m/%Y %H:%M:%S')
                
                tx_hash = s.get('tx_hash', '')
                if tx_hash and len(tx_hash) == 66 and tx_hash.startswith('0x'):
                    lien = f'<a href="https://sepolia.etherscan.io/tx/{tx_hash}" target="_blank">🔍 Voir</a>'
                else:
                    lien = "⏳ En attente"
                
                statut_map = {
                    'en_attente': '⏳ En attente',
                    'en_cours': '🔄 En cours',
                    'resolu': '✅ Résolu'
                }
                statut_fr = statut_map.get(s['statut'], s['statut'])
                
                data.append({
                    'ID': s['id'],
                    'Type': s['type'],
                    'Quartier': s['quartier'],
                    'Date': date_str,
                    'Statut': statut_fr,
                    'Hash': lien
                })
            
            df = pd.DataFrame(data)
            st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            st.caption(f"📊 Total : {len(st.session_state.signalements)} signalements")

    st.markdown("---")
    if st.button("➕ NOUVEAU SIGNALEMENT", width='stretch'):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()

# ==================== PAGE CARTE PUBLIQUE ====================
elif st.session_state.page == 'carte_publique':
    st.markdown("## 🗺️ SentinelleCI - Carte Publique")
    
    with st.expander("🔍 FILTRES", expanded=True):
        colF1, colF2, colF3, colF4 = st.columns(4)
        with colF1:
            st.multiselect("Type de problème", ["Route", "École", "Éclairage", "Eau"], key="filter_type_carte")
        with colF2:
            st.selectbox("Statut", ["Tous", "En attente", "En cours", "Résolu"], key="select_statut_carte")
        with colF3:
            st.selectbox("Période", ["30 derniers jours", "Ce mois", "Cette année"], key="select_periode_carte")
        with colF4:
            st.selectbox("Commune", ["Toutes", "Yopougon", "Abobo", "Cocody", "Plateau"], key="select_commune_carte")
    
    col_map, col_list = st.columns([2, 1])
    
    with col_map:
        m = create_map(zoom=12)
        st_folium(m, width=600, height=500, key="folium_carte_publique")
    
    with col_list:
        st.markdown("### 📍 Signalements à proximité")
        for s in st.session_state.signalements[:5]:
            tx_hash = s.get('tx_hash')
            if tx_hash and isinstance(tx_hash, str) and len(tx_hash) >= 15:
                hash_display = tx_hash[:15] + '...'
            else:
                hash_display = "⏳ En attente"
            st.markdown(f"""
            <div style="background: #FFF8F0; border-radius: 10px; padding: 10px; margin-bottom: 10px; border: 1px solid #FF7F00;">
                <b style="color:#FF7F00;">#{s['id']}</b> – {s['type']}<br>
                📍 {s['quartier']}<br>
                <code style="background: #f0f0f0; color: #FF7F00; padding: 2px 5px; border-radius: 4px;">{hash_display}</code>
            </div>
            """, unsafe_allow_html=True)
        
        # Ajouter un bouton d'impression pour le premier signalement
        if st.session_state.signalements:
            s = st.session_state.signalements[0]
            if st.button(f"🖨️ PDF #{s['id']}", key=f"print_carte_{s['id']}", width='stretch'):
                try:
                    photo = st.session_state.get(f'photo_{s["id"]}', None)
                    pdf_buffer = generate_report_pdf(s, photo)
                    st.download_button(
                        label="📥 Télécharger",
                        data=pdf_buffer,
                        file_name=f"Signalement_{s['id']}.pdf",
                        mime="application/pdf",
                        key=f"download_carte_{s['id']}"
                    )
                except Exception as e:
                    st.error(f"Erreur: {str(e)}") 

# ==================== PAGE MAIRIE ====================
elif st.session_state.page == 'mairie':
    st.markdown("## 🏛️ MAIRIE DE YOPOUGON")
    st.markdown("### Tableau de bord")
    
    # Statistiques
    colK1, colK2, colK3, colK4 = st.columns(4)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    en_cours = len([s for s in st.session_state.signalements if s['statut'] == 'en_cours'])
    resolus = len([s for s in st.session_state.signalements if s['statut'] == 'resolu'])
    total = len(st.session_state.signalements)
    
    with colK1:
        st.metric("📋 En attente", en_attente)
    with colK2:
        st.metric("🚧 En cours", en_cours)
    with colK3:
        st.metric("✅ Résolus", resolus)
    with colK4:
        st.metric("📊 Total", total)
    
    st.markdown("---")

    # Section Export
    st.markdown("### 📥 EXPORT DES DONNÉES")
    col_export1, col_export2, col_export3 = st.columns(3)
    
    with col_export1:
        # Filtre pour l'export
        export_filter = st.selectbox(
            "Filtrer par statut", 
            ["Tous", "En attente", "En cours", "Résolus"],
            key="export_filter"
        )
    with col_export2:
        if st.button("📊 Exporter vers Excel", type="primary", width='stretch'):
            filter_map = {
                "Tous": None,
                "En attente": "en_attente",
                "En cours": "en_cours",
                "Résolus": "resolu"
            }
            status_filter = filter_map.get(export_filter)
            
            excel_data = export_signalements_to_excel(st.session_state.signalements, status_filter)
            st.download_button(
                label="📥 Télécharger Excel",
                data=excel_data,
                file_name=f"signalements_mairie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
    
    with col_export3:
        if st.button("📄 Rapport PDF", width='stretch'):
            pdf_data = generate_mairie_pdf(st.session_state.signalements)
            st.download_button(
                label="📥 Télécharger PDF",
                data=pdf_data,
                file_name=f"rapport_mairie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                width='stretch'
            )
    
    st.markdown("---") 

    # Carte améliorée avec zoom
    st.markdown("### 🗺️ CARTE DÉTAILLÉE DES SIGNALEMENTS")
    
    # Contrôles de zoom
    col_zoom1, col_zoom2, col_zoom3, col_zoom4 = st.columns(4)
    with col_zoom1:
        zoom_level = st.slider("Niveau de zoom", 10, 18, 13, key="map_zoom")
    with col_zoom2:
        show_attente = st.checkbox("Afficher en attente", value=True, key="show_attente")
    with col_zoom3:
        show_cours = st.checkbox("Afficher en cours", value=True, key="show_cours")
    with col_zoom4:
        show_resolu = st.checkbox("Afficher résolus", value=True, key="show_resolu")
    
    # Filtrer les signalements pour la carte
    filtered_signalements = []
    for s in st.session_state.signalements:
        if s['statut'] == 'en_attente' and show_attente:
            filtered_signalements.append(s)
        elif s['statut'] == 'en_cours' and show_cours:
            filtered_signalements.append(s)
        elif s['statut'] == 'resolu' and show_resolu:
            filtered_signalements.append(s)
    m = create_detailed_map(filtered_signalements, zoom_start=zoom_level)
    st_folium(m, width=1100, height=550, key="folium_mairie_detailed")
    
    st.markdown("---")
    
    col_chart, col_list = st.columns([1, 1])
    with col_chart:
        st.markdown("### 📊 RÉPARTITION STATISTIQUE")
        fig = create_donut_chart()
        st.plotly_chart(fig, use_container_width=True, key="plotly_donut_mairie")
        
        st.markdown("""
        <div style="background: #FFF8F0; padding: 15px; border-radius: 12px; margin-top: 10px; border: 1px solid #FF7F00;">
            <b style="color:#FF7F00;">📖 Légende :</b><br>
            <span style="color: #FF7F00;">🔴 En attente</span> - Signalements non encore traités<br>
            <span style="color: #ffa500;">🟠 En cours</span> - Signalements en cours de traitement<br>
            <span style="color: #00CD00;">🟢 Résolus</span> - Signalements terminés
        </div>
        """, unsafe_allow_html=True)
    
    with col_list:
        st.markdown("### 🚨 SIGNALEMENTS NON PRIS EN CHARGE")
        non_pris = [s for s in st.session_state.signalements if s['statut'] == 'en_attente']
        if non_pris:
            for i, s in enumerate(non_pris[:5]):
                col_id, col_type, col_quartier, col_action = st.columns([1, 1, 1, 2])
                with col_id:
                   st.write(s['id'])
                with col_type:
                   st.write(s['type'])
                with col_quartier:
                   st.write(s['quartier'])
                with col_action:
                    # Bouton PRENDRE pour la prise en charge
                    if st.button("PRENDRE", key=f"btn_prendre_mairie_{i}", width='stretch'):
                       st.session_state.selected_signalement = s
                       st.session_state.show_prise_en_charge = True
                       st.rerun()
                
                    # Bouton Fiche (optionnel)
                    if st.button("🖨️ Fiche", key=f"btn_fiche_{i}", width='stretch'):
                        pdf_fiche = generate_report_pdf(s, None)
                        st.download_button(
                            label="📥 Télécharger",
                            data=pdf_fiche,
                            file_name=f"Signalement_{s['id']}.pdf",
                            mime="application/pdf",
                            key=f"download_fiche_{i}"
                        )
            if len(non_pris) > 5:
                st.info(f"... et {len(non_pris) - 5} autres")
        else:
            st.info("✅ Aucun signalement en attente")

    # Vue zoomée sur un signalement spécifique
    st.markdown("### 🔍 VUE ZOOMÉE SUR UN SIGNALEMENT")
    
    col_select, col_btn_zoom = st.columns([3, 1])
    with col_select:
        selected_report_id = st.selectbox(
            "Sélectionnez un signalement à zoomer",
            options=[s['id'] for s in st.session_state.signalements],
            key="zoom_select"
        )
    
    with col_btn_zoom:
        if st.button("🔍 Zoomer sur ce signalement", width='stretch'):
            for s in st.session_state.signalements:
                if s['id'] == selected_report_id and s.get('lat') and s.get('lng'):
                    # Créer une carte zoomée sur ce signalement
                    zoom_map = folium.Map(
                        location=[s['lat'], s['lng']], 
                        zoom_start=16,
                        tiles='OpenStreetMap'
                    )
                    
                    # Marker avec toutes les infos
                    popup_html = f"""
                    <div style="min-width: 250px;">
                        <h4 style="color: #FF7F00;">{s['type']}</h4>
                        <b>ID:</b> {s['id']}<br>
                        <b>Quartier:</b> {s['quartier']}<br>
                        <b>Statut:</b> {get_status_fr(s['statut'])}<br>
                        <b>Date:</b> {s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime) else str(s['date'])[:10]}<br>
                        <b>Lat/Lng:</b> {s['lat']:.6f}, {s['lng']:.6f}<br>
                        <a href="https://www.google.com/maps?q={s['lat']},{s['lng']}" target="_blank">
                            🗺️ Ouvrir dans Google Maps
                        </a>
                    </div>
                    """
                    
                    folium.Marker(
                        location=[s['lat'], s['lng']],
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(color='red', icon='info-sign', icon_color='white')
                    ).add_to(zoom_map)
                    
                    # Ajouter un cercle pour mieux voir
                    folium.Circle(
                        radius=50,
                        location=[s['lat'], s['lng']],
                        popup="Zone du signalement",
                        color='#FF7F00',
                        fill=True
                    ).add_to(zoom_map)
                    
                    st_folium(zoom_map, width=800, height=400, key="zoomed_map")
                    break
    
    st.markdown("---")
    
    st.markdown("### 🔧 SIGNALEMENTS EN COURS DE TRAITEMENT")
    en_cours_list = [s for s in st.session_state.signalements if s['statut'] == 'en_cours']
    if en_cours_list:
        for i, s in enumerate(en_cours_list):
            col_id, col_type, col_quartier, col_agent, col_action = st.columns([1, 1, 1, 1, 1])
            with col_id:
                st.write(s['id'])
            with col_type:
                st.write(s['type'])
            with col_quartier:
                st.write(s['quartier'])
            with col_agent:
                agent = s.get('agent', 'Non assigné')
                st.write(agent)
            with col_action:
                if st.button("✅ RÉSOUDRE", key=f"btn_resoudre_{i}"):
                    for sig in st.session_state.signalements:
                        if sig['id'] == s['id']:
                            sig['statut'] = 'resolu'
                            sig['date_resolution'] = datetime.now().isoformat()
                            break
                    st.success(f"Signalement {s['id']} marqué comme résolu !")
                    st.rerun()
            st.divider()
    else:
        st.info("🎉 Aucun signalement en cours")

    st.markdown("---")
    st.markdown("### ✅ SIGNALEMENTS RÉSOLUS")
    resolus_list = [s for s in st.session_state.signalements if s['statut'] == 'resolu']
    if resolus_list:
        for i, s in enumerate(resolus_list):
            col_id, col_type, col_quartier, col_agent, col_date = st.columns([1, 1, 1, 1, 2])
            with col_id:
                st.write(s['id'])
            with col_type:
                st.write(s['type'])
            with col_quartier:
                st.write(s['quartier'])
            with col_agent:
                agent = s.get('agent', 'Non assigné')
                st.write(agent)
            with col_date:
                date_reso = s.get('date_resolution', 'Date inconnue')
                if isinstance(date_reso, str):
                    try:
                        date_reso = datetime.fromisoformat(date_reso).strftime('%d/%m/%Y')
                    except:
                        pass
                st.write(f"📅 {date_reso}")
            st.divider()
    else:
        st.info("📭 Aucun signalement résolu pour le moment")

    # PRISE EN CHARGE
    st.markdown("""
<style>
    /* Forcer le style du calendrier - Version complète */
    
    /* Conteneur du date input */
    .stDateInput > div > div {
        background-color: white !important;
    }
    
    /* Champ de saisie */
    .stDateInput input {
        background-color: white !important;
        color: #1a1a1a !important;
        border: 2px solid #FF7F00 !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
    }
    
    /* Overlay du calendrier */
    .stDateInput [data-baseweb="popover"] {
        background-color: white !important;
        border: 2px solid #FF7F00 !important;
        border-radius: 10px !important;
    }
    
    /* Calendrier lui-même */
    [data-baseweb="calendar"] {
        background-color: white !important;
        border: none !important;
    }
    
    /* En-tête du calendrier */
    [data-baseweb="calendar"] [aria-label="calendar header"] {
        background-color: #FF7F00 !important;
        color: white !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 12px !important;
    }
    
    /* Mois et année */
    [data-baseweb="calendar"] [aria-label="month"] {
        color: white !important;
        font-weight: bold !important;
    }
    
    /* Navigation */
    [data-baseweb="calendar"] [aria-label="calendar previous month"] svg,
    [data-baseweb="calendar"] [aria-label="calendar next month"] svg {
        fill: white !important;
    }
    
    /* Jours de la semaine */
    [data-baseweb="calendar"] button[aria-label="day of week"] {
        color: #FF7F00 !important;
        font-weight: bold !important;
    }
    
    /* Jours normaux */
    [data-baseweb="calendar"] button[aria-label="calendar day"] {
        color: #1a1a1a !important;
        background-color: white !important;
    }
    
    /* Hover sur les jours */
    [data-baseweb="calendar"] button[aria-label="calendar day"]:hover {
        background-color: #FFF8F0 !important;
        color: #FF7F00 !important;
        border-radius: 50% !important;
    }
    
    /* Jour sélectionné */
    [data-baseweb="calendar"] button[aria-selected="true"] {
        background-color: #FF7F00 !important;
        color: white !important;
        border-radius: 50% !important;
    }
    
    /* Jour actuel */
    [data-baseweb="calendar"] button[aria-current="date"] {
        border: 2px solid #FF7F00 !important;
        font-weight: bold !important;
    }
    
    /* Jours désactivés */
    [data-baseweb="calendar"] button:disabled {
        color: #cccccc !important;
    }
    
    /* Sélecteur de mois/année */
    [data-baseweb="calendar"] select {
        background-color: #FF7F00 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }
    
    /* Option du select */
    [data-baseweb="calendar"] select option {
        background-color: white !important;
        color: #FF7F00 !important;
    }
    
    /* Icône du calendrier */
    .stDateInput svg {
        fill: #FF7F00 !important;
        stroke: #FF7F00 !important;
    }
    
    /* Bouton d'ouverture */
    .stDateInput button {
        background-color: #FF7F00 !important;
        border-radius: 0 8px 8px 0 !important;
    }
</style>
""", unsafe_allow_html=True)
    
    if st.session_state.show_prise_en_charge and st.session_state.get('selected_signalement'):
        st.markdown("---")
        st.markdown("## 📋 PRISE EN CHARGE")
        
        s = st.session_state.selected_signalement
        with st.form("prise_en_charge_unique"):
            st.info(f"**#{s['id']}** – {s['type']} – {s['quartier']}")
            agent = st.selectbox("Assigner à", ["Koffi A.", "Diallo M.", "Kouadio L.", "Yao B."], key="select_agent_unique")
            commentaire = st.text_area("Commentaire", key="textarea_comment_unique")
            date_interv = st.date_input("Date prévue", datetime.now() + timedelta(days=7), key="date_interv_unique")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submitted = st.form_submit_button("✅ VALIDER", type="primary")
                if submitted:
                    for sig in st.session_state.signalements:
                        if sig['id'] == s['id']:
                            sig['statut'] = 'en_cours'
                            sig['agent'] = agent
                            sig['commentaire'] = commentaire
                            sig['date_intervention'] = date_interv.isoformat()
                            break
                    st.session_state.show_prise_en_charge = False
                    st.success("✅ Signalement pris en charge")
                    st.rerun()
            with col_btn2:
                if st.form_submit_button("❌ ANNULER"):
                    st.session_state.show_prise_en_charge = False
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### 👥 AGENTS MAIRIE")
    st.markdown("""
    <style>
         .agents-list {
             background: #FFF8F0; 
             padding: 15px; 
             border-radius: 10px;
             color: #1a1a1a;
             border: 1px solid #FF7F00;
         }
         .agents-list span {
             color: #1a1a1a;
         }
    </style>
    <div class="agents-list">
        - 👤 <strong>Koffi A.</strong> (3 interventions)<br>
        - 👤 <strong>Diallo M.</strong> (2 interventions)<br>
        - 👤 <strong>Kouadio L.</strong> (1 intervention)<br>
        - 👤 <strong>Yao B.</strong> (1 intervention)
    </div>
    """, unsafe_allow_html=True)

# ==================== PAGE PROFIL ====================
elif st.session_state.page == 'profil':
    st.markdown("## 👤 Mon profil")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 👤 Citoyen")
        st.markdown("Membre depuis avril 2026")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mes signalements", len(st.session_state.signalements))
    with col2:
        st.metric("Résolus", len([s for s in st.session_state.signalements if s['statut'] == 'resolu']))
    
    st.markdown("### ⚙️ Préférences")
    st.checkbox("Notifications", value=True, key="pref_notifications")
    st.selectbox("Langue", ["Français", "English"], key="pref_langue")

# ==================== FOOTER ====================
st.markdown("""
<div class="footer">
    <p style="color: #1a1a1a; margin: 0;">© 2026 Sentinelle.CI - Plateforme citoyenne de signalement sur blockchain | Version 2.0 - Transactions réelles sur Sepolia</p>
</div>
""", unsafe_allow_html=True)
