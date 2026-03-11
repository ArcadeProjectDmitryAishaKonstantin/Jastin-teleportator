import arcade
import math
import enum
import random
from arcade.camera import Camera2D

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Герой против монстров — меню"

GAME_WIDTH = 1400
GAME_HEIGHT = 750

WORLD_WIDTH = 1900
WORLD_HEIGHT = 750

GAME_TITLE = "Спрайтовый герой"
MONSTER_SPAWN_INTERVAL = 3.0

CAMERA_LERP = 0.12

unlocked_levels = [1]
completed_levels = []

class FaceDirection(enum.Enum):
    LEFT = 0
    RIGHT = 1


#-------------------Уровень 3----------------------
class Hero(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.scale = 1.0
        self.speed = 300
        self.health = 100

        self.idle_texture = arcade.load_texture(
            ":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.texture = self.idle_texture

        self.walk_textures = []
        for i in range(0, 8):
            texture = arcade.load_texture(f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.walk_textures.append(texture)

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

        self.is_walking = False
        self.face_direction = FaceDirection.RIGHT

        self.center_x = 100
        self.center_y = 130

        self.change_y = 0
        self.gravity = 0.5
        self.jump_strength = 12
        self.can_jump = True

        self.is_alive = True

    def update_animation(self, delta_time: float = 1 / 60):
        if not self.is_alive:
            return

        if self.is_walking:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.walk_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.walk_textures[self.current_texture]
                else:
                    self.texture = self.walk_textures[self.current_texture].flip_horizontally()
        else:
            if self.face_direction == FaceDirection.RIGHT:
                self.texture = self.idle_texture
            else:
                self.texture = self.idle_texture.flip_horizontally()

    def update(self, delta_time, keys_pressed):
        if not self.is_alive:
            return

        dx, dy = 0, 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed * delta_time
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed * delta_time

        self.change_y -= self.gravity

        if arcade.key.SPACE in keys_pressed and self.can_jump:
            self.change_y = self.jump_strength
            self.can_jump = False

        dy = self.change_y

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        self.center_x += dx
        self.center_y += dy

        if dx < 0:
            self.face_direction = FaceDirection.LEFT
        elif dx > 0:
            self.face_direction = FaceDirection.RIGHT

        self.center_x = max(self.width / 2, min(WORLD_WIDTH - self.width / 2, self.center_x))

        self.is_walking = dx != 0


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y, speed=800, damage=10):
        super().__init__()
        self.texture = arcade.load_texture(":resources:/images/space_shooter/laserBlue01.png")
        self.center_x = start_x
        self.center_y = start_y
        self.speed = speed
        self.damage = damage

        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.angle = math.degrees(-angle)

    def update(self, delta_time):
        if (self.center_x < -100 or self.center_x > WORLD_WIDTH + 100 or
                self.center_y < -100 or self.center_y > WORLD_HEIGHT + 100):
            self.remove_from_sprite_lists()
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time


class Monster(arcade.Sprite):
    def __init__(self, player):
        super().__init__(":resources:images/enemies/frog.png", scale=0.5)
        self.center_x = random.randint(50, WORLD_WIDTH - 50)
        self.center_y = WORLD_HEIGHT + 50

        self.width = self.texture.width * 0.5
        self.height = self.texture.height * 0.5

        self.change_y = -2
        self.change_x = 0
        self.speed = 150
        self.player = player
        self.is_grounded = False
        self.gravity = 0.5

        self.idle_texture = arcade.load_texture(":resources:images/enemies/frog.png")
        self.texture = self.idle_texture

    def update(self, delta_time):
        self.change_y -= self.gravity * delta_time * 60
        self.center_y += self.change_y * delta_time * 60
        if self.change_y < 0:
            highest_platform_top = -float('inf')
            landed = False

            for platform in self.parent.platforms_list:
                if (self.right > platform.left and
                        self.left < platform.right):
                    next_bottom = self.center_y - self.height / 2 + self.change_y * delta_time * 60
                    if next_bottom <= platform.top <= self.bottom:
                        if platform.top > highest_platform_top:
                            highest_platform_top = platform.top
                            landed = True

            if landed:
                self.bottom = highest_platform_top + 1
                self.change_y = 0
                self.is_grounded = True

        if self.player and self.player.is_alive:
            dx = self.player.center_x - self.center_x
            distance = abs(dx)

            # прыжок, если монстр на земле
            if self.is_grounded:
                direction = 1 if dx > 0 else -1
                check_x = self.center_x + (self.width / 2 + 10) * direction
                check_y = self.center_y

                obstacle_ahead = False
                for platform in self.parent.platforms_list:
                    if (abs(check_x - platform.center_x) < platform.width / 2 + self.width / 2 and
                            abs(check_y - platform.center_y) < platform.height / 2 + self.height / 2 + 20):
                        obstacle_ahead = True
                        break

                if obstacle_ahead or (self.player.center_y > self.center_y + 30):
                    self.change_y = 12
                    self.is_grounded = False

            # движение к игроку
            if distance > 5:
                direction = 1 if dx > 0 else -1
                movement = direction * self.speed * delta_time
                old_x = self.center_x
                self.center_x += movement
                collision = False
                for platform in self.parent.platforms_list:
                    if (self.bottom <= platform.top + 10 and
                            self.top >= platform.bottom - 10):
                        if arcade.check_for_collision(self, platform):
                            collision = True
                            self.center_x = old_x
                            break

                # проверка, стоит ли монстр на платформе
                on_any_platform = False
                for platform in self.parent.platforms_list:
                    if (self.bottom <= platform.top + 5 and
                            self.right > platform.left and
                            self.left < platform.right):
                        on_any_platform = True
                        break

                if not on_any_platform:
                    self.is_grounded = False

                if direction > 0:
                    self.texture = self.idle_texture
                else:
                    self.texture = self.idle_texture.flip_horizontally()


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.LIGHT_BLUE)

        # камеры
        self.world_camera = Camera2D()
        self.gui_camera = Camera2D()

        self.game_state = "PLAYING"

        self.background_sprite_list = arcade.SpriteList()

        # движ платформы
        self.moving_platform = None
        self.moving_platform_2 = None
        self.moving_platform_3 = None
        self.platform_start_x = 0
        self.platform_start_x_2 = 0
        self.platform_start_y_3 = 0
        self.platform_time = 0
        self.platform_time_2 = math.pi
        self.platform_time_3 = 0
        self.platform_range = 150
        self.platform_speed = 1.4
        self.platform_range_2 = 300
        self.platform_speed_2 = 1
        self.platform_range_3 = 200
        self.platform_speed_3 = 1.4

        # Для отслеживания прыжка с батута
        self.trampoline_jump_ready = True

        # Флаг для создания земли
        self.ground_created = False

        self.victory_sound = arcade.load_sound(":resources:/sounds/upgrade1.wav")

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.box_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.new_sprite_list = arcade.SpriteList()
        self.new_ground_list = arcade.SpriteList()
        self.water_list_3 = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.trampoline_list = arcade.SpriteList()
        self.target_list = arcade.SpriteList()
        self.door_list = arcade.SpriteList()

        # для воды создаём два отдельных списка
        self.water_list_1 = arcade.SpriteList()
        self.water_list_2 = arcade.SpriteList()

        self.player = Hero()
        self.player_list.append(self.player)

        self.box_list = arcade.SpriteList()
        '''
        # Первая коробка (нижняя)
        box1 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box1.center_x = 400
        box1.center_y = 100
        self.box_list.append(box1)

        # Вторая коробка (на первой)
        box2 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box2.center_x = 400
        box2.center_y = 100 + box2.height
        self.box_list.append(box2)

        # Третья коробка (рядом)
        box3 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box3.center_x = 400 + box3.width + 20
        box3.center_y = 100
        self.box_list.append(box3)

        # Четвёртая коробка (рядом)
        box4 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box4.center_x = 600
        box4.center_y = 200
        self.box_list.append(box4)

        # Пятая коробка (рядом)
        box5 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box5.center_x = 700
        box5.center_y = 230
        self.box_list.append(box5)

        # Шестая коробка (рядом)
        box6 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box6.center_x = 800
        box6.center_y = 250
        self.box_list.append(box6)

        # Седьмая коробка (рядом)
        box7 = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
        box7.center_x = 850
        box7.center_y = 271
        self.box_list.append(box7)
        '''

        # Новый спрайт
        new_sprite_1 = arcade.Sprite("platform_1.png", 0.5)
        new_sprite_1.center_x = 300
        new_sprite_1.center_y = 150
        self.new_sprite_list.append(new_sprite_1)

        new_sprite_2 = arcade.Sprite("platform_2.png", 0.3)
        new_sprite_2.center_x = 800
        new_sprite_2.center_y = 300
        self.new_sprite_list.append(new_sprite_2)
        self.moving_platform = new_sprite_2
        self.platform_start_x = 800
        self.platform_time = 0

        new_sprite_3 = arcade.Sprite("ground_platform.png", 0.4)
        new_sprite_3.center_x = 450
        new_sprite_3.center_y = 300
        self.new_sprite_list.append(new_sprite_3)

        # Вторая движущаяся платформа
        new_sprite_4 = arcade.Sprite("platform_2.png", 0.4)
        new_sprite_4.center_x = 750
        new_sprite_4.center_y = 550
        self.new_sprite_list.append(new_sprite_4)
        self.moving_platform_2 = new_sprite_4
        self.platform_start_x_2 = 750
        self.platform_time_2 = 0

        # Третья движущаяся платформа
        new_sprite_5 = arcade.Sprite("platform_2.png", 0.4)
        new_sprite_5.center_x = 1050
        new_sprite_5.center_y = 400
        self.new_sprite_list.append(new_sprite_5)
        self.moving_platform_3 = new_sprite_5
        self.platform_start_y_3 = 400
        self.platform_time_3 = 0

        # монетки
        x_coords = [300, 750, 1050, 1100, 1170, 1570, 1850, 1500, 1550, 500]
        y_coords = [250, 400, 300, 250, 600, 150, 230, 500, 400, 500]

        for i in range(10):
            coin = arcade.Sprite(":resources:images/items/coinGold.png", 0.5)
            coin.center_x = x_coords[i]
            coin.center_y = y_coords[i]
            self.coin_list.append(coin)

        self.shoot_sound = arcade.load_sound(":resources:/sounds/laser1.wav")
        self.keys_pressed = set()

        self.wall_list = arcade.SpriteList()

        # Рисуем землю от 0 до 500
        for x in range(0, 500, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.5)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)

        # Рисуем воду от 500 до 1100 (НЕ в monster_list!)
        for x in range(500, 1100, 64):
            water = arcade.Sprite(":resources:images/tiles/water.png", 0.5)
            water.center_x = x
            water.center_y = 32
            self.water_list_1.append(water)

        # Рисуем второй участок воды (1100-3000) - НЕ в monster_list!
        for x in range(1100, WORLD_WIDTH, 64):
            water = arcade.Sprite(":resources:images/tiles/water.png", 0.5)
            water.center_x = x
            water.center_y = 32
            self.water_list_2.append(water)

        # батут
        self.trampoline = arcade.Sprite("trampoline.png", 0.15)
        self.trampoline.center_x = 500
        self.trampoline.center_y = 350
        self.trampoline_list.append(self.trampoline)

        self.target = arcade.Sprite("target.png", 0.1)
        self.target.center_x = 1500
        self.target.center_y = 500

        # дверь
        self.door = arcade.Sprite("door.png", 0.5)
        self.door.center_x = 1700
        self.door.center_y = 550

        self.platforms_list = arcade.SpriteList()
        self.platforms_list.extend(self.wall_list)
        self.platforms_list.extend(self.box_list)
        self.platforms_list.extend(self.new_sprite_list)

        # Фоновый спрайт
        background = arcade.Sprite("jungle.png")
        background.center_x = WORLD_WIDTH // 2
        background.center_y = WORLD_HEIGHT // 2
        self.background_sprite_list.append(background)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            platforms=self.platforms_list,
            gravity_constant=0.5
        )

        # Сброс всех игровых переменных
        self.monster_spawn_timer = 0.0
        self.coin_score = 0  # очки за монетки
        self.frog_score = 0  # счётчик побеждённых врагов
        self.game_state = "PLAYING"
        self.trampoline_jump_ready = True
        self.ground_created = False
        self.target_spawned = False  # флаг, появилась ли мишень
        self.target_list = arcade.SpriteList()  # очищаем список мишеней

        # Номер уровня
        self.level_number = 3

    def on_draw(self):
        self.clear()
        self.world_camera.use()
        self.background_sprite_list.draw()
        self.wall_list.draw()

        # Рисуем оба участка воды
        self.water_list_1.draw()
        self.water_list_2.draw()

        self.coin_list.draw()
        self.new_ground_list.draw()
        self.water_list_3.draw()
        self.trampoline_list.draw()

        # Мишень рисуем, если она есть в списке
        self.target_list.draw()

        # Дверь рисуем, если она появилась
        self.door_list.draw()

        self.box_list.draw()
        self.player_list.draw()
        self.bullet_list.draw()
        self.monster_list.draw()
        self.new_sprite_list.draw()
        self.gui_camera.use()

        # Отображаем оба счёта
        arcade.draw_text(f"Coins: {self.coin_score}", 10, self.height - 30, arcade.color.WHITE, 20)
        arcade.draw_text(f"Frogs: {self.frog_score}", 10, self.height - 60, arcade.color.WHITE, 20)

        if self.game_state == "GAME_OVER":
            arcade.draw_lrbt_rectangle_filled(0, self.width, self.height, 750, (0, 60, 0, 128))
            arcade.draw_text("GAME OVER", self.width // 2, self.height // 2 + 50,
                             arcade.color.RED, 50, anchor_x="center")
            arcade.draw_text(f"Coins: {self.coin_score}  Frogs: {self.frog_score}",
                             self.width // 2, self.height // 2,
                             arcade.color.WHITE, 30, anchor_x="center")
            arcade.draw_text("Press R to Restart or ESC to Exit", self.width // 2,
                             self.height // 2 - 50, arcade.color.YELLOW, 20, anchor_x="center")
        elif self.game_state == "VICTORY":
            arcade.draw_lrbt_rectangle_filled(0, self.width, 0, self.height, (0, 255, 127, 100))
            arcade.draw_text("ПОБЕДА!", self.width // 2, self.height // 2 + 100,
                             arcade.color.GOLD, 70, anchor_x="center", font_name="Kenney Pixel")
            arcade.draw_text("ВЫ ПРОШЛИ УРОВЕНЬ 3!", self.width // 2, self.height // 2 + 30,
                             arcade.color.WHITE, 30, anchor_x="center")
            arcade.draw_text(f"Coins: {self.coin_score}  Frogs: {self.frog_score}",
                             self.width // 2, self.height // 2 - 20,
                             arcade.color.YELLOW, 30, anchor_x="center")
            arcade.draw_text("Возврат в меню...", self.width // 2,
                             self.height // 2 - 70, arcade.color.YELLOW, 20, anchor_x="center")

    def on_update(self, delta_time):
        global unlocked_levels, completed_levels

        if self.game_state != "PLAYING":
            if self.game_state == "VICTORY":
                if self.level_number not in completed_levels:
                    completed_levels.append(self.level_number)
                next_level = self.level_number + 1
                if next_level <= 3 and next_level not in unlocked_levels:
                    unlocked_levels.append(next_level)

                # Возврат в меню после победы
                arcade.pause(1.5)
                self.close()
                menu = MenuWindow()
                arcade.run()
                return
            return

        self.physics_engine.update()
        self.player_list.update(delta_time, self.keys_pressed)
        self.bullet_list.update()
        self.player_list.update_animation(delta_time)
        self.player.can_jump = self.physics_engine.can_jump()

        for bullet in self.bullet_list:
            monsters_hit_list = arcade.check_for_collision_with_list(bullet, self.monster_list)
            if monsters_hit_list:
                bullet.remove_from_sprite_lists()
                for monster in monsters_hit_list:
                    monster.remove_from_sprite_lists()
                    self.frog_score += 1
                    print(f"ВРАГ! Всего врагов: {self.frog_score}")

        for bullet in self.bullet_list:
            if arcade.check_for_collision_with_list(bullet, self.platforms_list):
                bullet.remove_from_sprite_lists()

        if self.frog_score >= 3 and self.coin_score >= 15 and not self.target_spawned:
            self.target_list.append(self.target)
            self.target_spawned = True
            print("МИШЕНЬ ПОЯВИЛАСЬ!")

        if self.target_spawned and self.target in self.target_list and not self.ground_created:
            for bullet in self.bullet_list:
                if arcade.check_for_collision(bullet, self.target) and self.coin_score >= 15 and self.frog_score >= 3:
                    bullet.remove_from_sprite_lists()
                    self.target.remove_from_sprite_lists()
                    self.door_list.append(self.door)

                    # Убираем второй участок воды
                    self.water_list_2 = arcade.SpriteList()

                    # Создаём землю
                    for x in range(1100, 1500, 64):
                        ground = arcade.Sprite(":resources:images/tiles/sandMid.png", 0.5)
                        ground.center_x = x
                        ground.center_y = 32
                        self.new_ground_list.append(ground)
                        self.platforms_list.append(ground)

                    # Создаём новый участок воды (1500-WORLD_WIDTH)
                    for x in range(1500, WORLD_WIDTH, 64):
                        water = arcade.Sprite(":resources:images/tiles/water.png", 0.5)
                        water.center_x = x
                        water.center_y = 32
                        self.water_list_3.append(water)  # добавляем в новый список

                    palka_1 = arcade.Sprite("palka1.png", 0.2)
                    palka_1.center_x = 1570
                    palka_1.center_y = 100
                    self.new_ground_list.append(palka_1)
                    self.platforms_list.append(palka_1)

                    palka_2 = arcade.Sprite("palka1.png", 0.2)
                    palka_2.center_x = 1800
                    palka_2.center_y = 200
                    self.new_ground_list.append(palka_2)
                    self.platforms_list.append(palka_2)

                    palka_3 = arcade.Sprite("palka1.png", 0.3)
                    palka_3.center_x = 1550
                    palka_3.center_y = 320
                    self.new_ground_list.append(palka_3)
                    self.platforms_list.append(palka_3)

        # Проверка сбора монеток
        coins_hit_list = arcade.check_for_collision_with_list(self.player, self.coin_list)
        for coin in coins_hit_list:
            coin.remove_from_sprite_lists()
            self.coin_score += 5
            print("МОНЕТКА! +5 очков")

        for water in self.water_list_1:
            if arcade.check_for_collision(self.player, water) and self.player.is_alive:
                self.player.is_alive = False
                self.player.remove_from_sprite_lists()
                self.game_state = "GAME_OVER"
                break

        for water in self.water_list_2:
            if arcade.check_for_collision(self.player, water) and self.player.is_alive:
                self.player.is_alive = False
                self.player.remove_from_sprite_lists()
                self.game_state = "GAME_OVER"
                break

        for water in self.water_list_3:
            if arcade.check_for_collision(self.player, water) and self.player.is_alive:
                self.player.is_alive = False
                self.player.remove_from_sprite_lists()
                self.game_state = "GAME_OVER"
                break

        for door in self.door_list:
            if arcade.check_for_collision(self.player,
                                          door) and self.player.is_alive and self.coin_score >= 35 and self.frog_score >= 5:
                self.game_state = "VICTORY"
                arcade.play_sound(self.victory_sound)
                return

        for monster in self.monster_list:
            if arcade.check_for_collision(self.player, monster) and self.player.is_alive:
                self.player.is_alive = False
                self.player.remove_from_sprite_lists()
                self.game_state = "GAME_OVER"
                break

        for monster in self.monster_list:
            monster.parent = self
            monster.update(delta_time)
            if monster.center_y < -50:
                monster.remove_from_sprite_lists()

        # Проверка коллизии с батутом
        if self.player.is_alive:
            if arcade.check_for_collision(self.player, self.trampoline):
                if self.player.change_y < 0 and self.trampoline_jump_ready:
                    self.player.change_y = 18
                    self.trampoline_jump_ready = False
                    print("БАТУТ!")
            else:
                self.trampoline_jump_ready = True

        if self.game_state == "PLAYING":
            self.monster_spawn_timer += delta_time
            if self.monster_spawn_timer >= MONSTER_SPAWN_INTERVAL:
                monster = Monster(self.player)
                self.monster_list.append(monster)
                self.monster_spawn_timer = 0.0

        # Камера
        target = (self.player.center_x, self.player.center_y)
        cx, cy = self.world_camera.position
        smooth = (cx + (target[0] - cx) * CAMERA_LERP,
                  cy + (target[1] - cy) * CAMERA_LERP)

        half_w = self.world_camera.viewport_width / 2
        half_h = self.world_camera.viewport_height / 2
        world_w = WORLD_WIDTH
        world_h = WORLD_HEIGHT
        cam_x = max(half_w, min(world_w - half_w, smooth[0]))
        cam_y = max(half_h, min(world_h - half_h, smooth[1]))

        self.world_camera.position = (cam_x, cam_y)

        # Движение платформ
        if self.moving_platform:
            self.platform_time += delta_time * self.platform_speed
            offset = math.sin(self.platform_time) * self.platform_range
            self.moving_platform.center_x = self.platform_start_x + offset

        if self.moving_platform_2:
            self.platform_time_2 += delta_time * self.platform_speed_2
            offset = math.sin(self.platform_time_2) * (-self.platform_range_2)
            self.moving_platform_2.center_x = self.platform_start_x_2 + offset

        if hasattr(self, 'moving_platform_3') and self.moving_platform_3:
            self.platform_time_3 += delta_time * self.platform_speed
            offset = math.sin(self.platform_time_3) * self.platform_range
            self.moving_platform_3.center_y = self.platform_start_y_3 + offset

    def on_mouse_press(self, x, y, button, modifiers):
        if (button == arcade.MOUSE_BUTTON_LEFT and
                self.game_state == "PLAYING" and
                self.player.is_alive):
            cam_x, cam_y = self.world_camera.position
            world_x = cam_x - self.width / 2 + x
            world_y = cam_y - self.height / 2 + y

            bullet = Bullet(
                self.player.center_x,
                self.player.center_y,
                world_x,
                world_y
            )
            self.bullet_list.append(bullet)
            arcade.play_sound(self.shoot_sound)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close()
            menu = MenuWindow()
            arcade.run()
            return

        if self.game_state == "PLAYING":
            self.keys_pressed.add(key)

        if self.game_state == "GAME_OVER" or self.game_state == "VICTORY":
            if key == arcade.key.R:
                self.setup()

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)


# ----------------------Уровень 1 ------------------------- #

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
WINDOW_CAPTION = "Джастин - телепортатор — меню"

PLAY_AREA_WIDTH = 1400
PLAY_AREA_HEIGHT = 750

MAP_WIDTH = 3000
MAP_HEIGHT = 750

GAME_CAPTION = "Спрайтовый герой"
ENEMY_SPAWN_RATE = 0.7

CAMERA_SMOOTHING = 0.12


class Orientation(enum.Enum):
    LEFT = 0
    RIGHT = 1


class Player(arcade.Sprite):
    """Герой с физикой как в первом файле (ручное управление, гравитация, коллизии)."""

    def __init__(self):
        super().__init__()

        self.scale = 1.0
        self.movement_speed = 300
        self.hit_points = 100
        self.max_hit_points = 100

        self.stationary_texture = arcade.load_texture(
            ":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.texture = self.stationary_texture

        self.moving_textures = []
        for i in range(0, 8):
            texture = arcade.load_texture(
                f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.moving_textures.append(texture)

        self.current_frame = 0
        self.frame_timer = 0
        self.frame_delay = 0.1

        self.is_moving = False
        self.facing = Orientation.RIGHT

        self.center_x = 100
        self.center_y = 130

        self.vertical_velocity = 0
        self.gravity_force = 0.5
        self.jump_force = 12
        self.can_jump_flag = True

        self.is_active = True

        # Время неуязвимости после получения урона
        self.invulnerability_timer = 0
        self.invulnerability_period = 1.0
        self.damage_effect_timer = 0

        self.game_ref = None

    def update_animation(self, delta_time: float = 1 / 60):
        if not self.is_active:
            return

        # Обновление времени неуязвимости
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= delta_time
            self.damage_effect_timer += delta_time
        else:
            self.damage_effect_timer = 0

        if self.is_moving:
            self.frame_timer += delta_time
            if self.frame_timer >= self.frame_delay:
                self.frame_timer = 0
                self.current_frame += 1
                if self.current_frame >= len(self.moving_textures):
                    self.current_frame = 0
                if self.facing == Orientation.RIGHT:
                    self.texture = self.moving_textures[self.current_frame]
                else:
                    self.texture = self.moving_textures[self.current_frame].flip_horizontally()
        else:
            if self.facing == Orientation.RIGHT:
                self.texture = self.stationary_texture
            else:
                self.texture = self.stationary_texture.flip_horizontally()

    def update(self, delta_time, pressed_keys):
        if not self.is_active:
            return

        # 1. Вычисляем желаемое перемещение от клавиш
        dx, dy = 0, 0
        if arcade.key.LEFT in pressed_keys or arcade.key.A in pressed_keys:
            dx -= self.movement_speed * delta_time
        if arcade.key.RIGHT in pressed_keys or arcade.key.D in pressed_keys:
            dx += self.movement_speed * delta_time

        # 2. Гравитация
        self.vertical_velocity -= self.gravity_force

        # 3. Прыжок
        if arcade.key.SPACE in pressed_keys and self.can_jump_flag:
            self.vertical_velocity = self.jump_force
            self.can_jump_flag = False

        dy = self.vertical_velocity

        # 4. Коррекция диагонального движения
        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        # 5. Движение по X с проверкой коллизий
        old_x = self.center_x
        self.center_x += dx
        if self.game_ref:
            # Горизонтальные столкновения
            hit_list = arcade.check_for_collision_with_list(self, self.game_ref.obstacle_list)
            if hit_list:
                self.center_x = old_x

        # 6. Движение по Y с проверкой коллизий
        old_y = self.center_y
        self.center_y += dy
        if self.game_ref:
            # Вертикальные столкновения
            hit_list = arcade.check_for_collision_with_list(self, self.game_ref.obstacle_list)
            if hit_list:
                # Определяем направление движения
                if dy > 0:  # движение вверх
                    # Корректируем позицию так, чтобы верх персонажа не заходил в платформу
                    for platform in hit_list:
                        if self.top > platform.bottom:
                            self.top = platform.bottom - 1
                    self.vertical_velocity = 0
                elif dy < 0:  # движение вниз
                    # Корректируем позицию так, чтобы низ персонажа стоял на платформе
                    for platform in hit_list:
                        if self.bottom < platform.top:
                            self.bottom = platform.top + 1
                            self.can_jump_flag = True
                    self.vertical_velocity = 0
            else:
                # Если нет коллизий при движении вниз, то мы в воздухе
                if dy < 0:
                    self.can_jump_flag = False

        # 7. Ограничение границами мира
        self.center_x = max(self.width / 2, min(MAP_WIDTH - self.width / 2, self.center_x))
        self.center_y = max(self.height / 2, min(MAP_HEIGHT - self.height / 2, self.center_y))

        # 8. Направление и анимация ходьбы
        if dx < 0:
            self.facing = Orientation.LEFT
        elif dx > 0:
            self.facing = Orientation.RIGHT

        self.is_moving = dx != 0

    def receive_damage(self, damage_amount):
        if self.invulnerability_timer <= 0 and self.is_active:
            self.hit_points -= damage_amount
            self.invulnerability_timer = self.invulnerability_period
            if self.hit_points <= 0:
                self.hit_points = 0
                self.is_active = False
            return True
        return False


class Projectile(arcade.Sprite):
    """Пуля, летящая в сторону курсора."""

    def __init__(self, start_x, start_y, target_x, target_y, projectile_speed=800, impact_damage=10):
        super().__init__()
        self.texture = arcade.load_texture(":resources:/images/space_shooter/laserBlue01.png")
        self.center_x = start_x
        self.center_y = start_y
        self.projectile_speed = projectile_speed
        self.impact_damage = impact_damage

        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)
        self.change_x = math.cos(angle) * projectile_speed
        self.change_y = math.sin(angle) * projectile_speed
        self.angle = math.degrees(-angle)

    def update(self, delta_time):
        if (self.center_x < -100 or self.center_x > MAP_WIDTH + 100 or
                self.center_y < -100 or self.center_y > MAP_HEIGHT + 100):
            self.remove_from_sprite_lists()
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time


class EnemyBee(arcade.Sprite):
    """Пчела, которая летает за игроком."""

    def __init__(self, target_player):
        super().__init__()
        self.target_player = target_player

        self.original_bee_texture = arcade.load_texture(":resources:images/enemies/bee.png")
        self.mirrored_bee_texture = self.original_bee_texture.flip_horizontally()
        self.texture = self.original_bee_texture
        self.scale = 0.4

        self.center_x = random.randint(50, MAP_WIDTH - 50)
        self.center_y = MAP_HEIGHT + 50

        self.flying_speed = 375

    def update(self, delta_time):
        if not self.target_player or not self.target_player.is_active:
            return

        dx = self.target_player.center_x - self.center_x
        dy = self.target_player.center_y - self.center_y
        distance = math.hypot(dx, dy)
        if distance > 0:
            self.center_x += (dx / distance) * self.flying_speed * delta_time
            self.center_y += (dy / distance) * self.flying_speed * delta_time

            if dx > 0:
                self.texture = self.mirrored_bee_texture
            else:
                self.texture = self.original_bee_texture


class GameLevel3(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.BARN_RED)

        self.world_view = Camera2D()
        self.ui_view = Camera2D()
        self.victory_sound = arcade.load_sound(":resources:/sounds/upgrade1.wav")

    def initialize_level(self):
        self.character_list = arcade.SpriteList()
        self.ground_list = arcade.SpriteList()
        self.crate_list = arcade.SpriteList()
        self.shot_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        self.main_character = Player()
        self.main_character.game_ref = self  # даём ссылку на игру для доступа к platforms_list
        self.character_list.append(self.main_character)

        self.fire_sound = arcade.load_sound(":resources:/sounds/laser1.wav")
        self.impact_sound = arcade.load_sound(":resources:/sounds/hit1.wav")
        self.defeat_sound = arcade.load_sound(":resources:/sounds/gameover1.wav")
        self.collect_sound = arcade.load_sound(":resources:/sounds/coin1.wav")

        self.active_keys = set()

        # Платформы
        for x in range(0, MAP_WIDTH, 64):
            ground_tile = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.5)
            ground_tile.center_x = x
            ground_tile.center_y = 32
            self.ground_list.append(ground_tile)

        crate_positions = []
        for x in range(900, 1900, 64):
            crate_positions.append((x, 100))
        for x in range(964, 1836, 64):
            crate_positions.append((x, 164))

        for x, y in crate_positions:
            crate = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
            crate.center_x = x
            crate.center_y = y
            self.crate_list.append(crate)

        self.obstacle_list = arcade.SpriteList()
        self.obstacle_list.extend(self.ground_list)
        self.obstacle_list.extend(self.crate_list)

        self.enemy_spawn_clock = 0.0
        self.player_score = 0
        self.current_game_state = "PLAYING"
        self.game_over_audio_played = False

        self.victory_target = 50
        self.defeated_enemies = 0

        # Номер уровня
        self.level_number = 1

    def on_draw(self):
        self.clear()
        self.world_view.use()
        self.ground_list.draw()
        self.crate_list.draw()
        self.character_list.draw()
        self.shot_list.draw()
        self.enemy_list.draw()
        self.ui_view.use()

        arcade.draw_text(f"Счёт: {self.player_score}", 10, self.height - 30,
                         arcade.color.WHITE, 20)

        remaining = max(0, self.victory_target - self.defeated_enemies)
        arcade.draw_text(f"Осталось пчёл: {remaining}", 10, self.height - 60,
                         arcade.color.WHITE, 20)

        if self.current_game_state == "GAME_OVER":
            arcade.draw_lrbt_rectangle_filled(0, self.width, 0, self.height,
                                              (0, 0, 0, 180))
            arcade.draw_text("GAME OVER", self.width // 2, self.height // 2 + 50,
                             arcade.color.RED, 50, anchor_x="center")
            arcade.draw_text(f"Final Score: {self.player_score}", self.width // 2, self.height // 2,
                             arcade.color.WHITE, 30, anchor_x="center")
            arcade.draw_text("Press R to Restart or ESC to Exit", self.width // 2,
                             self.height // 2 - 50, arcade.color.YELLOW, 20, anchor_x="center")

        if self.current_game_state == "VICTORY":
            arcade.draw_lrbt_rectangle_filled(0, self.width, 0, self.height,
                                              (0, 100, 0, 180))
            arcade.draw_text("ПОБЕДА!", self.width // 2, self.height // 2 + 50,
                             arcade.color.GOLD, 50, anchor_x="center")
            arcade.draw_text("ВЫ ПРОШЛИ УРОВЕНЬ 1!", self.width // 2, self.height // 2,
                             arcade.color.WHITE, 30, anchor_x="center")
            arcade.draw_text(f"Final Score: {self.player_score}", self.width // 2, self.height // 2 - 40,
                             arcade.color.YELLOW, 25, anchor_x="center")
            arcade.draw_text("Возврат в меню...", self.width // 2,
                             self.height // 2 - 80, arcade.color.YELLOW, 20, anchor_x="center")

    def on_update(self, delta_time):
        global unlocked_levels, completed_levels

        if self.current_game_state != "PLAYING":
            # Если победа, разблокируем следующий уровень и отмечаем текущий как пройденный
            if self.current_game_state == "VICTORY":
                if self.level_number not in completed_levels:
                    completed_levels.append(self.level_number)
                next_level = self.level_number + 1
                if next_level <= 3 and next_level not in unlocked_levels:
                    unlocked_levels.append(next_level)

                # Возврат в меню после победы
                arcade.pause(1.5)
                self.close()
                menu = MenuWindow()
                arcade.run()
                return
            return

        # Обновление игрока (ручная физика)
        if self.main_character.is_active:
            self.main_character.update(delta_time, self.active_keys)
            self.main_character.update_animation(delta_time)
        else:
            self.current_game_state = "GAME_OVER"
            if not self.game_over_audio_played:
                arcade.play_sound(self.defeat_sound)
                self.game_over_audio_played = True
            return

        # Пули
        self.shot_list.update(delta_time)

        # Столкновения пуль с монстрами
        for projectile in self.shot_list:
            enemies_hit = arcade.check_for_collision_with_list(projectile, self.enemy_list)
            if enemies_hit:
                projectile.remove_from_sprite_lists()
                for enemy in enemies_hit:
                    enemy.remove_from_sprite_lists()
                    self.player_score += 20
                    self.defeated_enemies += 1
                    arcade.play_sound(self.impact_sound)

                if self.defeated_enemies >= self.victory_target:
                    self.current_game_state = "VICTORY"
                    arcade.play_sound(self.victory_sound)

        # Пули о платформы
        for projectile in self.shot_list:
            if arcade.check_for_collision_with_list(projectile, self.obstacle_list):
                projectile.remove_from_sprite_lists()

        # Монстры
        for enemy in self.enemy_list:
            enemy.update(delta_time)

        # Столкновение героя с монстрами (с учётом здоровья)
        if self.main_character.is_active:
            if arcade.check_for_collision_with_list(self.main_character, self.enemy_list):
                self.main_character.is_active = False
                self.current_game_state = "GAME_OVER"

        # Спавн монстров
        if self.current_game_state == "PLAYING":
            self.enemy_spawn_clock += delta_time
            if self.enemy_spawn_clock >= ENEMY_SPAWN_RATE:
                new_enemy = EnemyBee(self.main_character)
                self.enemy_list.append(new_enemy)
                self.enemy_spawn_clock = 0.0

        # Камера
        if self.main_character.is_active:
            target_x = self.main_character.center_x
            target_y = self.main_character.center_y
        else:
            target_x, target_y = self.world_view.position

        current_x, current_y = self.world_view.position
        smooth_x = current_x + (target_x - current_x) * CAMERA_SMOOTHING
        smooth_y = current_y + (target_y - current_y) * CAMERA_SMOOTHING

        half_w = self.world_view.viewport_width / 2
        half_h = self.world_view.viewport_height / 2
        cam_x = max(half_w, min(MAP_WIDTH - half_w, smooth_x))
        cam_y = max(half_h, min(MAP_HEIGHT - half_h, smooth_y))

        self.world_view.position = (cam_x, cam_y)
        self.ui_view.position = (self.width / 2, self.height / 2)

    def on_mouse_press(self, x, y, button, modifiers):
        if (button == arcade.MOUSE_BUTTON_LEFT and
                self.current_game_state == "PLAYING" and
                self.main_character.is_active):
            cam_x, cam_y = self.world_view.position
            world_x = cam_x - self.width / 2 + x
            world_y = cam_y - self.height / 2 + y

            new_shot = Projectile(
                self.main_character.center_x,
                self.main_character.center_y,
                world_x,
                world_y
            )
            self.shot_list.append(new_shot)
            arcade.play_sound(self.fire_sound)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close()
            menu = MenuWindow()
            arcade.run()
            return

        if self.current_game_state == "PLAYING":
            self.active_keys.add(key)

        if self.current_game_state in ["GAME_OVER", "VICTORY"] and key == arcade.key.R:
            self.initialize_level()

    def on_key_release(self, key, modifiers):
        if key in self.active_keys:
            self.active_keys.remove(key)


SHIRINA_EKRANA = 1000
VYSOTA_EKRANA = 600
ZAGOLOVOK_EKRANA = "Джастин - телепортатор — меню"

SHIRINA_IGRY = 1400
VYSOTA_IGRY = 750

SHIRINA_MIRA = 3000
VYSOTA_MIRA = 750

NAZVANIE_UROVNYA2 = "Спрайтовый герой - Уровень 2"
INTERVAL_POYAVLENIYA_MONSTROV = 3.5
SKOROST_KAMERY = 0.12


class NapravlenieLica(enum.Enum):
    VLEVO = 0
    VPRAVO = 1


class Geroy(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.masshtab = 1.0
        self.skorost = 5
        self.zdorovie = 100
        self.max_zdorovie = 100

        self.change_x = 0
        self.change_y = 0

        self.tekstura_pokoya = arcade.load_texture(
            ":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.texture = self.tekstura_pokoya

        self.tekstury_hodby = []
        for i in range(0, 8):
            tekstura = arcade.load_texture(f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.tekstury_hodby.append(tekstura)

        self.nomer_tekstury = 0
        self.vremya_smeny_tekstury = 0
        self.zaderzhka_smeny_tekstury = 0.1

        self.idet = False
        self.napravlenie = NapravlenieLica.VPRAVO

        self.center_x = 100
        self.center_y = 130

        self.gravitaciya = 0.5
        self.sila_pryzhka = 12
        self.mozhet_prygnut = True

        self.zhiv = True
        self.vremya_do_smerti = 0
        self.smert_aktivirovana = False

        self.vremya_nezashchity = 0
        self.dlitelnost_nezashchity = 1.0
        self.vremya_effekta_udara = 0

    def obnovit_animaciyu(self, delta_time: float = 1 / 60):
        # Обновление анимации героя (ходьба/покой, неуязвимость, смерть)
        if not self.zhiv and self.vremya_do_smerti <= 0:
            return

        if self.vremya_nezashchity > 0:
            self.vremya_nezashchity -= delta_time
            self.vremya_effekta_udara += delta_time
        else:
            self.vremya_effekta_udara = 0

        if self.smert_aktivirovana and self.zhiv:
            self.vremya_do_smerti -= delta_time
            if self.vremya_do_smerti <= 0:
                self.zhiv = False
                self.smert_aktivirovana = False

        if self.idet:
            self.vremya_smeny_tekstury += delta_time
            if self.vremya_smeny_tekstury >= self.zaderzhka_smeny_tekstury:
                self.vremya_smeny_tekstury = 0
                self.nomer_tekstury += 1
                if self.nomer_tekstury >= len(self.tekstury_hodby):
                    self.nomer_tekstury = 0
                if self.napravlenie == NapravlenieLica.VPRAVO:
                    self.texture = self.tekstury_hodby[self.nomer_tekstury]
                else:
                    self.texture = self.tekstury_hodby[self.nomer_tekstury].flip_horizontally()
        else:
            if self.napravlenie == NapravlenieLica.VPRAVO:
                self.texture = self.tekstura_pokoya
            else:
                self.texture = self.tekstura_pokoya.flip_horizontally()

    def obnovit_skorost(self, nazhatye_klavishi):
        if not self.zhiv and self.vremya_do_smerti <= 0:
            return

        if arcade.key.LEFT in nazhatye_klavishi or arcade.key.A in nazhatye_klavishi:
            self.change_x = -self.skorost
            self.napravlenie = NapravlenieLica.VLEVO
            self.idet = True
        elif arcade.key.RIGHT in nazhatye_klavishi or arcade.key.D in nazhatye_klavishi:
            self.change_x = self.skorost
            self.napravlenie = NapravlenieLica.VPRAVO
            self.idet = True
        else:
            self.change_x = 0
            self.idet = False

        if arcade.key.SPACE in nazhatye_klavishi and self.mozhet_prygnut:
            self.change_y = self.sila_pryzhka
            self.mozhet_prygnut = False

    def poluchit_uron(self, uron):
        # получения урона героем
        if self.vremya_nezashchity <= 0 and self.zhiv and not self.smert_aktivirovana:
            self.zdorovie -= uron
            self.vremya_nezashchity = self.dlitelnost_nezashchity

            if self.zdorovie <= 0:
                self.zdorovie = 0
                self.smert_aktivirovana = True
                self.vremya_do_smerti = 2.0
                return True
        return False


#пуля
class Pulya(arcade.Sprite):
    def __init__(self, start_x, start_y, cel_x, cel_y, skorost=800, uron=10):
        super().__init__()
        self.texture = arcade.load_texture(":resources:/images/space_shooter/laserBlue01.png")
        self.center_x = start_x
        self.center_y = start_y
        self.skorost = skorost
        self.uron = uron

        raznost_x = cel_x - start_x
        raznost_y = cel_y - start_y
        ugol = math.atan2(raznost_y, raznost_x)
        self.change_x = math.cos(ugol) * skorost
        self.change_y = math.sin(ugol) * skorost
        self.angle = math.degrees(-ugol)

    def update(self, delta_time):
        if (self.center_x < -100 or self.center_x > SHIRINA_MIRA + 100 or
                self.center_y < -100 or self.center_y > VYSOTA_MIRA + 100):
            self.remove_from_sprite_lists()
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time

# монстр
class LetayushchiyMonstr(arcade.Sprite):
    def __init__(self, igrok):
        super().__init__(":resources:images/enemies/slimePurple.png", scale=0.35)

        storona_poyavleniya = random.choice(['top', 'left', 'right'])
        if storona_poyavleniya == 'top':
            self.center_x = random.randint(50, SHIRINA_MIRA - 50)
            self.center_y = VYSOTA_MIRA - 50
        elif storona_poyavleniya == 'left':
            self.center_x = 50
            self.center_y = random.randint(200, VYSOTA_MIRA - 200)
        else:
            self.center_x = SHIRINA_MIRA - 50
            self.center_y = random.randint(200, VYSOTA_MIRA - 200)

        self.masshtab = 0.35
        self.igrok = igrok

        self.bazovaya_skorost = 180
        self.skorost_ataki = 280
        self.amplituda = random.randint(30, 60)
        self.chastota = random.uniform(1.5, 3.0)
        self.vremya = random.uniform(0, math.pi * 2)
        self.iznachalnaya_y = self.center_y

        self.zdorovie = 3
        self.max_zdorovie = 3

        self.atakuet = False
        self.vremya_ozhidaniya_ataki = 0
        self.vremya_effekta_udara = 0

    def poluchit_uron(self, uron):
        self.zdorovie -= uron
        self.vremya_effekta_udara = 0.2
        return self.zdorovie <= 0

    def update(self, delta_time):
        if not self.igrok or not self.igrok.zhiv:
            return

        self.vremya += delta_time

        if self.vremya_effekta_udara > 0:
            self.vremya_effekta_udara -= delta_time

        if self.vremya_ozhidaniya_ataki > 0:
            self.vremya_ozhidaniya_ataki -= delta_time

        raznost_x = self.igrok.center_x - self.center_x
        raznost_y = self.igrok.center_y - self.center_y
        rasstoyanie = math.sqrt(raznost_x * raznost_x + raznost_y * raznost_y)

        if rasstoyanie < 350 and self.vremya_ozhidaniya_ataki <= 0:
            self.atakuet = True
        elif rasstoyanie > 450:
            self.atakuet = False

        if self.atakuet:
            if rasstoyanie > 50:
                if rasstoyanie > 0:
                    napravlenie_x = raznost_x / rasstoyanie
                    napravlenie_y = raznost_y / rasstoyanie
                    self.center_x += napravlenie_x * self.skorost_ataki * delta_time
                    self.center_y += napravlenie_y * self.skorost_ataki * delta_time
            if rasstoyanie < 100:
                self.atakuet = False
                self.vremya_ozhidaniya_ataki = 2.0
        else:
            if abs(raznost_x) > 150:
                napravlenie = 1 if raznost_x > 0 else -1
                self.center_x += napravlenie * self.bazovaya_skorost * delta_time
            self.center_y = self.iznachalnaya_y + math.sin(self.vremya * self.chastota) * self.amplituda
            self.iznachalnaya_y += (self.igrok.center_y - self.iznachalnaya_y) * 0.01 * delta_time * 60

        self.center_x = max(20, min(SHIRINA_MIRA - 20, self.center_x))
        self.center_y = max(20, min(VYSOTA_MIRA - 20, self.center_y))

        if raznost_x > 0:
            self.texture = self.texture
        else:
            self.texture = self.texture.flip_horizontally()


# (синий слизень) - появляется сверху, прыгает к игроку
class BystryyMonstr(arcade.Sprite):
    def __init__(self, igrok):
        super().__init__(":resources:images/enemies/slimeBlue.png", scale=0.4)
        self.center_x = random.randint(50, SHIRINA_MIRA - 50)
        self.center_y = VYSOTA_MIRA + 50

        self.change_y = -2
        self.change_x = 0
        self.skorost = 220
        self.igrok = igrok
        self.na_zemle = False
        self.gravitaciya = 0.5

        self.zdorovie = 1
        self.vremya_effekta_udara = 0

        self.tekstura_pokoya = arcade.load_texture(":resources:images/enemies/slimeBlue.png")
        self.texture = self.tekstura_pokoya

        self.roditel = None

    def poluchit_uron(self, uron):
        self.zdorovie -= uron
        self.vremya_effekta_udara = 0.2
        return self.zdorovie <= 0

    def update(self, delta_time):
        if self.vremya_effekta_udara > 0:
            self.vremya_effekta_udara -= delta_time

        self.change_y -= self.gravitaciya * delta_time * 60
        self.center_y += self.change_y * delta_time * 60

        if self.change_y < 0:
            samaya_vysokaya_platforma = -float('inf')
            prizemlilsya = False

            if self.roditel and hasattr(self.roditel, 'spisok_platform'):
                for platforma in self.roditel.spisok_platform:
                    if (self.right > platforma.left and
                            self.left < platforma.right):
                        sleduyushchiy_niz = self.center_y - self.height / 2 + self.change_y * delta_time * 60
                        if sleduyushchiy_niz <= platforma.top <= self.bottom:
                            if platforma.top > samaya_vysokaya_platforma:
                                samaya_vysokaya_platforma = platforma.top
                                prizemlilsya = True

                if prizemlilsya:
                    self.bottom = samaya_vysokaya_platforma + 1
                    self.change_y = 0
                    self.na_zemle = True

        if self.igrok and self.igrok.zhiv:
            raznost_x = self.igrok.center_x - self.center_x
            rasstoyanie = abs(raznost_x)

            if self.na_zemle:
                if rasstoyanie < 250:
                    self.change_y = 16
                    self.na_zemle = False

            # Движение монстра в сторону игрока по горизонтали
            if rasstoyanie > 5:
                napravlenie = 1 if raznost_x > 0 else -1
                dvizhenie = napravlenie * self.skorost * delta_time
                staraya_x = self.center_x
                self.center_x += dvizhenie

                # откат позиции если врезался
                if self.roditel and hasattr(self.roditel, 'spisok_platform'):
                    for platforma in self.roditel.spisok_platform:
                        if arcade.check_for_collision(self, platforma):
                            self.center_x = staraya_x
                            break

                if napravlenie > 0:
                    self.texture = self.tekstura_pokoya
                else:
                    self.texture = self.tekstura_pokoya.flip_horizontally()


#звездочка аптечка
class Aptechka(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(":resources:images/items/star.png", scale=0.5)
        self.center_x = x
        self.center_y = y
        self.kolichestvo_lecheniya = 25
        self.vremya = 0
        self.amplituda_parreniya = 5
        self.skorost_parreniya = 2

    def update(self, delta_time):
        self.vremya += delta_time
        self.center_y += math.sin(self.vremya * self.skorost_parreniya) * self.amplituda_parreniya * delta_time * 30

#патрон
class Patrony(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(":resources:images/items/gemBlue.png", scale=0.5)
        self.center_x = x
        self.center_y = y
        self.kolichestvo_patronov = 10
        self.skorost_vrashcheniya = 2
        self.vremya = 0

    def update(self, delta_time):
        self.vremya += delta_time
        self.angle += self.skorost_vrashcheniya * delta_time * 60

#финал
class FlagFinish(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(":resources:images/items/flagGreen1.png", scale=0.8)
        self.center_x = x
        self.center_y = y
        self.vremya = 0
        self.amplituda_volny = 5
        self.skorost_volny = 3

    def update(self, delta_time):
        self.vremya += delta_time
        self.center_y += math.sin(self.vremya * self.skorost_volny) * self.amplituda_volny * delta_time * 30


class IgraUroven2(arcade.Window):
    def __init__(self, shirina, vysota, nazvanie):
        super().__init__(shirina, vysota, nazvanie)
        arcade.set_background_color(arcade.color.DARK_GREEN)

        self.kamera_mira = Camera2D()
        self.kamera_gui = Camera2D()

        self.sostoyanie_igry = "PLAYING"

        self.zvuk_udara = arcade.load_sound(":resources:/sounds/hit1.wav")
        self.zvuk_podbora = arcade.load_sound(":resources:/sounds/coin1.wav")
        self.zvuk_proigrysha = arcade.load_sound(":resources:/sounds/gameover1.wav")
        self.zvuk_pobedy = arcade.load_sound(":resources:/sounds/upgrade1.wav")

    def setup(self):
        self.spisok_geroya = arcade.SpriteList()
        self.spisok_sten = arcade.SpriteList()
        self.spisok_yashchikov = arcade.SpriteList()
        self.spisok_pul = arcade.SpriteList()
        self.spisok_monstrov = arcade.SpriteList()
        self.spisok_aptechek = arcade.SpriteList()
        self.spisok_patronov = arcade.SpriteList()
        self.spisok_flaga = arcade.SpriteList()

        self.geroy = Geroy()
        self.geroy.center_x = 100
        self.geroy.center_y = 130
        self.spisok_geroya.append(self.geroy)

        for x in range(0, SHIRINA_MIRA, 64):
            stena = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.5)
            stena.center_x = x
            stena.center_y = 32
            self.spisok_sten.append(stena)

        pozitsii_platform = [
            (300, 150), (500, 200), (700, 250), (900, 300),
            (1100, 350), (1300, 400), (1500, 350), (1700, 300),
            (1900, 250), (2100, 200), (2300, 150), (2500, 100),
            (400, 400), (800, 450), (1200, 500), (1600, 450),
            (2000, 400), (2400, 350), (2800, 300)
        ]

        for pozitsiya in pozitsii_platform:
            platforma = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
            platforma.center_x = pozitsiya[0]
            platforma.center_y = pozitsiya[1]
            self.spisok_yashchikov.append(platforma)

        for i in range(8):
            yashchik = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", 0.5)
            yashchik.center_x = random.randint(1200, 2800)
            yashchik.center_y = random.randint(80, 200)
            self.spisok_yashchikov.append(yashchik)

        for i in range(10):
            ship = arcade.Sprite(":resources:images/tiles/grassHill_right.png", 0.5)
            ship.center_x = random.randint(500, 2800)
            ship.center_y = 60
            ship.angle = 180
            self.spisok_sten.append(ship)

        self.zvuk_vystrela = arcade.load_sound(":resources:/sounds/laser1.wav")
        self.nazhatye_klavishi = set()

        self.spisok_platform = arcade.SpriteList()
        self.spisok_platform.extend(self.spisok_sten)
        self.spisok_platform.extend(self.spisok_yashchikov)

        self.fizika = arcade.PhysicsEnginePlatformer(
            self.geroy,
            platforms=self.spisok_platform,
            gravity_constant=0.5
        )

        flag = FlagFinish(SHIRINA_MIRA - 200, 150)
        self.spisok_flaga.append(flag)

        self.tsel_ubijstv = 25
        self.finish_dostig = False

        self.taymer_poyavleniya_monstrov = 0.0
        self.taymer_poyavleniya_letayushchih = 0.0
        self.taymer_poyavleniya_aptechek = 0.0
        self.taymer_poyavleniya_patronov = 0.0
        self.schet = 0
        self.kolichestvo_patronov = 30
        self.schetchik_ubijstv = 0
        self.schetchik_voln = 0
        self.vremya_igry = 0
        self.sostoyanie_igry = "PLAYING"

        self.zvuk_proigrysha_sygra = False

        self.level_number = 2

#Отрисовка всех элементов игры
    def on_draw(self):
        self.clear()

        self.kamera_mira.use()

        self.spisok_sten.draw()
        self.spisok_yashchikov.draw()
        self.spisok_flaga.draw()
        self.spisok_aptechek.draw()
        self.spisok_patronov.draw()

        if self.geroy.zhiv or self.geroy.vremya_do_smerti > 0:
            self.spisok_geroya.draw()

        self.spisok_pul.draw()
        self.spisok_monstrov.draw()

        self.kamera_gui.use()

        if self.geroy.smert_aktivirovana:
            tekst_zdorovya = f"❤️ 0/{self.geroy.max_zdorovie} (Смерть через {self.geroy.vremya_do_smerti:.1f}с)"
            arcade.draw_text(tekst_zdorovya, 10, VYSOTA_IGRY - 30, arcade.color.RED, 20)

            arcade.draw_text("⚠️ СМЕРТЕЛЬНО РАНЕН ⚠️",
                             SHIRINA_IGRY // 2, VYSOTA_IGRY // 2 + 50,
                             arcade.color.RED, 30, anchor_x="center")
        else:
            tekst_zdorovya = f"❤️ {self.geroy.zdorovie}/{self.geroy.max_zdorovie}"
            arcade.draw_text(tekst_zdorovya, 10, VYSOTA_IGRY - 30, arcade.color.RED, 20)

        tekst_patronov = f"🔫 {self.kolichestvo_patronov}"
        arcade.draw_text(tekst_patronov, 10, VYSOTA_IGRY - 60, arcade.color.YELLOW, 20)

        arcade.draw_text(f"Счет: {self.schet}", 200, VYSOTA_IGRY - 30, arcade.color.WHITE, 20)
        arcade.draw_text(f"Убийств: {self.schetchik_ubijstv}/{self.tsel_ubijstv}", 200, VYSOTA_IGRY - 60,
                         arcade.color.WHITE, 16)

        minuty = int(self.vremya_igry) // 60
        sekundy = int(self.vremya_igry) % 60
        tekst_vremeni = f"Время: {minuty:02d}:{sekundy:02d}"
        arcade.draw_text(tekst_vremeni, SHIRINA_IGRY - 200, VYSOTA_IGRY - 30, arcade.color.CYAN, 16)

        arcade.draw_text("УРОВЕНЬ 2 - ЛЕТАЮЩИЕ МОНСТРЫ", 10, VYSOTA_IGRY - 90, arcade.color.YELLOW, 16)

        if not self.finish_dostig and (self.geroy.zhiv or self.geroy.smert_aktivirovana):
            rasstoyanie_do_finisha = SHIRINA_MIRA - 200 - self.geroy.center_x
            if rasstoyanie_do_finisha > 0:
                arcade.draw_text(f"До финиша: {int(rasstoyanie_do_finisha)}м",
                                 SHIRINA_IGRY - 200, VYSOTA_IGRY - 90,
                                 arcade.color.LIGHT_GREEN, 16)

        if self.sostoyanie_igry == "GAME_OVER":
            arcade.draw_lrbt_rectangle_filled(0, self.width, 0, self.height, (0, 0, 0, 180))

            arcade.draw_text("ВЫ ПРОИГРАЛИ!",
                             self.width // 2, self.height // 2 + 100,
                             arcade.color.RED, 60, anchor_x="center",
                             font_name="Kenney Pixel")

            arcade.draw_text(f"Счет: {self.schet}",
                             self.width // 2, self.height // 2 + 20,
                             arcade.color.WHITE, 30, anchor_x="center")

            arcade.draw_text(f"Убито монстров: {self.schetchik_ubijstv}",
                             self.width // 2, self.height // 2 - 20,
                             arcade.color.WHITE, 25, anchor_x="center")

            arcade.draw_text(f"Время выживания: {minuty:02d}:{sekundy:02d}",
                             self.width // 2, self.height // 2 - 60,
                             arcade.color.CYAN, 25, anchor_x="center")

            arcade.draw_text("Нажми R для рестарта",
                             self.width // 2, self.height // 2 - 120,
                             arcade.color.YELLOW, 20, anchor_x="center")

            arcade.draw_text("ESC для выхода в меню",
                             self.width // 2, self.height // 2 - 150,
                             arcade.color.ORANGE, 20, anchor_x="center")

        elif self.sostoyanie_igry == "VICTORY":
            arcade.draw_lrbt_rectangle_filled(0, self.width, 0, self.height, (255, 215, 0, 100))

            arcade.draw_text("ПОБЕДА!",
                             self.width // 2, self.height // 2 + 120,
                             arcade.color.GOLD, 70, anchor_x="center",
                             font_name="Kenney Pixel")

            arcade.draw_text("ВЫ ПРОШЛИ УРОВЕНЬ 2!",
                             self.width // 2, self.height // 2 + 50,
                             arcade.color.WHITE, 30, anchor_x="center")

            arcade.draw_text(f"Итоговый счет: {self.schet}",
                             self.width // 2, self.height // 2,
                             arcade.color.YELLOW, 35, anchor_x="center")

            arcade.draw_text(f"Уничтожено монстров: {self.schetchik_ubijstv}",
                             self.width // 2, self.height // 2 - 40,
                             arcade.color.WHITE, 25, anchor_x="center")

            arcade.draw_text(f"Время прохождения: {minuty:02d}:{sekundy:02d}",
                             self.width // 2, self.height // 2 - 80,
                             arcade.color.CYAN, 25, anchor_x="center")

            arcade.draw_text("Возврат в меню...",
                             self.width // 2, self.height // 2 - 120,
                             arcade.color.YELLOW, 20, anchor_x="center")

    def on_update(self, delta_time):
        global unlocked_levels, completed_levels

        if self.sostoyanie_igry != "PLAYING":
            # Если победа, разблокируем следующий уровень и отмечаем текущий как пройденный
            if self.sostoyanie_igry == "VICTORY":
                if self.level_number not in completed_levels:
                    completed_levels.append(self.level_number)
                next_level = self.level_number + 1
                if next_level <= 3 and next_level not in unlocked_levels:
                    unlocked_levels.append(next_level)

                # Возврат в меню после победы
                arcade.pause(1.5)
                self.close()
                menu = MenuWindow()
                arcade.run()
                return
            return

        self.vremya_igry += delta_time

        self.spisok_flaga.update(delta_time)

        self.fizika.update()
        # Обновление состояния героя (движение, анимация, проверка достижения флага)
        # Если герой мертв - переключение в состояние GAME_OVER
        # Обновление пуль, аптечек и патронов
        if self.geroy.zhiv or self.geroy.smert_aktivirovana:
            self.geroy.obnovit_skorost(self.nazhatye_klavishi)
            self.geroy.obnovit_animaciyu(delta_time)
            self.geroy.mozhet_prygnut = self.fizika.can_jump()

            self.geroy.center_x = max(self.geroy.width / 2,
                                      min(SHIRINA_MIRA - self.geroy.width / 2,
                                          self.geroy.center_x))

            if self.spisok_flaga and not self.finish_dostig:
                flag_hits = arcade.check_for_collision_with_list(self.geroy, self.spisok_flaga)
                if flag_hits and (self.geroy.zhiv or self.geroy.smert_aktivirovana):
                    self.finish_dostig = True
                    self.sostoyanie_igry = "VICTORY"
                    arcade.play_sound(self.zvuk_pobedy)
                    return
        else:
            self.sostoyanie_igry = "GAME_OVER"
            if not self.zvuk_proigrysha_sygra:
                arcade.play_sound(self.zvuk_proigrysha)
                self.zvuk_proigrysha_sygra = True
            return

        self.spisok_pul.update(delta_time)
        self.spisok_aptechek.update(delta_time)
        self.spisok_patronov.update(delta_time)

        aptechki_podobrany = arcade.check_for_collision_with_list(self.geroy, self.spisok_aptechek)
        for aptechka in aptechki_podobrany:
            if self.geroy.zhiv and not self.geroy.smert_aktivirovana:
                self.geroy.zdorovie = min(self.geroy.zdorovie + aptechka.kolichestvo_lecheniya, self.geroy.max_zdorovie)
                aptechka.remove_from_sprite_lists()
                arcade.play_sound(self.zvuk_podbora)

        patrony_podobrany = arcade.check_for_collision_with_list(self.geroy, self.spisok_patronov)
        for patron in patrony_podobrany:
            if self.geroy.zhiv or self.geroy.smert_aktivirovana:
                self.kolichestvo_patronov += patron.kolichestvo_patronov
                patron.remove_from_sprite_lists()
                arcade.play_sound(self.zvuk_podbora)

        for pulya in self.spisok_pul:
            monstr_popali = arcade.check_for_collision_with_list(pulya, self.spisok_monstrov)
            if monstr_popali:
                pulya.remove_from_sprite_lists()
                for monstr in monstr_popali:
                    if hasattr(monstr, 'poluchit_uron'):
                        if monstr.poluchit_uron(pulya.uron):
                            monstr.remove_from_sprite_lists()
                            self.schet += 20 if isinstance(monstr, LetayushchiyMonstr) else 15
                            self.schetchik_ubijstv += 1
                            arcade.play_sound(self.zvuk_udara)

                            if self.schetchik_ubijstv % 5 == 0:
                                self.schetchik_voln += 1
                    else:
                        monstr.remove_from_sprite_lists()
                        self.schet += 10
                        self.schetchik_ubijstv += 1

        for pulya in self.spisok_pul:
            if arcade.check_for_collision_with_list(pulya, self.spisok_platform):
                pulya.remove_from_sprite_lists()

        for monstr in self.spisok_monstrov:
            if arcade.check_for_collision(self.geroy, monstr) and (self.geroy.zhiv or self.geroy.smert_aktivirovana):
                if self.geroy.poluchit_uron(15):
                    arcade.play_sound(self.zvuk_udara)

        for monstr in self.spisok_monstrov:
            monstr.roditel = self
            monstr.update(delta_time)

            if monstr.center_y < -100:
                monstr.remove_from_sprite_lists()

        if self.sostoyanie_igry == "PLAYING" and (self.geroy.zhiv or self.geroy.smert_aktivirovana):
            self.taymer_poyavleniya_monstrov += delta_time
            if self.taymer_poyavleniya_monstrov >= INTERVAL_POYAVLENIYA_MONSTROV:
                for _ in range(random.randint(1, 2)):
                    monstr = BystryyMonstr(self.geroy)
                    self.spisok_monstrov.append(monstr)
                self.taymer_poyavleniya_monstrov = 0.0

            self.taymer_poyavleniya_letayushchih += delta_time
            if self.taymer_poyavleniya_letayushchih >= 4.0:
                for _ in range(random.randint(1, 2)):
                    monstr = LetayushchiyMonstr(self.geroy)
                    self.spisok_monstrov.append(monstr)
                self.taymer_poyavleniya_letayushchih = 0.0

            self.taymer_poyavleniya_aptechek += delta_time
            if self.taymer_poyavleniya_aptechek >= 20.0 and self.geroy.zdorovie < 50:
                x = random.randint(200, SHIRINA_MIRA - 200)
                y = random.randint(100, 400)
                aptechka = Aptechka(x, y)
                self.spisok_aptechek.append(aptechka)
                self.taymer_poyavleniya_aptechek = 0.0

            self.taymer_poyavleniya_patronov += delta_time
            if self.taymer_poyavleniya_patronov >= 12.0 and self.kolichestvo_patronov < 50:
                x = random.randint(200, SHIRINA_MIRA - 200)
                y = random.randint(100, 400)
                patron = Patrony(x, y)
                self.spisok_patronov.append(patron)
                self.taymer_poyavleniya_patronov = 0.0

        #  следование камеры за героем с ограничением по границам мира
        if self.geroy.zhiv or self.geroy.smert_aktivirovana:
            target = (self.geroy.center_x, self.geroy.center_y)
            cx, cy = self.kamera_mira.position
            smooth = (cx + (target[0] - cx) * SKOROST_KAMERY,
                      cy + (target[1] - cy) * SKOROST_KAMERY)

            half_w = self.kamera_mira.viewport_width / 2
            half_h = self.kamera_mira.viewport_height / 2
            kam_x = max(half_w, min(SHIRINA_MIRA - half_w, smooth[0]))
            kam_y = max(half_h, min(VYSOTA_MIRA - half_h, smooth[1]))

            self.kamera_mira.position = (kam_x, kam_y)
            self.kamera_gui.position = (SHIRINA_EKRANA / 2, VYSOTA_EKRANA / 2)

#выстрел левой кнопкой мыши
    def on_mouse_press(self, x, y, knopka, modifikatory):
        if (knopka == arcade.MOUSE_BUTTON_LEFT and
                self.sostoyanie_igry == "PLAYING" and
                (self.geroy.zhiv or self.geroy.smert_aktivirovana) and
                self.kolichestvo_patronov > 0):
            kam_x, kam_y = self.kamera_mira.position
            mir_x = kam_x - self.width / 2 + x
            mir_y = kam_y - self.height / 2 + y

            pulya = Pulya(
                self.geroy.center_x,
                self.geroy.center_y,
                mir_x,
                mir_y
            )
            self.spisok_pul.append(pulya)
            self.kolichestvo_patronov -= 1
            arcade.play_sound(self.zvuk_vystrela)

    def on_key_press(self, klavisha, modifikatory):
        if klavisha == arcade.key.ESCAPE:
            self.close()
            menu = MenuWindow()
            arcade.run()
            return

        if self.sostoyanie_igry == "PLAYING":
            self.nazhatye_klavishi.add(klavisha)

        if self.sostoyanie_igry in ["GAME_OVER", "VICTORY"]:
            if klavisha == arcade.key.R:
                self.setup()
                return

    def on_key_release(self, klavisha, modifikatory):
        if klavisha in self.nazhatye_klavishi:
            self.nazhatye_klavishi.remove(klavisha)


class MenuWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.SKY_BLUE)

        self.clouds = []
        self.buttons = []
        self.mouse_x = 0
        self.mouse_y = 0

        self.create_clouds()
        self.create_buttons()

    def create_clouds(self):
        for _ in range(6):
            self.clouds.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(350, 550),
                "speed": random.uniform(20, 60)
            })

    def update_clouds(self, delta_time):
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"] * delta_time
            if cloud["x"] > SCREEN_WIDTH + 150:
                cloud["x"] = -150
                cloud["y"] = random.randint(350, 550)

    def draw_cloud(self, x, y):
        arcade.draw_circle_filled(x, y, 40, arcade.color.WHITE)
        arcade.draw_circle_filled(x + 40, y, 50, arcade.color.WHITE)
        arcade.draw_circle_filled(x - 40, y, 50, arcade.color.WHITE)

    #кнопки
    def create_buttons(self):
        levels = ["1", "2", "3"]
        button_width = 260
        button_height = 60
        spacing = 40

        total_width = len(levels) * button_width + (len(levels) - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2 + button_width // 2
        center_y = SCREEN_HEIGHT // 2

        for i, text in enumerate(levels):
            center_x = start_x + i * (button_width + spacing)
            x = center_x - button_width // 2
            y = center_y - button_height // 2

            self.buttons.append({
                "text": text,
                "level": i + 1,
                "x": x,
                "y": y,
                "center_x": center_x,
                "center_y": center_y,
                "w": button_width,
                "h": button_height
            })

    def is_mouse_over(self, btn):
        return (
                btn["x"] < self.mouse_x < btn["x"] + btn["w"] and
                btn["y"] < self.mouse_y < btn["y"] + btn["h"]
        )

    def on_draw(self):
        global unlocked_levels, completed_levels
        self.clear()
        for cloud in self.clouds:
            self.draw_cloud(cloud["x"], cloud["y"])
        arcade.draw_text(
            "ДЖАСТИН - ТЕЛЕПОРТАТОР",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - 100,
            arcade.color.GOLD,
            44,
            anchor_x="center"
        )

        arcade.draw_text(
            "Выберите уровень для прохождения",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - 160,
            arcade.color.BLUE,
            24,
            anchor_x="center"
        )

        for btn in self.buttons:
            hovered = self.is_mouse_over(btn)
            if btn['level'] in completed_levels:
                # Пройденные уровни — зеленые
                color = arcade.color.DARK_GREEN if hovered else arcade.color.GREEN
            elif btn['level'] in unlocked_levels:
                # Доступные, но не пройденные — синие
                color = arcade.color.DARK_BLUE if hovered else arcade.color.BLUE
            else:
                # Заблокированные — серые
                color = arcade.color.GRAY if hovered else arcade.color.DARK_GRAY

            arcade.draw_lbwh_rectangle_filled(
                btn["x"],
                btn["y"],
                btn["w"],
                btn["h"],
                color
            )

            arcade.draw_lbwh_rectangle_outline(
                btn["x"],
                btn["y"],
                btn["w"],
                btn["h"],
                arcade.color.WHITE,
                3
            )

            arcade.draw_text(
                btn["text"],
                btn["center_x"],
                btn["center_y"],
                arcade.color.WHITE,
                22,
                anchor_x="center",
                anchor_y="center"
            )

            # галочка для пройденных, замок для заблокированных
            if btn['level'] in completed_levels:
                arcade.draw_text("✓", btn["center_x"] + 80, btn["center_y"],
                                 arcade.color.WHITE, 24, anchor_x="center", anchor_y="center")
            elif btn['level'] not in unlocked_levels:
                arcade.draw_text("🔒", btn["center_x"] + 80, btn["center_y"],
                                 arcade.color.WHITE, 18, anchor_x="center", anchor_y="center")

    def on_update(self, delta_time):
        self.update_clouds(delta_time)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        global unlocked_levels
        for btn in self.buttons:
            if self.is_mouse_over(btn):
                if btn['level'] in unlocked_levels:
                    print(f"Выбран уровень {btn['level']} — {btn['text']}")
                    if btn['level'] == 1:
                        self.close()
                        game = GameLevel3(GAME_WIDTH, GAME_HEIGHT, GAME_TITLE)
                        game.initialize_level()
                        arcade.run()
                    elif btn['level'] == 2:
                        self.close()
                        game = IgraUroven2(GAME_WIDTH, GAME_HEIGHT, GAME_TITLE)
                        game.setup()
                        arcade.run()
                    elif btn['level'] == 3:
                        self.close()
                        game = MyGame(GAME_WIDTH, GAME_HEIGHT, GAME_TITLE)
                        game.setup()
                        arcade.run()
                else:
                    print(f"Уровень {btn['level']} заблокирован. Сначала пройдите предыдущий уровень.")


def main():
    MenuWindow()
    arcade.run()


if __name__ == "__main__":
    main()