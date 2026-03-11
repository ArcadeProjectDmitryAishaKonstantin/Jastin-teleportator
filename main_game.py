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
