# Team 7 - Photon Laser Tag System
Sprint 3 Project  
University of Arkansas - CSCE 36103 (Operating Systems / Software Engineering)

## Overview
This project simulates a laser tag player entry and game management system using Python and UDP networking.  
It provides a GUI for player registration, team assignment, and game display screens.

## File Structure
| File | Description |
|------|--------------|
| `player_entry.py` | Main GUI interface for player entry and game screens. |
| `db_players.py` | Handles player information and mock database storage. |
| `db_util.py` | Utility for connecting to or mocking a PostgreSQL database. |
| `udp_util.py` | Manages UDP socket setup, sending, and receiving. |
| `udp_server_test.py` | Simple server/client test for UDP communication. |
| `install.sh` | Installs required system and Python dependencies. |
| `logo.jpg` | Splash image shown on startup. |


Install dependencies automatically using:
```bash
./install.sh
