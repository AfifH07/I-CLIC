import os
from groq import Groq

# Inisialisasi klien Groq dengan API key dari variabel lingkungan
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def get_response_from_groq(prompt):
    try:
        # Membuat permintaan chat completion
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",  # Ganti dengan model yang sesuai jika diperlukan
        )
        
        # Mengembalikan konten dari respons
        return chat_completion.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Terjadi kesalahan dalam memproses permintaan: {str(e)}"