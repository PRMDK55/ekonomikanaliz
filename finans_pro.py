import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(page_title="Finans Ana", layout="wide", page_icon="📱")

# CSS: Hem mobili düzeltir hem de GitHub/Streamlit ikonlarını gizler
st.markdown("""
<style>
    /* 1. İstenmeyen İkonları ve Menüleri Gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stToolbar"] {visibility: hidden !important;}

    /* 2. Genel Arka Plan ve Mobil Ayarlar */
    .stApp {background-color: #f4f7f6;}
    
    /* Mobil İçin Kart Tasarımı */
    .stat-card {
        background-color: white; 
        padding: 15px; 
        border-radius: 12px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
        border-left: 5px solid #3498db;
    }
    
    /* Mobilde Yazı Boyutlarını Düzelt */
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
    }
    
    /* Butonları Mobilde Parmakla Basılacak Hale Getir */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 50px;
        font-weight: bold;
    }
    
    /* Üst Boşluğu Al (Telefonda yer kazanmak için) */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. VARLIK HAVUZU ---
varlik_havuzu = {
    "🇹🇷 BIST (Popüler)": [
        "THYAO", "ASELS", "GARAN", "EREGL", "SISE", "BIMAS", "AKBNK", "KCHOL", "SAHOL",
        "TUPRS", "FROTO", "SASA", "HEKTS", "PETKM", "TCELL", "YKBNK", "ISCTR",
        "ARCLK", "VESTL", "TOASO", "PGSUS", "KONYA", "EGEEN", "MIATK", "ASTOR", 
        "EUPWR", "KONTR", "SMRTG", "GUBRF", "KOZAL", "ODAS", "ZOREN"
    ],
    "🥇 Altın & Döviz": [
        "Gram Altın", "Çeyrek Altın", "Yarım Altın", "Ons Altın", "Gümüş (Gram)",
        "Dolar/TL", "Euro/TL", "Sterlin/TL"
    ],
    "₿ Kripto & ABD": [
        "BTC (Bitcoin)", "ETH (Ethereum)", "SOL (Solana)", "AVAX", "DOGE",
        "AAPL (Apple)", "TSLA (Tesla)", "NVDA (NVIDIA)", "AMZN"
    ]
}

# --- 3. AKILLI SEMBOL MOTORU ---
def sembol_cozucu(secim, manuel, kat):
    # Manuel giriş varsa öncelik ver
    if manuel:
        kod = manuel.upper().strip()
        # Kullanıcı sadece kodu yazarsa sonuna uzantı ekle
        if "BIST" in kat and ".IS" not in kod: return f"{kod}.IS", kod
        if "Kripto" in kat and "-USD" not in kod and len(kod) <= 4: return f"{kod}-USD", kod
        return kod, kod
    
    isim = secim
    ozel_map = {
        "Gram Altın": "GRAM_ALTIN", "Çeyrek Altın": "CEYREK_ALTIN",
        "Yarım Altın": "YARIM_ALTIN", "Ons Altın": "GC=F", "Gümüş (Gram)": "GUMUS_TL",
        "Dolar/TL": "TRY=X", "Euro/TL": "EURTRY=X", "Sterlin/TL": "GBPTRY=X"
    }
    
    for k, v in ozel_map.items():
        if k in isim: return v, k
        
    # BIST Hissesi mi?
    if "BIST" in kat: return f"{isim}.IS", isim
    
    # Kripto mu?
    if "Kripto" in kat:
        kod = isim.split("(")[0].strip()
        return f"{kod}-USD", kod
    
    return "THYAO.IS", "THYAO"

# --- 4. VERİ ÇEKME (HATA KORUMALI) ---
@st.cache_data(ttl=300)
def veri_getir(sembol, vade_gun):
    try:
        ozel_hesaplar = ["GRAM_ALTIN", "CEYREK_ALTIN", "YARIM_ALTIN", "GUMUS_TL"]
        periyot = "2y" # Yeterli veri için sabit
        
        # Özel Hesaplama Gerektirenler (Altın Çeşitleri)
        if sembol in ozel_hesaplar:
            ana_kod = "GC=F" if "ALTIN" in sembol else "SI=F"
            # MultiIndex sorununu çözmek için auto_adjust=False kullanabiliriz veya sütunları düzeltebiliriz
            ons = yf.download(ana_kod, period=periyot, progress=False)
            usd = yf.download("TRY=X", period=periyot, progress=False)
            
            # Sütun düzeltme (yfinance güncellemesi için kritik)
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            # Veri birleştirme
            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))
            
            # Hesaplamalar
            gram_saf = (df['Close_Ons'] * df['Close_Usd']) / 31.1035
            
            if sembol == "GRAM_ALTIN": df['Close'] = gram_saf
            elif sembol == "CEYREK_ALTIN": df['Close'] = gram_saf * 1.63 # Yaklaşık çarpan
            elif sembol == "YARIM_ALTIN": df['Close'] = gram_saf * 3.26
            elif sembol == "GUMUS_TL": df['Close'] = gram_saf # Gümüş ons/tl hesabı
            
            df['Open'] = df['High'] = df['Low'] = df['Close']
            df.reset_index(inplace=True)
            
        else:
            # Standart Hisse/Kripto
            df = yf.download(sembol, period=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)
        
        # Tarih sütunu standardizasyonu
        if 'Date' not in df.columns:
            if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Date'}, inplace=True)
            else: df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Veri hatası: {e}")
        return None

# --- 5. ARAYÜZ (YAN MENÜ) ---
with st.sidebar:
    st.title("📱 Cep Analiz")
    kat = st.selectbox("Pazar:", list(varlik_havuzu.keys()))
    secim = st.selectbox("Varlık:", varlik_havuzu[kat])
    
    st.write("---")
    manuel = st.text_input("🔍 Başka Ara (Örn: ASELS):", placeholder="Kod yaz...")
    
    st.write("---")
    vade = st.select_slider("Süre:", ["1 Hafta", "1 Ay", "6 Ay", "1 Yıl"], value="6 Ay")
    gun_map = {"1 Hafta": 7, "1 Ay": 30, "6 Ay": 180, "1 Yıl": 365}
    
    if st.button("🔄 Yenile"): st.rerun()

# --- 6. ANA EKRAN ---
kod, isim = sembol_cozucu(secim, manuel, kat)
st.subheader(f"📊 {isim}")

df_full = veri_getir(kod, gun_map[vade])

if df_full is not None and not df_full.empty:
    df_view = df_full.tail(gun_map[vade])
    
    # Son Veriler
    try:
        son = float(df_view['Close'].iloc[-1])
        onceki = float(df_view['Close'].iloc[0])
        degisim = ((son - onceki) / onceki) * 100
        
        # Metrikler
        c1, c2 = st.columns(2)
        c1.metric("Fiyat", f"{son:.2f}", f"%{degisim:.2f}")
        c2.metric("En Yüksek", f"{df_view['High'].max():.2f}")
        
        # Grafikler ve Yorum
        tab1, tab2 = st.tabs(["Grafik", "Analiz"])
        
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_view['Date'], 
                y=df_view['Close'], 
                mode='lines',
                line=dict(color='#2980b9', width=3),
                name='Fiyat'
            ))
            
            fig.update_layout(
                template="plotly_white", 
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#eee'),
                dragmode=False # Mobilde kaydırmayı engellemek için
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with tab2:
            if degisim > 0:
                st.success(f"**YÜKSELİŞ TRENDİ:** {vade} içinde %{degisim:.1f} değer kazandı.")
            else:
                st.error(f"**DÜŞÜŞ TRENDİ:** {vade} içinde %{abs(degisim):.1f} değer kaybetti.")
                
            st.caption(f"Veri kaynağı: Yahoo Finance | Son Güncelleme: {datetime.now().strftime('%H:%M')}")
            
    except Exception as e:
        st.error("Hesaplama hatası oluştu. Lütfen başka bir hisse deneyin.")
else:
    st.warning("Veri yükleniyor veya sembol bulunamadı...")
