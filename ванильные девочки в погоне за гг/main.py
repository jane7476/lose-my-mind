import math
import os
import random
import sys
import pygame

# Инициализация Pygame-CE
pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Цвета
COLOR_ROAD = (80, 80, 80)
COLOR_LINE = (255, 255, 255)
COLOR_GRASS = (34, 139, 34)
COLOR_TEXT = (255, 255, 255)

# Настройка экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("F1 Simulator - Pygame-CE")
clock = pygame.time.Clock()


class Car:

  def __init__(self, x, y, image_path, width=30, height=56, is_player=False):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.speed = 0
    self.max_speed = 10 if is_player else random.uniform(6.5, 8.5)
    self.acceleration = 0.2
    self.friction = 0.1
    self.is_player = is_player
    self.lane = random.randint(0, 3)

    # Загрузка PNG спрайта
    try:
      self.image = pygame.image.load(image_path).convert_alpha()
      self.image = pygame.transform.scale(
          self.image, (self.width, self.height)
      )
    except (pygame.error, FileNotFoundError):
      # Заглушка, если картинка не найдена
      self.image = pygame.Surface((self.width, self.height))
      self.image.fill((255, 0, 0) if is_player else (0, 0, 255))

  def get_rect(self):
    return pygame.Rect(
        int(self.x - self.width / 2),
        int(self.y - self.height / 2),
        self.width,
        self.height,
    )

  def update(self, player_speed=0):
    if self.is_player:
      keys = pygame.key.get_pressed()
      if keys[pygame.K_UP] or keys[pygame.K_w]:
        self.speed = min(self.speed + self.acceleration, self.max_speed)
      elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        self.speed = max(self.speed - self.acceleration, -2)
      else:
        if self.speed > 0:
          self.speed = max(0, self.speed - self.friction)
        elif self.speed < 0:
          self.speed = min(0, self.speed + self.friction)

      if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        self.x -= 5
      if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        self.x += 5

      self.x = max(220, min(580, self.x))
    else:
      relative_speed = self.speed - player_speed
      self.y += relative_speed

      target_x = 260 + self.lane * 100
      if self.x < target_x:
        self.x += 1.5
      elif self.x > target_x:
        self.x -= 1.5

      if random.random() < 0.01:
        self.lane = random.randint(0, 3)

  def draw(self, surface):
    rect = self.get_rect()
    surface.blit(self.image, (rect.x, rect.y))


def draw_checkered_finish(surface, x, y, width, height):
  """Рисует классическую клетчатую финишную линию"""
  box_size = 20
  for row in range(0, height, box_size):
    for col in range(0, width, box_size):
      color = (255, 255, 255) if (row // box_size + col // box_size) % 2 == 0 else (0, 0, 0)
      pygame.draw.rect(surface, color, (x + col, y + row, box_size, box_size))


def main():
  # Создание папки assets если её нет
  if not os.path.exists("assets"):
    os.makedirs("assets")

  # Игрок и соперники (пути к вашим PNG файлам)
  player = Car(400, 550, "assets/player.png", is_player=True)

  enemies = []
  for i in range(11):
    ex = 260 + (i % 4) * 100
    ey = -random.randint(200, 2000)
    enemies.append(Car(ex, ey, "assets/enemy.png"))

  # Трасса длиной 1000 метров до финиша
  TOTAL_DISTANCE = 1000
  finish_line_y = -TOTAL_DISTANCE * 10  # Позиция финиша в игровом мире

  road_scroll = 0
  score_distance = 0
  overtrakes = 0
  
  # Настройки таймера (например, 60 секунд на гонку)
  time_left = 60.0 

  font = pygame.font.SysFont("Arial", 24)
  game_over = False
  game_won = False

  while True:
    dt = clock.tick(FPS) / 1000.0  # Время кадра в секундах

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
      if (game_over or game_won) and event.type == pygame.KEYDOWN:
        if event.key == pygame.K_r:
          return main()

    if not game_over and not game_won:
      # Уменьшаем таймер, пока идет игра
      time_left -= dt
      if time_left <= 0:
        time_left = 0
        game_over = True

      player.update()
      road_scroll = (road_scroll + player.speed) % 40
      score_distance += player.speed / 10

      # Двигаем финишную линию относительно скорости игрока
      finish_line_y += player.speed

      # Проверка победы (если проехали всю дистанцию)
      if score_distance >= TOTAL_DISTANCE:
        game_won = True

      for enemy in enemies:
        enemy.update(player.speed)

        if enemy.y > SCREEN_HEIGHT + 100:
          enemy.y = -random.randint(400, 1000)
          enemy.x = 260 + random.randint(0, 3) * 100
          overtrakes += 1

        if player.get_rect().colliderect(enemy.get_rect()):
          game_over = True

      if player.x < 210 or player.x > 590:
        player.speed *= 0.95

    # --- Отрисовка ---
    screen.fill(COLOR_GRASS)

    road_rect = pygame.Rect(200, 0, 400, SCREEN_HEIGHT)
    pygame.draw.rect(screen, COLOR_ROAD, road_rect)

    # Разметка дороги
    for i in range(-1, SCREEN_HEIGHT // 40 + 2):
      y_pos = i * 40 + road_scroll
      pygame.draw.line(screen, COLOR_LINE, (300, y_pos), (300, y_pos + 20), 3)
      pygame.draw.line(screen, COLOR_LINE, (400, y_pos), (400, y_pos + 20), 3)
      pygame.draw.line(screen, COLOR_LINE, (500, y_pos), (500, y_pos + 20), 3)

    # Отрисовка финишной линии (если она в пределах или близко к экрану)
    if -200 < finish_line_y < SCREEN_HEIGHT + 200:
      draw_checkered_finish(screen, 200, int(finish_line_y), 400, 40)

    # Отрисовка соперников и игрока
    for enemy in enemies:
      enemy.draw(screen)
    player.draw(screen)

    # Интерфейс
    speed_text = font.render(f"Скорость: {int(player.speed * 20)} км/ч", True, COLOR_TEXT)
    overtake_text = font.render(f"Обгоны: {overtrakes}", True, COLOR_TEXT)
    dist_text = font.render(f"Дистанция: {int(score_distance)} / {TOTAL_DISTANCE} м", True, COLOR_TEXT)
    
    # Рендер таймера (выводим целое число секунд, можно сделать с десятыми: f"{time_left:.1f}")
    timer_color = (255, 50, 50) if time_left <= 10 else COLOR_TEXT  # Краснеет за 10 секунд до конца
    timer_text = font.render(f"Время: {int(time_left)} сек", True, timer_color)

    screen.blit(speed_text, (20, 20))
    screen.blit(overtake_text, (20, 50))
    screen.blit(dist_text, (20, 80))
    screen.blit(timer_text, (20, 110))

    if game_over or game_won:
      overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      screen.blit(overlay, (0, 0))

      if game_won:
        main_text = font.render("Simply Lovely, huh?", True, (50, 255, 50))
      else:
        main_text = font.render("I'm stupid. I'm stupid.", True, (255, 50, 50))

      restart_text = font.render("press 'R' to restart", True, COLOR_TEXT)

      screen.blit(main_text, (SCREEN_WIDTH / 2 - main_text.get_width() / 2, SCREEN_HEIGHT / 2 - 40))
      screen.blit(restart_text, (SCREEN_WIDTH / 2 - restart_text.get_width() / 2, SCREEN_HEIGHT / 2 + 10))

    pygame.display.flip()


if __name__ == "__main__":
  main()