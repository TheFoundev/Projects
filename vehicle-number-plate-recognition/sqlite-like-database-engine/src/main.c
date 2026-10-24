#include "db.h"

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "demo.db";
    db_t *database = db_open(path);
    if (database == NULL) {
        fprintf(stderr, "could not open %s\n", path);
        return 1;
    }
    if (argc > 3 && strcmp(argv[2], "put") == 0) {
        db_put(database, argv[3], argc > 4 ? argv[4] : "");
        db_save(database);
        printf("stored %s\n", argv[3]);
    } else if (argc > 3 && strcmp(argv[2], "get") == 0) {
        const char *value = db_get(database, argv[3]);
        printf("%s\n", value != NULL ? value : "(not found)");
    } else if (argc > 3 && strcmp(argv[2], "delete") == 0) {
        printf("%s\n", db_delete(database, argv[3]) ? "deleted" : "missing");
        db_save(database);
    } else {
        db_put(database, "name", "foundev");
        db_put(database, "kind", "student database");
        db_put(database, "pages", "array index");
        db_save(database);
        printf("record count: %zu\n", db_count(database));
        db_dump(database);
    }
    db_close(database);
    return 0;
}
