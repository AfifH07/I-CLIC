import time

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
    
    def get_response(self, message):
        message = message.lower()
        
        # Check if message contains any keywords in responses
        for key in self.responses:
            if key in message:
                return self.responses[key]
        
        # Default response if no match found
        return "Maaf, saya tidak memiliki informasi spesifik tentang hal tersebut. Untuk kondisi medis yang memerlukan perhatian khusus, sebaiknya konsultasikan dengan dokter atau tenaga medis profesional."
    
    def show_menu(self):
        print("\n===== MENU LAYANAN ICLIK =====")
        print("1. Konsultasi Umum")
        print("2. Info Obat")
        print("3. Jadwal Dokter")
        print("4. Gejala Penyakit")
        print("5. Tips Kesehatan")
        print("6. FAQ")
        print("7. Kontak Darurat")
        print("0. Keluar")
        print("============================")
    
    def process_menu_choice(self, choice):
        menu_options = {
            "1": "Konsultasi Umum",
            "2": "Info Obat",
            "3": "Jadwal Dokter",
            "4": "Gejala Penyakit",
            "5": "Tips Kesehatan",
            "6": "FAQ",
            "7": "Kontak Darurat"
        }
        
        if choice in menu_options:
            option = menu_options[choice]
            print(f"\nAnda memilih: {option}")
            return self.menu_responses[option]
        elif choice == "0":
            return "exit"
        else:
            return "Pilihan tidak valid. Silakan pilih menu 1-7 atau 0 untuk keluar."

def main():
    bot = HealthcareBot()
    print("=" * 50)
    print("Selamat datang di Asisten ICLIK!")
    print("Saya adalah asisten kesehatan virtual yang siap membantu Anda.")
    print("Ketik 'menu' untuk melihat layanan yang tersedia atau 'exit' untuk keluar.")
    print("=" * 50)
    
    while True:
        if user_input := input("\nAnda: ").strip():
            if user_input.lower() == 'exit':
                print("\nBot: Terima kasih telah menggunakan layanan ICLIK. Sampai jumpa!")
                break
            elif user_input.lower() == 'menu':
                bot.show_menu()
                menu_choice = input("\nPilih menu (1-7) atau 0 untuk keluar: ")
                response = bot.process_menu_choice(menu_choice)
                if response == "exit":
                    print("\nBot: Terima kasih telah menggunakan layanan ICLIK. Sampai jumpa!")
                    break
                print(f"\nBot: {response}")
            else:
                # Simulate typing delay for more natural interaction
                print("Bot sedang mengetik", end="")
                for _ in range(3):
                    time.sleep(0.3)
                    print(".", end="", flush=True)
                print()
                
                response = bot.get_response(user_input)
                print(f"Bot: {response}")

if __name__ == "__main__":
    main()