# bot_logic.py
from groq_api import extract_medical_info
from schemas import Symptom, UserCreate, DataInput
from fastapi.testclient import TestClient
from main import app  # tetap di sini karena tidak akan menimbulkan circular import
from main import User, UserSymptoms, Symptoms  # buat file models.py jika perlu

client = TestClient(app)


class HealthcareBot:
    def __init__(self):
        self.responses = {
            "halo": "Halo! Bagaimana saya bisa membantu kesehatan Anda hari ini?",
            "hai": "Hai! Ada keluhan kesehatan yang ingin Anda konsultasikan?",
            "siapa kamu": "Saya adalah chatbot layanan kesehatan yang siap membantu Anda dengan informasi kesehatan umum. Perlu diingat bahwa saya bukan pengganti konsultasi dengan dokter.",
            "sakit kepala": "Sakit kepala bisa disebabkan oleh berbagai faktor seperti stres, kurang tidur, atau dehidrasi. Jika sakit kepala Anda parah atau terus-menerus, sebaiknya konsultasikan dengan dokter.",
            "flu": "Gejala flu biasanya meliputi demam, sakit tenggorokan, batuk, dan nyeri otot. Istirahat yang cukup, minum banyak air, dan konsumsi obat pereda gejala dapat membantu. Jika gejala memburuk, segera hubungi dokter.",
            "demam": "Demam merupakan tanda tubuh sedang melawan infeksi. Istirahat yang cukup dan minum banyak cairan sangat penting. Jika demam tinggi (>39°C) atau berlangsung lebih dari 3 hari, segera konsultasikan dengan dokter.",
            "vitamin": "Vitamin penting untuk menjaga fungsi tubuh yang normal. Makanan seimbang biasanya dapat memenuhi kebutuhan vitamin harian. Konsultasikan dengan dokter sebelum mengonsumsi suplemen vitamin.",
            "olahraga": "Olahraga teratur sangat bermanfaat untuk kesehatan fisik dan mental. Minimal 30 menit aktivitas fisik sedang setiap hari dapat membantu menjaga kesehatan jantung dan meningkatkan imunitas.",
            "terima kasih": "Sama-sama! Senang bisa membantu. Jangan ragu untuk bertanya lagi jika ada pertanyaan kesehatan lainnya.",
            "bye": "Sampai jumpa! Tetap jaga kesehatan Anda!"
        }
        
        self.menu_responses = {
            "Konsultasi Umum": "Untuk konsultasi umum, silakan jelaskan keluhan atau pertanyaan kesehatan Anda. Saya akan memberikan informasi umum yang mungkin membantu.",
            "Info Obat": "Anda dapat menanyakan informasi umum tentang obat seperti kegunaan dan efek samping. Namun, selalu ikuti petunjuk dokter atau apoteker untuk penggunaan obat.",
            "Jadwal Dokter": "Untuk informasi jadwal dokter, silakan hubungi rumah sakit atau klinik terdekat. Anda juga dapat menyebutkan spesialisasi dokter yang Anda cari.",
            "Gejala Penyakit": "Silakan jelaskan gejala yang Anda alami, dan saya akan coba memberikan informasi umum. Ingat, ini bukan pengganti diagnosis dokter.",
            "Tips Kesehatan": "Beberapa tips kesehatan dasar: konsumsi makanan seimbang, olahraga teratur, tidur cukup (7-8 jam), minum banyak air, dan kelola stres. Ada area spesifik yang ingin Anda ketahui?",
            "FAQ": "Beberapa pertanyaan umum yang sering ditanyakan: cara mencegah flu, tips meningkatkan imunitas, atau informasi nutrisi. Apa yang ingin Anda ketahui?",
            "Kontak Darurat": "Untuk keadaan darurat, segera hubungi nomor darurat 119 atau IGD rumah sakit terdekat. Jangan tunda penanganan medis untuk kondisi serius!"
        }
    
    def get_response(self, message: str, db_session=None, user_email=None):
        lower_msg = message.lower().strip()
        if lower_msg in self.responses:
                return self.responses[lower_msg]
        extracted = extract_medical_info(message)


        if "error" in extracted:
            return "Maaf, saya tidak bisa mengekstrak informasi dari pesan Anda. Bisa Anda jelaskan lagi?"

        # Ambil data user
        user = db_session.query(User).filter(User.email == user_email).first()
        if not user:
            return "User belum terdaftar. Mohon buat akun terlebih dahulu."

        # Update usia & gender jika belum diisi
        updated = False
        if not user.age and extracted.get("age") is not None:
            user.age = extracted["age"]
            updated = True
        if not user.gender and extracted.get("gender") is not None:
            user.gender = extracted["gender"]
            updated = True
        if updated:
            db_session.commit()

        # Simpan gejala ke UserSymptoms
        for sym in extracted.get("symptoms", []):
            # Cek apakah sudah pernah disimpan
            existing = db_session.query(UserSymptoms).filter_by(
                user_id=user.user_id, symptom_name=sym["name"]
            ).first()
            if not existing:
                us = UserSymptoms(
                    user_id=user.user_id,
                    symptom_name=sym["name"],
                    symptom_value=str(sym["value"])
                )
                db_session.add(us)
        db_session.commit()

        # Cek apakah semua data yang dibutuhkan sudah tersedia
        required_symptoms = [
            'Heart_Rate_bpm', 'Body_Temperature_C', 'Oxygen_Saturation_%', 'Systolic',
            'Diastolic', 'Runny nose', 'Shortness of breath', 'Body ache',
            'Headache', 'Cough', 'Fever', 'Sore throat', 'Fatigue'
        ]
        available = db_session.query(UserSymptoms).filter_by(user_id=user.user_id).all()
        available_symptoms = {s.symptom_name: int(s.symptom_value) for s in available}

        # Prediksi hanya jika semua symptom tersedia + umur dan gender
        if all(sym in available_symptoms for sym in required_symptoms) and user.age is not None and user.gender is not None:
            symptoms_input = []
            for sym_name in required_symptoms:
                symptom = db_session.query(Symptoms).filter(Symptoms.symptom_name == sym_name).first()
                if symptom:
                    symptoms_input.append(Symptom(symptom_id=symptom.symptom_id, value_symptom=available_symptoms[sym_name]))

            input_data = DataInput(
                user={
                    "username": user.username,
                    "email": user.email,
                    "password": user.password,
                    "age": user.age,
                    "gender": user.gender
                },
                symptoms=symptoms_input
            )
            result = client.post("/predict/", json=input_data.dict())
            if result.status_code == 200:
                result_data = result.json()
                return f"Hasil prediksi: {result_data['prediction']} (confidence: {result_data['confidence_score']:.2f})"
            else:
                return "Gagal memproses prediksi."

        else:
            return "Terima kasih. Saya telah mencatat gejala Anda. Mohon lanjutkan jika ada gejala lain atau ingin melanjutkan."

