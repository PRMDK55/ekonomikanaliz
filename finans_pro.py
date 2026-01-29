import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="Finans Ana v3.0", 
    layout="wide", 
    page_icon="💰",
    initial_sidebar_state="collapsed"
)

# --- 2. GÖRÜNÜMÜ TEMİZLEME (CSS) ---
st.markdown("""
    <style>
        /* Ana Menü ve Footer Gizleme */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Gelişmiş Gizleme (Toolbar vb.) */
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        
        /* Sayfa Kenar Boşluklarını Sıfırla */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Mobilde Kart Görünümü */
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. BAŞLIK VE VERSİYON KONTROLÜ ---
# Eğer bu yazıyı görmüyorsanız kod güncellenmemiştir!
st.markdown("<h3 style='text-align: center;'>FİNANS ANA V3.0</h3>", unsafe_allow_html=True)

# --- 4. VERİ LİSTESİ ---
# Tüm varlıkları tek bir havuzda topladım ki araması kolay olsun
TUM_VARLIKLAR = {
    # ALTIN VE DÖVİZ (Özel Kodlar)
    "Gram Altın": "GRAM_ALTIN",
    "Çeyrek Altın": "CEYREK_ALTIN",
    "Yarım Altın": "YARIM_ALTIN",
    "Ons Altın": "GC=F",
    "Gümüş": "GUMUS_TL",
    "Dolar/TL": "TRY=X",
    "Euro/TL": "EURTRY=X",
    "Sterlin/TL": "GBPTRY=X",
    
    # KRİPTO
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "Avax": "AVAX-USD",
    "Dogecoin": "DOGE-USD",
    
    # BORSA İSTANBUL (Popülerler)
    "THY (THYAO)": "THYAO.IS",
    "Aselsan (ASELS)": "ASELS.IS",
    "Garanti (GARAN)": "GARAN.IS",
    "Ereğli (EREGL)": "EREGL.IS",
    "Şişecam (SISE)": "SISE.IS",
    "BİM (BIMAS)": "BIMAS.IS",
    "Akbank (AKBNK)": "AKBNK.IS",
    "Koç Holding (KCHOL)": "KCHOL.IS",
    "Sasa (SASA)": "SASA.IS",
    "Hektaş (HEKTS)": "HEKTS.IS",
    "Tüpraş (TUPRS)": "TUPRS.IS",
    "Ford Otosan (FROTO)": "FROTO.IS",
    "Astor Enerji": "ASTOR.IS",
    "Kontrolmatik": "KONTR.IS",
    "Mia Teknoloji": "MIATK.IS"
}

# --- 5. GELİŞMİŞ ARAMA KUTUSU ---
st.write("---")
# Kullanıcıya hem seçim kutusu sunuyoruz hem de içine yazabiliyor
secilen_isim = st.selectbox(
    "🔍 Ne aramak istiyorsun? (Örn: Altın, Dolar, THY)",
    options=list(TUM_VARLIKLAR.keys()),
    index=0,
    placeholder="Yazmaya başla..."
)

# --- 6. VERİ ÇEKME FONKSİYONU ---
@st.cache_data(ttl=600) # 10 dakika önbellek
def veri_getir_ve_islet(isim, sembol):
    try:
        periyot = "1y"
        
        # ÖZEL HESAPLAMA (ALTIN/GÜMÜŞ)
        if sembol in ["GRAM_ALTIN", "CEYREK_ALTIN", "YARIM_ALTIN", "GUMUS_TL"]:
            ons_kodu = "GC=F" if "ALTIN" in sembol else "SI=F"
            ons = yf.download(ons_kodu, period=periyot, progress=False)
            usd = yf.download("TRY=X", period=periyot, progress=False)
            
            # Veri Düzeltme
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            # Birleştir
            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))
            df.dropna(inplace=True)
            
            gram_tl = (df['Close_Ons'] * df['Close_Usd']) / 31.1035
            
            if sembol == "GRAM_ALTIN": serisi = gram_tl
            elif sembol == "CEYREK_ALTIN": serisi = gram_tl * 1.63
            elif sembol == "YARIM_ALTIN": serisi = gram_tl * 3.26
            elif sembol == "GUMUS_TL": serisi = gram_tl
            
            df_final = pd.DataFrame({'Date': df.index, 'Close': serisi})
            
        else:
            # NORMAL HİSSE/KRİPTO
            df = yf.download(sembol, period=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df.reset_index(inplace=True)
            # Tarih sütunu adını garantile
            if 'Date' not in df.columns:
                if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Date'}, inplace=True)
                else: df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
            
            df_final = df[['Date', 'Close']]

        return df_final
    except Exception as e:
        return None

# --- 7. EKRANA BASMA ---
if secilen_isim:
    sembol = TUM_VARLIKLAR[secilen_isim]
    
    # Yükleniyor animasyonu
    with st.spinner(f"{secilen_isim} verileri çekiliyor..."):
        df = veri_getir_ve_islet(secilen_isim, sembol)
    
    if df is not None and not df.empty:
        # Son veriler
        son_fiyat = float(df['Close'].iloc[-1])
        onceki_fiyat = float(df['Close'].iloc[-2])
        degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
        
        # KART TASARIMI (HTML ile)
        renk = "#2ecc71" if degisim > 0 else "#e74c3c" # Yeşil veya Kırmızı
        ok = "⬆" if degisim > 0 else "⬇"
        
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="margin:0; color: #555;">{secilen_isim}</h2>
            <h1 style="margin:0; font-size: 40px;">{son_fiyat:,.2f} <span style="font-size: 20px;">TL</span></h1>
            <h3 style="margin:0; color: {renk};">{ok} %{degisim:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # GRAFİK
        st.write("")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'],
            mode='lines',
            fill='tozeroy', # Altını doldur
            line=dict(color='#3498db', width=2)
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
        st.error(f"⚠️ {secilen_isim} için şu an veri alınamıyor. Piyasalar kapalı olabilir veya bağlantı sorunu var.")
