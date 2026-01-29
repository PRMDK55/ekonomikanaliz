import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. AYARLAR VE ÖNBELLEK TEMİZLİĞİ ---
st.set_page_config(
    page_title="Finans Ana", 
    layout="wide", 
    page_icon="📱",
    initial_sidebar_state="collapsed" # Menüyü kapalı başlatır
)

# Her yüklemede önbelleği zorla temizle (Sorun çözülene kadar)
# st.cache_data.clear() 

# --- 2. AGRESİF GİZLEME CSS (GÜNCELLENDİ) ---
st.markdown("""
    <style>
        /* 1. Tüm Header ve Toolbar Alanlarını Yok Et */
        header, .stAppHeader, [data-testid="stHeader"] {
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
            height: 0px !important;
        }

        /* 2. Sağ Üstteki Seçenekler Menüsü ve GitHub İkonu */
        [data-testid="stToolbar"], [data-testid="stStatusWidget"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* 3. Footer ve 'Made with Streamlit' */
        footer, .stFooter {
            display: none !important;
        }
        
        /* 4. Sayfayı Yukarı İt (Header gidince boşluk kalmasın) */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 2rem !important;
            margin-top: -20px !important;
        }
        
        /* 5. Mobilde Yazı Boyutları */
        div[data-testid="stMetricValue"] { font-size: 26px !important; }
        
        /* 6. Gereksiz Kenar Boşluklarını Sil */
        .stApp {
            margin: 0 !important;
            padding: 0 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. VARLIK HAVUZU ---
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

# --- 4. GELİŞMİŞ ARAMA MOTORU ---
def sembol_bul(aranan, kategori_secimi):
    # Eğer arama boşsa, seçili kategoriden ilkini getir
    if not aranan:
        return None, None

    girdi = aranan.lower().strip()
    
    # 1. ÖZEL KELİME EŞLEŞTİRME (Kullanıcının şikayet ettiği "alt" burada çözülür)
    # Eğer içinde "alt" geçiyorsa direkt Gram Altın'a yönlendir
    if "alt" in girdi: return "GRAM_ALTIN", "Gram Altın (Otomatik)"
    if "dol" in girdi or "usd" in girdi: return "TRY=X", "Dolar/TL"
    if "eur" in girdi: return "EURTRY=X", "Euro/TL"
    if "güm" in girdi: return "GUMUS_TL", "Gümüş"
    
    # 2. HİSSE KODU TAHMİNİ
    # Eğer kullanıcı 5 harften az yazdıysa (Örn: ASELS) sonuna .IS ekle
    # Ancak kripto da olabilir, bu yüzden kategoriye bak
    kod = aranan.upper()
    
    if "BIST" in kategori_secimi and ".IS" not in kod:
        return f"{kod}.IS", kod
    elif "Kripto" in kategori_secimi and "-USD" not in kod:
        return f"{kod}-USD", kod
    
    return kod, kod # Hiçbir şeye uymuyorsa olduğu gibi döndür

# --- 5. VERİ ÇEKME ---
@st.cache_data(ttl=300) # 5 dakikada bir veri yeniler
def veri_getir(sembol, gun_sayisi):
    try:
        periyot = "2y"
        ozel_hesaplar = ["GRAM_ALTIN", "CEYREK_ALTIN", "YARIM_ALTIN", "GUMUS_TL"]
        
        if sembol in ozel_hesaplar:
            # Altın/Gümüş hesaplaması
            ana_kod = "GC=F" if "ALTIN" in sembol else "SI=F"
            ons = yf.download(ana_kod, period=periyot, progress=False)
            usd = yf.download("TRY=X", period=periyot, progress=False)
            
            # Veri Düzeltme
            if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
            if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
            
            # Birleştirme
            df = pd.merge(ons['Close'], usd['Close'], left_index=True, right_index=True, suffixes=('_Ons', '_Usd'))
            
            # Gram Formülü: (Ons * Dolar) / 31.10
            gram_saf = (df['Close_Ons'] * df['Close_Usd']) / 31.1035
            
            if sembol == "GRAM_ALTIN": df['Close'] = gram_saf
            elif sembol == "CEYREK_ALTIN": df['Close'] = gram_saf * 1.63
            elif sembol == "YARIM_ALTIN": df['Close'] = gram_saf * 3.26
            elif sembol == "GUMUS_TL": df['Close'] = gram_saf
            
            df['Open'] = df['High'] = df['Low'] = df['Close']
            df.reset_index(inplace=True)
        else:
            # Normal Hisse
            df = yf.download(sembol, period=periyot, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)
            
        # Sütun isim düzeltme
        if 'Date' not in df.columns:
            if 'Datetime' in df.columns: df.rename(columns={'Datetime': 'Date'}, inplace=True)
            else: df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
            
        return df
    except:
        return None

# --- ARAYÜZ ---
with st.sidebar:
    st.title("Ayarlar")
    kat = st.selectbox("Pazar Seç:", list(varlik_havuzu.keys()))
    secim_liste = st.selectbox("Listeden Seç:", varlik_havuzu[kat])
    
    st.write("---")
    # Arama kutusu - Buraya 'alt' yazınca çalışacak
    manuel_arama = st.text_input("🔍 ARA (Örn: alt, asels)", placeholder="Yazıp Enter'a bas...")
    st.caption("İpucu: 'alt' yazarsan Gram Altın gelir.")
    
    vade = st.select_slider("Vade:", ["1 Hafta", "1 Ay", "6 Ay"], value="1 Ay")
    
    if st.button("Yenile"): st.rerun()

# --- ARKA PLAN MANTIĞI ---

# 1. Hangi sembolü göstereceğiz?
if manuel_arama:
    # Kullanıcı elle bir şey yazdıysa (Örn: "alt")
    kod, isim = sembol_bul(manuel_arama, kat)
else:
    # Elle yazmadıysa listeden geleni kullan (Örn: "THYAO")
    kod, isim = sembol_bul(secim_liste, kat)

# --- EKRAN ---
st.subheader(f"📊 {isim}")

if kod:
    gun_map = {"1 Hafta": 7, "1 Ay": 30, "6 Ay": 180}
    df = veri_getir(kod, gun_map[vade])

    if df is not None and not df.empty:
        son_data = df.tail(gun_map[vade])
        son_fiyat = float(son_data['Close'].iloc[-1])
        ilk_fiyat = float(son_data['Close'].iloc[0])
        yuzde = ((son_fiyat - ilk_fiyat) / ilk_fiyat) * 100
        
        # Metrikler
        col1, col2 = st.columns(2)
        col1.metric("Fiyat", f"{son_fiyat:.2f}", f"%{yuzde:.2f}")
        col2.metric("En Yüksek", f"{son_data['High'].max():.2f}")
        
        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=son_data['Date'], y=son_data['Close'], 
                                mode='lines', 
                                line=dict(color='#0078FF', width=3)))
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#eee'),
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Durum Mesajı
        if yuzde > 0:
            st.success(f"📈 {vade} içinde yükselişte.")
        else:
            st.error(f"📉 {vade} içinde düşüşte.")
            
    else:
        st.warning(f"⚠️ '{isim}' verisi bulunamadı. Lütfen tam kodu yazmayı deneyin (Örn: EREGL.IS)")
else:
    st.info("Lütfen bir seçim yapın veya arama kutusunu kullanın.")
