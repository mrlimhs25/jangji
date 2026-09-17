import sys
import random
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QFont, QCursor

class DriftyDogPet(QWidget):
    def __init__(self):
        super().__init__()

        # 투명 배경, 테두리 없음, 최상단 고정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(110, 80)

        # 뽀모도로 타이머 (집중 25분 / 휴식 5분)
        self.WORK_TIME = 25 * 60
        self.REST_TIME = 5 * 60
        self.pomo_seconds = self.WORK_TIME
        self.is_running = True
        self.mode = "WORK"

        # 물리 파라미터
        self.x = 300.0
        self.y = 200.0
        self.vx = 2.0
        self.vy = 0.0
        self.gravity = 0.55
        self.bounce = 0.45
        self.friction = 0.98

        # 인터랙션 상태
        self.is_grabbed = False
        self.last_cursor_pos = QPoint()
        self.facing_right = True

        # 스프라이트 프레임 (애니메이션 박동감)
        self.anim_frame = 0

        # 메인 물리 및 루프 타이머 (60 FPS)
        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_timer.start(16)

        # 뽀모도로 카운트다운 (1초 주기)
        self.pomo_timer = QTimer(self)
        self.pomo_timer.timeout.connect(self.tick_pomo)
        self.pomo_timer.start(1000)

        self.move(int(self.x), int(self.y))
        self.show()

    def tick_pomo(self):
        if self.is_running and self.pomo_seconds > 0:
            self.pomo_seconds -= 1
        elif self.pomo_seconds <= 0:
            # 시간 다 되면 세션 전환
            self.mode = "REST" if self.mode == "WORK" else "WORK"
            self.pomo_seconds = self.REST_TIME if self.mode == "REST" else self.WORK_TIME
            # 휴식 시간엔 높이 뜀!
            self.vy = -12

    def update_physics(self):
        self.anim_frame += 1

        # 작업표시줄을 감안한 가용 화면 영역
        screen_geo = QApplication.primaryScreen().availableGeometry()
        floor = screen_geo.height() - self.height()
        wall_right = screen_geo.width() - self.width()

        if not self.is_grabbed:
            # 중력 적용
            self.vy += self.gravity
            self.x += self.vx
            self.y += self.vy

            # 바닥 충돌 처리
            if self.y >= floor:
                self.y = floor
                if abs(self.vy) > 2.5:
                    self.vy = -self.vy * self.bounce
                else:
                    self.vy = 0
                    # 바닥에 있을 때 자율 주행 및 방황
                    if random.random() < 0.02:
                        self.vx = random.choice([-2.5, -1.8, 0, 1.8, 2.5])

            # 좌우 벽 충돌 처리
            if self.x <= 0:
                self.x = 0
                self.vx = -self.vx * self.bounce
            elif self.x >= wall_right:
                self.x = wall_right
                self.vx = -self.vx * self.bounce

            # 감속 마찰
            self.vx *= self.friction
            if abs(self.vx) > 0.3:
                self.facing_right = self.vx > 0

            self.move(int(self.x), int(self.y))

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_grabbed = True
            self.last_cursor_pos = QCursor.pos()
            self.vx = 0
            self.vy = 0
        elif event.button() == Qt.RightButton:
            self.show_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.is_grabbed:
            current_cursor = QCursor.pos()
            delta = current_cursor - self.last_cursor_pos

            # 마우스로 잡고 휘두른 속도 기록
            self.vx = delta.x() * 0.7
            self.vy = delta.y() * 0.7

            self.x += delta.x()
            self.y += delta.y()
            self.move(int(self.x), int(self.y))
            self.last_cursor_pos = current_cursor

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_grabbed:
            self.is_grabbed = False
            # 던져진 관성 적용 (너무 빠르면 제한)
            self.vx = max(-18, min(18, self.vx))
            self.vy = max(-18, min(18, self.vy))

    def show_menu(self, pos):
        menu = QMenu(self)
        toggle_txt = "타이머 일시정지" if self.is_running else "타이머 재개"
        action_toggle = menu.addAction(toggle_txt)
        action_reset = menu.addAction("타이머 25분 리셋")
        menu.addSeparator()
        action_quit = menu.addAction("강아지 보내기 (종료)")

        chosen = menu.exec_(pos)
        if chosen == action_toggle:
            self.is_running = not self.is_running
        elif chosen == action_reset:
            self.pomo_seconds = self.WORK_TIME
            self.mode = "WORK"
        elif chosen == action_quit:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 뽀모도로 미니멀 인디케이터 (머리 위 작은 캡슐)
        mins = self.pomo_seconds // 60
        secs = self.pomo_seconds % 60
        time_text = f"{mins:02}:{secs:02}"

        bg_color = QColor(245, 120, 80, 220) if self.mode == "WORK" else QColor(46, 204, 113, 220)
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(15, 2, 80, 18), 9, 9)

        painter.setPen(QColor("white"))
        font = QFont("Arial", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(15, 2, 80, 18), Qt.AlignCenter, f"{'🔥' if self.mode == 'WORK' else '☕'} {time_text}")

        # 2. 강아지 본체 렌더링
        dog_font = QFont("Segoe UI Emoji", 30)
        painter.setFont(dog_font)

        # 상태별 애니메이션 텍스트
        if self.is_grabbed:
            sprite = "🐶"  # 들려있을 때
        elif abs(self.vy) > 2.0:
            sprite = "🐕"  # 점프/낙하 중
        elif abs(self.vx) > 0.8:
            # 걷는 모션 틱
            sprite = "🐕" if (self.anim_frame // 10) % 2 == 0 else "🐾"
        else:
            sprite = "🐶" if (self.anim_frame // 30) % 2 == 0 else "💤"

        # 좌우 반전 느낌을 위한 위치 조정
        text_rect = QRectF(10, 20, 90, 55)
        painter.drawText(text_rect, Qt.AlignCenter, sprite)
