import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Piyasa Durumu", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# --- 2. GÖRÜNÜMÜ SADELEŞTİRME (CSS) ---
st.markdown("""
    <style>
        /* Menüleri, Footer'ı ve Gereksiz İkonları Gizle */
        header, .stAppHeader, [data-testid="stHeader"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        footer {display: none !important;}
        
        /* Sayfa Düzeni */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* DURUM KUTUSU TASARIMI */
        .durum-kutu {
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-family: sans-serif;
            margin-bottom: 20px;
            border: 1px solid #ddd;
        }
        .baslik { font-size: 22px; font-weight: bold; display: block; margin-bottom: 8px; }
        .aciklama { font-size: 18px; }
        
        /* Renk Sınıfları */
        .pozitif { background-color: #e6fffa; color: #047481; border-color: #b2f5ea; }
        .negatif { background-color: #fff5f5; color: #c53030; border-color: #fed7d7; }
        .notr { background-color: #fffff0; color: #b7791f; border-color: #fefcbf; }
    </style>
""", unsafe_allow_html=True)

# --- 3. VARLIK LİSTESİ ---
VARLIKLAR = {
    "Gram Altın": "GRAM_ALTIN",
    "Dolar/TL": "TRY=X",
    "Euro/TL": "EURTRY=X",
    "BIST 100": "XU100.IS",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "THY": "THYAO.IS",
    "Aselsan": "ASELS.IS",
    "Garanti": "GARAN.IS",
    "Şişecam": "SISE.IS",
    "Tüpraş": "TUPRS.IS"
}

# --- 4. VERİ ÇEKME ---
@st.cache_data(ttl=300)
def veri_al(sembol):
    try:
        # Altın Hesabı
        if sembol == "GRAM_ALTIN":
            ons = yf.download("GC=F", period="1mo", progress=False)
            usd = yf.download("TRY=X", period="1mo", progress=False)
            
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            df = pd.DataFrame()
            df['Close'] = (ons['Close'] * usd['Close']) / 31.1035
            df.index = ons.index
        else:
            df = yf.download(sembol, period="1mo", progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        return df
    except:
        return None

# --- 5. GENEL KANI ANALİZİ (Kişi Yok, Sadece Durum) ---
def durum_analizi(df):
    if df is None or df.empty:
        return "Veri Yok", "Veri alınamadı.", "notr"

    son = df['Close'].iloc[-1]
    bas = df['Close'].iloc[0] # 1 ay başı
    fark = ((son - bas) / bas) * 100
    
    # 5 Günlük kısa trend
    son_5_gun = df['Close'].tail(5).mean()
    trend_kisa = "Yüksek" if son > son_5_gun else "Düşük"

    # SENARYOLAR (Tamamen Nesnel)
    if fark > 5:
        baslik = "GÜÇLÜ YÜKSELİŞ TRENDİ"
        metin = "Fiyatlar belirgin şekilde yukarı yönlü. Alıcılar piyasada baskın durumda. Değer kazancı yüksek."
        renk = "pozitif"
    elif fark > 1:
        baslik = "POZİTİF SEYİR"
        metin = "Piyasa sakin ama yönü yukarı. Aşırı bir hareketlilik yok, istikrarlı bir yükseliş gözleniyor."
        renk = "pozitif"
    elif fark > -1 and fark < 1:
        baslik = "YATAY / DURGUN"
        metin = "Fiyatlar belirgin bir değişim göstermiyor. Piyasa yön arayışında, kararsız bir seyir hakim."
        renk = "notr"
    elif fark < -5:
        baslik = "GÜÇLÜ SATIŞ BASKISI"
        metin = "Piyasada sert düşüş hakim. Satıcılar çok daha aktif, fiyatlarda ciddi geri çekilme var."
        renk = "negatif"
    else:
        baslik = "NEGATİF SEYİR"
        metin = "Piyasa hafif satıcılı. Fiyatlar gevşeme eğiliminde, talep zayıf görünüyor."
        renk = "negatif"
        
    return baslik, metin, renk, son, fark

# --- 6. ARAYÜZ ---
st.markdown("<h3 style='text-align: center;'>Piyasa Genel Görünümü</h3>", unsafe_allow_html=True)

secim = st.selectbox("İncelemek İstediğiniz Varlık:", list(VARLIKLAR.keys()))

if secim:
    df = veri_al(VARLIKLAR[secim])
    
    if df is not None and not df.empty:
        baslik, aciklama, renk, fiyat, yuzde = durum_analizi(df)
        
        # 1. DURUM KUTUSU (Tek Yorum, Kişisiz)
        st.markdown(f"""
            <div class="durum-kutu {renk}">
                <span class="baslik">{baslik}</span>
                <span class="aciklama">{aciklama}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. RAKAMLAR
        c1, c2 = st.columns(2)
        c1.metric("Fiyat", f"{fiyat:,.2f} TL")
        c2.metric("Aylık Değişim", f"%{yuzde:.2f}", delta_color="normal")
        
        # 3. GRAFİK
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines',
            line=dict(color='#333', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,0,0,0.05)'
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
        st.error("Veri alınamadı.")
