# 🍪 Bassu Cookie Clicker 

Charles PREVOST - FIPA 2A

## Description
This repository contains a simple web-based **Cookie Clicker** built using **Flask**. Players can increase their score by clicking, are able to view the leaderboard, and have their scores saved temporarily in **Redis** and then (after 5 mins) persistently using **PostgreSQL**.

## Features
- **Open User System**: Players can register without admin interaction and play by just entering a username.
- **Leaderboard**: Displays the top players based on their click counts.
- **Real-time storage**: Each click is recorded in real-time using Redis.
- **Persistent Storage**: Scores are periodically synced from Redis to PostgreSQL for persistence.
- **Background Job**: A scheduled job runs every 5 minutes to save data from Redis to PostgreSQL.

### A little background

A topic that was introduced in the course was that **writes are expensive** in SQL yet **reads are pretty cheap**. I made a system that would use Redis to act as a **cache for the Postgres DB** and not constantly update entries directly. Now Postgres only processes the bare minimum reads and only writes every 5 minutes (only the modified values). :)

## Installation

### Prerequisites (Debian)
- `docker`
- `docker-compose-plugin`

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/charlesbozzi/bassu-cookie-clicker.git
   cd cookie-clicker
   ```

2. Start the stack
   ```bash
   sudo docker compose up
   ```

3. Access the web interface locally from [`http://localhost:5000`](http://localhost:5000 "the cloud is just someone else's computer")

## Let's go further

### What could be enhanced?

Everything, I'm not sure my code is particularly secure or fancy yet it is simple and functionnal. I wouldn't recommend deploying my program on a public-facing server.

The bare minimum enhancement-wise would be to **setup a reverse-proxy in front of the app** with a Let's Encrypt certificate (not that the app is storing particularly sensitive data). I would also recommend **using the WSGI backend** instead of the bare python loader.

### What could go wrong?
1. I encountered in some deployments a latency in the database startup that **prevented my program from loading**. I tried to remedy that by adjusting the timeout used in setting up the connection but I have seen it happen again and could not pinpoint exactly why it would not just wait for full database availability (or respect the timeout for that matter).

2. Since there were no protections added to prevent **SQL injections**, it might be possible for an attacker to modify the actual Postgres data by crafting a malicious username.

3. An attacker could overload the redis database by stuffing as much usernames as possible and possibly **crash the redis instance** if the memory was to reach maximum capacity? (wild guess)

# That deserves a cookie, right?