import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Piyasa Özeti", 
    layout="wide", 
    page_icon="📢",
    initial_sidebar_state="collapsed"
)

# --- 2. GÖRÜNÜMÜ TEMİZLEME (CSS) ---
st.markdown("""
    <style>
        /* Gereksiz her şeyi gizle */
        header, .stAppHeader, [data-testid="stHeader"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        footer {display: none !important;}
        div[class^="viewerBadge"] {display: none !important;}
        
        /* Sayfa üst boşluğunu al */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Yorum Kutusu Tasarımı */
        .yorum-kutusu {
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: 500;
        }
        .pozitif { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .negatif { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .notr { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    </style>
""", unsafe_allow_html=True)

# --- 3. VARLIK LİSTESİ ---
VARLIKLAR = {
    "Gram Altın": "GRAM_ALTIN",
    "Dolar/TL": "TRY=X",
    "Euro/TL": "EURTRY=X",
    "BIST 100 Endeksi": "XU100.IS",
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "THY (THYAO)": "THYAO.IS",
    "Aselsan (ASELS)": "ASELS.IS",
    "Garanti (GARAN)": "GARAN.IS",
    "Ereğli (EREGL)": "EREGL.IS",
    "Şişecam (SISE)": "SISE.IS",
    "Tüpraş (TUPRS)": "TUPRS.IS",
    "Akbank (AKBNK)": "AKBNK.IS",
    "Koç Holding (KCHOL)": "KCHOL.IS",
    "Sasa (SASA)": "SASA.IS",
    "Hektaş (HEKTS)": "HEKTS.IS",
    "Astor Enerji": "ASTOR.IS"
}

# --- 4. VERİ MOTORU ---
@st.cache_data(ttl=300)
def veri_getir(sembol_kodu):
    try:
        # Trendi anlamak için son 6 aylık veriyi çekiyoruz
        df = yf.download(sembol_kodu, period="6mo", progress=False)
        
        # Eğer veri gelmezse (özellikle altın için özel işlem)
        if df.empty and "ALTIN" in sembol_kodu:
             ons = yf.download("GC=F", period="6mo", progress=False)
             usd = yf.download("TRY=X", period="6mo", progress=False)
             # Sütun düzeltme
             if isinstance(ons.columns, pd.MultiIndex): ons.columns = ons.columns.get_level_values(0)
             if isinstance(usd.columns, pd.MultiIndex): usd.columns = usd.columns.get_level_values(0)
             
             df = pd.DataFrame()
             df['Close'] = (ons['Close'] * usd['Close']) / 31.1035
             df['High'] = df['Close'] # Basit gösterim için
             df.index = ons.index
        
        # Sütun adı temizliği
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        col = next((c for c in df.columns if 'date' in c.lower()), None)
        if col: df.rename(columns={col: 'Date'}, inplace=True)
            
        return df
    except:
        return None

# --- 5. İNSANİ YORUM MOTORU (TEKNİK TERİM YOK) ---
def yorumla(df, isim):
    son_fiyat = df['Close'].iloc[-1]
    
    # 50 Günlük Ortalama (Piyasanın yönünü belirleyen ana hat)
    if len(df) > 50:
        ortalama = df['Close'].tail(50).mean()
    else:
        ortalama = son_fiyat # Veri azsa son fiyata eşitle

    # Haftalık Değişim (Kısa vade hissi)
    hafta_once = df['Close'].iloc[-5] if len(df) > 5 else df['Close'].iloc[0]
    degisim = ((son_fiyat - hafta_once) / hafta_once) * 100

    # YORUM MANTIĞI (Burada teknik terimleri halk diline çeviriyoruz)
    durum = ""
    stil = ""
    icon = ""

    if son_fiyat > ortalama * 1.02: # Ortalamanın %2 üzerindeyse
        if degisim > 3:
            durum = f"🔥 **GENEL KANI: İŞTAHLI VE COŞKULU**\n\nAnalistlere göre {isim} şu an yatırımcıların gözdesi durumunda. Talep çok güçlü ve fiyatlar yukarı gitme eğiliminde. Ancak çok hızlı yükseldiği için kısa vadeli ufak geri çekilmeler (kar satışı) normal karşılanmalı."
            stil = "pozitif"
            icon = "🚀"
        elif degisim > 0:
            durum = f"✅ **GENEL KANI: OLUMLU / GÜVENLİ LİMAN**\n\n{isim} tarafında işler yolunda görünüyor. Piyasa sakin ama yön yukarı. Yatırımcılar panik yapmadan ellerinde tutmaya devam ediyor. Genel hava pozitif."
            stil = "pozitif"
            icon = "📈"
        else:
            durum = f"🤔 **GENEL KANI: DİNLENME MODUNDA**\n\nGenel trend hala yukarı olsa da, {isim} son birkaç gündür biraz yorulmuş görünüyor. Piyasa şu an 'bekle-gör' moduna geçmiş durumda."
            stil = "notr"
            icon = "⏸️"
            
    elif son_fiyat < ortalama * 0.98: # Ortalamanın %2 altındaysa
        if degisim < -3:
            durum = f"⚠️ **GENEL KANI: SATIŞ BASKISI VAR**\n\nŞu an {isim} üzerinde kara bulutlar dolaşıyor. Yatırımcılar tedirgin ve satışlar ağır basıyor. Analistler 'düşen bıçak tutulmaz' diyerek temkinli olunmasını öneriyor."
            stil = "negatif"
            icon = "🔻"
        else:
            durum = f"❄️ **GENEL KANI: SOĞUK VE ZAYIF**\n\n{isim} şu an yatırımcısına heyecan vermiyor. Piyasa ilgisi düşük. Fiyatlar baskı altında ve toparlanmakta zorlanıyor."
            stil = "negatif"
            icon = "📉"
    else:
        durum = f"⚖️ **GENEL KANI: KARARSIZ / YATAY**\n\n{isim} şu an yönünü arıyor. Ne alıcılar ne satıcılar baskın gelebiliyor. Piyasa bir haber veya gelişme bekliyor gibi. Şu an için belirsizlik hakim."
        stil = "notr"
        icon = "😐"

    return durum, stil, icon, son_fiyat, degisim

# --- 6. ARAYÜZ ---
col_secim, col_bos = st.columns([3, 1])
with col_secim:
    secilen_isim = st.selectbox("Analiz Edilecek Varlık:", list(VARLIKLAR.keys()))

if secilen_isim:
    kodu = VARLIKLAR[secilen_isim]
    
    # Özel Altın/Gümüş Kod Ayarı
    if "Altın" in secilen_isim: kod_analiz = "GRAM_ALTIN" # Fonksiyon içinde hallediliyor
    else: kod_analiz = kodu

    with st.spinner("Piyasa nabzı ölçülüyor..."):
        df = veri_getir(kodu)

    if df is not None and not df.empty:
        yorum_metni, stil_sinifi, icon, son, yuzde = yorumla(df, secilen_isim)

        # 1. YORUM ALANI (EN ÜSTTE VE BELİRGİN)
        st.markdown(f"""
            <div class="yorum-kutusu {stil_sinifi}">
                {yorum_metni}
            </div>
        """, unsafe_allow_html=True)

        # 2. BASİT RAKAMLAR
        col1, col2 = st.columns(2)
        col1.metric("Anlık Fiyat", f"{son:,.2f} TL")
        col2.metric("Haftalık Performans", f"%{yuzde:.2f}", delta_color="normal")

        # 3. GRAFİK (SADE)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['Close'],
            mode='lines',
            line=dict(color='#333', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,0,0,0.05)'
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#eee'),
            template="plotly_white",
            dragmode=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.error("Veri alınamadı. Bağlantı hatası.")
