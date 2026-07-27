"""
YouTube Long-Form Video Automation - Bilingual English/Thai Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Thai translations
CATEGORIES_THAI = {
    "Motivation": "แรงบันดาลใจ",
    "Love": "ความรัก",
    "Success": "ความสำเร็จ",
    "Wisdom": "ปัญญา",
    "Happiness": "ความสุข",
    "Self Improvement": "การพัฒนาตนเอง",
    "Gratitude": "ความกตัญญู",
    "Friendship": "มิตรภาพ",
    "Hope": "ความหวัง",
    "Creativity": "ความคิดสร้างสรรค์",
    "Inner Peace": "สันติภายใน",
    "Confidence": "ความมั่นใจ",
    "Perseverance": "ความมานะบากบั่น",
    "Inspiration": "แรงบันดาลใจ",
    "Positive Life": "ชีวิตเชิงบวก",
    "Courage": "ความกล้าหาญ",
    "Kindness": "ความเมตตา",
    "Patience": "ความอดทน",
    "Forgiveness": "การให้อภัย",
    "Strength": "พลัง",
    "Joy": "ความปีติ",
    "Balance": "ความสมดุล",
    "Growth": "การเติบโต",
    "Purpose": "จุดมุ่งหมาย",
    "Mindfulness": "สติ",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "th-TH-PremwadeeNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "thai": phrase["thai"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_thai = CATEGORIES_THAI[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Thai.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Thai IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Thai words at all.
The "thai" field contains the Thai translation in Thai script.
The "pronunciation" field is phonetic English spelling.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Thai words): {{"english": "Don't say 'mai pen rai,' it means more than 'no problem.'", ...}}
WRONG (Thai word in english): {{"english": "Use 'jai yen yen' for take it easy", ...}}
WRONG (lesson tip): {{"english": "Say 'khrap' for men, 'kha' for women", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "thai": "ความรู้คือกุญแจสู่ปัญญา", "pronunciation": "khwam-ru kheu gun-jae su pan-ya"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "thai": "คนฉลาดฟังมากกว่าที่พวกเขาพูด", "pronunciation": "khon-cha-lat fang mak-kwa thi-phuak-khao phoot"}}

The english field MUST be 100% English words only. Absolutely NO Thai script or Thai words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Thai words) with commas for natural pauses
2. Thai translation (Thai script only)
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "thai": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Thai words - no Thai script, no Thai words, no romanized Thai. These are universal inspirational phrases, NOT language learning tips. Thai goes ONLY in the 'thai' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "thai": "เชื่อมั่นในตัวเอง", "pronunciation": "cheu-a-man nai-tua-eng"},
            {"english": "You are capable of amazing things.", "thai": "คุณสามารถทำสิ่งมหัศจรรย์ได้", "pronunciation": "khun-sa-mat tham sing-ma-hat-san dai"},
            {"english": "Dream big, start small.", "thai": "ฝันใหญ่ เริ่มเล็ก", "pronunciation": "fan-yai rerm-lek"},
            {"english": "Your future is created by your actions.", "thai": "อนาคตของคุณถูกสร้างขึ้นจากการกระทำของคุณ", "pronunciation": "a-na-khot khong-khun thuk-sang kuen jak kan-kra-tam khong-khun"},
            {"english": "Never give up on your dreams.", "thai": "อย่ายอมแพ้กับความฝันของคุณ", "pronunciation": "ya-yom-pae gap khwam-fan khong-khun"},
            {"english": "Small steps lead to big changes.", "thai": "ก้าวเล็กๆ นำไปสู่การเปลี่ยนแปลงครั้งใหญ่", "pronunciation": "kao-lek-lek nam-pai-su kan-plian-plaeng khrung-yai"},
            {"english": "You are stronger than you think.", "thai": "คุณแข็งแกร่งกว่าที่คุณคิด", "pronunciation": "khun-khaeng-graeng kwa-thi-khun-khit"},
        ],
        "Love": [
            {"english": "Love yourself first.", "thai": "รักตัวเองก่อน", "pronunciation": "rak-tua-eng kon"},
            {"english": "Love makes everything possible.", "thai": "ความรักทำให้ทุกสิ่งเป็นไปได้", "pronunciation": "khwam-rak tham-hai thook-sing pen-pai-dai"},
            {"english": "My heart beats for you.", "thai": "หัวใจของฉันเต้นเพื่อคุณ", "pronunciation": "hua-jai khong-chan ten pheua-khun"},
            {"english": "You are my everything.", "thai": "คุณคือทุกสิ่งของฉัน", "pronunciation": "khun-kheu thook-sing khong-chan"},
            {"english": "Together forever, hand in hand.", "thai": "ตลอดไป จับมือกัน", "pronunciation": "ta-lot-pai jap-meu-kan"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "thai": "ความสำเร็จมาจากการทำงานหนัก", "pronunciation": "khwam-sam-ret ma-jak kan-tham-ngan-nak"},
            {"english": "Keep going, you're getting there.", "thai": "เดินหน้าต่อไป คุณกำลังไปถึงแล้ว", "pronunciation": "doen-na-ta-pai khun-gam-lang-pai-thung-laew"},
            {"english": "Winners never quit.", "thai": "ผู้ชนะไม่เคยยอมแพ้", "pronunciation": "phu-cha-na mai-koei yom-pae"},
            {"english": "Your effort will pay off.", "thai": "ความพยายามของคุณจะได้รับผลตอบแทน", "pronunciation": "khwam-pha-ya-yam khong-khun ja-dai-rap phon-top-thaen"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "thai": "ความรู้คือพลัง", "pronunciation": "khwam-ru kheu pha-lang"},
            {"english": "Learn from yesterday, live for today.", "thai": "เรียนรู้จากเมื่อวาน ใช้ชีวิตเพื่อวันนี้", "pronunciation": "rian-ru jak-meua-wan chai-chee-wit pheua-wan-nee"},
            {"english": "Think before you act.", "thai": "คิดก่อนลงมือทำ", "pronunciation": "khit-kon long-meu-tham"},
            {"english": "Experience is the best teacher.", "thai": "ประสบการณ์คือครูที่ดีที่สุด", "pronunciation": "pra-sop-kan kheu khru thi-di-thi-sut"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "thai": "ความสุขคือทางเลือก", "pronunciation": "khwam-suk kheu thang-lueak"},
            {"english": "Find joy in the little things.", "thai": "จงพบความสุขในสิ่งเล็กๆ", "pronunciation": "jong-phob khwam-suk nai sing-lek-lek"},
            {"english": "Smile, it makes others happy.", "thai": "ยิ้มเข้าไว้ มันทำให้คนอื่นมีความสุข", "pronunciation": "yim-khao-wai man tham-hai khon-eun mi-khwam-suk"},
            {"english": "Today is a gift.", "thai": "วันนี้คือของขวัญ", "pronunciation": "wan-nee kheu khong-khwan"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "thai": "ทำให้ดีกว่าเมื่อวาน", "pronunciation": "tham-hai di-kwa meua-wan"},
            {"english": "Grow through what you go through.", "thai": "เติบโตจากสิ่งที่คุณผ่าน", "pronunciation": "teurp-to jak sing-thi khun-phan"},
            {"english": "Invest in yourself daily.", "thai": "ลงทุนในตัวเองทุกวัน", "pronunciation": "long-thun nai-tua-eng thook-wan"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "thai": "ขอบคุณสำหรับทุกสิ่ง", "pronunciation": "khob-khun sam-rap thook-sing"},
            {"english": "I appreciate your help.", "thai": "ฉันซาบซึ้งในความช่วยเหลือของคุณ", "pronunciation": "chan-sap-sueang nai-khwam-chuai-leua khong-khun"},
            {"english": "Grateful for this moment.", "thai": "รู้สึกขอบคุณสำหรับช่วงเวลานี้", "pronunciation": "ru-suek khob-khun sam-rap chuang-wela-nee"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "thai": "เพื่อนกันตลอดไป ไม่ว่ายังไงก็ตาม", "pronunciation": "pheuan-kan ta-lot-pai mai-wa yang-ngai gor-tam"},
            {"english": "You are my best friend.", "thai": "คุณคือเพื่อนที่ดีที่สุดของฉัน", "pronunciation": "khun-kheu pheuan-thi-di-thi-sut khong-chan"},
            {"english": "True friends stick together.", "thai": "เพื่อนแท้อยู่ด้วยกันเสมอ", "pronunciation": "pheuan-thae yoo-duai-kan sa-moe"},
        ],
        "Hope": [
            {"english": "There is always hope.", "thai": "ยังมีความหวังเสมอ", "pronunciation": "yang mi-khwam-wang sa-moe"},
            {"english": "Better days are coming.", "thai": "วันที่ดีกว่านี้กำลังจะมา", "pronunciation": "wan-thi-di-kwa-nee gam-lang ja-ma"},
            {"english": "Keep faith, keep going.", "thai": "รักษาศรัทธา เดินหน้าต่อไป", "pronunciation": "rak-sa sat-tha doen-na-ta-pai"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "thai": "สร้างสิ่งที่สวยงามในวันนี้", "pronunciation": "sang sing-thi suay-ngam nai wan-nee"},
            {"english": "Your imagination is unlimited.", "thai": "จินตนาการของคุณไร้ขีดจำกัด", "pronunciation": "jin-ta-na-kan khong-khun rai-khit-jam-kat"},
            {"english": "Art comes from the heart.", "thai": "ศิลปะมาจากหัวใจ", "pronunciation": "sin-la-pa ma-jak hua-jai"},
            {"english": "Express yourself freely.", "thai": "แสดงตัวตนของคุณอย่างอิสระ", "pronunciation": "sa-daeng-tua-ton khong-khun yang-it-sa-ra"},
            {"english": "Innovation starts with curiosity.", "thai": "นวัตกรรมเริ่มต้นจากความอยากรู้", "pronunciation": "na-wat-ta-kam rerm-ton jak khwam-yak-ru"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "thai": "จงพบสันติสุขภายในตัวคุณ", "pronunciation": "jong-phob san-ti-suk phai-nai-tua-khun"},
            {"english": "Breathe, relax, let go.", "thai": "หายใจ ผ่อนคลาย ปล่อยวาง", "pronunciation": "hai-jai phon-klai ploy-wang"},
            {"english": "Calm mind, happy heart.", "thai": "ใจที่สงบ หัวใจที่สุข", "pronunciation": "jai-thi sa-ngop hua-jai-thi-suk"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "thai": "คุณก็ดีพอแล้วอย่างที่เป็น", "pronunciation": "khun gor di-pho laew yang-thi-pen"},
            {"english": "Stand tall, speak up.", "thai": "ยืนให้สูงส่ง พูดให้ดัง", "pronunciation": "yeun-hai soong-sing phoot-hai dang"},
            {"english": "Believe in your abilities.", "thai": "เชื่อมั่นในความสามารถของคุณ", "pronunciation": "cheu-a-man nai-khwam-sa-mat khong-khun"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "thai": "อย่ายอมแพ้ พยายามต่อไป", "pronunciation": "ya-yom-pae pha-ya-yam ta-pai"},
            {"english": "Storms make trees take deeper roots.", "thai": "พายุทำให้ต้นไม้หยั่งรากลึก", "pronunciation": "pha-yu tham-hai ton-mai yang-rak-luek"},
            {"english": "Patience and persistence win.", "thai": "ความอดทนและความพากเพียรชนะทุกสิ่ง", "pronunciation": "khwam-ot-thon lae khwam-phak-phian cha-na thook-sing"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "thai": "ปล่อยให้แสงของคุณส่องสว่าง", "pronunciation": "ploy-hai saeng khong-khun song-sa-wang"},
            {"english": "Inspire others by your actions.", "thai": "สร้างแรงบันดาลใจให้ผู้อื่นด้วยการกระทำของคุณ", "pronunciation": "sang raeng-ban-dan-jai hai phoo-eun duai kan-kra-tam khong-khun"},
            {"english": "Be the change you want to see.", "thai": "จงเป็นความเปลี่ยนแปลงที่คุณอยากเห็น", "pronunciation": "jong-pen khwam-plian-plaeng thi-khun-yak-hen"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "thai": "เลือกคิดบวกทุกวัน", "pronunciation": "lueak-khit-buak thook-wan"},
            {"english": "Good vibes only.", "thai": "มีแต่พลังบวก", "pronunciation": "mi-dtae pha-lang-buak"},
            {"english": "Life is what you make it.", "thai": "ชีวิตเป็นอย่างที่คุณสร้างมัน", "pronunciation": "chee-wit pen-yang-thi-khun-sang-man"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "thai": "กล้าหาญ ก้าวแรกไปเลย", "pronunciation": "kla-han kao-raek-pai-loei"},
            {"english": "Courage is not the absence of fear.", "thai": "ความกล้าหาญไม่ใช่การไร้ซึ่งความกลัว", "pronunciation": "khwam-kla-han mai-chai kan-rai sueng khwam-klua"},
            {"english": "Face your fears head on.", "thai": "เผชิญหน้ากับความกลัวของคุณ", "pronunciation": "pha-chern-na gap khwam-klua khong-khun"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "thai": "จงมีเมตตากับทุกคนที่คุณพบเจอ", "pronunciation": "jong-mi-metta gap thook-khon thi-khun-phob-joer"},
            {"english": "Kindness costs nothing, means everything.", "thai": "ความเมตตาไม่เสียค่าใช้จ่าย แต่มีความหมายมหาศาล", "pronunciation": "khwam-metta mai-sia-kha-chai-jai dtae-mi-khwam-mai-maha-san"},
            {"english": "Spread kindness wherever you go.", "thai": "แผ่ความเมตตาไปทุกที่ที่คุณไป", "pronunciation": "phae khwam-metta pai thook-thi thi-khun-pai"},
        ],
        "Patience": [
            {"english": "Good things take time.", "thai": "สิ่งดีๆ ต้องใช้เวลา", "pronunciation": "sing-di-di tong-chai-we-la"},
            {"english": "Wait patiently, trust the process.", "thai": "รออย่างอดทน วางใจในกระบวนการ", "pronunciation": "roh-yang-ot-thon wang-jai nai-grabuankan"},
            {"english": "Rome wasn't built in a day.", "thai": "โรมไม่ได้สร้างเสร็จในวันเดียว", "pronunciation": "roh-mai-dai-sang-sret nai-wan-diao"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "thai": "ให้อภัยและปลดปล่อยตัวเอง", "pronunciation": "hai-a-phai lae plot-ploi-tua-eng"},
            {"english": "Let go of grudges, find peace.", "thai": "ปล่อยวางความขุ่นเคือง จงพบสันติสุข", "pronunciation": "ploy-wang khwam-khun-kueang jong-phob san-ti-suk"},
            {"english": "Forgiveness is a gift to yourself.", "thai": "การให้อภัยคือของขวัญให้ตัวเอง", "pronunciation": "kan-hai-a-phai kheu khong-khwan-hai-tua-eng"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "thai": "คุณแข็งแกร่งกว่าที่คุณรู้", "pronunciation": "khun-khaeng-graeng kwa-thi-khun-ru"},
            {"english": "Inner strength comes from within.", "thai": "พลังภายในมาจากข้างใน", "pronunciation": "pha-lang-phai-nai ma-jak-khang-nai"},
            {"english": "Challenges make you stronger.", "thai": "อุปสรรคทำให้คุณแข็งแกร่งขึ้น", "pronunciation": "up-sak tham-hai-khun khaeng-graeng khuen"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "thai": "จงพบความปีติในทุกช่วงเวลา", "pronunciation": "jong-phob khwam-pee-tee nai thook-chuang-we-la"},
            {"english": "Joy is contagious, spread it.", "thai": "ความปีติเป็นสิ่งที่แพร่กระจายได้ จงแพร่มันออกไป", "pronunciation": "khwam-pee-tee pen-sing-thi-phrae-gra-jai-dai jong-phrae-man-ok-pai"},
            {"english": "Dance like nobody's watching.", "thai": "เต้นรำราวกับไม่มีใครมอง", "pronunciation": "ten-ram rao-gap mai-mi-krai-mong"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "thai": "จงหาความสมดุลในชีวิต", "pronunciation": "jong-ha khwam-som-dun nai chee-wit"},
            {"english": "Work hard, rest well.", "thai": "ทำงานหนัก พักผ่อนให้เพียงพอ", "pronunciation": "tham-ngan-nak phak-phon-hai phiang-pho"},
            {"english": "Too much of anything is not good.", "thai": "อะไรที่มากเกินไปก็ไม่ดี", "pronunciation": "a-rai-thi-mak-koen-pai gor-mai-di"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "thai": "การเติบโตเกิดขึ้นนอกเขตสบายของคุณ", "pronunciation": "kan-teurp-to koet-khuen nok khet-sa-bai khong-khun"},
            {"english": "Embrace change, grow stronger.", "thai": "โอบรับการเปลี่ยนแปลง เติบโตแข็งแกร่งขึ้น", "pronunciation": "op-rap kan-plian-plaeng teurp-to khaeng-graeng khuen"},
            {"english": "Every challenge is a chance to grow.", "thai": "ทุกอุปสรรคคือโอกาสที่จะเติบโต", "pronunciation": "thook-up-sak kheu o-gat-thi-ja-teurp-to"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "thai": "ค้นหาจุดมุ่งหมายของคุณ แล้วเดินตามมัน", "pronunciation": "khon-ha-joot-moong-mai khong-khun laew doen-tam-man"},
            {"english": "Your life has meaning.", "thai": "ชีวิตของคุณมีความหมาย", "pronunciation": "chee-wit khong-khun mi-khwam-mai"},
            {"english": "Live with intention, not accident.", "thai": "ใช้ชีวิตอย่างมีเป้าหมาย ไม่ใช่แค่เรื่องบังเอิญ", "pronunciation": "chai-chee-wit yang-mi-phao-mai mai-chai kae rueang-bang-oern"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "thai": "จงอยู่กับปัจจุบันขณะนี้", "pronunciation": "jong-yoo gap pat-joo-ban kha-na-nee"},
            {"english": "Breathe deeply, stay grounded.", "thai": "หายใจลึกๆ ตั้งมั่นอยู่กับพื้น", "pronunciation": "hai-jai-luek-luek tang-man-yoo gap pheun"},
            {"english": "Notice the little things around you.", "thai": "สังเกตสิ่งเล็กๆ รอบตัวคุณ", "pronunciation": "song-chet sing-lek-lek rop-tua-khun"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["thai"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansThai-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    thai = phrase_data.get("thai", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(thai, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Thai Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY THAI"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_thai: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansThai-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER THAI", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_thai, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ÖNEMLİ İFADE"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY THAI", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_thai: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Thai in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_thai})",
        f"60 Thai Phrases for {category_english} | Speak Thai Like a Native! ({category_thai})",
        f"Master Thai {category_english} | 60 Essential Thai Phrases with Pronunciation | Velocity Thai",
        f"Thai Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Thai Fluently | {category_english} Phrases | English + Thai + Pronunciation",
    ]

    description = f"""🇹🇭 Learn Thai with Velocity Thai! 🇹🇭

In this video, you'll learn 60 essential Thai phrases about {category_english} ({category_thai}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Thai
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Thai: {phrase['thai']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Thai beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Thai language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Thai learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY THAI:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Thai Motivation Phrases
• Thai Love Expressions
• Basic Thai Greetings

#LearnThai #ThaiPhrases #ThaiLanguage #{category_english.replace(' ', '')} #VelocityThai #ThaiForBeginners #SpeakThai #ThaiVocabulary #Pronunciation #LanguageLearning #Thai101 #ThaiLesson

---
© Velocity Thai - Making Thai learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Thai",
            "Thai Phrases",
            "Thai Language",
            category_english,
            "Velocity Thai",
            "Thai for Beginners",
            "Speak Thai",
            "Thai Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Thai 101",
            "Thai Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_thai": category_thai,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_THAI[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['thai']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_THAI[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Thai: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Thai", "Thai Phrases", "Thai", category_english, "Velocity Thai"],
        "category_english": category_english,
        "category_thai": CATEGORIES_THAI[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Thai")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Thai YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY THAI - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_THAI[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
