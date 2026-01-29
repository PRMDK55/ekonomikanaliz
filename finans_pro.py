import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(
    page_title="Finans Ana", 
    layout="wide", 
    page_icon="📱",
    initial_sidebar_state="expanded"
)

# CSS: Üst barı, menüleri, footer'ı ve GitHub ikonlarını ZORLA gizler
st.markdown("""
<style>
    /* Üstteki Header (GitHub, Fork, Menü) Tamamen Yok Et */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Sağ üstteki Toolbar ve Seçenekler Menüsü */
    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Alttaki 'Made with Streamlit' Footer'ı */
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Geliştirici seçeneklerini gizle */
    .stDeployButton {
        display: none !important;
    }
    
    /* Sayfa üst boşluğunu sıfırla (Header gidince boşluk kalmasın) */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }
    
    /* Mobil Uyumlu Kart Tasarımı */
    .stApp {background-color: #f4f7f6;}
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
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

# --- 3. AKILLI SEMBOL MOTORU (GÜNCELLENDİ) ---
def sembol_cozucu(secim, manuel, kat):
    # Özel haritalama (Türkçe isim -> Yahoo Kodu)
    ozel_map = {
        "Gram Altın": "GRAM_ALTIN", "Çeyrek Altın": "CEYREK_ALTIN",
        "Yarım Altın": "YARIM_ALTIN", "Ons Altın": "GC=F", "Gümüş (Gram)": "GUMUS_TL",
        "Dolar/TL": "TRY=X", "Euro/TL": "EURTRY=X", "Sterlin/TL": "GBPTRY=X"
    }

    # 1. MANUEL ARAMA VARSA (Örn: "alt" veya "asels")
    if manuel:
        giris = manuel.strip()
        giris_lower = giris.lower()
        
        # A. Önce özel isimlerde ara (Örn: "alt" yazınca "Gram Altın" bulsun)
        for etiket, api_kodu in ozel_map.items():
            if giris_lower in etiket.lower():
                return api_kodu, etiket
        
        # B. Bulamazsa Hisse/Kripto kodu olarak varsay
        kod = giris.upper()
        
        # Kategoriye göre uzantı ekle (Eğer kullanıcı uzantı yazmadıysa)
        if "BIST" in kat and ".IS" not in kod: return f"{kod}.IS", kod
        if "Kripto" in kat and "-USD" not in kod and len(kod) <= 5: return f"{kod}-USD", kod
        return kod, kod

    # 2. LİSTEDEN SEÇİM VARSA
    isim = secim
    
    # Özel map kontrolü
    for k, v in ozel_map.items():
        if k in isim: return v, k
        
    # BIST Hissesi mi?
    if "BIST" in kat: return f"{isim}.IS", isim
    
    # Kripto mu?
    if "Kripto" in kat:
        kod = isim.split("(")[0].strip()
        return f"{kod}-USD", kod
    
    return "THYAO.IS", "THYAO"

# --- 4. VERİ ÇEKME ---
@st.cache_data(ttl=300)
def veri_getir(sembol, vade_gun):
    try:
        ozel_hesaplar = ["GRAM_ALTIN", "CEYREK_ALTIN", "YARIM_ALTIN", "GUMUS_TL"]
        periyot = "2y"
        
        if sembol in ozel_hesaplar:
            ana_kod = "GC=F" if "ALTIN" in sembol else "SI=F"
            ons = yf.download(ana_kod, period=periyot, progress=False)
            usd = yf.download("TRY=X", period=periyot, progress=False)
            
            # Sütun düzeltme
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))
            
            gram_saf = (df['Close_Ons'] * df['Close_Usd']) / 31.1035
            
            if sembol == "GRAM_ALTIN": df['Close'] = gram_saf
            elif sembol == "CEYREK_ALTIN": df['Close'] = gram_saf * 1.63
            elif sembol == "YARIM_ALTIN": df['Close'] = gram_saf * 3.26
            elif sembol == "GUMUS_TL": df['Close'] = gram_saf
            
            df['Open'] = df['High'] = df['Low'] = df['Close']
            df.reset_index(inplace=True)
            
        else:
            df = yf.download(sembol, period=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)
        
        if 'Date' not in df.columns:
            if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Date'}, inplace=True)
            else: df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
            
        return df
    except Exception as e:
        return None

# --- 5. ARAYÜZ ---
with st.sidebar:
    st.title("Cep Analiz")
    kat = st.selectbox("Pazar:", list(varlik_havuzu.keys()))
    secim = st.selectbox("Varlık:", varlik_havuzu[kat])
    
    st.write("---")
    # Placeholder'ı güncelledim
    manuel = st.text_input("🔍 Hızlı Ara (Örn: 'alt', 'asels'):", placeholder="Yaz ve Enter'a bas...")
    
    st.write("---")
    vade = st.select_slider("Süre:", ["1 Hafta", "1 Ay", "6 Ay", "1 Yıl"], value="6 Ay")
    gun_map = {"1 Hafta": 7, "1 Ay": 30, "6 Ay": 180, "1 Yıl": 365}
    
    if st.button("🔄 Yenile"): st.rerun()

# --- 6. ANA EKRAN ---
kod, isim = sembol_cozucu(secim, manuel, kat)

# Eğer manuel arama yapıldıysa ve bir şey bulunduysa kullanıcıya göster
if manuel and isim:
    st.info(f"🔍 Aranan: '{manuel}' -> Bulunan: **{isim}**")

st.subheader(f"📊 {isim}")

df_full = veri_getir(kod, gun_map[vade])

if df_full is not None and not df_full.empty:
    df_view = df_full.tail(gun_map[vade])
    
    try:
        son = float(df_view['Close'].iloc[-1])
        onceki = float(df_view['Close'].iloc[0])
        degisim = ((son - onceki) / onceki) * 100
        
        c1, c2 = st.columns(2)
        c1.metric("Fiyat", f"{son:.2f}", f"%{degisim:.2f}")
        c2.metric("Zirve", f"{df_view['High'].max():.2f}")
        
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
                dragmode=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with tab2:
            if degisim > 0:
                st.success(f"YÜKSELİŞ: {vade} içinde %{degisim:.1f} kazandırdı.")
            else:
                st.error(f"DÜŞÜŞ: {vade} içinde %{abs(degisim):.1f} kaybettirdi.")
            st.caption(f"Veri: Yahoo Finance | {datetime.now().strftime('%H:%M')}")
            
    except Exception:
        st.error("Veri işlenirken hata oluştu.")
else:
    st.warning(f"'{isim}' için veri bulunamadı veya bağlantı hatası.")
