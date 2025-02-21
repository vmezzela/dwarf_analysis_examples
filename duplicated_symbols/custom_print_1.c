#include <stdio.h>
#include "custom_print.h"

static void custom_print (char *str) {
	printf("%s", str);
}

void custom_print_1 (char *str) {
	char buffer[LEN];
	snprintf(buffer, LEN, "%s from [1]\n", str);
	custom_print(buffer);
}
