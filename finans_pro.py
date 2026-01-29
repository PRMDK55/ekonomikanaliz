import streamlit as st

import yfinance as yf

import pandas as pd

import numpy as np

import plotly.graph_objects as go

from datetime import datetime



# --- 1. MOBİL UYUMLU AYARLAR ---

st.set_page_config(page_title="Borsa Analiz", layout="wide", page_icon="📱")



# CSS: Telefondan girince kenar boşluklarını siler, tam ekran yapar

st.markdown("""

<style>

    /* Genel Arka Plan */

    .stApp {background-color: #f4f7f6;}

    

    /* Mobil İçin Kart Tasarımı */

    .stat-card {

        background-color: white; 

        padding: 15px; 

        border-radius: 12px; 

        box-shadow: 0 2px 8px rgba(0,0,0,0.08); 

        margin-bottom: 10px;

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

    # Mobilde yazmak zordur, o yüzden seçimi önceliklendirdik ama manuel de çalışır

    if manuel:

        kod = manuel.upper().strip()

        if "BIST" in kat and ".IS" not in kod: return f"{kod}.IS", kod

        if "Kripto" in kat and "-USD" not in kod: return f"{kod}-USD", kod

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

    if len(isim) <= 5 and " " not in isim: # Kısaltma ise (THYAO gibi)

         return f"{isim}.IS", isim



    # Listeden gelen isim

    if "BIST" in kat: return f"{isim}.IS", isim

    if "Kripto" in kat:

        kod = isim.split("(")[0].strip()

        return f"{kod}-USD", kod

    

    return "THYAO.IS", "THYAO"



# --- 4. VERİ ÇEKME (HIZLI & GÜVENLİ) ---

@st.cache_data(ttl=300)

def veri_getir(sembol, vade_gun):

    try:

        ozel_hesaplar = ["GRAM_ALTIN", "CEYREK_ALTIN", "YARIM_ALTIN", "GUMUS_TL"]

        periyot = "2y"

        

        if sembol in ozel_hesaplar:

            ana_kod = "GC=F" if "ALTIN" in sembol else "SI=F"

            ons = yf.download(ana_kod, period=periyot, progress=False)

            usd = yf.download("TRY=X", period=periyot, progress=False)

            

            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)

            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)

            

            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))

            gram_tl = (df['Close_Ons'] * df['Close_Usd']) / 31.1035

            

            if sembol == "GRAM_ALTIN": df['Close'] = gram_tl

            elif sembol == "CEYREK_ALTIN": df['Close'] = gram_tl * 1.63

            elif sembol == "YARIM_ALTIN": df['Close'] = gram_tl * 3.26

            elif sembol == "GUMUS_TL": df['Close'] = gram_tl

            

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

    except: return None



# --- 5. ARAYÜZ (MOBİL UYUMLU YAN MENÜ) ---

with st.sidebar:

    st.title("📱 Cep Analiz")

    kat = st.selectbox("Pazar:", list(varlik_havuzu.keys()))

    secim = st.selectbox("Varlık:", varlik_havuzu[kat])

    

    st.write("---")

    manuel = st.text_input("🔍 Başka Ara:", placeholder="Kod yaz...")

    

    st.write("---")

    vade = st.select_slider("Süre:", ["1 Hafta", "1 Ay", "6 Ay", "1 Yıl"], value="6 Ay")

    gun_map = {"1 Hafta": 7, "1 Ay": 30, "6 Ay": 180, "1 Yıl": 365}

    

    if st.button("🔄 Yenile"): st.rerun()



# --- 6. ANA EKRAN ---

kod, isim = sembol_cozucu(secim, manuel, kat)



# Başlık mobilde çok yer kaplamasın diye simple yapıyoruz

st.subheader(f"📊 {isim}")



df_full = veri_getir(kod, gun_map[vade])



if df_full is not None and not df_full.empty:

    df_view = df_full.tail(gun_map[vade])

    son = float(df_view['Close'].iloc[-1])

    onceki = float(df_view['Close'].iloc[0])

    degisim = ((son - onceki) / onceki) * 100

    

    # Mobilde 4 kolon sığmaz, 2'şerli yapıyoruz

    c1, c2 = st.columns(2)

    c1.metric("Fiyat", f"{son:.2f}", f"%{degisim:.2f}")

    c2.metric("En Yüksek", f"{df_view['High'].max():.2f}")

    

    # Grafik

    tab1, tab2 = st.tabs(["Grafik", "Yorum"])

    

    with tab1:

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df_view['Date'], y=df_view['Close'], line=dict(color='#2980b9', width=3)))

        # Mobilde grafiğin altındaki tarihleri sadeleştir

        fig.update_layout(

            template="plotly_white", 

            height=350, # Mobilde çok uzun olmasın

            margin=dict(l=10, r=10, t=10, b=10),

            xaxis=dict(showgrid=False),

            yaxis=dict(showgrid=True, gridcolor='#eee')

        )

        st.plotly_chart(fig, use_container_width=True)

        

    with tab2:

        st.markdown("### 🤖 Yapay Zeka Özeti")

        if degisim > 0:

            st.success(f"**YÜKSELİŞ:** {vade} periyodunda %{degisim:.1f} kazandırdı. Trend pozitif.")

        else:

            st.error(f"**DÜŞÜŞ:** {vade} periyodunda %{abs(degisim):.1f} kaybettirdi. Satış baskısı var.")

            

        st.info(f"💡 **Analist Notu:** Fiyat son kapanışta {son:.2f} seviyesinde. (Veri Zamanı: {datetime.now().strftime('%H:%M')})")



else:

    st.warning("Veri yükleniyor veya bağlantı hatası...") 
