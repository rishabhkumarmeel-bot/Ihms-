import streamlit as st
import pandas as pd
from datetime import datetime
import os
import easyocr
from PIL import Image
import numpy as np

st.set_page_config(page_title="IHMS AI Outreach + OCR", page_icon="🏥", layout="wide")

DATA_FILE = "ihms_survey_data.csv"
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["तारीख", "प्रकार", "आईडी/नाम", "मुख्य सदस्य", "उम्र/विवरण", "लक्षण/विभाग", "AI निष्कर्ष"])
    df_init.to_csv(DATA_FILE, index=False)

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['hi', 'en'], gpu=False)

reader = load_ocr_model()

def local_ai_engine(age, symptoms, bp):
    symptoms_lower = symptoms.lower()
    if "बुखार" in symptoms_lower or "fever" in symptoms_lower:
        if age > 60: return "⚠️ हाई रिस्क: बुजुर्ग मरीज को तेज बुखार है। तुरंत डॉक्टर से संपर्क करें।"
        return "ℹ️ सामान्य रिस्क: मौसमी बुखार के लक्षण। आराम की सलाह।"
    if "खांसी" in symptoms_lower or "cough" in symptoms_lower:
        if "सांस" in symptoms_lower or "breath" in symptoms_lower: return "🚨 गंभीर स्थिति: सांस लेने में तकलीफ। तुरंत नजदीकी CHC रेफरल।"
        return "ℹ️ सामान्य: खांसी की शिकायत। कफ सिरप की सलाह।"
    return "✅ स्थिति सामान्य: कोई गंभीर लक्षण नहीं दिखे।"

st.title("🏥 IHMS AI-Powered Outreach with Photo OCR")
st.write("फोटो से डेटा स्कैन करने और AI से निष्कर्ष निकालने वाला स्मार्ट हेल्थ पोर्टल।")

tab1, tab2, tab3 = st.tabs(["👥 फैमिली ऐड (OCR स्कैन)", "📝 हेल्थ सर्वे फॉर्म", "📊 रिकॉर्ड देखें"])

with tab1:
    st.header("🏢 फोटो से डेटा स्कैन करें और सदस्य जोड़ें")
    uploaded_image = st.file_uploader("📷 जन आधार / आईडी कार्ड की फोटो अपलोड करें", type=["jpg", "png", "jpeg"])
    scanned_text = ""
    
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="अपलोड की गई फोटो", width=300)
        with st.spinner("⏳ फोटो से टेक्स्ट पढ़ा जा रहा है..."):
            image_np = np.array(image)
            ocr_result = reader.readtext(image_np, detail=0)
            scanned_text = " ".join(ocr_result)
        st.success("📝 फोटो से पढ़ा गया डेटा नीचे बॉक्स में आ गया है!")
        st.text_area("📋 एक्सट्रैक्ट किया गया टेक्स्ट:", value=scanned_text, height=100)

    st.subheader("📋 सदस्य पंजीकरण फॉर्म")
    with st.form(key='family_form', clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            jan_aadhaar = st.text_input("💳 जन आधार / परिवार आईडी:")
            head_name = st.text_input("👤 परिवार के मुखिया का नाम:")
            village = st.selectbox("🏡 गांव का नाम:", ["रामपुर", "गोपालपुरा", "किशनगढ़", "नयापुरा"])
        with col2:
            member_name = st.text_input("👦 नए सदस्य का नाम:")
            relation = st.selectbox("🔗 मुखिया से संबंध:", ["स्वयं", "पति/पत्नी", "पुत्र", "पुत्री", "माता/पिता"])
            m_age = st.number_input("🎂 उम्र (Age):", min_value=0, max_value=120, value=25)
            
        if st.form_submit_button(label="👥 सदस्य सुरक्षित करें"):
            if jan_aadhaar and member_name:
                new_row = [datetime.now().strftime("%Y-%m-%d"), "फैमिली रजिस्ट्रेशन (OCR)", jan_aadhaar, head_name, member_name, f"उम्र: {m_age}, संबंध: {relation}, गांव: {village}", "✅ सदस्य पंजीकृत"]
                df = pd.read_csv(DATA_FILE)
                df.loc[len(df)] = new_row
                df.to_csv(DATA_FILE, index=False)
                st.success(f"🎉 {member_name} को सुरक्षित कर दिया गया है!")
            else:
                st.error("⚠️ कृपया जन आधार नंबर और सदस्य का नाम अवश्य भरें!")

with tab2:
    st.header("📝 एआई-असिस्टेड स्वास्थ्य सर्वे फॉर्म")
    col3, col4 = st.columns(2)
    with col3:
        s_name = st.text_input("मरीज का नाम:")
        s_age = st.number_input("उम्र दर्ज करें:", min_value=0, max_value=120, value=30)
        s_bp = st.text_input("🩺 ब्लड प्रेशर (BP):", value="120/80")
    with col4:
        s_symptoms = st.text_area("🤒 मुख्य लक्षण / बीमारी:", placeholder="उदाहरण: 3 दिन से बुखार है")

    if st.button("✨ AI से ऑटो-निष्कर्ष निकालें"):
        if s_symptoms:
            st.session_state['ai_remark'] = local_ai_engine(s_age, s_symptoms, s_bp)
            st.toast("AI ने डेटा प्रोसेस कर लिया है!")
        else:
            st.warning("⚠️ कृपया पहले लक्षण लिखें।")

    final_remark = st.text_area("✍️ सर्वे निष्कर्ष (AI द्वारा सुझाया गया):", value=st.session_state.get('ai_remark', ''))

    if st.button("💾 फाइनल सर्वे सबमिट करें"):
        if s_name and s_symptoms:
            new_row = [datetime.now().strftime("%Y-%m-%d"), "स्वास्थ्य सर्वे", s_name, f"उम्र: {s_age}", f"BP: {s_bp}", s_symptoms, final_remark]
            df = pd.read_csv(DATA_FILE)
            df.loc[len(df)] = new_row
            df.to_csv(DATA_FILE, index=False)
            st.success("🚀 स्वास्थ्य सर्वे डेटा सुरक्षित कर लिया गया है!")
            if 'ai_remark' in st.session_state: del st.session_state['ai_remark']
        else:
            st.error("⚠️ कृपया मरीज का नाम और लक्षण दर्ज करें!")

with tab3:
    st.header("📊 आज का सर्वे रिकॉर्ड डेटाबेस")
    if os.path.exists(DATA_FILE):
        df_show = pd.read_csv(DATA_FILE)
        if not df_show.empty:
            st.dataframe(df_show, use_container_width=True)
            csv = df_show.to_csv(index=False).encode('utf-8')
            st.download_button("📥 पूरी एक्सेल शीट डाउनलोड करें", data=csv, file_name="IHMS_OCR_Report.csv", mime="text/csv")
        else:
            st.info("📂 अभी तक कोई डेटा दर्ज नहीं किया गया है।")

