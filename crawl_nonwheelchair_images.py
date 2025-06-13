import os
import ssl
import requests
from PIL import Image
from io import BytesIO
from icrawler import ImageDownloader
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler

ssl._create_default_https_context = ssl._create_unverified_context

save_dir = './dataset/nonwheelchair_raw'
os.makedirs(save_dir, exist_ok=True)

# 고정 인덱싱 시작
current_index = len(os.listdir(save_dir))
target_per_keyword = 120  # 60 Google + 60 Bing

# 24개 키워드
keywords = [
    # 세발자전거
    "세발자전거", "tricycle", "三輪車", "三轮车",
    # 킥보드
    "킥보드", "kickboard", "キックボード", "滑板车",
    # 인력거
    "인력거", "rickshaw", "人力車", "黄包车",
    # 지게차
    "지게차", "forklift", "フォークリフト", "叉车",
    # 자전거
    "자전거", "bicycle", "自転車", "自行车",
    # 추가 키워드
    "아기자동차", "붕붕카", "유아자동차", "미니카"
]

# 다운로더 정의
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
            filename = f"nonwheel_{str(current_index + 1).zfill(5)}{ext}"
            path = os.path.join(save_dir, filename)
            img.convert('RGB').save(path)
            current_index += 1
            print(f"[{current_index}] 저장됨 → {filename}")
        except Exception:
            return

# 크롤러 실행 함수
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

# 실행
run_crawler(GoogleImageCrawler, "Google", 60)
run_crawler(BingImageCrawler, "Bing", 60)

print(f"\n✅ 논휠체어 이미지 수집 완료! 총 수집: {current_index}장")
