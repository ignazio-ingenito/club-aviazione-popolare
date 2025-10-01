# Importing postgres DB

## Export from local instance

```shell
sudo -u postgres pg_dump -Fc --no-owner -f /tmp/cap.bak cap
```

## Import to neon


```shell
psql $NEON_CONN
```

```sql
CREATE ROLE cap WITH LOGIN PASSWORD 'Foe-Doorframe-Mutate4';
ALTER TABLE public.directus_access OWNER TO neon_owner_user;
```

```shell
sudo -u postgres pg_restore --clean --no-owner --no-privileges -v -d $NEON_CONN /tmp/cap.bak
```
