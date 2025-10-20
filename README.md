# Team 7 - Photon Laser Tag System
University of Arkansas - CSCE 36103 (Operating Systems / Software Engineering)

| Name | Github Username |
|------|--------------|
|`Brodie Baugh` | brodiebaugh |
|`Javier Soler` | Javitoo27 |
|`Brigham Evans` | Bevans7471 |

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
| `install.sh` | Installs required system and Python dependencies. |
| `logo.jpg` | Splash image shown on startup. |


Install dependencies automatically using:
```bash
chmod a+x install.sh
./install.sh

How to run:
python3 player_entry.py
