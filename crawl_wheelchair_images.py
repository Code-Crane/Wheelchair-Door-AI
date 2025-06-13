import os
import ssl
import requests
from PIL import Image
from io import BytesIO
from icrawler import ImageDownloader
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler

ssl._create_default_https_context = ssl._create_unverified_context

save_dir = './dataset/wheelchair_raw'
os.makedirs(save_dir, exist_ok=True)

current_index = len(os.listdir(save_dir))
target_per_keyword = 120

keywords = [
    # 한국어
    "휠체어", "전동 휠체어", "수동 휠체어", "병원 휠체어", "장애인 휠체어", "휠체어 사용자", "노약자 휠체어",
    # 영어
    "wheelchair", "electric wheelchair", "manual wheelchair", "hospital wheelchair",
    "disabled person wheelchair", "wheelchair user", "elderly wheelchair",
    # 일본어
    "車椅子", "電動車椅子", "手動車椅子", "病院用車椅子", "障がい者 車椅子", "車椅子 ユーザー", "高齢者 車椅子",
    # 중국어
    "轮椅", "电动轮椅", "手动轮椅", "医院轮椅", "残疾人轮椅", "坐轮椅的人", "老年人轮椅"
]

class IndexedDownloader(ImageDownloader):
    def download(self, task, default_ext, timeout=5, **kwargs):
        global current_index
        try:
            resp = requests.get(task['file_url'], stream=True, timeout=timeout, headers={
                "User-Agent": "Mozilla/5.0"
            })
            img = Image.open(BytesIO(resp.content))
            if img.width < 128 or img.height < 128:
                return
            ext = '.' + img.format.lower()
            filename = f"wheelchair_{str(current_index + 1).zfill(5)}{ext}"
            path = os.path.join(save_dir, filename)
            img.convert('RGB').save(path)
            current_index += 1
            print(f"[{current_index}] 저장됨 → {filename}")
        except Exception:
            return

def run_crawler(CrawlerClass, engine_name, num_per_engine):
    for keyword in keywords:
        print(f"\n🔍 [{engine_name}] '{keyword}' 수집 중...")
        crawler = CrawlerClass(
            downloader_cls=IndexedDownloader,
            storage={'root_dir': save_dir}
        )
        try:
            crawler.crawl(
                keyword=keyword,
                max_num=num_per_engine,
                overwrite=False,
                filters=None
            )
        except Exception as e:
            print(f"❌ {keyword} 실패: {e}")
        print(f"🔸 누적: {current_index}장\n")

run_crawler(GoogleImageCrawler, "Google", 60)
run_crawler(BingImageCrawler, "Bing", 60)

print(f"\n✅ 휠체어 이미지 수집 완료! 총 수집: {current_index}장")
