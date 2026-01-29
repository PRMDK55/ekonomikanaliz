import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Finans Ana", 
    layout="wide", 
    page_icon="📉",
    initial_sidebar_state="collapsed"
)

# --- 2. GÖRÜNÜMÜ TAMAMEN TEMİZLEME (CSS) ---
st.markdown("""
    <style>
        /* 1. Üstteki Tüm Menüleri (Fork, GitHub, Toolbar) Yok Et */
        header, .stAppHeader, [data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
            opacity: 0 !important;
        }
        
        /* 2. Sağ Üst Menü (Üç Nokta) */
        [data-testid="stToolbar"] {
            display: none !important;
        }
        
        /* 3. Alttaki 'Manage App' ve Footer (Bunu zorlar ama Streamlit bazen engeller) */
        footer, .stFooter {
            display: none !important;
        }
        div[class^="viewerBadge"] {
            display: none !important;
        }
        
        /* 4. Sayfa Boşluklarını Ayarla */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* 5. Metrik Kutuları Tasarımı */
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. VERİ LİSTESİ (SADECE SEÇİLEBİLİR OLANLAR) ---
VARLIKLAR = {
    "Seçiniz...": None, # Başlangıçta boş gelsin
    "Gram Altın": "GRAM_ALTIN",
    "Dolar/TL": "TRY=X",
    "Euro/TL": "EURTRY=X",
    "BIST 100": "XU100.IS",
    "Türk Hava Yolları": "THYAO.IS",
    "Aselsan": "ASELS.IS",
    "Garanti BBVA": "GARAN.IS",
    "Ereğli Demir Çelik": "EREGL.IS",
    "Şişecam": "SISE.IS",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD"
}

# --- 4. ARAYÜZ (ARAMA YOK, SADECE LİSTE) ---
st.markdown("<h3 style='text-align: center;'>Piyasa Takip</h3>", unsafe_allow_html=True)

# Sadece açılır kutu (Dropdown)
secilen_isim = st.selectbox(
    "",
    options=list(VARLIKLAR.keys()),
    index=0, # İlk seçenek (Seçiniz) seçili gelsin
    label_visibility="collapsed" # Başlığı gizle
)

# --- 5. VERİ ÇEKME VE GÖSTERME ---
@st.cache_data(ttl=300)
def veri_getir(sembol_kodu):
    try:
        if not sembol_kodu: return None
        periyot = "1y"
        
        # ALTIN ÖZEL HESAPLAMA
        if sembol_kodu == "GRAM_ALTIN":
            ons = yf.download("GC=F", period=periyot, progress=False)
            usd = yf.download("TRY=X", period=periyot, progress=False)
            
            # Sütun temizliği
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))
            gram_tl = (df['Close_Ons'] * df['Close_Usd']) / 31.1035
            
            df_final = pd.DataFrame({'Date': df.index, 'Close': gram_tl})
            
        else:
            # NORMAL HİSSE
            df = yf.download(sembol_kodu, period=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)
            
            # Tarih sütununu bul
            if 'Date' not in df.columns:
                col = next((c for c in df.columns if 'date' in c.lower()), None)
                if col: df.rename(columns={col: 'Date'}, inplace=True)
            
            df_final = df[['Date', 'Close']]

        return df_final
    except:
        return None

# --- EKRAN MANTIĞI ---
if secilen_isim and VARLIKLAR[secilen_isim]:
    kod = VARLIKLAR[secilen_isim]
    
    with st.spinner(f"{secilen_isim} verisi yükleniyor..."):
        df = veri_getir(kod)
    
    if df is not None and not df.empty:
        # Hesaplamalar
        son_fiyat = float(df['Close'].iloc[-1])
        onceki_fiyat = float(df['Close'].iloc[-2])
        degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
        renk = "green" if degisim > 0 else "red"
        
        # Metrik Gösterimi
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.metric(label=secilen_isim, value=f"{son_fiyat:,.2f} ₺", delta=f"%{degisim:.2f}")
        
        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#0078FF', width=2)
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=20, b=0),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#eee'),
            template="plotly_white",
            dragmode=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.error("Veri alınamadı. Bağlantı sorunu olabilir.")
else:
    # Henüz seçim yapılmadıysa boş ekran veya bilgi mesajı
    st.info("👆 Lütfen yukarıdaki listeden bir varlık seçin.")
