import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import serial
import time

# --- 設定 ---
# ESP32が接続されているシリアルポート名を指定
SERIAL_PORT = 'COM3'  # ★★★★★自分の環境に合わせて変更★★★★★
BAUD_RATE = 115200    # ESP32のプログラムと合わせる
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# --- 設定ここまで ---


def draw_cube():
    """立方体を描画する関数"""
    vertices = (
        (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
        (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
    )
    edges = (
        (0, 1), (0, 3), (0, 4), (2, 1), (2, 3), (2, 7),
        (6, 3), (6, 4), (6, 7), (5, 1), (5, 4), (5, 7)
    )
    surfaces = (
        (0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4),
        (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6)
    )
    colors = (
        (1, 0, 0), (0, 1, 0), (0, 0, 1),
        (1, 1, 0), (0, 1, 1), (1, 0, 1)
    )

    glBegin(GL_QUADS)
    for i, surface in enumerate(surfaces):
        glColor3fv(colors[i])
        for vertex_index in surface:
            glVertex3fv(vertices[vertex_index])
    glEnd()

    # 立方体のエッジを黒で描画
    glColor3fv((0, 0, 0))
    glLineWidth(1)
    glBegin(GL_LINES)
    for edge in edges:
        for vertex_index in edge:
            glVertex3fv(vertices[vertex_index])
    glEnd()

def draw_text(x, y, text, font):
    """OpenGLの画面の指定した位置にテキストを描画する"""
    text_surface = font.render(text, True, (0, 0, 0, 255))  # 黒文字、背景透明
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    width, height = text_surface.get_width(), text_surface.get_height()

    # 2D描画モードに切り替え
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # テクスチャマッピングを有効化
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # テクスチャの生成と設定
    texid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Pygame座標系（左上原点）に合わせるためY座標を調整
    actual_y = WINDOW_HEIGHT - y - height
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x, actual_y)
    glTexCoord2f(1, 0); glVertex2f(x + width, actual_y)
    glTexCoord2f(1, 1); glVertex2f(x + width, actual_y + height)
    glTexCoord2f(0, 1); glVertex2f(x, actual_y + height)
    glEnd()

    # 設定を元に戻す
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)
    glDeleteTextures([texid])

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def main():
    # PygameとOpenGLの初期化
    pygame.init()
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("ESP32 MPU6050 Cube Demo")
    
    # フォントの準備
    font = pygame.font.Font(None, 36)

    # OpenGLの射影設定
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)
    glEnable(GL_DEPTH_TEST)

    # 背景色を薄い灰色に設定
    glClearColor(0.8, 0.8, 0.8, 1.0)

    # シリアルポートの初期化
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"Connected to {SERIAL_PORT}")
    except serial.SerialException as e:
        print(f"Error: Could not open port {SERIAL_PORT}. {e}")
        return

    # メインループ
    accel_x_list = []
    accel_y_list = []
    N = 8  # 平均化するデータ数を8に変更
    avg_x, avg_y = 0.0, 0.0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ser.close()
                pygame.quit()
                quit()

        # シリアルデータの読み取りと平均値の計算
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                data = line.split(',')
                if len(data) == 3:
                    accel_x = float(data[0])
                    accel_y = float(data[1])
                    accel_x_list.append(accel_x)
                    accel_y_list.append(accel_y)
                    if len(accel_x_list) > N:
                        accel_x_list.pop(0)
                    if len(accel_y_list) > N:
                        accel_y_list.pop(0)
                    
                    if len(accel_x_list) == N:
                        avg_x = sum(accel_x_list) / N
                        avg_y = sum(accel_y_list) / N
        except (ValueError, UnicodeDecodeError):
            continue

        # --- 描画処理 ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 3D立方体の描画
        glPushMatrix()
        glRotatef(-avg_x * 5, 1, 0, 0) 
        glRotatef(-avg_y * 5, 0, 0, 1)
        draw_cube()
        glPopMatrix()

        # 2Dテキストの描画
        text_x = f"Avg X: {avg_x:.2f}"
        text_y = f"Avg Y: {avg_y:.2f}"
        draw_text(10, 10, text_x, font)
        draw_text(10, 50, text_y, font)

        # 画面を更新
        pygame.display.flip()
        pygame.time.wait(33)

if __name__ == '__main__':
    main()
