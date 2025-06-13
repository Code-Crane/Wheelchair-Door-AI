import os
import shutil
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import EfficientNetB3
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.utils import class_weight

wheelchair_dir = './dataset/wheelchair_resized'
nonwheelchair_dir = './dataset/nonwheelchair_resized'
train_dir = './dataset/train'
val_dir = './dataset/val'


def reorganize_data():
    # 원본 이미지를 훈련/검증 폴더로 분할
    if os.path.exists(train_dir):
        shutil.rmtree(train_dir)
    if os.path.exists(val_dir):
        shutil.rmtree(val_dir)
    for label, src in [('wheelchair', wheelchair_dir), ('nonwheelchair', nonwheelchair_dir)]:
        files = os.listdir(src)
        random.shuffle(files)
        split = int(0.8 * len(files))
        for mode, file_list in [('train', files[:split]), ('val', files[split:])]:
            target_dir = os.path.join('./dataset', mode, label)
            os.makedirs(target_dir, exist_ok=True)
            for f in file_list:
                shutil.copy(os.path.join(src, f), os.path.join(target_dir, f))


reorganize_data()

# 데이터 증강 (최종 실험: 증강 파라미터 다름)
train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    rotation_range=20,
    zoom_range=0.2,
    width_shift_range=0.1,
    height_shift_range=0.1,
    brightness_range=[0.7, 1.3],
    shear_range=10,
    horizontal_flip=True
)
val_datagen = ImageDataGenerator(rescale=1. / 255)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode='binary'
)
val_generator = val_datagen.flow_from_directory(
    val_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode='binary'
)

# 클래스 불균형 보정용 가중치 계산
y_train = train_generator.classes
weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weights = dict(enumerate(weights))

# EfficientNetB3 기반 이진 분류 모델 구성
base_model = EfficientNetB3(include_top=False, weights='imagenet', input_shape=(224, 224, 3))
x = GlobalAveragePooling2D()(base_model.output)
x = Dropout(0.4)(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.3)(x)
output = Dense(1, activation='sigmoid')(x)

model = Model(inputs=base_model.input, outputs=output)
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
              loss='binary_crossentropy',
              metrics=['accuracy'])

# 조기 종료 및 최적 모델 저장 콜백 (최종 실험: patience, monitor 다름)
callbacks = [
    EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    ModelCheckpoint('best_model_effnetb3.h5', monitor='val_accuracy', save_best_only=True)
]

# 모델 학습 (핵심: 최종 실험, 증강/콜백/optimizer 다름)
model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=20,
    callbacks=callbacks,
    class_weight=class_weights
)

print("학습 완료: best_model_effnetb3.h5 저장됨")