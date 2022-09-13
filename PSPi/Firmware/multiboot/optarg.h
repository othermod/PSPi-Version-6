#ifndef _OPTARG_H_
#define _OPTARG_H_

#include <getopt.h>

int optarg_register(const struct option *opts, int count,
                    int (* parser_cb)(int val, const char *arg, void *privdata),
                    void *privdata);


void optarg_free(void);

int optarg_parse(int argc, char * const argv[]);

#endif /* _OPTARG_H_ */
