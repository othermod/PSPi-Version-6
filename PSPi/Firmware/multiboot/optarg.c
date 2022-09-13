/***************************************************************************
*   Copyright (C) 10/2010 by Olaf Rempel                                  *
*   razzor@kopf-tisch.de                                                  *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; version 2 of the License,               *
*                                                                         *
*   This program is distributed in the hope that it will be useful,       *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
*   GNU General Public License for more details.                          *
*                                                                         *
*   You should have received a copy of the GNU General Public License     *
*   along with this program; if not, write to the                         *
*   Free Software Foundation, Inc.,                                       *
*   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
***************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <getopt.h>

#include "list.h"
#include "optarg.h"

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))

struct optarg_entry
{
    struct list_head list;
    const struct option *opts;
    int count;

    int (* parser_cb)(int val, const char *arg, void *privdata);
    void *privdata;
};

static LIST_HEAD(option_list);


/* *************************************************************************
 * optarg_register
 * ************************************************************************* */
int optarg_register(const struct option *opts, int count,
                    int (* parser_cb)(int val, const char *arg, void *privdata),
                    void *privdata)
{
    struct optarg_entry *entry;

    entry = malloc(sizeof(struct optarg_entry));
    if (entry == NULL)
    {
        return -1;
    }

    entry->opts         = opts;     /* TODO: copy? */
    entry->count        = count;
    entry->parser_cb    = parser_cb;
    entry->privdata     = privdata;

    list_add_tail(&entry->list, &option_list);
    return 0;
} /* optarg_register */


/* *************************************************************************
 * optarg_free
 * ************************************************************************* */
void optarg_free(void)
{
    struct optarg_entry *entry, *entry_tmp;

    list_for_each_entry_safe(entry, entry_tmp, &option_list, list)
    {
        list_del(&entry->list);
        free(entry);
    }
} /* optarg_free */


/* *************************************************************************
 * optarg_getsize
 * ************************************************************************* */
static void optarg_getsize(int *opt_count, int *optstring_len)
{
    int count  = 0;
    int length = 0;

    struct optarg_entry *entry;

    list_for_each_entry(entry, &option_list, list)
    {
        count += entry->count;

        int i;
        for (i = 0; i < entry->count; i++)
        {
            switch (entry->opts[i].has_arg)
            {
                case 0: /* no arguments */
                case 1: /* has argument */
                case 2: /* optional argument */
                    length += entry->opts[i].has_arg +1;
                    break;

                default:
                    break;
            }
        }
    }

    *opt_count     = count  +1;
    *optstring_len = length +1;
} /* optarg_getsize */


/* *************************************************************************
 * optarg_copy
 * ************************************************************************* */
static void optarg_copy(struct option *opts, char *optstring)
{
    struct optarg_entry *entry;

    list_for_each_entry(entry, &option_list, list)
    {
        memcpy(opts, entry->opts, sizeof(struct option) * entry->count);
        opts += entry->count;

        int i;
        for (i = 0; i < entry->count; i++)
        {
            switch (entry->opts[i].has_arg)
            {
                case 0: /* no arguments */
                    *optstring++ = (char)entry->opts[i].val;
                    break;

                case 1: /* has argument */
                    *optstring++ = (char)entry->opts[i].val;
                    *optstring++ = ':';
                    break;

                case 2: /* optional argument */
                    *optstring++ = (char)entry->opts[i].val;
                    *optstring++ = ':';
                    *optstring++ = ':';
                    break;

                default:
                    break;
            }
        }
    }

    memset(opts++, 0x00, sizeof(struct option));
    *optstring++ = '\0';
} /* optarg_copy */


/* *************************************************************************
 * optarg_parse
 * ************************************************************************* */
int optarg_parse(int argc, char * const argv[])
{
    struct option *longopts;
    char *optstring;

    int opt_count;
    int optstring_len;
    optarg_getsize(&opt_count, &optstring_len);

    longopts = malloc(sizeof(struct option) * opt_count);
    if (longopts == NULL)
    {
        return -1;
    }

    optstring = malloc(optstring_len);
    if (optstring == NULL)
    {
        free(longopts);
        return -1;
    }

    optarg_copy(longopts, optstring);

    int retval = 0;
    int val = 0;
    while (val != -1 && retval == 0)
    {
        opterr = 1; /* print error message to stderr */
        val = getopt_long(argc, argv, optstring, longopts, NULL);

        /* variable assigned (not supported) */
        if (val == 0x00)
        {
            continue;
        }

        struct optarg_entry *entry;
        list_for_each_entry(entry, &option_list, list)
        {
            int ret = entry->parser_cb(val, optarg, entry->privdata);

            /* option recognized, with error */
            if (ret < 0)
            {
                retval = ret;
                break;
            }
            /* option recognized, no error */
            else if (ret == 0)
            {
                break;
            }
        }

        /* parsing completed */
        if (val == -1)
        {
            break;
        }

        /* parsing error */
        if (val == '?')
        {
            retval = 1;
            break;
        }
    }

    free(optstring);
    free(longopts);

    return retval;
} /* optarg_parse */
