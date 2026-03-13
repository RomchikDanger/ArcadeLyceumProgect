'''Это проект футбола от Гескина Романа'''

import arcade
import arcade.gui
import math
import random
import sqlite3

#______________________________________________КОНСТАНТЫ______________________________________________
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = 'Аркадный Футбол'

#физика
FIELD_WIDTH = 1600
FIELD_HEIGHT = 900
LOSE_ENERGY = 0.7 #потеря энегрии
FRICTION = 0.98 #трение

#игрок
PLAYER_SPEED = 5
PLAYER_RADIUS = 20
PLAYER_COLOR = arcade.color.BLUE

#мяч
BALL_RADIUS = 15
BALL_COLOR = arcade.color.ORANGE
KICK_FORCE = 25

#ворота
GOAL_WIDTH = 200
GOAL_HEIGHT = 100
GOAL_DEPTH = 50
GOAL_COLOR = arcade.color.WHITE
GOAL_DOT_COLOR = arcade.color.RED

#клетка
TILE_SIZE = 64

#БД
DB_NAME = 'arcade_football.db'

#все цвета
MENU_BACKGROUND = arcade.color.DARK_GREEN
GAME_BACKGROUND = arcade.color.GREEN
SCORE_BACKGROUND = arcade.color.DARK_GREEN

#______________________________________________БАЗА ДАННЫХ______________________________________________
def init_database():
    #создание таблицы
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            score INTEGER,
            goals_scored INTEGER,
            goals_conceded INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    con.commit()
    con.close()

def save_result(player_name, score, goals_scored, goals_conceded):
    #сохранение в БД
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute('''
        INSERT INTO results (player_name, score, goals_scored, goals_conceded)
        VALUES (?, ?, ?, ?)
    ''', (player_name, score, goals_scored, goals_conceded))
    con.commit()
    con.close()

def get_top_scores(limit=10):
    #лучшие резы(по убыванию)
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute('''
        SELECT player_name, score, goals_scored, goals_conceded, timestamp
        FROM results
        ORDER BY score DESC, goals_scored DESC
        LIMIT ?
    ''', (limit,))
    rows = cur.fetchall()
    con.close()
    return rows

#______________________________________________МЯЧ______________________________________________
class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS

    def update(self):
        self.vx *= FRICTION
        self.vy *= FRICTION
        self.x += self.vx
        self.y += self.vy

        #отскоки от границ
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = -self.vx * LOSE_ENERGY
        if self.x + self.radius > FIELD_WIDTH:
            self.x = FIELD_WIDTH - self.radius
            self.vx = -self.vx * LOSE_ENERGY
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = -self.vy * LOSE_ENERGY
        if self.y + self.radius > FIELD_HEIGHT:
            self.y = FIELD_HEIGHT - self.radius
            self.vy = -self.vy * LOSE_ENERGY

    def draw(self):
        #отрисовка мяча и блика
        arcade.draw_circle_filled(self.x, self.y, self.radius, BALL_COLOR)
        arcade.draw_circle_filled(self.x - 5, self.y + 5, self.radius // 3, arcade.color.WHITE)
        arcade.draw_circle_outline(self.x, self.y, self.radius, arcade.color.BLACK, 2)

    def kick(self, from_x, from_y, force=KICK_FORCE):
        #удар по мячу
        dx = self.x - from_x
        dy = self.y - from_y
        dist = math.hypot(dx, dy)
        if dist > 0.1:
            nx = dx / dist
            ny = dy / dist
            self.vx += nx * force
            self.vy += ny * force

#______________________________________________ИГРОК______________________________________________
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.speed = PLAYER_SPEED
        self.radius = PLAYER_RADIUS
        self.color = PLAYER_COLOR

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= FRICTION
        self.vy *= FRICTION

        #грани поля
        if self.x - self.radius < 0:
            self.x = self.radius
        if self.x + self.radius > FIELD_WIDTH:
            self.x = FIELD_WIDTH - self.radius
        if self.y - self.radius < 0:
            self.y = self.radius
        if self.y + self.radius > FIELD_HEIGHT:
            self.y = FIELD_HEIGHT - self.radius

    def draw(self):
        arcade.draw_circle_filled(self.x, self.y, self.radius, self.color)
        arcade.draw_circle_filled(self.x + 5, self.y + 5, 3, arcade.color.WHITE)
        arcade.draw_circle_filled(self.x - 5, self.y + 5, 3, arcade.color.WHITE)

    #управление
    def move_left(self):
        self.vx = -self.speed

    def move_right(self):
        self.vx = self.speed

    def move_up(self):
        self.vy = self.speed

    def move_down(self):
        self.vy = -self.speed

    def stop_x(self):
        self.vx = 0

    def stop_y(self):
        self.vy = 0

#______________________________________________ВОРОТА______________________________________________
class Goal:
    def __init__(self, x, y, width, height, is_left=True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_left = is_left   #True - левые, False - правые
        self.depth = GOAL_DEPTH

    def draw(self):
        #отрисовка ворот(левые и правые)
        if self.is_left:
            points = [
                (self.x - self.depth, self.y - self.height//2),
                (self.x, self.y - self.height//2),
                (self.x, self.y + self.height//2),
                (self.x - self.depth, self.y + self.height//2)
            ]
            arcade.draw_line_strip(points + [points[0]], GOAL_COLOR, 3)

            #точки(круги на углах)
            post_radius = 5
            arcade.draw_circle_filled(self.x, self.y - self.height//2, post_radius, GOAL_DOT_COLOR)
            arcade.draw_circle_filled(self.x, self.y + self.height//2, post_radius, GOAL_DOT_COLOR)
            arcade.draw_circle_filled(self.x - self.depth, self.y - self.height//2, post_radius, GOAL_DOT_COLOR)
            arcade.draw_circle_filled(self.x - self.depth, self.y + self.height//2, post_radius, GOAL_DOT_COLOR)

            #сетка
            for i in range(1, 4):
                x_pos = self.x - (self.depth * i / 4)
                arcade.draw_line(x_pos, self.y - self.height//2, x_pos, self.y + self.height//2,
                                 GOAL_COLOR, 1)
        else:
            points = [
                (self.x + self.depth, self.y - self.height//2),
                (self.x, self.y - self.height//2),
                (self.x, self.y + self.height//2),
                (self.x + self.depth, self.y + self.height//2)
            ]
            arcade.draw_line_strip(points + [points[0]], GOAL_COLOR, 3)

            post_radius = 5
            arcade.draw_circle_filled(self.x, self.y - self.height//2, post_radius, GOAL_DOT_COLOR)
            arcade.draw_circle_filled(self.x, self.y + self.height//2, post_radius, GOAL_DOT_COLOR)
            arcade.draw_circle_filled(self.x + self.depth, self.y - self.height//2, post_radius, GOAL_DOT_COLOR)
            arcade.draw_circle_filled(self.x + self.depth, self.y + self.height//2, post_radius, GOAL_DOT_COLOR)

            for i in range(1, 4):
                x_pos = self.x + (self.depth * i / 4)
                arcade.draw_line(x_pos, self.y - self.height//2, x_pos, self.y + self.height//2,
                                 GOAL_COLOR, 1)

    def check_goal(self, ball):
        #мяч в воротах
        if self.is_left:
            if (ball.x <= self.x and ball.x >= self.x - self.depth and
                ball.y >= self.y - self.height//2 and ball.y <= self.y + self.height//2):
                return True
        else:
            if (ball.x >= self.x and ball.x <= self.x + self.depth and
                ball.y >= self.y - self.height//2 and ball.y <= self.y + self.height//2):
                return True
        return False

#______________________________________________КАРТА(тайловая)______________________________________________
class TileMap:
    def __init__(self, width, height, tile_size):
        self.tile_size = tile_size
        self.tiles = []
        self.create_walls(width, height)

    def create_walls(self, width, height):
        #стены(верт)
        for y in range(0, height, self.tile_size):
            self.tiles.append({
                'x': self.tile_size // 2,
                'y': y + self.tile_size // 2,
                'width': self.tile_size,
                'height': self.tile_size
            })
            self.tiles.append({
                'x': width - self.tile_size // 2,
                'y': y + self.tile_size // 2,
                'width': self.tile_size,
                'height': self.tile_size
            })

        #стены(горизонт)
        for x in range(self.tile_size, width - self.tile_size, self.tile_size):
            self.tiles.append({
                'x': x + self.tile_size // 2,
                'y': self.tile_size // 2,
                'width': self.tile_size,
                'height': self.tile_size
            })
            self.tiles.append({
                'x': x + self.tile_size // 2,
                'y': height - self.tile_size // 2,
                'width': self.tile_size,
                'height': self.tile_size
            })

    def draw(self):
        for tile in self.tiles:
            arcade.draw_rectangle_filled(tile['x'], tile['y'],
                                         tile['width'], tile['height'],
                                         arcade.color.DARK_GREEN)

    def check_collision(self, x, y, radius):
        for tile in self.tiles:
            if (abs(x - tile['x']) < radius + tile['width']/2 and
                abs(y - tile['y']) < radius + tile['height']/2):
                return True
        return False

#______________________________________________КАМЕРА______________________________________________
class Camera:
    def __init__(self, width, height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height

    def update(self, target_x, target_y):
        #камера в центре
        self.x = target_x - self.width // 2
        self.y = target_y - self.height // 2
        self.x = max(0, min(self.x, FIELD_WIDTH - self.width))
        self.y = max(0, min(self.y, FIELD_HEIGHT - self.height))

    def apply(self, x, y):
        return x - self.x, y - self.y

#______________________________________________СТРАНИЦА ИГРЫ______________________________________________
class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        init_database()

        #создание объектов
        self.player = Player(400, 350)
        self.ball = Ball(800, 450)
        self.goal_left = Goal(100, FIELD_HEIGHT//2, GOAL_WIDTH, GOAL_HEIGHT, is_left=True)
        self.goal_right = Goal(FIELD_WIDTH-100, FIELD_HEIGHT//2, GOAL_WIDTH, GOAL_HEIGHT, is_left=False)
        self.tile_map = TileMap(FIELD_WIDTH, FIELD_HEIGHT, TILE_SIZE)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        #счетчики
        self.score_left = 0
        self.score_right = 0
        self.time_expired = 0

        #GUI
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.menu_btn = arcade.gui.UIFlatButton(text='Меню', width=100)
        self.menu_btn.on_click = self.on_menu_click
        self.manager.add(arcade.gui.UIAnchorWidget(anchor_x='right', anchor_y='top',
                                                   child=self.menu_btn, align_x=-10, align_y=-10))
        self.game_over = False

    def on_menu_click(self, _):
        if not self.game_over and self.time_expired > 0:
            save_result('Player', self.score_left + self.score_right,
                        self.score_left, self.score_right)
        self.window.show_view(MenuView())

    def on_show_view(self):
        arcade.set_background_color(GAME_BACKGROUND)

    def on_draw(self):
        self.clear()
        self.camera.update(self.player.x, self.player.y)

        #клетчатое поле
        start_x = int(self.camera.x) // TILE_SIZE * TILE_SIZE
        start_y = int(self.camera.y) // TILE_SIZE * TILE_SIZE
        for x in range(start_x, int(self.camera.x + SCREEN_WIDTH), TILE_SIZE):
            for y in range(start_y, int(self.camera.y + SCREEN_HEIGHT), TILE_SIZE):
                screen_x, screen_y = self.camera.apply(x, y)
                #раскраска как в шахматах
                if (x // TILE_SIZE + y // TILE_SIZE) % 2 == 0:
                    color = arcade.color.LIGHT_GREEN
                else:
                    color = arcade.color.GREEN
                arcade.draw_rectangle_filled(screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2,
                                             TILE_SIZE, TILE_SIZE, color)

        #стены
        for tile in self.tile_map.tiles:
            screen_x, screen_y = self.camera.apply(tile['x'], tile['y'])
            arcade.draw_rectangle_filled(screen_x, screen_y, tile['width'], tile['height'],
                                         arcade.color.DARK_GREEN)

        #игрок
        px, py = self.camera.apply(self.player.x, self.player.y)
        self.player.x, self.player.y = px, py
        self.player.draw()
        self.player.x, self.player.y = px + self.camera.x, py + self.camera.y

        #мяч
        bx, by = self.camera.apply(self.ball.x, self.ball.y)
        self.ball.x, self.ball.y = bx, by
        self.ball.draw()
        self.ball.x, self.ball.y = bx + self.camera.x, by + self.camera.y

        #ворота
        for goal in [self.goal_left, self.goal_right]:
            gx, gy = self.camera.apply(goal.x, goal.y)
            goal.x, goal.y = gx, gy
            goal.draw()
            goal.x, goal.y = gx + self.camera.x, gy + self.camera.y

        #счет
        arcade.draw_text(f'Счёт: {self.score_left} : {self.score_right}',
                         10, SCREEN_HEIGHT-40, arcade.color.WHITE, 20)
        self.manager.draw()

        #конец игры
        if self.game_over:
            arcade.draw_rectangle_filled(SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                                         500, 200, arcade.color.BLACK + (200,))
            arcade.draw_text('ИГРА ОКОНЧЕНА', SCREEN_WIDTH//2, SCREEN_HEIGHT//2+30,
                             arcade.color.WHITE, 30, anchor_x='center')
            arcade.draw_text(f'Итоговый счёт: {self.score_left} : {self.score_right}',
                             SCREEN_WIDTH//2, SCREEN_HEIGHT//2-10, arcade.color.WHITE, 20, anchor_x='center')
            arcade.draw_text('Нажмите R для рестарта или ESC для меню',
                             SCREEN_WIDTH//2, SCREEN_HEIGHT//2-50, arcade.color.WHITE, 15, anchor_x='center')

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.R:
                self.restart()
            elif key == arcade.key.ESCAPE:
                self.window.show_view(MenuView())
            return

        #управление
        if key in (arcade.key.LEFT, arcade.key.A):
            self.player.move_left()
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player.move_right()
        elif key in (arcade.key.UP, arcade.key.W):
            self.player.move_up()
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.player.move_down()
        elif key == arcade.key.ESCAPE:
            #выход с сохранением
            if not self.game_over and self.time_expired > 0:
                save_result('Player', self.score_left + self.score_right, self.score_left,
                            self.score_right)
            self.window.show_view(MenuView())

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D):
            self.player.stop_x()
        if key in (arcade.key.UP, arcade.key.W, arcade.key.DOWN, arcade.key.S):
            self.player.stop_y()

    def on_update(self, delta_time):
        if self.game_over:
            return

        self.player.update()
        self.ball.update()

        #столкновение мяча со стенами
        if self.tile_map.check_collision(self.ball.x, self.ball.y, self.ball.radius):
            self.ball.vx *= -LOSE_ENERGY
            self.ball.vy *= -LOSE_ENERGY

        #проверка гола
        if self.goal_left.check_goal(self.ball):
            self.score_right += 1
            self.reset_ball()
        if self.goal_right.check_goal(self.ball):
            self.score_left += 1
            self.reset_ball()

        #коллизия игрока с мячом(ведет мяч)
        if (math.hypot(self.player.x - self.ball.x, self.player.y - self.ball.y)
                < self.player.radius + self.ball.radius):
            dx = self.ball.x - self.player.x
            dy = self.ball.y - self.player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                nx = dx / dist
                ny = dy / dist
                overlap = self.player.radius + self.ball.radius - dist
                self.ball.x += nx * overlap
                self.ball.y += ny * overlap
                self.ball.vx += self.player.vx * 0.5
                self.ball.vy += self.player.vy * 0.5

        #таймер
        self.time_expired += delta_time
        if self.time_expired > 180:
            self.game_over = True
            save_result('Player', self.score_left + self.score_right, self.score_left, self.score_right)

    def reset_ball(self):
        #возвращение мяча в центр
        self.ball.x = FIELD_WIDTH // 2
        self.ball.y = FIELD_HEIGHT // 2
        self.ball.vx = 0
        self.ball.vy = 0

    def restart(self):
        #перезапуск игры
        self.score_left = 0
        self.score_right = 0
        self.time_expired = 0
        self.game_over = False
        self.reset_ball()
        self.player.x = 400
        self.player.y = 350
        self.player.vx = 0
        self.player.vy = 0

#______________________________________________СТРАНИЦА РЕКОРДОВ______________________________________________
class ScoreView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.scores = get_top_scores()

        #кнопки внизу
        box = arcade.gui.UIBoxLayout(space_between=20)

        back_btn = arcade.gui.UIFlatButton(text='Назад в меню', width=200)
        back_btn.on_click = self.on_back_click
        box.add(back_btn)

        menu_btn = arcade.gui.UIFlatButton(text='Меню', width=200)
        menu_btn.on_click = self.on_menu_click
        box.add(menu_btn)

        self.manager.add(arcade.gui.UIAnchorWidget(anchor_x='center', anchor_y='bottom',
                                                   child=box, align_y=-50))

    def on_back_click(self, _):
        self.window.show_view(MenuView())

    def on_menu_click(self, _):
        self.window.show_view(MenuView())

    def on_show_view(self):
        arcade.set_background_color(SCORE_BACKGROUND)
        self.scores = get_top_scores()

    def on_draw(self):
        self.clear()
        arcade.draw_text('ТАБЛИЦА РЕКОРДОВ', SCREEN_WIDTH//2, SCREEN_HEIGHT-50, arcade.color.WHITE,
                         30, anchor_x='center')

        #список результатов
        y = SCREEN_HEIGHT - 120
        for i, row in enumerate(self.scores):
            name, score, gol_t, gol_f, ts = row
            if ts:
                date = ts[:10]
            else:
                date = ''
            text = f'{i+1}. {name} - Очки: {score} (Забито: {gol_t} Пропущено: {gol_f}) - {date}'
            arcade.draw_text(text, SCREEN_WIDTH//2, y, arcade.color.WHITE, 14, anchor_x='center')
            y -= 25

        if not self.scores:
            arcade.draw_text('Пока нет результатов', SCREEN_WIDTH//2, SCREEN_HEIGHT//2, arcade.color.WHITE,
                             20, anchor_x='center')
        self.manager.draw()

#______________________________________________ГЛАВНАЯ СТРАНИЦА______________________________________________
class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        #блок кнопок
        box = arcade.gui.UIBoxLayout(space_between=20)

        start_btn = arcade.gui.UIFlatButton(text='Старт', width=200)
        scores_btn = arcade.gui.UIFlatButton(text='Рекорды', width=200)
        quit_btn = arcade.gui.UIFlatButton(text='Выход', width=200)

        start_btn.on_click = self.on_start_click
        scores_btn.on_click = self.on_scores_click
        quit_btn.on_click = self.on_quit_click

        box.add(start_btn)
        box.add(scores_btn)
        box.add(quit_btn)

        self.manager.add(arcade.gui.UIAnchorWidget(anchor_x='center', anchor_y='center', child=box))

    def on_start_click(self, _):
        self.window.show_view(GameView())

    def on_scores_click(self, _):
        self.window.show_view(ScoreView())

    def on_quit_click(self, _):
        arcade.exit()

    def on_show_view(self):
        arcade.set_background_color(MENU_BACKGROUND)

    def on_draw(self):
        self.clear()
        arcade.draw_text('ФУТБОЛ', SCREEN_WIDTH//2, SCREEN_HEIGHT-100, arcade.color.WHITE, 40,
                         anchor_x='center')
        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MenuView())
    arcade.run()

if __name__ == "__main__":
    main()
