import streamlit as st
import base64
import os
import io
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

# .env dosyasından değişkenleri yükle (Yerel geliştirme için)
load_dotenv()

# Sayfa Yapılandırması (Premium Görünüm)
st.set_page_config(
    page_title="VisionAI - Akıllı Nesne Tanımlayıcı",
    page_icon="🔍",
    layout="wide"
)

# Özel CSS ile Arayüzü Güzelleştirme
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stAlert {
        border-radius: 10px;
    }
    .res-card {
        padding: 20px;
        background-color: #1e1e1e;
        border-radius: 15px;
        border: 1px solid #3d3d3d;
        margin-bottom: 20px;
    }
    .confidence-text {
        font-size: 24px;
        font-weight: bold;
        color: #00ffcc;
    }
</style>
""", unsafe_allow_html=True)

# Görseli Base64 formatına dönüştürme fonksiyonu
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# Kenar Çubuğu (Sidebar)
with st.sidebar:
    st.title("🛠️ Kontrol Paneli")
    st.info("Bu uygulama Groq Cloud altyapısını kullanarak her türlü nesneyi tanımlayabilir.")
    
    # API Anahtarı Kontrolü (Önce Secrets, sonra Env)
    api_key_env = None
    if "GROQ_API_KEY" in st.secrets:
        api_key_env = st.secrets["GROQ_API_KEY"]
    elif os.getenv("GROQ_API_KEY"):
        api_key_env = os.getenv("GROQ_API_KEY")
    
    # Eğer sistemde/secrets'ta varsa, sormadan onu kullanıyoruz
    if api_key_env:
        st.success("✅ API Anahtarı Hazır (Sistem/Secrets)")
        api_key_input = api_key_env
    else:
        # Eğer yoksa manuel giriş istiyoruz
        api_key_input = st.text_input("Groq API Key", value="", type="password", help=".env dosyası bulunamadı, lütfen manuel girin.")
        if not api_key_input:
            st.warning("⚠️ Lütfen bir API anahtarı girin.")
    
    st.markdown("---")
    st.markdown("### Model Ayarları")
    model_choice = st.selectbox(
        "Görüntü Modeli Seçin",
        ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview", "llava-v1.5-7b-4096"],
        index=0,
        help="Groq üzerindeki güncel vision modellerinden birini seçin."
    )
    
    st.markdown("---")
    st.write("Geliştiren: Ali İhsan ÇETİN")

# Ana Ekran
st.title("🔍 VisionAI: Akıllı Nesne Tanımlayıcı")
st.markdown("#### Herhangi bir fotoğraf yükleyin, yapay zeka saniyeler içinde analiz etsin.")

# Dosya Yükleyici
uploaded_file = st.file_uploader("Bir resim seçin veya buraya sürükleyin...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Resmi Göster
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", use_container_width=True)
    
    with col2:
        if not api_key_input:
            st.error("Lütfen devam etmek için kenar çubuğuna bir API anahtarı girin.")
        else:
            if st.button("Nesneyi Tanımla ✨", use_container_width=True):
                with st.spinner("Yapay zeka analiz ediyor..."):
                    try:
                        # API İstemcisi
                        client = Groq(api_key=api_key_input)
                        
                        # Görseli hazırla
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
                        base64_image = encode_image(img_byte_arr.getvalue())
                        
                        # Groq API Çağrısı
                        response = client.chat.completions.create(
                            model=model_choice,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Sen çok yetenekli bir nesne tanımlama asistanısın. Görseldeki ana nesneyi bul, ona bir isim ver, kısa bir açıklama yap ve %0-100 arasında bir güven skoru (confidence score) ata. Yanıtını JSON formatında ver: {'name': 'nesne_adi', 'description': 'kisa_aciklama', 'confidence': '85%'}. Sadece JSON döndür."
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "Bu görselde ne var? Lütfen Türkçe açıkla."},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}",
                                            },
                                        },
                                    ],
                                }
                            ],
                            temperature=0.5,
                            max_tokens=500,
                            response_format={"type": "json_object"}
                        )
                        
                        # Yanıtı işle
                        import json
                        result = json.loads(response.choices[0].message.content)
                        
                        # Sonuçları Göster
                        st.balloons()
                        st.markdown(f"""
                        <div class="res-card">
                            <h3>🏷️ Nesne: {result.get('name', 'Bilinmiyor')}</h3>
                            <p style="font-size: 18px;">{result.get('description', '')}</p>
                            <hr>
                            <p>Güven Skoru:</p>
                            <span class="confidence-text">{result.get('confidence', 'N/A')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {str(e)}")

else:
    # Boş durum mesajı
    st.info("Analiz için yukarıdan bir fotoğraf yükleyerek başlayın.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>© 2026 VisionAI Project - Her Şeyi Tanıyan Modern Yapay Zeka</p>", unsafe_allow_html=True)