#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../src/db.h"

static void test_put_and_get(void) {
    db_t *db = db_open(":memory:");
    assert(db != NULL);

    assert(db_put(db, "greeting", "hello world") == 1);

    const char *found = db_get(db, "greeting");
    assert(found != NULL);
    assert(strcmp(found, "hello world") == 0);
    assert(db_count(db) == 1);

    db_close(db);
}

static void test_delete(void) {
    db_t *db = db_open(":memory:");
    assert(db != NULL);

    assert(db_put(db, "key", "value") == 1);
    assert(db_delete(db, "key") == 1);
    assert(db_get(db, "key") == NULL);
    assert(db_count(db) == 0);

    db_close(db);
}

static void test_a_key_that_is_not_there(void) {
    db_t *db = db_open(":memory:");
    assert(db != NULL);
    assert(db_get(db, "nope") == NULL);
    db_close(db);
}

static void test_the_database_is_written_and_read_back(void) {
    const char *path = "build/test-database.bin";
    remove(path);

    db_t *db = db_open(path);
    assert(db != NULL);
    assert(db_put(db, "answer", "42") == 1);
    assert(db_save(db) == 1);
    db_close(db);

    db_t *again = db_open(path);
    assert(again != NULL);
    const char *found = db_get(again, "answer");
    assert(found != NULL);
    assert(strcmp(found, "42") == 0);
    db_close(again);

    remove(path);
}

int main(void) {
    test_put_and_get();
    test_delete();
    test_a_key_that_is_not_there();
    test_the_database_is_written_and_read_back();
    printf("all database tests passed\n");
    return 0;
}
