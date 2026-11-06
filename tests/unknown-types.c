/* SPDX-License-Identifier: Apache-2.0 */
/* Test-only: emulate a filesystem whose directory listing omits entry types. */
#define _GNU_SOURCE
#include <dirent.h>
#include <dlfcn.h>
#include <stdlib.h>
struct dirent *readdir(DIR *directory) {
    static struct dirent *(*next)(DIR *);
    if (!next) {
        next = (struct dirent *(*)(DIR *))dlsym(RTLD_NEXT, "readdir");
        if (!next) abort();
    }
    struct dirent *entry = next(directory);
    if (entry) entry->d_type = DT_UNKNOWN;
    return entry;
}
