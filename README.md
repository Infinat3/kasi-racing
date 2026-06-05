# Kasi Racing 🏎️

A retro-inspired top-down racing game built with Pygame.

## Overview

Kasi Racing is a fast-paced, pixel-art style racing game where you compete against an AI opponent on a circuit track. The game features:

- **Player-controlled car** with realistic physics (acceleration, friction, braking)
- **AI opponent** that follows a predefined racing line
- **Lap counting** system to track progress
- **Retro aesthetic** with 1700s-inspired visuals

## Features

✅ Smooth car physics and controls  
✅ Keyboard controls (WASD or Arrow keys)  
✅ AI racing opponent  
✅ Lap tracking  
✅ Retro visual style  

## Installation

### Requirements
- Python 3.8+
- Pygame

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Infinat3/kasi-racing.git
cd kasi-racing
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| **W / ↑** | Accelerate |
| **S / ↓** | Brake |
| **A / ←** | Turn Left |
| **D / →** | Turn Right |

## Game Mechanics

- **Acceleration**: Smooth acceleration with max speed cap
- **Friction**: Natural deceleration when not accelerating
- **Steering**: Only works when moving; reverses when backing up
- **Lap Counting**: Automatically tracks completed laps
- **AI Opponent**: Follows waypoints around the track at near-player speed

## Future Enhancements

- [ ] Multiple difficulty levels
- [ ] Custom track editor
- [ ] Sound effects and music
- [ ] Particle effects (dust, skid marks)
- [ ] Collision detection and track boundaries
- [ ] Speed boost zones
- [ ] Leaderboard/scoring system
- [ ] Mobile controls

## License

MIT License - Feel free to fork and modify!

## Author

Created by [@Infinat3](https://github.com/Infinat3)
