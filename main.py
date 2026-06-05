import pygame
import math
import sys

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

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro 1700s-inspired Top-Down Racer")
clock = pygame.time.Clock()

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

    def move(self):
        # Apply friction
        if self.speed > 0:
            self.speed -= self.friction
        elif self.speed < 0:
            self.speed += self.friction

        # Absolute limit caps
        if self.speed > self.max_speed: self.speed = self.max_speed
        if self.speed < -self.max_speed / 2: self.speed = -self.max_speed / 2

        # Convert polar coordinates (speed, angle) to Cartesian coordinates (X, Y)
        # Subtract 90 because 0 degrees in math points right, but our car sprite points up
        rad = math.radians(self.angle - 90)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)


class PlayerCar(Car):
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


class AICar(Car):
    def __init__(self, x, y, color, waypoints):
        super().__init__(x, y, color)
        self.waypoints = waypoints
        self.current_waypoint = 0
        self.max_speed = 5.2  # Slightly slower than player to keep it fair

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


def draw_track(surface):
    # Background Grass
    surface.fill(GREEN)
    
    # Outer track boundaries (Drawn using thick geometric lines as a simple race circuit)
    track_points = [(150, 150), (850, 150), (850, 650), (500, 650), (500, 450), (150, 450)]
    pygame.draw.lines(surface, GREY, True, track_points, width=120)
    
    # Inner decorative lane line
    pygame.draw.lines(surface, WHITE, True, track_points, width=2)
    
    # Finish line
    pygame.draw.rect(surface, YELLOW, (150 - 60, 250, 120, 15))


def main():
    # Define track waypoints for the AI to follow blindly
    ai_waypoints = [(500, 150), (850, 150), (850, 400), (850, 650), (650, 650), (500, 650), (500, 450), (150, 450), (150, 250)]
    
    # Spawn cars at start line
    player = PlayerCar(150, 300, RED)
    ai_opponent = AICar(120, 320, BLUE, ai_waypoints)
    
    player_laps = 0
    passed_checkpoint = False

    running = True
    while running:
        clock.tick(FPS)
        
        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        # Update Game Logic
        player.update()
        ai_opponent.update()

        # Simple Lap Counting logic using Y coordinates on the left straightaway
        if player.y < 250 and not passed_checkpoint:
            passed_checkpoint = True
        if player.y > 350 and passed_checkpoint:
            player_laps += 1
            passed_checkpoint = False

        # Render Drawing
        draw_track(screen)
        player.draw(screen)
        ai_opponent.draw(screen)

        # Draw HUD UI text
        font = pygame.font.SysFont("Courier", 24, bold=True)
        lap_text = font.render(f"LAPS: {player_laps}", True, WHITE)
        controls_text = font.render("WASD / Arrows to Drive", True, WHITE)
        screen.blit(lap_text, (20, 20))
        screen.blit(controls_text, (20, 50))

        pygame.display.flip()

if __name__ == "__main__":
    main()
