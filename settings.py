from envparse import Env

env = Env()

REAL_DATABASE_URL = env.str(
    "REAL_DATABASE_URL",
    default="postgresql+asyncpg://www:mzDyr2g25041954@localhost:6432/scanning_users"
)
