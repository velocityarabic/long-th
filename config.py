"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY THAI"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "THAI"
HANDLE = "@velocitythai"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'th',
 'name': 'Thai',
 'native_name': 'ไทย',
 'history_key': 'thai',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'th-TH-NiwatNeural',
 'native_fallback_voice': 'th-TH-PremwadeeNeural',
 'native_engine': 'edge',
 'native_lang_code': 'th',
 'english_rate': '-4%',
 'native_rate': '+0%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'ไทย',
 'translit_label': 'SAY IT LIKE',
 'flag': 'th',
 'greeting': 'สวัสดี!',
 'encouragement': 'เยี่ยม!',
 'rtl': False,
 'char_tiles': False,
 'script_font': 'Script.ttf',
 'glyphs': 'กขคงจฉชซญฐณดตถทธนบปผพฟภมยรลวศษสหอฮ'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'แรงบันดาลใจ',
 'Love': 'ความรัก',
 'Success': 'ความสำเร็จ',
 'Wisdom': 'ปัญญา',
 'Happiness': 'ความสุข',
 'Self Improvement': 'การพัฒนาตนเอง',
 'Gratitude': 'ความกตัญญู',
 'Friendship': 'มิตรภาพ',
 'Hope': 'ความหวัง',
 'Creativity': 'ความคิดสร้างสรรค์',
 'Inner Peace': 'สันติภายใน',
 'Confidence': 'ความมั่นใจ',
 'Perseverance': 'ความมานะบากบั่น',
 'Inspiration': 'แรงบันดาลใจ',
 'Positive Life': 'ชีวิตเชิงบวก',
 'Courage': 'ความกล้าหาญ',
 'Kindness': 'ความเมตตา',
 'Patience': 'ความอดทน',
 'Forgiveness': 'การให้อภัย',
 'Strength': 'พลัง',
 'Joy': 'ความปีติ',
 'Balance': 'ความสมดุล',
 'Growth': 'การเติบโต',
 'Purpose': 'จุดมุ่งหมาย',
 'Mindfulness': 'สติ',
 'Travel & Airport': 'การเดินทางและสนามบิน',
 'Ordering Food & Dining': 'การสั่งอาหารและการรับประทานอาหาร',
 'Shopping & Prices': 'การซื้อของและราคา',
 'Asking for Directions': 'การถามทาง',
 'Hotel & Accommodation': 'โรงแรมและที่พัก',
 'Daily Routine': 'กิจวัตรประจำวัน',
 'Meeting People & Greetings': 'การพบปะผู้คนและการทักทาย',
 'Emergency & Health': 'เหตุฉุกเฉินและสุขภาพ',
 'Public Transportation': 'การขนส่งสาธารณะ',
 'Work & Office': 'การทำงานและสำนักงาน',
 'Weather & Small Talk': 'สภาพอากาศและการพูดคุยทั่วไป',
 'Coffee Shop & Bakery': 'ร้านกาแฟและเบเกอรี่',
 'Family & Home': 'ครอบครัวและบ้าน',
 'Hobbies & Free Time': 'งานอดิเรกและเวลาว่าง',
 'Dating & Romance': 'การออกเดทและความรัก',
 'Phone Calls & Messages': 'การโทรศัพท์และข้อความ',
 'Banking & Money': 'การธนาคารและเงิน',
 'Doctor & Pharmacy': 'หมอและร้านขายยา',
 'Sports & Fitness': 'กีฬาและฟิตเนส',
 'Celebrations & Parties': 'การเฉลิมฉลองและงานปาร์ตี้',
 'Feelings & Emotions': 'ความรู้สึกและอารมณ์',
 'Agreeing & Disagreeing': 'การเห็นด้วยและไม่เห็นด้วย',
 'Making Plans': 'การวางแผน',
 'Common Native Slang': 'คำสแลงทั่วไป',
 'Cultural Traditions': 'ประเพณีวัฒนธรรม'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnthai',
 '#thailessons',
 '#thaiforbeginners',
 '#languagelearning',
 '#thaivocabulary',
 '#velocitythai',
 '#dailythai',
 '#thai',
 '#learnlanguages',
 '#speakthai']
# ==== HASHTAGS END ====
