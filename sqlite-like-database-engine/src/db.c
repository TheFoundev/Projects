#define _POSIX_C_SOURCE 200809L

#include "db.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct entry {
    char *key;
    char *value;
};

struct db {
    char *path;
    struct entry *entries;
    size_t count;
    size_t capacity;
};

static long find_index(db_t *database, const char *key) {
    size_t low = 0;
    size_t high = database->count;
    while (low < high) {
        size_t middle = (low + high) / 2;
        int comparison = strcmp(database->entries[middle].key, key);
        if (comparison == 0) {
            return (long)middle;
        }
        if (comparison < 0) {
            low = middle + 1;
        } else {
            high = middle;
        }
    }
    return (long)low;
}

static int ensure_capacity(db_t *database) {
    if (database->count < database->capacity) {
        return 1;
    }
    size_t next = database->capacity == 0 ? 8 : database->capacity * 2;
    struct entry *grown = (struct entry *)realloc(database->entries, next * sizeof(struct entry));
    if (grown == NULL) {
        return 0;
    }
    database->entries = grown;
    database->capacity = next;
    return 1;
}

db_t *db_open(const char *path) {
    db_t *database = (db_t *)calloc(1, sizeof(db_t));
    FILE *file;
    unsigned int count = 0;
    unsigned int index;
    if (database == NULL) {
        return NULL;
    }
    database->path = strdup(path);
    file = fopen(path, "rb");
    if (file == NULL) {
        return database;
    }
    if (fread(&count, sizeof(count), 1, file) != 1) {
        fclose(file);
        return database;
    }
    for (index = 0; index < count; index++) {
        unsigned int key_length = 0;
        unsigned int value_length = 0;
        char *key;
        char *value;
        if (fread(&key_length, sizeof(key_length), 1, file) != 1 ||
            fread(&value_length, sizeof(value_length), 1, file) != 1) {
            break;
        }
        key = (char *)malloc(key_length + 1u);
        value = (char *)malloc(value_length + 1u);
        if (key == NULL || value == NULL) {
            free(key);
            free(value);
            break;
        }
        if (fread(key, 1, key_length, file) != key_length ||
            fread(value, 1, value_length, file) != value_length) {
            free(key);
            free(value);
            break;
        }
        key[key_length] = '\0';
        value[value_length] = '\0';
        if (!ensure_capacity(database)) {
            free(key);
            free(value);
            break;
        }
        database->entries[database->count].key = key;
        database->entries[database->count].value = value;
        database->count++;
    }
    fclose(file);
    return database;
}

void db_close(db_t *database) {
    size_t index;
    if (database == NULL) {
        return;
    }
    for (index = 0; index < database->count; index++) {
        free(database->entries[index].key);
        free(database->entries[index].value);
    }
    free(database->entries);
    free(database->path);
    free(database);
}

int db_put(db_t *database, const char *key, const char *value) {
    long index = find_index(database, key);
    if (index < (long)database->count && strcmp(database->entries[index].key, key) == 0) {
        char *copy = strdup(value);
        if (copy == NULL) {
            return 0;
        }
        free(database->entries[index].value);
        database->entries[index].value = copy;
        return 1;
    }
    if (!ensure_capacity(database)) {
        return 0;
    }
    memmove(&database->entries[index + 1], &database->entries[index],
            (database->count - (size_t)index) * sizeof(struct entry));
    database->entries[index].key = strdup(key);
    database->entries[index].value = strdup(value);
    if (database->entries[index].key == NULL || database->entries[index].value == NULL) {
        return 0;
    }
    database->count++;
    return 1;
}

const char *db_get(db_t *database, const char *key) {
    long index = find_index(database, key);
    if (index < (long)database->count && strcmp(database->entries[index].key, key) == 0) {
        return database->entries[index].value;
    }
    return NULL;
}

int db_delete(db_t *database, const char *key) {
    long index = find_index(database, key);
    if (index >= (long)database->count || strcmp(database->entries[index].key, key) != 0) {
        return 0;
    }
    free(database->entries[index].key);
    free(database->entries[index].value);
    memmove(&database->entries[index], &database->entries[index + 1],
            (database->count - (size_t)index - 1u) * sizeof(struct entry));
    database->count--;
    return 1;
}

size_t db_count(db_t *database) {
    return database->count;
}

int db_save(db_t *database) {
    FILE *file = fopen(database->path, "wb");
    unsigned int count = (unsigned int)database->count;
    unsigned int index;
    if (file == NULL) {
        return 0;
    }
    fwrite(&count, sizeof(count), 1, file);
    for (index = 0; index < count; index++) {
        unsigned int key_length = (unsigned int)strlen(database->entries[index].key);
        unsigned int value_length = (unsigned int)strlen(database->entries[index].value);
        fwrite(&key_length, sizeof(key_length), 1, file);
        fwrite(&value_length, sizeof(value_length), 1, file);
        fwrite(database->entries[index].key, 1, key_length, file);
        fwrite(database->entries[index].value, 1, value_length, file);
    }
    fclose(file);
    return 1;
}

int db_dump(db_t *database) {
    size_t index;
    for (index = 0; index < database->count; index++) {
        printf("%s = %s\n", database->entries[index].key, database->entries[index].value);
    }
    return (int)database->count;
}
