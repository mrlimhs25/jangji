import sys
import random
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QVBoxLayout
from PyQt5.QtGui import QCursor, QFont

class PomodoroDogPet(QWidget):
    def __init__(self):
        super().__init__()

        # 1. 윈도우 스타일 설정: 테두리 없음, 항상 위, 작업표시줄 제외, 배경 투명
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 2. 뽀모도로 설정 (기본: 집중 25분 / 휴식 5분)
        self.WORK_TIME = 25 * 60
        self.REST_TIME = 5 * 60
        self.current_time = self.WORK_TIME
        self.is_running = False
        self.session_mode = "WORK"  # "WORK" (집중) 또는 "REST" (휴식)

        # 3. 강아지 상태 머신 (IDLE, WALK, SLEEP, FOLLOW)
        self.state = "IDLE"
        self.direction = 1  # 1: 오른쪽, -1: 왼쪽
        self.walk_speed = 2
        self.follow_speed = 4

        # 4. UI 레이아웃 구성 (상단: 말풍선/타이머, 하단: 강아지 캐릭터)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        # 상태 말풍선 & 시간 표시 라벨
        self.bubble_label = QLabel(self)
        self.bubble_label.setAlignment(Qt.AlignCenter)
        self.bubble_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.92);
            color: #2c3e50;
            border: 2px solid #f39c12;
            border-radius: 12px;
            padding: 4px 10px;
            font-weight: bold;
            font-size: 13px;
        """)

        # 강아지 캐릭터 라벨
        self.dog_label = QLabel(self)
        self.dog_label.setAlignment(Qt.AlignCenter)
        self.dog_label.setStyleSheet("font-size: 38px; background: transparent;")

        layout.addWidget(self.bubble_label)
        layout.addWidget(self.dog_label)
        self.setLayout(layout)

        # 5. 화면 초기 위치 (화면 하단 우측)
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.move(self.screen_width - 240, self.screen_height - 180)

        # 6. 타이머들 설정
        # 뽀모도로 카운트다운 타이머 (1초 주기)
        self.pomo_timer = QTimer(self)
        self.pomo_timer.timeout.connect(self.tick_timer)

        # 애니메이션/이동 주기 타이머 (50ms 주기)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_movement)
        self.anim_timer.start(50)

        # 랜덤 행동 변경 타이머 (4초 주기)
        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self.decide_random_behavior)
        self.behavior_timer.start(4000)

        # 마우스 드래그 이동을 위한 변수
        self.drag_position = QPoint()

        self.update_ui()
        self.show()

    # --- 뽀모도로 타이머 로직 ---
    def tick_timer(self):
        if self.current_time > 0:
            self.current_time -= 1
        else:
            # 시간 종료 시 세션 전환
            if self.session_mode == "WORK":
                self.session_mode = "REST"
                self.current_time = self.REST_TIME
                self.state = "WALK"  # 휴식 시간엔 기분 좋아서 산책 모드
            else:
                self.session_mode = "WORK"
                self.current_time = self.WORK_TIME
                self.state = "SLEEP" # 다시 집중 시간엔 조용히 잠자기

        self.update_ui()

    def toggle_timer(self):
        if self.is_running:
            self.pomo_timer.stop()
            self.is_running = False
        else:
            self.pomo_timer.start(1000)
            self.is_running = True
        self.update_ui()

    def reset_timer(self):
        self.pomo_timer.stop()
        self.is_running = False
        self.session_mode = "WORK"
        self.current_time = self.WORK_TIME
        self.state = "IDLE"
        self.update_ui()

    # --- 행동 및 외형 업데이트 ---
    def update_ui(self):
        # 1) 시간 포맷팅 (MM:SS)
        mins = self.current_time // 60
        secs = self.current_time % 60
        time_str = f"{mins:02d}:{secs:02d}"

        mode_badge = "🔥집중" if self.session_mode == "WORK" else "☕휴식"
        run_status = "▶" if self.is_running else "❚❚"

        # 2) 상태별 말풍선 대사 & 캐릭터 표정
        if self.state == "FOLLOW":
            status_text = "주인님 놀아줘!"
            pet_sprite = "🐶💨"
        elif self.state == "SLEEP":
            status_text = "조용히 코자는 중..."
            pet_sprite = "💤 🐕"
        elif self.state == "WALK":
            status_text = "총총 순찰 중~"
            pet_sprite = "🐾 🐕" if self.direction == 1 else "🐕 🐾"
        else:  # IDLE
            if self.session_mode == "WORK" and self.is_running:
                status_text = "열심히 열공 중!"
                pet_sprite = "👓 🐶"
            else:
                status_text = "우클릭: 메뉴 열기"
                pet_sprite = "🐶"

        # 말풍선 텍스트 갱신
        self.bubble_label.setText(f"[{mode_badge} {time_str} {run_status}]\n{status_text}")
        self.dog_label.setText(pet_sprite)

        self.adjustSize()

    def decide_random_behavior(self):
        # 마우스를 따라가는 중이거나 드래그 중엔 상태 변경 안 함
        if self.state == "FOLLOW":
            return

        # 집중 세션 중일 때는 방해되지 않게 자거나(SLEEP), 얌전히(IDLE) 있는 확률 높임
        if self.session_mode == "WORK" and self.is_running:
            self.state = random.choices(["SLEEP", "IDLE", "WALK"], weights=[60, 30, 10])[0]
        else:
            # 휴식 시간 또는 대기 중일 때는 활발하게 산책
            self.state = random.choices(["WALK", "IDLE", "SLEEP"], weights=[50, 30, 20])[0]

        self.direction = random.choice([-1, 1])
        self.update_ui()

    def update_movement(self):
        x, y = self.x(), self.y()

        # 1) 산책(WALK) 상태: 좌우로 이동
        if self.state == "WALK":
            x += self.direction * self.walk_speed
            # 화면 좌우 경계 도달 시 방향 전환
            if x <= 10:
                self.direction = 1
            elif x >= self.screen_width - self.width() - 10:
                self.direction = -1
            self.move(x, y)

        # 2) 마우스 따라오기(FOLLOW) 상태
        elif self.state == "FOLLOW":
            target = QCursor.pos()
            dx = target.x() - (x + self.width() // 2)
            dy = target.y() - (y + self.height() // 2)

            # 마우스에 도달하면 만족하고 대기(IDLE)로 전환
            if abs(dx) < 20 and abs(dy) < 20:
                self.state = "IDLE"
                self.update_ui()
            else:
                step_x = self.follow_speed if dx > 0 else -self.follow_speed
                step_y = self.follow_speed if dy > 0 else -self.follow_speed
                self.move(x + int(step_x), y + int(step_y))

    # --- 마우스 클릭 & 메뉴 조작 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 좌클릭: 마우스를 쫓아오게 하거나 드래그 준비
            self.state = "FOLLOW"
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.update_ui()

        elif event.button() == Qt.RightButton:
            # 우클릭: 뽀모도로 제어 팝업 메뉴 열기
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        # 마우스로 꾹 눌러서 끌어다 원하는 곳에 놓기
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)

    def show_context_menu(self, global_pos):
        menu = QMenu(self)

        # 타이머 시작/일시정지
        action_toggle = QAction("타이머 일시정지" if self.is_running else "타이머 시작", self)
        action_toggle.triggered.connect(self.toggle_timer)
        menu.addAction(action_toggle)

        # 초기화
        action_reset = QAction("타이머 리셋", self)
        action_reset.triggered.connect(self.reset_timer)
        menu.addAction(action_reset)

        menu.addSeparator()

        # 세션 강제 전환
        action_switch = QAction("집중/휴식 모드 강제 전환", self)
        action_switch.triggered.connect(self.force_switch_mode)
        menu.addAction(action_switch)

        menu.addSeparator()

        # 프로그램 종료
        action_quit = QAction("종료", self)
        action_quit.triggered.connect(self.close)
        menu.addAction(action_quit)

        menu.exec_(global_pos)

    def force_switch_mode(self):
        if self.session_mode == "WORK":
            self.session_mode = "REST"
            self.current_time = self.REST_TIME
        else:
            self.session_mode = "WORK"
            self.current_time = self.WORK_TIME
        self.update_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = PomodoroDogPet()
    sys.exit(app.exec_())
