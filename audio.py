import streamlit as st
import os
import asyncio
import re
import base64
import json
import tempfile
from pydub import AudioSegment
import edge_tts
import PyPDF2
from groq import Groq  # بدلاً من ollama

st.set_page_config(page_title="🎙️ بودكاست جامعة الإسكندرية", page_icon="🤖", layout="wide")

# ==========================================
# تصميم متطور: زجاجي، خلفية روبوت، فقاعات نيون
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

* {
    font-family: 'Cairo', sans-serif;
}

.stApp {
    background: radial-gradient(ellipse at 20% 50%, #0a0f1f 0%, #010101 100%);
    color: #e2e8f0;
    direction: rtl;
}

/* روبوت متحرك في الخلفية */
.robot-bg {
    position: fixed;
    bottom: 20px;
    left: 20px;
    font-size: 9rem;
    opacity: 0.06;
    pointer-events: none;
    z-index: 0;
    animation: robotFloat 12s infinite ease-in-out;
}

@keyframes robotFloat {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-15px) rotate(3deg); }
    100% { transform: translateY(0px) rotate(0deg); }
}

/* الحاوية الزجاجية الرئيسية */
.main-glass {
    background: rgba(15, 25, 45, 0.6);
    backdrop-filter: blur(18px);
    border-radius: 48px;
    padding: 2rem;
    margin: 2rem auto 160px auto;
    max-width: 1100px;
    border: 1px solid rgba(96, 165, 250, 0.25);
    box-shadow: 0 25px 45px rgba(0,0,0,0.5);
    position: relative;
    z-index: 1;
}

.title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}

.sub {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 2rem;
}

/* زر الإنتاج */
.stButton > button {
    background: linear-gradient(95deg, #1e40af, #6b21a5);
    color: white;
    border: none;
    border-radius: 60px;
    padding: 0.8rem 1.5rem;
    font-weight: bold;
    transition: 0.3s;
    width: 100%;
    font-size: 1.1rem;
}
.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 20px #3b82f6;
}

/* عداد الكلمات */
.word-counter {
    background: rgba(0,0,0,0.3);
    border-radius: 40px;
    padding: 6px 18px;
    display: inline-block;
    font-size: 0.9rem;
    margin: 10px 0;
    border: 1px solid rgba(255,255,255,0.1);
}
.warning-box {
    background: rgba(234, 179, 8, 0.15);
    border: 1px solid #eab308;
    border-radius: 16px;
    padding: 1rem;
    margin: 1rem 0;
    color: #fde047;
}
.error-box {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: 16px;
    padding: 1rem;
    margin: 1rem 0;
    color: #fca5a5;
}

/* الفقاعات */
.bubble {
    transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}
.bubble.active {
    box-shadow: 0 0 30px rgba(96,165,250,0.7), inset 0 0 30px rgba(96,165,250,0.1) !important;
    transform: scale(1.02) !important;
    border-color: #60a5fa !important;
}
.bubble .live-icon {
    transition: all 0.3s ease;
}
.bubble.active .live-icon {
    opacity: 1 !important;
    animation: pulse 0.8s infinite;
}
@keyframes pulse {
    0% { opacity: 0.5; transform: scale(0.9); }
    100% { opacity: 1; transform: scale(1.2); }
}

/* منطقة التمرير الخاصة بالنص */
#transcript {
    max-height: 420px;
    overflow-y: auto;
    background: rgba(0,0,0,0.2);
    border-radius: 36px;
    padding: 20px;
    scroll-behavior: smooth;
}
#transcript::-webkit-scrollbar {
    width: 6px;
}
#transcript::-webkit-scrollbar-track {
    background: #1e293b;
    border-radius: 10px;
}
#transcript::-webkit-scrollbar-thumb {
    background: #3b82f6;
    border-radius: 10px;
}

/* مشغل الصوت الثابت */
.player-fixed {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    z-index: 9999;
    background: rgba(10, 15, 30, 0.85);
    backdrop-filter: blur(24px);
    border-top: 1px solid rgba(255,255,255,0.08);
    padding: 12px 24px 16px 24px;
    box-shadow: 0 -10px 40px rgba(0,0,0,0.7);
}
.player-fixed audio {
    width: 100%;
    border-radius: 40px;
    background: #0f172a;
    height: 40px;
}
.player-controls {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-top: 8px;
    flex-wrap: wrap;
}
.player-controls button {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 40px;
    padding: 5px 14px;
    color: #e2e8f0;
    cursor: pointer;
    transition: 0.2s;
    font-size: 13px;
    min-width: 44px;
    font-weight: 500;
    backdrop-filter: blur(4px);
}
.player-controls button:hover {
    background: rgba(59,130,246,0.4);
    transform: translateY(-2px);
    border-color: #60a5fa;
}
.player-controls .play-btn {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border: none;
    font-size: 16px;
    padding: 6px 24px;
    border-radius: 40px;
    font-weight: bold;
    color: white;
    box-shadow: 0 4px 15px rgba(59,130,246,0.3);
}
.player-controls .play-btn:hover {
    box-shadow: 0 0 25px rgba(59,130,246,0.6);
    transform: scale(1.05);
}
.progress-time {
    color: #94a3b8;
    font-size: 13px;
    min-width: 100px;
    text-align: center;
    font-weight: 500;
    letter-spacing: 0.5px;
}
</style>
<div class="robot-bg">🤖</div>
""", unsafe_allow_html=True)

# ==========================================
# الإعدادات
# ==========================================
VOICE_PROF = "ar-EG-ShakirNeural"
VOICE_STUDENT = "ar-EG-SalmaNeural"

# حدود الكلمات
MAX_WORDS = 3000
WARN_WORDS = 1500

# ==========================================
# تهيئة عميل Groq
# ==========================================
@st.cache_resource
def get_groq_client():
    try:
        # استخدام st.secrets للحصول على المفتاح في Streamlit Cloud
        api_key = st.secrets.get("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")
        if not api_key:
            # تجربة المفتاح من متغيرات البيئة
            api_key = os.environ.get("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")
        if not api_key:
            raise ValueError("لم يتم العثور على GROQ_API_KEY")
        return Groq(api_key=api_key)
    except Exception as e:
        st.error(f"فشل تهيئة عميل Groq: {e}")
        return None

# ==========================================
# دوال المساعدة
# ==========================================
def extract_pdf_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join([p.extract_text() or "" for p in reader.pages])
        return text.strip()
    except:
        return None

def count_words(text):
    return len(text.split())

def split_text_into_chunks(text, max_words_per_chunk=800):
    words = text.split()
    if len(words) <= max_words_per_chunk:
        return [text]
    chunks = []
    current_chunk_words = []
    current_chunk_len = 0
    for word in words:
        if current_chunk_len + len(word) + 1 <= max_words_per_chunk:
            current_chunk_words.append(word)
            current_chunk_len += len(word) + 1
        else:
            chunks.append(" ".join(current_chunk_words))
            current_chunk_words = [word]
            current_chunk_len = len(word) + 1
    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))
    return chunks

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s\.،!؟…:؛-]', '', text)
    return text.strip()

def parse_script(script):
    lines = script.split('\n')
    dialogue = []
    for line in lines:
        line = line.strip()
        if ':' not in line:
            continue
        parts = line.split(':', 1)
        if len(parts) != 2:
            continue
        speaker = parts[0].strip()
        txt = parts[1].strip()
        if speaker in ['الأستاذ', 'دكتور', 'أستاذ', 'البروفيسور']:
            role = 'doctor'
        elif speaker in ['الطالب', 'طالب']:
            role = 'student'
        else:
            continue
        txt = clean_text(txt)
        if len(txt) < 8:
            continue
        dialogue.append({"role": role, "text": txt})
    return dialogue

# ==========================================
# توليد الحوار باستخدام Groq (بدلاً من Ollama)
# ==========================================
def generate_script(text, model="llama3-70b-8192"):
    client = get_groq_client()
    if not client:
        return None
    
    word_count = count_words(text)
    chunks = split_text_into_chunks(text, max_words_per_chunk=800)
    
    if word_count > WARN_WORDS:
        st.warning(f"⚠️ المحتوى كبير نسبياً ({word_count} كلمة). سيتم تقسيمه إلى {len(chunks)} جزء لتسهيل المعالجة، قد يستغرق وقتاً أطول.")
    
    all_scripts = []
    progress_bar_chunks = st.progress(0)
    
    for idx, chunk in enumerate(chunks):
        context = "" if idx == 0 else "هذا هو الجزء التالي من النص، استمر في الحوار بنفس الأسلوب مع تجنب تكرار الأسئلة."
        
        prompt = f"""
أنت منتج بودكاست تعليمي متميز، مثل بودكاست "NotebookLM". حول النص الأكاديمي التالي إلى حوار شيق وواضح بين أستاذ وطالب.

تعليمات:
1. **اللغة**: العربية الفصحى فقط، بدون كلمات إنجليزية. اكتب المصطلحات بالعربية مع شرح.
2. **التنسيق**: كل جملة تبدأ بـ "الأستاذ:" أو "الطالب:".
3. **طبيعة الحوار**: الأستاذ يشرح بأسلوب قصصي، والطالب يسأل أسئلة ذكية.
4. **تجنب التكرار**: لا تكرر نفس السؤال، استخدم صيغاً متنوعة للأسئلة.
5. **الطول**: حوالي 10-15 جملة لكل جزء.
6. **الاستمرارية**: {context}

النص:
{chunk}

اكتب الحوار الآن:
"""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.35,
                max_tokens=3000,
                top_p=0.9,
            )
            script_part = response.choices[0].message.content.strip()
            all_scripts.append(script_part)
        except Exception as e:
            st.error(f"فشل توليد الجزء {idx+1}: {e}")
            return None
        progress_bar_chunks.progress((idx + 1) / len(chunks))
    
    progress_bar_chunks.empty()
    full_script = "\n\n".join(all_scripts)
    return full_script

# ==========================================
# توليد الصوت (نفس الكود السابق)
# ==========================================
async def gen_segment(text, voice, filepath):
    try:
        clean = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s.,!؟]', '', text)
        if len(clean) < 5:
            return False
        comm = edge_tts.Communicate(text=clean, voice=voice, rate="+0%")
        await comm.save(filepath)
        return os.path.getsize(filepath) > 1000
    except:
        return False

async def build_audio(dialogue, progress_bar, status_text):
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_files = []
        tasks = []
        for i, item in enumerate(dialogue):
            voice = VOICE_PROF if item["role"] == "doctor" else VOICE_STUDENT
            fname = os.path.join(tmpdir, f"seg_{i}.mp3")
            temp_files.append(fname)
            tasks.append(gen_segment(item["text"], voice, fname))

        results = []
        for i, task in enumerate(tasks):
            ok = await task
            results.append(ok)
            progress_bar.progress((i+1)/len(tasks))
            status_text.text(f"🎙️ توليد الصوت... {i+1}/{len(tasks)}")

        combined = AudioSegment.empty()
        timestamps = []
        current = 0.0
        pause = AudioSegment.silent(400)

        for i, ok in enumerate(results):
            if ok:
                audio = AudioSegment.from_file(temp_files[i])
                combined += audio + pause
                timestamps.append(round(current, 2))
                current += (len(audio) + len(pause)) / 1000.0
            else:
                combined += pause
                timestamps.append(round(current, 2))
                current += 0.5

        final_path = os.path.join(tmpdir, "final.mp3")
        combined.export(final_path, format="mp3")
        with open(final_path, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes, timestamps

# ==========================================
# مشغل HTML مع فقاعات زجاجية وهايلايت
# ==========================================
def player_html(audio_b64, timestamps, dialogue):
    bubbles = ""
    for i, item in enumerate(dialogue):
        is_doctor = item['role'] == 'doctor'
        align = "flex-end" if is_doctor else "flex-start"
        bg = "linear-gradient(125deg, rgba(37,99,235,0.85), rgba(124,58,237,0.7))" if is_doctor else "rgba(30,41,59,0.95)"
        name = "👨‍🏫 الأستاذ" if is_doctor else "👩‍🎓 الطالب"
        icon = "👨‍🏫" if is_doctor else "👩‍🎓"
        text_display = item['text']
        bubbles += f"""
        <div class="msg" data-index="{i}" style="display: flex; justify-content: {align}; margin: 14px 0;">
            <div class="bubble" style="background: {bg}; max-width: 85%; border-radius: 32px; padding: 14px 24px; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.2); transition: all 0.25s ease; cursor: pointer;">
                <div style="display: flex; gap: 14px; align-items: flex-start;">
                    <div style="font-size: 32px;">{icon}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: bold; font-size: 0.9rem; opacity: 0.8; margin-bottom: 6px;">{name}</div>
                        <div style="font-size: 1rem; line-height: 1.55;">{text_display}</div>
                    </div>
                    <div class="live-icon" style="font-size: 22px; opacity: 0; transition: 0.2s;">🔊</div>
                </div>
            </div>
        </div>"""

    html = f"""
    <div>
        <div id="transcript">
            {bubbles}
        </div>
    </div>

    <!-- مشغل الصوت الثابت -->
    <div class="player-fixed">
        <audio id="player" controls style="width: 100%; border-radius: 50px; background: #0f172a; height: 40px;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mpeg">
        </audio>
        <div class="player-controls">
            <button class="play-btn" id="playPauseBtn">▶️ تشغيل</button>
            <button class="speed-btn" data-rate="0.5">0.5x</button>
            <button class="speed-btn" data-rate="0.75">0.75x</button>
            <button class="speed-btn" data-rate="1">1x</button>
            <button class="speed-btn" data-rate="1.25">1.25x</button>
            <button class="speed-btn" data-rate="1.5">1.5x</button>
            <button class="speed-btn" data-rate="2">2x</button>
            <button id="skip-back">⏪ -10</button>
            <button id="skip-fwd">+10 ⏩</button>
            <span class="progress-time" id="timeDisplay">00:00 / 00:00</span>
        </div>
    </div>

    <script>
        const player = document.getElementById('player');
        const playBtn = document.getElementById('playPauseBtn');
        const timeDisplay = document.getElementById('timeDisplay');
        const stamps = {json.dumps(timestamps)};

        function formatTime(seconds) {{
            if (!seconds) return '00:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${{String(mins).padStart(2, '0')}}:${{String(secs).padStart(2, '0')}}`;
        }}

        function updateTime() {{
            if (player.duration) {{
                timeDisplay.textContent = `${{formatTime(player.currentTime)}} / ${{formatTime(player.duration)}}`;
            }}
        }}

        playBtn.addEventListener('click', () => {{
            if (player.paused) {{
                player.play();
                playBtn.textContent = '⏸️ إيقاف';
            }} else {{
                player.pause();
                playBtn.textContent = '▶️ تشغيل';
            }}
        }});

        player.addEventListener('ended', () => {{
            playBtn.textContent = '▶️ تشغيل';
        }});

        player.addEventListener('timeupdate', () => {{
            updateTime();
        }});

        document.querySelectorAll('.speed-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                player.playbackRate = parseFloat(btn.getAttribute('data-rate'));
            }});
        }});

        document.getElementById('skip-back').onclick = () => {{
            player.currentTime = Math.max(0, player.currentTime - 10);
        }};
        document.getElementById('skip-fwd').onclick = () => {{
            player.currentTime = Math.min(player.duration, player.currentTime + 10);
        }};

        player.ontimeupdate = () => {{
            let cur = player.currentTime;
            let activeIndex = -1;
            for(let i=0; i<stamps.length; i++) {{
                if(stamps[i] <= cur) activeIndex = i;
                else break;
            }}
            document.querySelectorAll('.bubble').forEach(b => {{
                b.classList.remove('active');
            }});
            if(activeIndex !== -1) {{
                let activeBubble = document.querySelector(`.msg[data-index='${{activeIndex}}'] .bubble`);
                if(activeBubble) {{
                    activeBubble.classList.add('active');
                    activeBubble.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }}
        }};

        document.querySelectorAll('.msg').forEach(msg => {{
            msg.addEventListener('click', () => {{
                let idx = parseInt(msg.getAttribute('data-index'));
                if(!isNaN(idx) && stamps[idx] !== undefined) {{
                    player.currentTime = stamps[idx];
                    player.play();
                    playBtn.textContent = '⏸️ إيقاف';
                }}
            }});
        }});

        player.addEventListener('loadedmetadata', updateTime);
        player.addEventListener('canplay', updateTime);
    </script>
    """
    return html

# ==========================================
# واجهة التطبيق
# ==========================================
with st.container():
    st.markdown('<div class="main-glass">', unsafe_allow_html=True)
    st.markdown('<div class="title">🎓 بودكاست جامعة الإسكندرية الذكي</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">أدخل نصاً أو رفع PDF وسنحوله إلى بودكاست تعليمي تفاعلي</div>', unsafe_allow_html=True)

    pdf_file = st.file_uploader("📁 رفع ملف PDF (اختياري)", type=['pdf'], label_visibility="collapsed")
    default_text = ""
    if pdf_file:
        with st.spinner("قراءة PDF..."):
            default_text = extract_pdf_text(pdf_file) or ""
        if default_text:
            st.success("تم استخراج النص بنجاح ✅")

    user_text = st.text_area("📝 المحتوى الدراسي", value=default_text, height=180,
                             placeholder="الصق هنا نص المحاضرة أو المقال...")

    if user_text.strip():
        word_count = count_words(user_text)
        color = "green" if word_count <= WARN_WORDS else "orange" if word_count <= MAX_WORDS else "red"
        st.markdown(f"""
        <div class="word-counter" style="border-color: {color};">
            📊 عدد الكلمات: <strong>{word_count}</strong> 
            (الحد الأقصى: {MAX_WORDS} كلمة)
        </div>
        """, unsafe_allow_html=True)
        if word_count > MAX_WORDS:
            st.markdown(f"""
            <div class="error-box">
            ❌ **تجاوز الحد الأقصى**  
            عدد الكلمات ({word_count}) يتجاوز الحد المسموح ({MAX_WORDS}).  
            يرجى **تقسيم المحتوى** إلى أجزاء أصغر (مثلاً 1500 كلمة لكل جزء) ثم إعادة المحاولة.
            </div>
            """, unsafe_allow_html=True)
        elif word_count > WARN_WORDS:
            st.markdown(f"""
            <div class="warning-box">
            ⚠️ **تنبيه:** المحتوى كبير نسبياً (عدد الكلمات: {word_count})  
            سيتم تقسيم النص إلى أجزاء لتسهيل المعالجة، قد يستغرق وقتاً أطول.
            </div>
            """, unsafe_allow_html=True)

    if st.button("🚀 إنتاج البودكاست", use_container_width=True):
        if not user_text.strip():
            st.warning("يرجى إدخال نص أو رفع ملف PDF")
        else:
            word_count = count_words(user_text)
            if word_count > MAX_WORDS:
                st.error(f"❌ النص كبير جداً ({word_count} كلمة). الحد الأقصى {MAX_WORDS} كلمة. يرجى تقسيم المحتوى.")
                st.stop()

            with st.spinner("🤖 الذكاء الاصطناعي يصوغ الحوار..."):
                script_raw = generate_script(user_text)
            if not script_raw:
                st.error("فشل توليد الحوار، تأكد من إعداد مفتاح Groq API")
            else:
                with st.expander("📄 نص الحوار الخام (للمطورين)"):
                    st.code(script_raw, language='text')
                
                dialogue = parse_script(script_raw)
                st.info(f"📊 تم استخراج {len(dialogue)} مقطع حوار")
                if len(dialogue) < 2:
                    st.error("الحوار قصير جداً، حاول مرة أخرى بنص أكثر تفصيلاً")
                else:
                    progress_bar = st.progress(0)
                    status = st.empty()
                    try:
                        audio_bytes, stamps = asyncio.run(build_audio(dialogue, progress_bar, status))
                    except Exception as e:
                        st.error(f"خطأ في توليد الصوت: {e}")
                        st.stop()
                    status.empty()
                    progress_bar.empty()
                    b64 = base64.b64encode(audio_bytes).decode()
                    st.components.v1.html(player_html(b64, stamps, dialogue), height=580)
                    st.download_button("⬇️ تحميل البودكاست (MP3)", data=audio_bytes, file_name="podcast.mp3", mime="audio/mpeg", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='text-align:center;margin:1rem;opacity:0.4;'>© 2025 جامعة الإسكندرية - تقنية زجاجية وذكاء اصطناعي</div>", unsafe_allow_html=True)
