#!/usr/bin/env python3
import os
import psycopg2

def get_conn():
    dbname = os.getenv("PGDATABASE", "photon")
    user   = os.getenv("PGUSER",     "student")
    host   = os.getenv("PGHOST",     "localhost")
    port   = int(os.getenv("PGPORT", "5432"))
    pw     = os.getenv("PGPASSWORD")
    params = {'dbname': dbname, 'user': user, 'host': host, 'port': port}
    if pw: params['password'] = pw
    return psycopg2.connect(**params)

def ensure_players_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS players(
          id TEXT PRIMARY KEY,
          codename VARCHAR(100) NOT NULL,
          hardware_id INTEGER,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def fetch_player(conn, userid):
    with conn.cursor() as cur:
        cur.execute("SELECT id, codename, hardware_id FROM players WHERE id=%s;", (userid,))
        r = cur.fetchone()
        return None if not r else {'id': r[0], 'codename': r[1], 'hardware_id': r[2]}

def upsert_player(conn, userid, codename, hardware_id):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO players(id, codename, hardware_id)
            VALUES (%s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET codename=EXCLUDED.codename,
                                          hardware_id=EXCLUDED.hardware_id;
        """, (userid, codename, hardware_id))
        conn.commit()
