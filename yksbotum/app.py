import streamlit as st
import pandas as pd
import json
from topsis_module import topsis_hesapla
from openai import OpenAI  


client = OpenAI(api_key=st.secrets["openai"]["api_key"])

@st.cache_data
def load_data():
    iller_df = pd.read_csv("illerdata.csv")
    universiteler_df = pd.read_csv("universitelerdata.csv")
    bolumler_df = pd.read_csv("bolumdata.csv")
    return iller_df, universiteler_df, bolumler_df

iller_df, universiteler_df, bolumler_df = load_data()

st.title(" Üniversite Tercih Yardımcısı")

st.subheader("1. Tercih Bilgilerinizi Girin")
puan_turu = st.selectbox("Puan türünüz", ["SAY", "EA", "SÖZ", "DİL"])
puan = st.number_input("YKS puanınız", min_value=0.0, max_value=600.0, step=0.5)
aranan_bolum = st.text_input("İstediğiniz bölüm (örn: Bilgisayar Mühendisliği)")

if puan and aranan_bolum:
    uygun_bolumler = bolumler_df[
        (bolumler_df['puan_turu'] == puan_turu) &
        (bolumler_df['puan'].astype(float) <= puan) &
        (bolumler_df['bolum_adi'].str.contains(aranan_bolum, case=False))
    ]
    uygun_uni_ids = uygun_bolumler['uni_id'].unique()
    uygun_uniler = universiteler_df[universiteler_df['uni_id'].isin(uygun_uni_ids)]

    if uygun_uniler.empty:
        st.warning("❗ Bu puan ve bölüm ile eşleşen üniversite bulunamadı.")
    else:
        st.success(f"✅ {len(uygun_uniler)} uygun üniversite bulundu.")

        st.subheader("2. Sizin İçin Önemli Kriterleri Seçin")

        kriterler = {
            "Ihracat_gelir": st.slider("Şehrin ihracat geliri", 0, 100, 0),
            "yurt_sayisi": st.slider("Yurt sayısı", 0, 100, 0),
            "yasam_maliyeti": st.slider("Yaşam maliyeti", 0, 100, 0),
            "yasanabilirlik": st.slider("Şehrin yaşanabilirliği", 0, 100, 0),
            "Uni_egitim": st.slider("Üniversitenin eğitim seviyesi", 0, 100, 0),
            "girisim_destek": st.slider("Girişimcilik desteği", 0, 100, 0),
            "akademisyen": st.slider("Akademisyen sayısı", 0, 100, 0),
            "sosyal": st.slider("Sosyal imkanlar", 0, 100, 0),
            "yurtdisi_egitim": st.slider("Yurtdışı eğitime giden öğrenci sayısı", 0, 100, 0),
            "arastirma_olanaklari": st.slider("Araştırma olanakları", 0, 100, 0)
        }

        if st.checkbox("Eğitim dili (İngilizce tercih ediyorum)"):
            kriterler["egitim_dili"] = 100
        if st.checkbox("Büyükşehir olması önemli"):
            kriterler["buyuksehir"] = 100

        kriter_agirliklari = {k: v for k, v in kriterler.items() if v > 0}

        if st.button(" Üniversiteleri Sırala"):
            if not kriter_agirliklari:
                st.warning("Lütfen en az bir kritere önem derecesi giriniz.")
            else:
                sonuc_df = topsis_hesapla(uygun_uniler, bolumler_df, iller_df, kriter_agirliklari)
                st.dataframe(sonuc_df)

                try:
                    # GPT'ye verilecek prompt
                    prompt = f"""
Aşağıda TOPSIS skorlarına göre sıralanmış üniversite listesi var:

{sonuc_df.head(10).to_string(index=False)}

Kullanıcının tercih ettiği kriterler ve önem dereceleri şu şekildedir:
{json.dumps(kriter_agirliklari, indent=2, ensure_ascii=False)}

Bu verilere göre aşağıdaki analizleri yap:
1. Kullanıcının en yüksek ağırlık verdiği kriter(ler) hangileri?
2. Bu kriterlerde hangi üniversiteler öne çıkmış olabilir?
3. İlk 3 üniversitenin neden yüksek skor almış olabileceğini açıklamaya çalış.
4. Birbirine yakın skorlu üniversiteler varsa, aralarındaki farkı anlamaya çalış.
5. Kullanıcıya önerilerde bulun: hangi kritere göre nasıl tercih yapmalı?

Anlaşılır, kullanıcı dostu ve tavsiye odaklı bir analiz sun.
"""

                    with st.spinner("🔍 ChatGPT kriterlere göre yorumluyor..."):
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "Sen bir üniversite tercih danışmanısın ve TOPSIS skoru ile üniversiteleri analiz ediyorsun."},
                                {"role": "user", "content": prompt}
                            ]
                        )

                        yorum = response.choices[0].message.content

                    st.markdown("### Asistan Yorumu")
                    st.write(yorum)

                except Exception as e:
                    st.error(f"GPT yorum alınamadı: {str(e)}")
