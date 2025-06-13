import os
from PIL import Image
import imagehash

# 디렉토리 설정
image_dir = './dataset/nonwheelchair_raw'
hashes = set()
removed = 0

# 중복 제거 실행
for filename in os.listdir(image_dir):
    filepath = os.path.join(image_dir, filename)
    try:
        with Image.open(filepath) as img:
            h = imagehash.average_hash(img)
            if h in hashes:
                os.remove(filepath)
                removed += 1
                print(f"❌ 중복 제거: {filename}")
            else:
                hashes.add(h)
    except Exception as e:
        print(f"⚠️ 오류: {filename} → {e}")

print(f"\n✅ 중복 제거 완료! 제거된 이미지 수: {removed}장")
