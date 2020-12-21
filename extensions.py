import os
from cs50 import SQL

db = SQL(os.environ.get("DATABASE_URL"))