from flaskr.db import get_db

class User:
  def get_or_create_for_discord_user(discord_user):
      username = discord_user["username"]
      user = User.get_by_username(username)

      if user is None:
          db = get_db()
          db.execute(
              "INSERT INTO user (username, discord_id)" " VALUES (?, ?)",
              (username, discord_user["id"]),
          )
          db.commit()

      return User.get_by_username(username)


  def get_by_username(username):
      db = get_db()
      user = db.execute(
          "SELECT u.id, u.username, u.discord_id FROM user u WHERE u.username = ?", (username,)
      ).fetchone()

      return User(user_id=user['id'], username=user['username'], discord_id=user['discord_id'])
        
  def __init__(self, user_id, username, discord_id):
      self.id = user_id
      self.username = username
      self.discord_id = discord_id
      self._artists = None

  def get_artists(self):
      if self._artists is not None:
          return self._artists
      self._artists = (
          get_db()
          .execute(
              "SELECT * FROM artist WHERE user_id = ?" " ORDER BY rating ASC",
              (self.id,),
          )
          .fetchall()
      )
      return self._artists
