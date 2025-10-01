# Step 1: Set up a Database

## Automated repository configuration:
```
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
```

## Setup
```
sudo apt install -y postgresql
```

## Starting / Stopping Postgres
```
sudo systemctl start postgresql
sudo systemctl status postgresql
sudo systemctl stop postgresql
```

```
sudo -u postgres psql
```

```
ALTER ROLE postgres WITH PASSWORD 'postgres';
\q
```

to test (-W forces a password prompt)
```
psql -U postgres -h localhost -W
```

## Create DB
```
CREATE USER cap WITH PASSWORD 'your_strong_password_here';
CREATE DATABASE cap OWNER cap;
ALTER USER cap CREATEDB;
```

# Step 2: Install Directus

```
pnpm install directus
```

# Step 3: Initialize Directus

```
pnpx directus init
```
 - Select the proper DB Type
 - Set your admin password


Step 4: Start Directus
```
npx directus start
```