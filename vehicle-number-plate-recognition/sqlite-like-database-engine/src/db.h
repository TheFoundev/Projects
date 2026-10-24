#ifndef DB_H
#define DB_H

#include <stddef.h>

typedef struct db db_t;

db_t *db_open(const char *path);
void db_close(db_t *database);
int db_put(db_t *database, const char *key, const char *value);
const char *db_get(db_t *database, const char *key);
int db_delete(db_t *database, const char *key);
size_t db_count(db_t *database);
int db_save(db_t *database);
int db_dump(db_t *database);

#endif
