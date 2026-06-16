import streamlit as st
import os
import asyncio
import ollama
import re
from pydub import AudioSegment
import edge_tts

# ==========================================
# إعداد الصفحة
# ==========================================
st.set_page_config(
    page_title="🎙️ AI Egyptian Podcast Generator",
    page_icon="🎙️",
    layout="centered"
)

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    font-family: Arial;
}
textarea, input {
    direction: rtl !important;
    text-align: right !important;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# النموذج الافتراضي (خفيف وقوي)
# ==========================================
DEFAULT_MODEL = "qwen2.5:1.5b"  # 1.5 مليار معلمة – سريع ودقيق

# ==========================================
# البرومبت الاحترافي
# ==========================================
def generate_podcast_script(text, model):
    prompt = f"""
حوّل النص التالي إلى حوار قصير بين سلمى وشاكر. الحوار يجب أن **يشرح النص فقط**، دون أي معلومات إضافية من عندك.

- سلمى تسأل أسئلة عن الأفكار الواردة في النص (مثل: ما معنى ...؟ كيف يعمل ...؟).
- شاكر يجيب باختصار ويضرب مثالاً بسيطاً من الحياة اليومية لشرح الفكرة.
- لا تذكر أي شيء غير موجود في النص الأصلي.
- لا تحية، لا مقدمات، لا نهايات.
- عدد التبادلات: 6 إلى 8 جمل متبادلة (أي 12-16 سطراً).
- التنسيق بالضبط:
سلمى: ...
شاكر: ...

النص:
{text}
"""
    try:
        res = ollama.generate(
            model=model,
            prompt=prompt,
           options={
                "temperature": 0.3,      # أقل إبداع = أسرع وأكثر دقة
                "num_predict": 500,      # تكفي 8-10 جمل
                "num_thread": 4          # حسب جهازك (لو 8 أنوية حقيقية استخدم 8)
            }
        )
        return res["response"].strip()
    except Exception as e:
        st.error(f"فشل التوليد: {e}")
        return None

# ==========================================
# تحويل النص إلى صوت (بدون تقطيع)
# ==========================================
async def tts(text, voice, file):
    try:
        # تنظيف النص مع الحفاظ على علامات الترقيم
        text = re.sub(r"[^\w\s\u0600-\u06FF.,!?؟،-]", "", text).strip()
        if len(text) < 2:
            return False
        comm = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+0%"   # سرعة طبيعية محترمة
        )
        await comm.save(file)
        return os.path.exists(file) and os.path.getsize(file) > 800
    except:
        return False

# ==========================================
# تجميع البودكاست (تتابعي لضمان الثبات)
# ==========================================
async def process(script, v1, v2):
    lines = [l.strip() for l in script.split("\n") if l.strip()]
    tasks = []
    files = []
    last_voice = v1
    counter = 0

    for line in lines:
        line = re.sub(r"^[*\-•\s]+", "", line).replace("：", ":")
        text = None
        voice = None

        if "سلمى" in line and ":" in line:
            text = line.split(":", 1)[1].strip()
            voice = v1
            last_voice = v1
        elif "شاكر" in line and ":" in line:
            text = line.split(":", 1)[1].strip()
            voice = v2
            last_voice = v2
        else:
            text = line
            voice = last_voice

        if not text or len(text) < 2:
            continue

        file = f"temp_{counter}.mp3"
        tasks.append((tts(text, voice, file), text, voice, file))
        files.append(file)
        counter += 1

    if not tasks:
        return False

    # تشغيل تتابعي مع كشف الفشل
    results = []
    for t, txt, v, f in tasks:
        ok = await t
        if not ok or not os.path.exists(f) or os.path.getsize(f) < 800:
            # محاولة إنقاذ: استخدام الصوت الآخر (لو متاح)
            alt_voice = v1 if v == v2 else v2
            st.warning(f"فشل توليد الصوت لـ `{v}` مع النص: {txt[:50]}... ❌ سيتم المحاولة بـ {alt_voice}")
            # إعادة المحاولة مرة واحدة
            await tts(txt, alt_voice, f)
            ok = os.path.exists(f) and os.path.getsize(f) > 800
        results.append(ok)

    valid_files = [f for f, ok in zip(files, results) if ok]
    if not valid_files:
        return False

    # دمج المقاطع
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(300)
    for f in valid_files:
        audio = AudioSegment.from_file(f)
        combined += audio + pause

    combined.export("output.mp3", format="mp3")

    # تنظيف
    for f in files:
        try:
            os.remove(f)
        except:
            pass

    return True

# ==========================================
# واجهة المستخدم
# ==========================================
st.title("🎙️ صانع البودكاست المصري بالذكاء الاصطناعي")
st.caption("حوّل أي نص علمي إلى حوار بودكاست مشوّق بين سلمى والخبير شاكر")

# الشريط الجانبي
model = st.sidebar.selectbox(
    "🧠 الموديل",
    [DEFAULT_MODEL, "qwen2.5:3b-instruct", "qwen2.5:0.5b"],
    help="اختر نموذج 1.5b للسرعة والجودة المتوازنة"
)

voice1 = st.sidebar.selectbox("🎤 صوت سلمى", ["ar-EG-SalmaNeural"])
voice2 = st.sidebar.selectbox("🎤 صوت شاكر", ["ar-EG-ShakirNeural"])

# منطقة النص
text = st.text_area(
    "✍️ اكتب النص العلمي اللي عايز تحوّله لبودكاست:",
    height=200,
    placeholder="مثال: الذكاء الاصطناعي التوليدي هو نوع من الذكاء الاصطناعي..."
)

# ==========================================
# زر البدء والتنفيذ
# ==========================================
if st.button("🚀 ابدأ البودكاست"):
    if not text.strip():
        st.warning("من فضلك اكتب النص الأول!")
        st.stop()

    # مؤشر التقدم (نوع Spinner)
    with st.spinner("🧠 جاري كتابة السكريبت..."):
        script = generate_podcast_script(text, model)

    if script is None:
        st.stop()

    # تنظيف الناتج
    script = script.replace("سلمي", "سلمى")
    script = script.replace("شاكر ", "شاكر:")
    script = "\n".join(script.split("\n")[:40])  # أمان من الطول الزائد

    st.subheader("📜 السكريبت")
    st.code(script)

    with st.spinner("🎙️ جاري توليد الصوت..."):
        success = asyncio.run(process(script, voice1, voice2))

    if success:
        with open("output.mp3", "rb") as f:
            st.audio(f.read())
            st.download_button(
                "⬇️ تحميل البودكاست",
                f,
                file_name="egyptian_podcast.mp3"
            )
    else:
        st.error("فشل توليد الصوت، تأكد من اتصال الإنترنت.")