import arcade
import math
import enum
import random
from arcade.camera import Camera2D

SHIRINA_EKRANA = 1000
VYSOTA_EKRANA = 600
ZAGOLOVOK_EKRANA = "Герой против монстров — меню"

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
        if self.vremya_nezashchity <= 0 and self.zhiv and not self.smert_aktivirovana:
            self.zdorovie -= uron
            self.vremya_nezashchity = self.dlitelnost_nezashchity

            if self.zdorovie <= 0:
                self.zdorovie = 0
                self.smert_aktivirovana = True
                self.vremya_do_smerti = 2.0
                return True
        return False


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

            if rasstoyanie > 5:
                napravlenie = 1 if raznost_x > 0 else -1
                dvizhenie = napravlenie * self.skorost * delta_time
                staraya_x = self.center_x
                self.center_x += dvizhenie

                if self.roditel and hasattr(self.roditel, 'spisok_platform'):
                    for platforma in self.roditel.spisok_platform:
                        if arcade.check_for_collision(self, platforma):
                            self.center_x = staraya_x
                            break

                if napravlenie > 0:
                    self.texture = self.tekstura_pokoya
                else:
                    self.texture = self.tekstura_pokoya.flip_horizontally()


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

            arcade.draw_text("ФИНИШ ДОСТИГНУТ!",
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

            if self.schetchik_ubijstv >= self.tsel_ubijstv:
                ocenka = "ОТЛИЧНАЯ РАБОТА! ВСЕ МОНСТРЫ УНИЧТОЖЕНЫ!"
                cvet_ocenki = arcade.color.GOLD
            elif self.schetchik_ubijstv >= 15:
                ocenka = "ХОРОШО, НО МОЖНО БЫЛО УБИТЬ БОЛЬШЕ"
                cvet_ocenki = arcade.color.ORANGE
            else:
                ocenka = "ГЛАВНОЕ - ДОБРАТЬСЯ ДО ФИНИША!"
                cvet_ocenki = arcade.color.GREEN

            arcade.draw_text(ocenka,
                             self.width // 2, self.height // 2 - 120,
                             cvet_ocenki, 20, anchor_x="center")

            arcade.draw_text("Нажми R чтобы сыграть снова",
                             self.width // 2, self.height // 2 - 170,
                             arcade.color.YELLOW, 18, anchor_x="center")

            arcade.draw_text("ESC для выхода в меню",
                             self.width // 2, self.height // 2 - 200,
                             arcade.color.ORANGE, 18, anchor_x="center")

    def on_update(self, delta_time):
        if self.sostoyanie_igry != "PLAYING":
            return

        self.vremya_igry += delta_time

        self.spisok_flaga.update(delta_time)

        self.fizika.update()

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
            menu.setup()
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
        super().__init__(SHIRINA_EKRANA, VYSOTA_EKRANA, ZAGOLOVOK_EKRANA)
        arcade.set_background_color(arcade.color.SKY_BLUE)

        self.oblaka = []
        self.knopki = []
        self.mx = 0
        self.my = 0

        self.sozdat_oblaka()
        self.sozdat_knopki()

    def setup(self):
        pass

    def sozdat_oblaka(self):
        for _ in range(6):
            self.oblaka.append({
                "x": random.randint(0, SHIRINA_EKRANA),
                "y": random.randint(350, 550),
                "skorost": random.uniform(20, 60)
            })

    def obnovit_oblaka(self, delta_time):
        for oblako in self.oblaka:
            oblako["x"] += oblako["skorost"] * delta_time
            if oblako["x"] > SHIRINA_EKRANA + 150:
                oblako["x"] = -150
                oblako["y"] = random.randint(350, 550)

    def narisovat_oblako(self, x, y):
        arcade.draw_circle_filled(x, y, 40, arcade.color.WHITE)
        arcade.draw_circle_filled(x + 40, y, 50, arcade.color.WHITE)
        arcade.draw_circle_filled(x - 40, y, 50, arcade.color.WHITE)

    def sozdat_knopki(self):
        urovni = ["1", "2", "3"]
        shirina_knopki = 260
        vysota_knopki = 60
        rasstoyanie = 40

        obshchaya_shirina = len(urovni) * shirina_knopki + (len(urovni) - 1) * rasstoyanie
        start_x = (SHIRINA_EKRANA - obshchaya_shirina) // 2 + shirina_knopki // 2
        centr_y = VYSOTA_EKRANA // 2

        for i, tekst in enumerate(urovni):
            centr_x = start_x + i * (shirina_knopki + rasstoyanie)
            x = centr_x - shirina_knopki // 2
            y = centr_y - vysota_knopki // 2

            self.knopki.append({
                "tekst": tekst,
                "uroven": i + 1,
                "x": x,
                "y": y,
                "centr_x": centr_x,
                "centr_y": centr_y,
                "shirina": shirina_knopki,
                "vysota": vysota_knopki
            })

    def mysh_nad_knopkoy(self, knopka):
        return (
                knopka["x"] < self.mx < knopka["x"] + knopka["shirina"] and
                knopka["y"] < self.my < knopka["y"] + knopka["vysota"]
        )

    def on_draw(self):
        self.clear()
        for oblako in self.oblaka:
            self.narisovat_oblako(oblako["x"], oblako["y"])
        arcade.draw_text(
            "ГЕРОЙ ПРОТИВ МОНСТРОВ",
            SHIRINA_EKRANA // 2,
            VYSOTA_EKRANA - 100,
            arcade.color.GOLD,
            44,
            anchor_x="center"
        )

        arcade.draw_text(
            "Выберите уровень",
            SHIRINA_EKRANA // 2,
            VYSOTA_EKRANA - 160,
            arcade.color.BLUE,
            24,
            anchor_x="center"
        )

        for knopka in self.knopki:
            navedeno = self.mysh_nad_knopkoy(knopka)
            cvet = arcade.color.DARK_BLUE if navedeno else arcade.color.BLUE
            arcade.draw_lbwh_rectangle_filled(
                knopka["x"],
                knopka["y"],
                knopka["shirina"],
                knopka["vysota"],
                cvet
            )

            arcade.draw_lbwh_rectangle_outline(
                knopka["x"],
                knopka["y"],
                knopka["shirina"],
                knopka["vysota"],
                arcade.color.WHITE,
                3
            )

            arcade.draw_text(
                knopka["tekst"],
                knopka["centr_x"],
                knopka["centr_y"],
                arcade.color.WHITE,
                22,
                anchor_x="center",
                anchor_y="center"
            )

    def on_update(self, delta_time):
        self.obnovit_oblaka(delta_time)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mx = x
        self.my = y

    def on_mouse_press(self, x, y, knopka, modifikatory):
        for knopka_dannye in self.knopki:
            if self.mysh_nad_knopkoy(knopka_dannye):
                print(f"Выбран уровень {knopka_dannye['uroven']} — {knopka_dannye['tekst']}")
                if knopka_dannye['uroven'] == 1:
                    print("Уровень 1 в разработке")
                elif knopka_dannye['uroven'] == 2:
                    self.close()
                    igra = IgraUroven2(SHIRINA_IGRY, VYSOTA_IGRY, NAZVANIE_UROVNYA2)
                    igra.setup()
                    arcade.run()
                else:
                    print(f"Уровень {knopka_dannye['uroven']} в разработке")


def main():
    okno = MenuWindow()
    okno.setup()
    arcade.run()


if __name__ == "__main__":
    main()