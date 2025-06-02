# bot_logic.py
from groq_api import extract_medical_info
from schemas import Symptom, UserCreate, DataInput
from fastapi.testclient import TestClient
from main import app
from main import User, UserSymptoms, Symptoms
import logging
import pandas as pd
from typing import Dict, List, Optional

logging.basicConfig(level=logging.DEBUG)
client = TestClient(app)

class TemporaryDataStorage:
    """Class untuk menyimpan data sementara dalam DataFrame"""
    def __init__(self):
        self.data = pd.DataFrame(columns=[
            'user_email',
            'Age',
            'gender',
            'Heart_Rate_bpm', 
            'Body_Temperature_C',
            'Oxygen_Saturation_%',
            'Blood_Pressure',
            'Systolic_BP',
            'Diastolic_BP',
            'Shortness_of_breath', 
            'Body_ache',
            'Cough', 
            'Fever', 
            'Headache',
            'Fatigue'
            # 'Runny_nose',
            # 'Sore_throat'
        ]).set_index('user_email')

    
    def add_data(self, user_email: str, extracted: Dict):
        print(f"RAW EXTRACTED DATA: {extracted}")
        if not isinstance(extracted, dict) or all(isinstance(v, (int, float)) for v in extracted.values()):
            print("Skipping invalid extracted structure (possibly raw symptom dict)")
            return
        """Menambahkan/memperbarui data user secara partial"""
        if user_email not in self.data.index:
            # Inisialisasi baru dengan semua nilai None
            self.data.loc[user_email] = None

        # Simpan Age dan gender (pastikan sesuai model)
        if 'Age' in extracted:
            try:
                self.data.at[user_email, 'Age'] = int(extracted['Age'])
            except (ValueError, TypeError):
                pass

        if 'gender' in extracted:
            try:
                self.data.at[user_email, 'gender'] = int(extracted['gender'])
            except (ValueError, TypeError):
                pass

        # Update tekanan darah jika ada
        bp_value = extracted.get('Bp') or extracted.get('Blood_Pressure')
        if bp_value:
            try:
                bp_parts = str(bp_value).split('/')
                if len(bp_parts) == 2:
                    self.data.at[user_email, 'Blood_Pressure'] = bp_value
                    self.data.at[user_email, 'Systolic_BP'] = int(bp_parts[0])
                    self.data.at[user_email, 'Diastolic_BP'] = int(bp_parts[1])
            except (ValueError, AttributeError):
                pass

        # Update vital signs
        vital_mapping = {
            'Hr': 'Heart_Rate_bpm',
            'Bt': 'Body_Temperature_C',
            'Oxy': 'Oxygen_Saturation_%',
            'Systolic': 'Systolic_BP',
            'Diastolic': 'Diastolic_BP'
        }

        for src, dest in vital_mapping.items():
            if src in extracted:
                try:
                    value = extracted[src]
                    if isinstance(value, (int, float, str)) and str(value).replace('.', '', 1).isdigit():
                        self.data.at[user_email, dest] = float(value)
                except Exception:
                    pass



        # Update gejala
        symptom_mapping = {
            'Shortness of breath': 'Shortness_of_breath',
            'Body ache': 'Body_ache',
            'Cough': 'Cough',
            'Fever': 'Fever',
            'Fatigue': 'Fatigue',
            'Headache': 'Headache'
        }

        print(f"Data sebelum update:\n{self.data.loc[user_email]}")

        if 'symptoms' in extracted:
            mentioned_symptoms = {s['name'] for s in extracted['symptoms']}

            for symptom in extracted['symptoms']:
                symptom_name = symptom['name']
                if symptom_name in symptom_mapping:
                    col_name = symptom_mapping[symptom_name]
                    try:
                        self.data.at[user_email, col_name] = int(symptom['value'])
                    except (ValueError, TypeError):
                        pass

            for eng_name, col_name in symptom_mapping.items():
                if eng_name not in mentioned_symptoms and pd.isna(self.data.at[user_email, col_name]):
                    self.data.at[user_email, col_name] = None

        print(f"Data yang akan diupdate:\n{extracted}")
        print(f"Data setelah update:\n{self.data.loc[user_email]}\n")

    
    def is_complete(self, user_email: str) -> bool:
        """Cek apakah semua data sudah lengkap"""
        if user_email not in self.data.index:
            return False
        return not self.data.loc[user_email].isnull().any()
    
    def get_user_data(self, user_email: str) -> Optional[Dict]:
        """Mengambil data user dalam format dictionary"""
        if user_email in self.data.index:
            return self.data.loc[user_email].to_dict()
        return None

# Inisialisasi temporary storage
temp_storage = TemporaryDataStorage()

class HealthcareBot:
    def __init__(self):
        # Ubah nama variabel dari standard_responses menjadi responses
        self.responses = {
            "halo": "Halo! Saya adalah asisten kesehatan Anda. Silakan ceritakan gejala atau keluhan Anda.",
            "hai": "Hai! Ada yang bisa saya bantu terkait kesehatan Anda?",
            "siapa kamu": "Saya adalah chatbot layanan kesehatan yang siap membantu Anda dengan informasi kesehatan umum. Perlu diingat bahwa saya bukan pengganti konsultasi dengan dokter.",
            "terima kasih": "Sama-sama! Semoga Anda cepat sembuh.",
            "bye": "Terima kasih telah menggunakan layanan kami. Jaga kesehatan selalu!"
        }
        
        self.required_fields = [
            'Heart_Rate_bpm', 'Body_Temperature_C', 'Oxygen_Saturation_%', 'Blood_Pressure',
            'Shortness_of_breath', 'Body_ache', 'Cough', 'Fever', 'Fatigue', 'Headache'
        ]
    def is_standard_message(self, message: str) -> bool:
        return message.lower().strip() in self.responses
    
    def get_response(self, message: str, db_session=None, user_email=None) -> str:
        """Fungsi utama untuk menangani pesan dari user"""
        lower_msg = message.lower().strip()

        # 1. Cek pesan standar
        if self.is_standard_message(message):
            return self.responses[lower_msg]
        
        # 2. Ekstrak informasi medis
        try:
            # Perbaiki input pengguna jika perlu
            if "suhu tubu" in message:
                message = message.replace("suhu tubu", "suhu tubuh")

            extracted = extract_medical_info(message)
            logging.debug(f"Extracted data: {extracted}")
            
            if not extracted or ('symptoms' not in extracted and not any(k in extracted for k in ['Hr', 'Bt', 'Bp', 'Oxy'])):
                return "Saya tidak mengenali informasi kesehatan dalam pesan Anda. Mohon jelaskan gejala atau kondisi Anda lebih detail."
                
            if user_email:
                # Filter out null values before processing
                processed_data = {k: v for k, v in extracted.items() if v is not None}
                
                # Ambil data age dan gender dari database
                if db_session:
                    user = db_session.query(User).filter(User.email == user_email).first()
                    if user:
                        processed_data['Age'] = user.umur
                        processed_data['gender'] = user.gender
                
                # Tambahkan logging untuk memeriksa processed_data
                logging.debug(f"Processed data before prediction: {processed_data}")

                # Tambahkan logging untuk memeriksa gejala
                if 'symptoms' in processed_data:
                    logging.debug(f"Processed symptoms: {processed_data['symptoms']}")
                else:
                    logging.debug("No symptoms found in processed data.")

                # Tambahkan gejala ke temporary storage
                if 'symptoms' in processed_data:
                    for symptom in processed_data['symptoms']:
                        symptom_name = symptom['name']
                        symptom_value = symptom['value']
                        temp_storage.add_data(user_email, {symptom_name: symptom_value})

                # Tambahkan pemeriksaan untuk 'Age'
                if 'Age' not in processed_data or processed_data['Age'] is None:
                    logging.error("Field 'Age' tidak ditemukan dalam processed_data.")
                    return "Field 'Age' tidak ditemukan. Silakan lengkapi data Anda."
                
                # Logging untuk memeriksa nilai 'Age'
                logging.debug(f"Value of 'Age': {processed_data['Age']}")

                try:
                    temp_storage.add_data(user_email, processed_data)
                    current_data = temp_storage.get_user_data(user_email) or {}
                    
                    # Format response based on available data
                    response_msg = self._format_current_data(current_data)
                    
                    if temp_storage.is_complete(user_email):
                        prediction = self._make_prediction(user_email, db_session)
                        return f"{response_msg}\n\n{prediction}"
                    else:
                        missing_data = self._request_missing_data(user_email)
                        return f"{response_msg}\n\n{missing_data}"
                        
                except Exception as e:
                    logging.error(f"Data processing error: {str(e)}", exc_info=True)
                    return "Mohon maaf, sistem sedang mengalami gangguan. Silakan coba lagi nanti."
            
            return "Silakan login atau berikan email Anda untuk melanjutkan."
            
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return "Maaf, terjadi kesalahan saat memproses pesan Anda."



    def _format_current_data(self, user_data: Dict) -> str:
        """Format data yang sudah terkumpul"""
        lines = []
        
        # Vital signs
        vitals = {
            'Heart_Rate_bpm': 'Detak jantung',
            'Body_Temperature_C': 'Suhu tubuh',
            'Oxygen_Saturation_%': 'Kadar oksigen'
        }
        
        # Format tekanan darah dengan pengecekan tipe data
        if 'Blood_Pressure' in user_data and pd.notna(user_data['Blood_Pressure']):
            bp = user_data['Blood_Pressure']
            if isinstance(bp, str):  # Jika format string "120/80"
                try:
                    systolic, diastolic = bp.split('/')
                    lines.append(f"- Tekanan darah: {bp} (Sistolik: {systolic}, Diastolik: {diastolic})")
                except:
                    lines.append(f"- Tekanan darah: {bp}")
            else:  # Jika format numerik
                lines.append(f"- Tekanan darah: {bp}")

        for field, label in vitals.items():
            if field in user_data and not pd.isna(user_data[field]):
                lines.append(f"- {label}: {user_data[field]}")
        
        # Gejala
        symptoms = {
            'Shortness_of_breath': 'Sesak napas',
            'Body_ache': 'Nyeri badan',
            'Cough': 'Batuk',
            'Fever': 'Demam',
            'Fatigue': 'Lelah',
            'Headache': 'Sakit kepala'
        }
        
        symptom_lines = []
        for field, label in symptoms.items():
            if field in user_data and not pd.isna(user_data[field]):
                status = "Iya" if user_data[field] == 1 else "Tidak"
                symptom_lines.append(f"- {label}: {status}")
        
        if symptom_lines:
            lines.append("\nGejala yang sudah dilaporkan:")
            lines.extend(symptom_lines)
        
        return "\n".join(lines) if lines else "Belum ada data kesehatan yang dilaporkan."

    def _request_missing_data(self, user_email: str) -> str:
        user_data = temp_storage.get_user_data(user_email)
        if user_data is None:
            return "Silakan mulai dengan memberikan informasi kesehatan Anda."

        # Kelompokkan field vital dan gejala
        vital_fields = [
            'Heart_Rate_bpm', 'Body_Temperature_C', 'Oxygen_Saturation_%', 'Blood_Pressure'
        ]
        symptom_fields = [
            'Shortness_of_breath', 'Body_ache', 'Cough', 'Fever', 'Fatigue', 'Headache'
        ]

        field_questions = {
            'Heart_Rate_bpm': "Berapa detak jantung Anda (dalam bpm)?",
            'Body_Temperature_C': "Berapa suhu tubuh Anda (dalam Celsius)?",
            'Oxygen_Saturation_%': "Berapa kadar oksigen Anda (dalam persen)?",
            'Blood_Pressure': "Berapa tekanan darah Anda? (format: Sistolik/Diastolik, contoh: 120/80)",
            'Shortness_of_breath': "Apakah Anda mengalami sesak napas? (1 untuk Ya, 0 untuk Tidak)",
            'Body_ache': "Apakah Anda mengalami nyeri badan? (1 untuk Ya, 0 untuk Tidak)",
            'Cough': "Apakah Anda batuk? (1 untuk Ya, 0 untuk Tidak)",
            'Fever': "Apakah Anda demam? (1 untuk Ya, 0 untuk Tidak)",
            'Fatigue': "Apakah Anda merasa lelah? (1 untuk Ya, 0 untuk Tidak)",
            'Headache': "Apakah Anda mengalami pusing atau sakit kepala? (1 untuk Ya, 0 untuk Tidak)"
        }

        # Cek field yang masih kosong, urutkan vital dulu
        missing_fields = []
        for field in vital_fields + symptom_fields:
            if pd.isna(user_data.get(field)):
                missing_fields.append(field)

        if not missing_fields:
            return "Terima kasih telah melengkapi semua data. Sistem sedang menganalisis..."

        response_lines = [
            "Mohon lengkapi data berikut:",
            *(f"{i+1}. {field_questions[field]}" for i, field in enumerate(missing_fields)),
            "\nAnda bisa menjawab dengan format:",
            "[nama_gejala] [nilai]",
            "Contoh: Suhu 37.5 atau Tekanan darah 120/80 atau Sesak_napas 1"
        ]
        return "\n".join(response_lines)

    def _make_prediction(self, user_email: str, db_session) -> str:
        """Membuat prediksi ketika semua data sudah lengkap"""
        try:
            # 1. Ambil data dari temporary storage
            user_data = temp_storage.get_user_data(user_email)
            if user_data is None:
                logging.error("Data tidak ditemukan di temporary storage.")
                return "Data tidak ditemukan. Silakan mulai dari awal."
            print(user_data)
            
            # 2. Persiapkan gejala untuk prediksi
            symptoms = self._prepare_symptoms(user_data, db_session)
            
            # 3. Buat input untuk prediksi
            input_data = self._create_prediction_input(user_email, user_data, symptoms, db_session)
            print(input_data)
            
            # ** Tambahkan logging untuk memeriksa input_data sebelum prediksi **
            logging.debug(f"Input data untuk prediksi: {input_data.dict()}")
            
            # 4. Panggil endpoint prediksi
            response = client.post("/predict/", json=input_data.dict())
            
            if response.status_code == 200:
                result = response.json()
                # 5. Bersihkan data sementara setelah prediksi
                temp_storage.data.drop(user_email, inplace=True, errors='ignore')
                
                return (
                    f"Hasil diagnosa: {result['prediction']}\n"
                    f"Tingkat kepercayaan: {result['confidence_score']*100:.1f}%\n"
                    "Disarankan untuk berkonsultasi dengan dokter untuk hasil lebih akurat."
                )
            else:
                logging.error(f"Kesalahan saat memanggil endpoint prediksi: {response.status_code} - {response.text}")
                return "Maaf, terjadi kesalahan saat memproses prediksi."
                
        except Exception as e:
            logging.error(f"Prediction error: {str(e)}")
            return "Maaf, terjadi kesalahan sistem. Silakan coba lagi nanti."


    def _prepare_symptoms(self, user_data: Dict, db_session) -> List[Symptom]:
        """Mempersiapkan data gejala untuk prediksi"""
        symptoms = []
        symptom_mapping = {
            'Shortness_of_breath': 'Shortness of breath',
            'Body_ache': 'Body ache',
            'Cough': 'Cough',
            'Fever': 'Fever',
            'Fatigue': 'Fatigue',
            'Headache': 'Headache'
            # 'Runny_nose': 'Runny nose',
            # 'Sore_throat': 'Sore throat'
        }


        # Tambahkan logging untuk memeriksa user_data
        logging.debug(f"User  data for symptoms: {user_data}")

        for field, symptom_name in symptom_mapping.items():
            value = int(user_data.get(field, 0) or 0)
            symptom = db_session.query(Symptoms).filter(
                Symptoms.symptom_name == symptom_name
            ).first()
            if symptom:
                symptoms.append(Symptom(
                    symptom_id=symptom.symptom_id,
                    value_symptom=value
                ))

        # Tambahkan logging untuk memeriksa symptoms yang telah dipersiapkan
        logging.debug(f"Prepared symptoms: {symptoms}")

        return symptoms



    def _create_prediction_input(self, user_email: str, user_data: Dict, 
                                symptoms: List[Symptom], db_session) -> DataInput:
        """Membuat objek DataInput untuk prediksi"""
        user = db_session.query(User).filter(User.email == user_email).first()
        
        # if not user:
        #     # Fallback jika user tidak ditemukan
        #     user_info = {
        #         "username": "user_" + user_email.split('@')[0],
        #         "email": user_email,
        #         "password": "default_password",
        #         "Age": int(user_data['Age']) if 'Age' in user_data else 0,  # Pastikan Age ada
        #         "gender": int(user_data['gender']) if 'gender' in user_data else 0
        #     }
        
        user_info = {
                "username": user.username,
                "email": user.email,
                "password": user.password,
                "age": user.umur,
                "gender": user.gender
            }
        
        # Tambahkan vital signs
        user_info.update({
            "Heart_Rate_bpm": float(user_data['Heart_Rate_bpm']),
            "Body_Temperature_C": float(user_data['Body_Temperature_C']),
            "Oxygen_Saturation_%": float(user_data['Oxygen_Saturation_%']),
            "age": int(user_data['Age']) if 'Age' in user_data else 0  # Pastikan Age ada
        })

        return DataInput(
            user=user_info,
            symptoms=symptoms
        )


    # Fungsi-fungsi tambahan yang sudah ada (extract_vital_info, dll) tetap dipertahankan
    def extract_vital_info(self, user_input):
        extracted = extract_medical_info(user_input)
        
        if "error" in extracted or (not extracted.get("Hr") and not extracted.get("Bt") and 
                                not extracted.get("Bp") and not extracted.get("Oxy") and
                                not extracted.get("symptoms")):
            return {"error": "Tidak bisa mengekstrak informasi"}
            
        symptom_mapping = {
            'Shortness of breath': 'Shortness_of_breath',
            'Body ache': 'Body_ache',
            'Cough': 'Cough',
            'Fever': 'Fever',
            'Fatigue': 'Fatigue',
            'Headache': 'Headache'
            # 'Runny nose': 'Runny_nose',
            # 'Sore throat': 'Sore_throat'
        }

        
        if "symptoms" in extracted:
            for symptom in extracted["symptoms"]:
                if symptom["name"] in symptom_mapping:
                    symptom["name"] = symptom_mapping[symptom["name"]]
        
        if "Bp" in extracted and extracted["Bp"]:
            try:
                systolic, diastolic = extracted["Bp"].split("/")
                extracted["Systolic"] = int(systolic)
                extracted["Diastolic"] = int(diastolic)
            except:
                pass
        
        name_mapping = {
            "Hr": "Heart_Rate_bpm",
            "Bt": "Body_Temperature_C",
            "Oxy": "Oxygen_Saturation_%"
        }
        
        for old_name, new_name in name_mapping.items():
            if old_name in extracted:
                extracted[new_name] = extracted[old_name]
        
        return extracted

