import threading
import time
import datetime
import re
import string
import requests
from bs4 import BeautifulSoup
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.utils import timezone
from .models import Article

keyword_map = {
    'Healthy': 1,
    'Bronchitis': 2,
    'Flu': 3,
    'Cold': 4,
    'Pneumonia': 5
}

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.lower()
    text = re.sub(r'[0-9]', '', text)
    text = re.sub(r'[{}]'.format(re.escape(string.punctuation)), '', text)
    return text

def get_similar_articles(query, base_url="https://www.halodoc.com", search_path="/artikel/search/"):
    search_url = f"{base_url}{search_path}{query.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    articles = soup.find_all("a", href=True)

    links = []
    for article in articles:
        if "/artikel/" in article["href"]:
            full_link = base_url + article["href"]
            links.append(full_link)

    documents = []
    titles = []
    for link in links:
        try:
            article_response = requests.get(link, headers=headers)
            article_soup = BeautifulSoup(article_response.content, "html.parser")
            paragraphs = article_soup.find_all("p")
            content = " ".join([p.text for p in paragraphs])
            documents.append(content)

            # Title
            titles.append(link.split("/")[-1].replace("-", " ").capitalize())
        except Exception as e:
            print(f"[ERROR] Gagal ambil artikel dari {link}: {e}")
            documents.append("")
            titles.append("Unknown")

    cleaned = [clean_text(doc) for doc in documents]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(cleaned)
    query_vec = vectorizer.transform([clean_text(query)])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = np.argsort(similarities)[-2:][::-1]
    top_articles = [(titles[idx], documents[idx]) for idx in top_indices]

    return top_articles

def scrape_and_store():
    print(f"[INFO] Scraping dimulai pada {timezone.now()}")
    for keyword, pid in keyword_map.items():
        print(f"[INFO] Scraping keyword: {keyword}")
        articles = get_similar_articles(keyword)
        for title, content in articles:
            if not content.strip():
                print(f"[SKIP] Kosong: {title}")
                continue
            Article.objects.create(
                title=title,
                content=content,
                prediction_id=pid
            )
            print(f"[INSERT] Artikel: '{title}' (Prediction ID: {pid})")

def scheduler():
    print("[INIT] Scheduler dimulai...")
    time.sleep(5)  # Tunggu agar Django siap sepenuhnya

    while True:
        try:
            now = timezone.localtime(timezone.now())
            current_hour = now.hour
            current_day = now.date()

            try:
                article_count = Article.objects.count()

                # Cari apakah ada artikel dengan jam dan tanggal yang sama
                hour_articles = Article.objects.filter(
                    date_scraping__hour=current_hour,
                    date_scraping__date=current_day
                ).count()
            except Exception as e:
                print(f"[ERROR] Gagal membaca tabel articles: {e}")
                article_count = -1
                hour_articles = -1

            should_scrape = False

            if article_count == 0:
                print("[TRIGGER] Database kosong.")
                should_scrape = True
            elif hour_articles == 0:
                print(f"[TRIGGER] Belum ada artikel pada jam {current_hour}:00 hari ini.")
                should_scrape = True
            else:
                print(f"[WAIT] Artikel sudah ada untuk jam {current_hour}:00. Jumlah total: {article_count}")

            if should_scrape:
                scrape_and_store()

        except Exception as e:
            print(f"[ERROR] Dalam loop utama scheduler: {e}")

        time.sleep(60)
