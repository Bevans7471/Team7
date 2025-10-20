import psycopg2


def get_player(player_id):
    """
    Look up player by ID, return their codename or None
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="photon",
            user="student",
            password="student"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT codename FROM players WHERE id = %s", (int(player_id),))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return result[0]  # Return the codename
        return None  # Player not found

    except:
        return None  # Error occurred


def save_player(player_id, codename):
    """
    Save new player to database
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="photon",
            user="student",
            password="student"
        )
        cursor = conn.cursor()

        cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s)",
                       (int(player_id), codename))
        conn.commit()

        cursor.close()
        conn.close()
        return True

    except:
        return False