# groq_api.py (versi yang diperbaiki)
import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY tidak ditemukan. Pastikan sudah diset di file .env.")

client = Groq(api_key=GROQ_API_KEY)

def extract_medical_info(user_text: str) -> dict:
    """Ekstrak informasi medis dari input pengguna"""
    # Pastikan input pengguna bersih
    user_text = user_text.replace(";", ",")
    print(f"Input to Groq API: {user_text}")
    # Coba ekstrak dengan regex terlebih dahulu (fallback jika API gagal)
    extracted_by_regex = extract_with_regex(user_text)
    
    # Persiapkan prompt yang sangat eksplisit untuk LLM
    prompt = f"""
    TUGAS: Ekstrak informasi medis dari input pengguna dan kembalikan hanya dalam format JSON.

    Data yang harus diekstrak:
    1. Heart Rate (Hr) - angka dalam satuan bpm (detak per menit)
    2. Body Temperature (Bt) - angka dalam derajat Celsius
    3. Blood Pressure (Bp) - dalam format "sistol/diastol", contoh: "120/80"
    4. Oxygen Level (Oxy) - persentase oksigen, angka antara 0-100
    5. Usia (age) - umur dalam tahun, jika disebutkan
    6. Gender (gender) - 1 jika laki-laki, 0 jika perempuan, jika disebutkan
    7. Gejala yang disebutkan (cek apakah disebut positif atau negatif):
    - Jika pengguna menyebut gejala secara positif, beri value: 1
    - Jika pengguna menyebut gejala dengan kata negatif seperti "tidak", "tanpa", "bukan", beri value: 0
    - Jika tidak disebut sama sekali, jangan sertakan dalam daftar

    Gejala:
    - Demam/Fever
    - Batuk/Cough
    - Sakit kepala/Headache 
    - Pilek/Runny nose
    - Sesak napas/Shortness of breath
    - Nyeri badan/Body ache
    - Sakit tenggorokan/Sore throat
    - Kelelahan/Fatigue


    Input pengguna:
    "{user_text}"

    PENTING: Berikan HANYA objek JSON. Jangan berikan penjelasan, kalimat pengantar, atau teks apa pun selain objek JSON. Format yang benar:
    
    {{
      "Hr": [angka],
      "Bt": [angka],
      "Bp": "[sistol/diastol]",
      "Oxy": [angka],
      "age": [angka atau null jika tidak ada],
      "gender": [1 atau 0 atau null jika tidak ada],
      "symptoms": [
        {{"name": "Fever", "value": 1}},
        {{"name": "Cough", "value": 1}},
        dst...
      ]
    }}
    
    Jika item tidak disebutkan, jangan sertakan dalam JSON atau gunakan null. Berikan HANYA objek JSON.
    """

    try:
        # Coba dengan Groq API
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192", #llama-3.3-70b-versatile
            stream=False,
            temperature=0.1,  # Lebih rendah untuk mendapatkan hasil yang lebih konsisten
            max_tokens=500
        )
        print(f"Raw Groq API response: {response}")
        content = response.choices[0].message.content.strip()
        print(f"Groq API content: {content}")
        # Coba parsing respons JSON
        try:
            # Cari objek JSON dengan regex
            json_match = re.search(r'{[\s\S]*}', content)
            if json_match:
                json_str = json_match.group(0)
                extracted = json.loads(json_str)
                
                # Pastikan symptoms selalu ada
                if "symptoms" not in extracted:
                    extracted["symptoms"] = []
                
                # Gabungkan dengan hasil regex jika ada yang hilang
                for key in ["Hr", "Bt", "Bp", "Oxy"]:
                    if key not in extracted and key in extracted_by_regex:
                        extracted[key] = extracted_by_regex[key]
                
                # Gabungkan gejala jika ada
                extracted_symptoms = {s["name"]: s["value"] for s in extracted.get("symptoms", [])}
                for s in extracted_by_regex.get("symptoms", []):
                    if s["name"] not in extracted_symptoms:
                        extracted["symptoms"].append(s)
                print(f"Extracted: {extracted}")  # Sebelum return
                return extracted
            else:
                # Jika tidak menemukan JSON, gunakan hasil regex
                return extracted_by_regex
                
        except json.JSONDecodeError:
            print(f"Gagal parsing JSON dari respons: {content}")
            # Gunakan hasil ekstraksi regex sebagai fallback
            return extracted_by_regex
            
    except Exception as e:
        print(f"Error Groq API: {str(e)}")
        # Gunakan hasil ekstraksi regex sebagai fallback
        return extracted_by_regex

negations = ["tidak", "bukan", "tanpa", "ga", "gak", "enggak", "tak"]

def is_negated(term, text):
    for neg in negations:
        if re.search(rf'{neg}\s+{re.escape(term)}', text):
            return True
    return False


def extract_with_regex(user_text: str) -> dict:
    """Ekstrak informasi medis menggunakan regex - sebagai fallback"""
    user_text = user_text.lower()
    
    # Inisialisasi hasil
    result = {
        "symptoms": []
    }
    
    # Ekstrak vital signs dengan pattern yang lebih komprehensif
    hr_patterns = [
        r'(detak jantung|heart rate|hr|pulse)[:\s]*(\d+)',
        r'jantung[^0-9]*(\d+)[^0-9]*bpm'
    ]
    bt_patterns = [
        r'(suhu|temperature|bt)[:\s]*(\d+\.?\d*)',
        r'demam[^0-9]*(\d+\.?\d*)'
    ]
    bp_patterns = [
        r'(tekanan darah|blood pressure|bp)[:\s]*(\d+)[/\\](\d+)',
        r'(sistol|systolic)[:\s]*(\d+)[^0-9]*(diastol|diastolic)[:\s]*(\d+)'
    ]
    oxy_patterns = [
        r'(oksigen|oxygen|oxy|o2|saturasi)[:\s]*(\d+)',
        r'(spo2|sp-o2|sp o2)[:\s]*(\d+)'
    ]
    
    # Cek semua pattern dan ambil yang pertama ditemukan
    for pattern in hr_patterns:
        hr_match = re.search(pattern, user_text)
        if hr_match:
            result["Hr"] = int(hr_match.group(2) if len(hr_match.groups()) == 2 else hr_match.group(1))
            break
    
    for pattern in bt_patterns:
        bt_match = re.search(pattern, user_text)
        if bt_match:
            result["Bt"] = float(bt_match.group(2) if len(bt_match.groups()) == 2 else bt_match.group(1))
            break
    
    for pattern in bp_patterns:
        bp_match = re.search(pattern, user_text)
        if bp_match:
            if len(bp_match.groups()) == 3:
                result["Bp"] = f"{bp_match.group(2)}/{bp_match.group(3)}"
            else:
                result["Bp"] = f"{bp_match.group(2)}/{bp_match.group(4)}"
            break
    
    for pattern in oxy_patterns:
        oxy_match = re.search(pattern, user_text)
        if oxy_match:
            result["Oxy"] = int(oxy_match.group(2) if len(oxy_match.groups()) == 2 else oxy_match.group(1))
            break
    
    # Ekstrak gejala umum dengan lebih banyak sinonim
    symptoms_mapping = {
        "demam": "Fever",
        "fever": "Fever",
        "panas": "Fever",
        
        "batuk": "Cough", 
        "cough": "Cough",
        "batuk-batuk": "Cough",
        
        "sakit kepala": "Headache",
        "headache": "Headache",
        "pusing": "Headache",
        "nyeri kepala": "Headache",
        
        "pilek": "Runny nose",
        "runny nose": "Runny nose",
        "hidung meler": "Runny nose",
        "hidung tersumbat": "Runny nose",
        
        "sesak": "Shortness of breath",
        "sesak nafas": "Shortness of breath",
        "shortness of breath": "Shortness of breath",
        "nafas pendek": "Shortness of breath",
        "sulit bernafas": "Shortness of breath",
        
        "nyeri badan": "Body ache",
        "body ache": "Body ache",
        "sakit badan": "Body ache",
        "badan pegal": "Body ache",
        "badan sakit": "Body ache",
        
        "sakit tenggorokan": "Sore throat",
        "sore throat": "Sore throat",
        "radang tenggorokan": "Sore throat",
        "tenggorokan sakit": "Sore throat",
        
        "lelah": "Fatigue",
        "fatigue": "Fatigue",
        "lemas": "Fatigue",
        "lesu": "Fatigue",
        "tidak bertenaga": "Fatigue"
    }
    
    for indo_term, eng_term in symptoms_mapping.items():
        indo_term = indo_term.lower().strip()
        if indo_term in user_text:
            if not any(s["name"] == eng_term for s in result["symptoms"]):
                # Jika ada negasi, set value = 0
                value = 0 if is_negated(indo_term, user_text) else 1
                result["symptoms"].append({"name": eng_term, "value": value})

    
    # Ekstrak usia dan gender jika ada
    age_match = re.search(r'(usia|umur|age)[:\s]*(\d+)', user_text)
    if age_match:
        result["age"] = int(age_match.group(2))
    
    # Pengecekan gender
    if re.search(r'\b(pria|laki|laki-laki|cowok|male|man)\b', user_text):
        result["gender"] = 1
    elif re.search(r'\b(wanita|perempuan|cewek|female|woman)\b', user_text):
        result["gender"] = 0
    
    return result