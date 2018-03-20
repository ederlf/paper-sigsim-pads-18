#include <stdio.h>
#include <stdlib.h>
#include "uthash.h"

struct super_test {
	struct test *tests;
};

struct test {
	int key;
	int value;
	UT_hash_handle hh;
};

void add_value(struct super_test *super, struct test *t)
{
	printf("(t)->key) %d\n", t->key);
	HASH_ADD(hh, super->tests, key, sizeof(int), t);
}

void change_value(struct super_test *super, int key, int value)
{
	struct test *found;
	HASH_FIND(hh, super->tests, &key, sizeof(int), found);
	if (found) {
		printf("Found\n");
		found->value = value;
	}
}


int main(int argc, char const *argv[])
{

	struct test *test_arr[2]; 
	struct super_test super;
	super.tests = NULL;
	struct test *t = malloc(sizeof(struct test));
	t->key = 1;
	t->value = 2;
	test_arr[0] = t;
	add_value(&super, t);
	change_value(&super, 1, 10);
	printf("Value %d\n", test_arr[0]->value);
	/* code */
	return 0;
}