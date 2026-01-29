import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Finans Ekranı", 
    layout="wide", 
    page_icon="📈",
    initial_sidebar_state="collapsed"
)

# --- 2. GÖRÜNÜMÜ TEMİZLEME (CSS) ---
st.markdown("""
    <style>
        /* Gereksiz Menüleri ve İkonları Gizle */
        header, .stAppHeader, [data-testid="stHeader"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        footer, .stFooter {display: none !important;}
        div[class^="viewerBadge"] {display: none !important;}
        
        /* Sayfa Düzeni */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Metrik Kutuları */
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. VARLIK LİSTESİ ---
VARLIKLAR = {
    "Gram Altın": "GRAM_ALTIN",
    "Dolar/TL": "TRY=X",
    "Euro/TL": "EURTRY=X",
    "Sterlin/TL": "GBPTRY=X",
    "BIST 100": "XU100.IS",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Ons Altın": "GC=F",
    "Gümüş": "GUMUS_TL",
    "THY (THYAO)": "THYAO.IS",
    "Aselsan (ASELS)": "ASELS.IS",
    "Garanti (GARAN)": "GARAN.IS",
    "Ereğli (EREGL)": "EREGL.IS",
    "Şişecam (SISE)": "SISE.IS",
    "Tüpraş (TUPRS)": "TUPRS.IS",
    "Akbank (AKBNK)": "AKBNK.IS",
    "Koç Holding (KCHOL)": "KCHOL.IS"
}

# --- 4. ÜST PANEL (SEÇİM VE VADE) ---
col_secim, col_vade = st.columns([3, 1])

with col_secim:
    secilen_isim = st.selectbox(
        "Varlık Seçiniz:",
        options=list(VARLIKLAR.keys()),
        index=0
    )

with col_vade:
    # Vade seçeneğini geri getirdim
    vade_secimi = st.selectbox(
        "Süre:",
        options=["1 Hafta", "1 Ay", "3 Ay", "6 Ay", "1 Yıl", "5 Yıl"],
        index=1
    )

# Vadeye göre gün sayısı haritası
vade_map = {
    "1 Hafta": "5d", # 5 işlem günü
    "1 Ay": "1mo",
    "3 Ay": "3mo",
    "6 Ay": "6mo",
    "1 Yıl": "1y",
    "5 Yıl": "5y"
}

# --- 5. VERİ MOTORU ---
@st.cache_data(ttl=300)
def veri_getir(sembol_kodu, periyot):
    try:
        # ALTIN ÖZEL HESAPLAMA
        if sembol_kodu in ["GRAM_ALTIN", "GUMUS_TL"]:
            ons_kodu = "GC=F" if sembol_kodu == "GRAM_ALTIN" else "SI=F"
            
            # Veriyi biraz geniş çekip filtreleyeceğiz (daha sağlıklı grafik için)
            ons = yf.download(ons_kodu, period=periyot, progress=False)
            usd = yf.download("TRY=X", period=periyot, progress=False)
            
            # MultiIndex düzeltme
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            # Birleştir
            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))
            df.dropna(inplace=True)
            
            # Gram Formülü
            gram_tl = (df['Close_Ons'] * df['Close_Usd']) / 31.1035
            df_final = pd.DataFrame({'Date': df.index, 'Close': gram_tl})
            
        else:
            # NORMAL HİSSE/KRİPTO
            df = yf.download(sembol_kodu, period=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # Reset Index
            df.reset_index(inplace=True)
            
            # Tarih sütunu düzeltme
            if 'Date' not in df.columns:
                col = next((c for c in df.columns if 'date' in c.lower()), None)
                if col: df.rename(columns={col: 'Date'}, inplace=True)
            
            df_final = df[['Date', 'Close']]

        return df_final
    except:
        return None

# --- 6. EKRAN GÖSTERİMİ ---
if secilen_isim:
    kod = VARLIKLAR[secilen_isim]
    secilen_periyot = vade_map[vade_secimi]
    
    with st.spinner("Veriler yükleniyor..."):
        df = veri_getir(kod, secilen_periyot)
    
    if df is not None and not df.empty:
        # Son Veriler
        son_fiyat = float(df['Close'].iloc[-1])
        ilk_fiyat = float(df['Close'].iloc[0]) # Seçilen periyodun başı
        
        degisim = son_fiyat - ilk_fiyat
        yuzde_degisim = (degisim / ilk_fiyat) * 100
        
        # Metrikler (Yan Yana)
        m1, m2, m3 = st.columns(3)
        m1.metric("Son Fiyat", f"{son_fiyat:,.2f} TL")
        m2.metric(f"{vade_secimi} Değişim", f"{degisim:,.2f} TL", f"%{yuzde_degisim:.2f}")
        m3.metric("En Yüksek (Dönem)", f"{df['Close'].max():,.2f} TL")
        
        # Grafik (Sade, Yorumsuz)
        st.write("")
        fig = go.Figure()
        
        # Çizgi Grafik
        fig.add_trace(go.Scatter(
            x=df['Date'], 
            y=df['Close'],
            mode='lines',
            name=secilen_isim,
            line=dict(color='#0078FF', width=2),
            fill='tozeroy', # Altını hafif dolu göster
            fillcolor='rgba(0, 120, 255, 0.1)'
        ))
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=450, # PC için daha yüksek grafik
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#eee'),
            template="plotly_white",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.error("Veri alınamadı. Piyasa kapalı veya bağlantı sorunu olabilir.")
