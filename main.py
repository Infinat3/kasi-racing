import pygame
import math
import sys
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
FPS = 60

# Colors (RGB)
WHITE = (255, 255, 255)
GREY = (50, 50, 50)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
LIGHT_GREY = (200, 200, 200)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro 1700s-inspired Top-Down Racer")
clock = pygame.time.Clock()


@dataclass
class CollisionInfo:
    """Stores collision information"""
    collided: bool
    collision_point: Tuple[float, float] = (0, 0)
    normal: Tuple[float, float] = (0, 0)


class DifficultyLevel(Enum):
    EASY = 0.7
    NORMAL = 0.9
    HARD = 1.1


class Car:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.width = 20
        self.height = 40
        
        # Physics variables
        self.angle = 0
        self.speed = 0
        self.max_speed = 6
        self.acceleration = 0.15
        self.brake_deceleration = 0.2
        self.friction = 0.05
        self.turn_speed = 4
        
        # Collision
        self.collision_rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)

    def draw(self, surface):
        # Create a surface for the car to handle rotation smoothly
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw the car body
        pygame.draw.rect(car_surface, self.color, (0, 0, self.width, self.height), border_radius=4)
        # Draw windshield to show direction (top of rect)
        pygame.draw.rect(car_surface, BLACK, (2, 5, self.width - 4, 8))
        # Draw wheels
        pygame.draw.rect(car_surface, BLACK, (-2, 8, 2, 8))
        pygame.draw.rect(car_surface, BLACK, (self.width, 8, 2, 8))
        pygame.draw.rect(car_surface, BLACK, (-2, 28, 2, 8))
        pygame.draw.rect(car_surface, BLACK, (self.width, 28, 2, 8))

        # Rotate the car surface (Pygame rotates counter-clockwise, hence the negative sign)
        rotated_surface = pygame.transform.rotate(car_surface, -self.angle)
        new_rect = rotated_surface.get_rect(center=(self.x, self.y))
        
        surface.blit(rotated_surface, new_rect.topleft)
        
        # Update collision rect
        self.collision_rect.center = (self.x, self.y)

    def move(self):
        # Apply friction
        if self.speed > 0:
            self.speed -= self.friction
        elif self.speed < 0:
            self.speed += self.friction

        # Absolute limit caps
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed < -self.max_speed / 2:
            self.speed = -self.max_speed / 2

        # Convert polar coordinates (speed, angle) to Cartesian coordinates (X, Y)
        # Subtract 90 because 0 degrees in math points right, but our car sprite points up
        rad = math.radians(self.angle - 90)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)

    def check_track_collision(self, track_boundaries):
        """Check collision with track boundaries"""
        # Simple point-in-polygon collision
        return self._point_in_polygon(self.x, self.y, track_boundaries)

    @staticmethod
    def _point_in_polygon(x, y, polygon):
        """Ray casting algorithm for point-in-polygon collision"""
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def check_car_collision(self, other_car):
        """Check collision with another car"""
        distance = math.hypot(self.x - other_car.x, self.y - other_car.y)
        min_distance = (self.width + other_car.width) / 2
        return distance < min_distance


class PlayerCar(Car):
    def __init__(self, x, y, color):
        super().__init__(x, y, color)
        self.lap_time = 0
        self.best_lap_time = float('inf')
        self.current_lap_started = False

    def update(self):
        keys = pygame.key.get_pressed()
        
        # Steering (Only turn if moving)
        if self.speed != 0:
            # Reverse steering direction if driving backward
            direction = 1 if self.speed > 0 else -1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.angle -= self.turn_speed * direction
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.angle += self.turn_speed * direction

        # Acceleration / Braking
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= self.brake_deceleration
            
        self.move()
        
        # Update lap timer
        if self.current_lap_started:
            self.lap_time += 1

    def reset_lap_timer(self):
        """Reset the lap timer and save best lap if applicable"""
        if self.lap_time > 0:
            if self.lap_time < self.best_lap_time:
                self.best_lap_time = self.lap_time
        self.lap_time = 0
        self.current_lap_started = True


class AICar(Car):
    def __init__(self, x, y, color, waypoints, difficulty=DifficultyLevel.NORMAL):
        super().__init__(x, y, color)
        self.waypoints = waypoints
        self.current_waypoint = 0
        self.max_speed = 5.2 * difficulty.value
        self.acceleration = 0.15 * (difficulty.value ** 0.8)  # Slightly less aggressive acceleration scaling
        self.difficulty = difficulty
        self.laps = 0
        self.passed_checkpoint = False

    def update(self):
        if self.current_waypoint < len(self.waypoints):
            target_x, target_y = self.waypoints[self.current_waypoint]
            
            # Calculate angle to target waypoint
            dx = target_x - self.x
            dy = target_y - self.y
            target_angle = math.degrees(math.atan2(dy, dx)) + 90
            
            # Simple angle interpolation (steering towards target)
            angle_diff = (target_angle - self.angle + 180) % 360 - 180
            if angle_diff > 2:
                self.angle += self.turn_speed
            elif angle_diff < -2:
                self.angle -= self.turn_speed

            # Always accelerate
            self.speed += self.acceleration
            
            # Check if close enough to waypoint to target the next one
            distance = math.hypot(dx, dy)
            if distance < 40:
                self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
                
        self.move()


class Track:
    def __init__(self):
        # Define track boundaries (outer and inner)
        self.outer_boundary = [(150, 150), (850, 150), (850, 650), (500, 650), (500, 450), (150, 450)]
        self.inner_boundary = [(250, 250), (750, 250), (750, 550), (600, 550), (600, 350), (250, 350)]
        self.finish_line = pygame.Rect(150 - 60, 250, 120, 15)
        self.track_width = 120
        self.safe_zone = self._create_safe_zone()

    def _create_safe_zone(self):
        """Create an expanded polygon for collision detection"""
        # Offset the boundaries inward/outward for collision detection
        return self.outer_boundary

    def draw(self, surface):
        # Background Grass
        surface.fill(GREEN)
        
        # Outer track boundaries (Drawn using thick geometric lines as a simple race circuit)
        pygame.draw.lines(surface, GREY, True, self.outer_boundary, width=self.track_width)
        
        # Inner decorative lane line
        pygame.draw.lines(surface, WHITE, True, self.outer_boundary, width=2)
        
        # Finish line
        pygame.draw.rect(surface, YELLOW, self.finish_line)
        pygame.draw.rect(surface, BLACK, self.finish_line, width=2)

    def is_on_track(self, x, y):
        """Check if a position is on the track"""
        return Car._point_in_polygon(x, y, self.outer_boundary)

    def get_finish_line(self):
        """Return the finish line rectangle"""
        return self.finish_line


def draw_hud(surface, player, ai, font_small, font_large, player_laps):
    """Draw HUD elements"""
    # Lap counter
    lap_text = font_large.render(f"LAPS: {player_laps}", True, WHITE)
    surface.blit(lap_text, (20, 20))
    
    # Current lap time
    current_time = format_time(player.lap_time)
    time_text = font_small.render(f"Current: {current_time}", True, WHITE)
    surface.blit(time_text, (20, 50))
    
    # Best lap time
    best_time_str = "N/A" if player.best_lap_time == float('inf') else format_time(int(player.best_lap_time))
    best_text = font_small.render(f"Best: {best_time_str}", True, YELLOW)
    surface.blit(best_text, (20, 75))
    
    # Speed indicator
    speed_text = font_small.render(f"Speed: {abs(player.speed):.1f}", True, BLUE)
    surface.blit(speed_text, (20, 100))
    
    # AI opponent position
    ai_text = font_small.render(f"AI Laps: {ai.laps}", True, ORANGE)
    surface.blit(ai_text, (SCREEN_WIDTH - 200, 20))
    
    # Controls
    controls_text = font_small.render("WASD / Arrows to Drive | R to Reset", True, LIGHT_GREY)
    surface.blit(controls_text, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 30))


def format_time(milliseconds):
    """Convert milliseconds to MM:SS.MS format"""
    total_seconds = milliseconds / FPS
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    centiseconds = int((total_seconds % 1) * 100)
    return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def main():
    # Create track
    track = Track()
    
    # Define track waypoints for the AI to follow
    ai_waypoints = [(500, 150), (850, 150), (850, 400), (850, 650), (650, 650), (500, 650), (500, 450), (150, 450), (150, 250)]
    
    # Spawn cars at start line
    player = PlayerCar(150, 300, RED)
    
    # Change AI difficulty here: DifficultyLevel.EASY, NORMAL, or HARD
    ai_opponent = AICar(120, 320, BLUE, ai_waypoints, DifficultyLevel.NORMAL)
    
    player_laps = 0
    player.passed_checkpoint = False
    ai_opponent.passed_checkpoint = False
    
    # Fonts
    font_small = pygame.font.SysFont("Courier", 18, bold=False)
    font_large = pygame.font.SysFont("Courier", 24, bold=True)
    
    # Game state
    collision_cooldown = 0
    
    running = True
    while running:
        clock.tick(FPS)
        
        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game
                    player = PlayerCar(150, 300, RED)
                    ai_opponent = AICar(120, 320, BLUE, ai_waypoints, DifficultyLevel.NORMAL)
                    player_laps = 0
                    player.passed_checkpoint = False
                    ai_opponent.passed_checkpoint = False

        # Update Game Logic
        player.update()
        ai_opponent.update()
        
        # Track collision (bounce cars back if off track)
        if not track.is_on_track(player.x, player.y):
            # Simple bounce back
            player.speed *= -0.3
            rad = math.radians(player.angle - 90)
            player.x -= player.speed * 2 * math.cos(rad)
            player.y -= player.speed * 2 * math.sin(rad)
        
        if not track.is_on_track(ai_opponent.x, ai_opponent.y):
            ai_opponent.speed *= -0.3
            rad = math.radians(ai_opponent.angle - 90)
            ai_opponent.x -= ai_opponent.speed * 2 * math.cos(rad)
            ai_opponent.y -= ai_opponent.speed * 2 * math.sin(rad)
        
        # Car-to-car collision
        collision_cooldown = max(0, collision_cooldown - 1)
        if collision_cooldown == 0 and player.check_car_collision(ai_opponent):
            # Simple elastic collision
            dx = ai_opponent.x - player.x
            dy = ai_opponent.y - player.y
            distance = math.hypot(dx, dy)
            if distance > 0:
                nx = dx / distance
                ny = dy / distance
                player.x -= nx * 2
                player.y -= ny * 2
                ai_opponent.x += nx * 2
                ai_opponent.y += ny * 2
                player.speed *= 0.7
                ai_opponent.speed *= 0.7
                collision_cooldown = 30

        # Lap counting for player (using Y coordinates on the left straightaway)
        if player.y < 250 and not player.passed_checkpoint:
            player.passed_checkpoint = True
        if player.y > 350 and player.passed_checkpoint:
            player_laps += 1
            player.reset_lap_timer()
            player.passed_checkpoint = False

        # Lap counting for AI
        if ai_opponent.y < 250 and not ai_opponent.passed_checkpoint:
            ai_opponent.passed_checkpoint = True
        if ai_opponent.y > 350 and ai_opponent.passed_checkpoint:
            ai_opponent.laps += 1
            ai_opponent.passed_checkpoint = False

        # Render Drawing
        track.draw(screen)
        player.draw(screen)
        ai_opponent.draw(screen)

        # Draw HUD
        draw_hud(screen, player, ai_opponent, font_small, font_large, player_laps)

        pygame.display.flip()


if __name__ == "__main__":
    main()
