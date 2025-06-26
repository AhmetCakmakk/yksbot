import numpy as np
import pandas as pd

def topsis_hesapla(veri_df, bolumler_df, iller_df, kullanici_kriter_agirliklari):
    # Eğitim dili: en az bir İngilizce bölüm varsa 1
    egitim_dilleri = bolumler_df.groupby("uni_id")['egitim_dili'].apply(lambda x: 1 if "İngilizce" in x.values else 0)
    veri_df['egitim_dili'] = veri_df['uni_id'].map(egitim_dilleri)

    # Eğer il_id yoksa şehir ismine göre eşleştir
    if "il_id" not in veri_df.columns:
        sehir_to_il_id = dict(zip(iller_df["İL"].str.lower(), iller_df["il_id"]))
        veri_df["il_id"] = veri_df["sehir"].str.lower().map(sehir_to_il_id)

    # Şehir verilerini ekle
    veri_df = veri_df.merge(
        iller_df[['il_id', 'Ihracat_gelir', 'yurt_sayisi', 'yasam_maliyeti', 'yasanabilirlik', 'buyuksehir']],
        on='il_id', how='left'
    )

    secili_kriterler = list(kullanici_kriter_agirliklari.keys())
    karar_matrisi = veri_df.set_index("Universite")[secili_kriterler].fillna(0).copy()

    negatif_kriterler = ["yasam_maliyeti", "Uni_egitim"]

    karar_normalize = karar_matrisi.copy()
    for col in karar_normalize.columns:
        min_val = karar_normalize[col].min()
        max_val = karar_normalize[col].max()
        if max_val - min_val == 0:
            karar_normalize[col] = 0
        elif col in negatif_kriterler:
            karar_normalize[col] = (max_val - karar_normalize[col]) / (max_val - min_val)
        else:
            karar_normalize[col] = (karar_normalize[col] - min_val) / (max_val - min_val)

    toplam_agirlik = sum(kullanici_kriter_agirliklari.values())
    agirliklar = np.array([kullanici_kriter_agirliklari[k] / toplam_agirlik for k in karar_normalize.columns])
    agirlikli_matris = karar_normalize * agirliklar

    ideal_cozum = agirlikli_matris.max()
    negatif_ideal = agirlikli_matris.min()

    pozitif_uzaklik = np.linalg.norm(agirlikli_matris - ideal_cozum, axis=1)
    negatif_uzaklik = np.linalg.norm(agirlikli_matris - negatif_ideal, axis=1)

    topsis_skor = negatif_uzaklik / (pozitif_uzaklik + negatif_uzaklik)

    sonuc_df = pd.DataFrame({
        "Üniversite": karar_matrisi.index,
        "TOPSIS Skoru": topsis_skor
    }).sort_values(by="TOPSIS Skoru", ascending=False).reset_index(drop=True)

    return sonuc_df
