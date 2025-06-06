import pygame
import random
import os
import math
import numpy as np
from scipy.io import wavfile

# Prepare pop sound
sample_rate = 44100
duration = 0.1
t = np.linspace(0, duration, int(sample_rate * duration))

# Generate a short burst of noise with an envelope to fade out sound
noise = np.random.normal(0, 1, len(t))
envelope = np.exp(-t * 50)  # Quick decay
pop = noise * envelope

# Normalize sound to 16-bit
pop = pop / np.max(np.abs(pop))
pop = (pop * 32767).astype(np.int16)

# Save as WAV file
wavfile.write('pop.wav', sample_rate, pop)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Window constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BUBBLE_SIZE = 60
BUBBLE_SPACING = 10
ROWS = 8
COLS = 11

# Colors
WHITE = (255, 255, 255)
LIGHT_BLUE = (173, 216, 230)
POPPED_COLOR = (200, 200, 200)
BUTTON_COLOR = (100, 200, 100)
BUTTON_HOVER_COLOR = (80, 180, 80)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Button constants
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_FONT_SIZE = 32

# Animation constants
SQUISH_DURATION = 10  # frames
POP_DURATION = 15  # frames
MAX_SQUISH = 0.8  # minimum scale when pressed
POP_SCALE = 1.3  # maximum scale during pop animation

# Set up game display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Bubble Wrap Popper")

class Bubble:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_rect = pygame.Rect(x, y, BUBBLE_SIZE, BUBBLE_SIZE)
        self.rect = self.base_rect.copy()
        self.popped = False
        self.hover = False
        self.pressing = False
        self.pop_animation = 0
        self.press_animation = 0
        
    def update(self):
        # Update pop animation
        if self.pop_animation > 0:
            self.pop_animation -= 1
            
        # Update press animation
        if self.pressing and self.press_animation < SQUISH_DURATION:
            self.press_animation += 1
        elif not self.pressing and self.press_animation > 0:
            self.press_animation -= 1
            
        # Calculate current scale and position based on animations
        if self.popped and self.pop_animation > 0:
            # Pop animation scaling
            progress = self.pop_animation / POP_DURATION
            scale = 1.0 + (POP_SCALE - 1.0) * math.sin(progress * math.pi)
            
            width = int(BUBBLE_SIZE * scale)
            height = int(BUBBLE_SIZE * scale)
            x = self.x + (BUBBLE_SIZE - width) // 2
            y = self.y + (BUBBLE_SIZE - height) // 2
            self.rect = pygame.Rect(x, y, width, height)
        else:
            # Press animation squishing
            progress = self.press_animation / SQUISH_DURATION
            scale_y = 1.0 - (1.0 - MAX_SQUISH) * progress
            scale_x = 1.0 + (1.0 - scale_y) * 0.5  # Conserve area by expanding width
            
            width = int(BUBBLE_SIZE * scale_x)
            height = int(BUBBLE_SIZE * scale_y)
            x = self.x + (BUBBLE_SIZE - width) // 2
            y = self.y + (BUBBLE_SIZE - height) // 2
            self.rect = pygame.Rect(x, y, width, height)

    def draw(self):
        if self.popped:
            color = POPPED_COLOR
        elif self.hover or self.pressing:
            color = (143, 186, 200)
        else:
            color = LIGHT_BLUE
        
        # Draw the bubble
        pygame.draw.ellipse(screen, color, self.rect)
        pygame.draw.ellipse(screen, (100, 100, 100), self.rect, 1)
        
        if not self.popped:
            # Add highlight effect - adjust for current bubble size
            highlight_width = self.rect.width // 2
            highlight_height = self.rect.height // 4
            highlight = pygame.Surface((highlight_width, highlight_height), pygame.SRCALPHA)
            pygame.draw.ellipse(highlight, (255, 255, 255, 100), highlight.get_rect())
            screen.blit(highlight, (self.rect.x + self.rect.width//4, self.rect.y + self.rect.height//4))
            
            # Add shadow when pressing
            if self.pressing:
                shadow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, 50), shadow.get_rect())
                screen.blit(shadow, (self.rect.x, self.rect.y + 2))

    def pop(self):
        if not self.popped:
            self.popped = True
            self.pop_animation = POP_DURATION
            return True
        return False

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, BUTTON_FONT_SIZE)
        self.hover = False
        
    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.hover else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        
        text_surface = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover:
                return True
        return False

# Create bubbles
def reset_game():
    bubbles = []
    start_x = (WINDOW_WIDTH - (COLS * (BUBBLE_SIZE + BUBBLE_SPACING))) // 2
    start_y = (WINDOW_HEIGHT - (ROWS * (BUBBLE_SIZE + BUBBLE_SPACING))) // 2

    for row in range(ROWS):
        for col in range(COLS):
            x = start_x + col * (BUBBLE_SIZE + BUBBLE_SPACING)
            y = start_y + row * (BUBBLE_SIZE + BUBBLE_SPACING)
            bubbles.append(Bubble(x, y))
    return bubbles

bubbles = reset_game()

# Create reload button (centered at bottom of screen)
reload_button = Button(
    (WINDOW_WIDTH - BUTTON_WIDTH) // 2,
    WINDOW_HEIGHT - BUTTON_HEIGHT - 20,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    "Play Again"
)

# Pop sound
pop_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "pop.wav"))

# Game loop
running = True
clock = pygame.time.Clock()
mouse_pressed = False

while running:
    mouse_pos = pygame.mouse.get_pos()
    prev_mouse_pressed = mouse_pressed
    mouse_pressed = pygame.mouse.get_pressed()[0]
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Check for button click when all bubbles are popped
        if all(bubble.popped for bubble in bubbles):
            if reload_button.handle_event(event):
                bubbles = reset_game()
    
    # Update bubble states
    for bubble in bubbles:
        bubble.hover = bubble.rect.collidepoint(mouse_pos) and not bubble.popped
        
        # Handle mouse press and release
        if bubble.hover:
            if mouse_pressed and not prev_mouse_pressed:
                bubble.pressing = True
            elif not mouse_pressed and prev_mouse_pressed:
                if bubble.pressing and not bubble.popped:
                    if bubble.pop():
                        pop_sound.play()
                bubble.pressing = False
        else:
            bubble.pressing = False
            
        # Update animations
        bubble.update()
    
    # Draw
    screen.fill(WHITE)
    
    # Draw bubbles
    for bubble in bubbles:
        bubble.draw()
    
    # Draw reload button if all bubbles are popped
    if all(bubble.popped for bubble in bubbles):
        reload_button.draw(screen)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit() 