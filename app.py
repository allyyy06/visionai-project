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
        background-color: #0b0e14;
        color: #e0e0e0;
    }
    .stAlert {
        border-radius: 12px;
    }
    .res-card {
        padding: 24px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 25px;
        transition: transform 0.3s ease;
    }
    .res-card:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 255, 204, 0.3);
    }
    .confidence-text {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(45deg, #00ffcc, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton>button {
        border-radius: 10px;
        height: 3em;
        background: linear-gradient(45deg, #00ffcc, #0099ff);
        color: white;
        border: none;
        font-weight: bold;
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
st.markdown("#### Herhangi bir fotoğraf yükleyin veya kameranızı kullanın, yapay zeka analiz etsin.")

# Giriş Seçenekleri
tabs = st.tabs(["📁 Dosya Yükle", "📸 Kamera Kullan"])

with tabs[0]:
    uploaded_file = st.file_uploader("Bir resim seçin...", type=["jpg", "jpeg", "png"], key="file_upload")

with tabs[1]:
    camera_file = st.camera_input("Kameranızla bir fotoğraf çekin", key="camera_input")

# Hangi kaynaktan veri geldiğini kontrol et
input_file = camera_file if camera_file is not None else uploaded_file

if input_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Resmi Göster
        image = Image.open(input_file)
        st.image(image, caption="Analiz Edilen Görsel", use_container_width=True)
    
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
                        # RGB'ye dönüştür ki RGBA veya farklı formatlar hata vermesin (özellikle kameradan gelenler)
                        image_rgb = image.convert("RGB")
                        image_rgb.save(img_byte_arr, format='JPEG')
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
                            temperature=0.3,
                            max_tokens=600,
                            response_format={"type": "json_object"}
                        )
                        
                        # Yanıtı işle
                        import json
                        result_str = response.choices[0].message.content
                        result = json.loads(result_str)
                        
                        # Sonuçları Göster
                        st.balloons()
                        st.markdown(f"""
                        <div class="res-card">
                            <h3 style="color: #00ffcc; margin-top: 0;">🏷️ {result.get('name', 'Bilinmiyor')}</h3>
                            <p style="font-size: 18px; line-height: 1.6;">{result.get('description', '')}</p>
                            <div style="margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                                <span style="font-size: 14px; color: #888;">Güven Skoru:</span><br>
                                <span class="confidence-text">{result.get('confidence', 'N/A')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {str(e)}")
                        st.info("İpucu: API anahtarınızın doğruluğunu ve internet bağlantınızı kontrol edin.")

else:
    # Boş durum mesajı
    st.info("Analiz için yukarıdan bir fotoğraf yükleyin veya kameranızı kullanın.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>© 2026 VisionAI Project - Her Şeyi Tanıyan Modern Yapay Zeka</p>", unsafe_allow_html=True)