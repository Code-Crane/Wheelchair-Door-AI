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

# 데이터셋 디렉토리 설정
wheelchair_dir = './dataset/wheelchair_resized'
nonwheelchair_dir = './dataset/nonwheelchair_resized'
train_dir = './dataset/train'
val_dir = './dataset/val'

# 데이터 정리 및 분할
def reorganize_data():
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

# 모델 훈련
def train_model(exp_name, train_datagen, dropout_rate1, dropout_rate2, learning_rate):
    val_datagen = ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(train_dir, target_size=(224, 224), batch_size=32, class_mode='binary')
    val_generator = val_datagen.flow_from_directory(val_dir, target_size=(224, 224), batch_size=32, class_mode='binary')

    y_train = train_generator.classes
    weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
    class_weights = dict(enumerate(weights))

    base_model = EfficientNetB3(include_top=False, weights='imagenet', input_shape=(224, 224, 3))
    x = GlobalAveragePooling2D()(base_model.output)
    x = Dropout(dropout_rate1)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(dropout_rate2)(x)
    output = Dense(1, activation='sigmoid')(x)
    model = Model(inputs=base_model.input, outputs=output)

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                  loss='binary_crossentropy', metrics=['accuracy'])

    callbacks = [
        EarlyStopping(monitor='val_accuracy', patience=4, restore_best_weights=True),
        ModelCheckpoint(f'best_model_{exp_name}.h5', monitor='val_accuracy', save_best_only=True)
    ]

    print(f"\n[EXPERIMENT: {exp_name}] Training started...")
    model.fit(train_generator, validation_data=val_generator, epochs=20, callbacks=callbacks, class_weight=class_weights)
    print(f"[EXPERIMENT: {exp_name}] Training completed. Model saved as best_model_{exp_name}.h5")

# 데이터 정리 및 분할 실행
reorganize_data()

# 실험 1: 데이터 증강 강하게 적용
train_datagen_exp1 = ImageDataGenerator(
    rescale=1./255,
    rotation_range=40,
    zoom_range=0.3,
    width_shift_range=0.2,
    height_shift_range=0.2,
    brightness_range=[0.5, 1.5],
    shear_range=20,
    horizontal_flip=True
)
train_model("exp1", train_datagen_exp1, 0.4, 0.3, 1e-4)

# 실험 2: Dropout 비율 증가
train_datagen_exp2 = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    zoom_range=0.2,
    width_shift_range=0.1,
    height_shift_range=0.1,
    brightness_range=[0.7, 1.3],
    shear_range=10,
    horizontal_flip=True
)
train_model("exp2", train_datagen_exp2, 0.6, 0.5, 1e-4)

# 실험 3: 학습률 감소
train_datagen_exp3 = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    zoom_range=0.2,
    width_shift_range=0.1,
    height_shift_range=0.1,
    brightness_range=[0.7, 1.3],
    shear_range=10,
    horizontal_flip=True
)
train_model("exp3", train_datagen_exp3, 0.4, 0.3, 1e-5)