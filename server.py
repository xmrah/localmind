from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings
import os
import uuid

# Sunucuyu 'localmind' kimliğiyle başlat
mcp = FastMCP("localmind-Core")

# Veritabanı Yolu
DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

# TELEMETRİ KAPALI: Tam gizlilik (Forensic) ve yerel izolasyon.
chroma_client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(anonymized_telemetry=False)
)

# Zihin Sarayı Koleksiyonu
palace = chroma_client.get_or_create_collection(name="zihin_sarayi")

@mcp.tool()
def hafizaya_yaz(konu: str, bilgi: str, oda: str = "genel") -> str:
    """
    Yapay zekanın önemli kararları ve sistem mimarilerini kalıcı olarak localmind'a kaydetmesini sağlar.
    
    Argümanlar:
    - konu: Hatırlanması gereken bilginin başlığı (Örn: 'Tailscale Kararı')
    - bilgi: Bilginin tüm detayları
    - oda: Zihin sarayındaki kategori (Örn: 'mimari', 'guvenlik', 'nixos', 'python')
    """
    doc_id = str(uuid.uuid4())
    
    palace.add(
        documents=[bilgi],
        metadatas=[{"konu": konu, "oda": oda}],
        ids=[doc_id]
    )
    return f"✅ [{oda.upper()}] odasına '{konu}' başarıyla Vektör Veritabanına işlendi!"

@mcp.tool()
def hafizada_ara(sorgu: str, sonuc_sayisi: int = 2) -> str:
    """
    Yapay zekanın geçmiş kararları anlamsal (semantic/vector) olarak arayıp bulmasını sağlar.
    Tam kelime eşleşmesi gerekmez, cümlenin anlamına göre bulur.
    
    Argümanlar:
    - sorgu: Neyi aradığın (Örn: 'Ağ güvenliği için hangi aracı seçmiştik?')
    - sonuc_sayisi: Kaç adet benzer sonuç getirileceği
    """
    results = palace.query(
        query_texts=[sorgu],
        n_results=sonuc_sayisi
    )
    
    if not results["documents"] or not results["documents"][0]:
        return "❌ Zihin sarayında bu konuya benzer hiçbir anı/bilgi bulunamadı."
        
    cevap = "🧠 BULUNAN HAFIZA KAYITLARI:\n"
    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        cevap += f"\n👉 ODA: {meta.get('oda')} | KONU: {meta.get('konu')}\n   BİLGİ: {doc}\n"
        
    return cevap

if __name__ == "__main__":
    # Ağ üzerinden (SSE) yayına başla. 
    # 0.0.0.0 seçildi çünkü Tailscale arayüzünden de erişilmesini istiyoruz.
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
