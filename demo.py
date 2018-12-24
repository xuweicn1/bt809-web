import sqlite3 as lite

#建库
con = lite.connect('BT809Data.db')
cur = con.cursor()

# 数据格式：Firstname,Lastname,Email
purchases = [('admin','zhang', 'admin@example.com'),
              ('guest1','wang', 'guest1@example.com'),
              ('guest2', 'li','guest2@example.com'),
              ('guest3', 'zhao','guest3@example.com'),
              ('guest4', 'qian','guest4@example.com')]


# 建表
def creat():
  with con:
    cur.execute("DROP TABLE IF EXISTS user")
    cur.execute('''CREATE TABLE user (\
              id INTEGER PRIMARY KEY AUTOINCREMENT,\
              Firstname TEXT,
              Lastname TEXT,
              Email TEXT)''')

#插入单条数据
def in_one():
  with con:
    cur.execute("INSERT INTO user(Firstname,Lastname, Email) VALUES('admin1','zhang1', 'admin1@example.com')")

# 插入多条数据 方法1：
def in_many():
  with con:
    cur.executemany('INSERT INTO user(Firstname,Lastname, Email) VALUES (?,?,?)', purchases)

# 插入多条数据 方法2：
def in_more():
  with con:
    for user_t in purchases:
      cur.execute("insert into user(Firstname,Lastname, Email) values (?,?,?)", user_t)


if __name__ == "__main__":
  in_one()