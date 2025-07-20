#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// MPU6050オブジェクトを作成
Adafruit_MPU6050 mpu;

void setup() {
  // シリアル通信を開始 (ボーレートはPython側と合わせる)
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // シリアルポートの接続を待つ
  }

  // MPU6050の初期化
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  // センサーのレンジ設定
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  delay(100);
}

void loop() {
  // センサーイベント（加速度、ジャイロ、温度）を取得するための変数
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // 3軸の加速度データをカンマ区切りでシリアルポートに出力
  // フォーマット: "x,y,z\n"
  Serial.printf("%.2f,%.2f,%.2f\n", a.acceleration.x, a.acceleration.y, a.acceleration.z);

  // 50ms待機 (送信レート: 約20Hz)
  delay(50);
}