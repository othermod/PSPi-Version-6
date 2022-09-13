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

#include "filedata.h"
#include "list.h"
#include "multiboot.h"
#include "optarg.h"

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))

#define ACTION_READ     0x01
#define ACTION_WRITE    0x02

static struct multiboot_ops * prog_ops[] =
{
    &twi_ops,
    &mpm_ops,
    &funk_ops,
    &eprog_ops,
    &butterfly_ops,
};

struct mboot_action
{
    struct list_head list;

    char *filename;
    int memtype;
    int mode;
};

static LIST_HEAD(action_list);

static struct option main_optargs[] =
{
    { "help",       0, 0, 'h'}, /* [ -h ]                           */
    { "progress",   1, 0, 'p'}, /* [ -p <0|1|2> ]                   */
    { "read",       1, 0, 'r'}, /* [ -r <flash|eeprom>:<file.hex> ] */
    { "write",      1, 0, 'w'}, /* [ -w <flash|eeprom>:<file.hex> ] */
    { "no-verify",  0, 0, 'n'}, /* [ -n ]                           */
    { 0, 0, 0, 0}
};

/* *************************************************************************
 * progress_mode0_cb
 * ************************************************************************* */
static void progress_mode0_cb(const char *msg, int pos, int size)
{
    /* unused parameter */
    (void)msg;
    (void)pos;
    (void)size;

    /* no progress output */
} /* progress_mode0_cb */


/* *************************************************************************
 * progress_mode1_cb
 * ************************************************************************* */
static void progress_mode1_cb(const char *msg, int pos, int size)
{
    if (pos != -1 && size > 0)
    {
        char stars[51];
        int i;
        int count = (pos * 50 / size);

        for (i = 0; i < 50; i++)
        {
            stars[i] = (i < count) ? '*' : ' ';
        }

        stars[50] = '\0';
        printf("%-15s: [%s] (%d)\r", msg, stars, pos);
    }

    if (pos == size)
    {
        printf("\n");
    }
} /* progress_mode1_cb */


/* *************************************************************************
 * progress_mode2_cb
 * ************************************************************************* */
static void progress_mode2_cb(const char *msg, int pos, int size)
{
    static int old_count;

    if (pos != -1 && size > 0)
    {
        if (pos == 0)
        {
            old_count = 0;
            printf("%-15s: [", msg);

        }
        else if (pos <=size)
        {
            int i;
            int count = (pos * 50 / size);

            for (i = old_count; i < count; i++)
            {
                printf("*");
            }

            old_count = count;

            if (pos == size)
            {
                printf("] (%d)\n", pos);
            }
        }
    }
} /* progress_mode2_cb */


/* *************************************************************************
 * add_action
 * ************************************************************************* */
static int add_action(struct multiboot *mboot, int mode, const char *arg)
{
    struct mboot_action *action = malloc(sizeof(struct mboot_action));
    if (action == NULL)
    {
        perror("malloc()");
        return -1;
    }

    char *argcopy = strdup(arg);
    if (argcopy == NULL)
    {
        perror("strdup()");
        free(action);
        return -1;
    }

    char *tok = strtok(argcopy, ":");
    if (tok == NULL)
    {
        fprintf(stderr, "invalid argument: '%s'\n", arg);
        free(argcopy);
        free(action);
        return -1;
    }

    action->memtype = mboot->ops->get_memtype(mboot, tok);
    if (action->memtype == -1)
    {
        fprintf(stderr, "invalid memtype: '%s'\n", tok);
        free(argcopy);
        free(action);
        return -1;
    }

    tok = strtok(NULL, ":");
    if (tok == NULL)
    {
        fprintf(stderr, "invalid argument: '%s'\n", arg);
        free(argcopy);
        free(action);
        return -1;
    }

    action->filename = strdup(tok);
    if (action->filename == NULL)
    {
        perror("strdup()");
        free(argcopy);
        free(action);
        return -1;
    }

    action->mode = mode;

    list_add_tail(&action->list, &action_list);
    free(argcopy);
    return 0;
} /* add_action */


/* *************************************************************************
 * main_optarg_cb
 * ************************************************************************* */
static int main_optarg_cb(int val, const char *arg, void *privdata)
{
    struct multiboot *mboot = (struct multiboot *)privdata;

    switch (val)
    {
        case 'r': /* read */
            if ((mboot->ops->read == NULL) ||
                (add_action(mboot, ACTION_READ, arg) < 0)
               )
            {
                return -1;
            }
            break;

        case 'w': /* write */
            if ((mboot->ops->write == NULL) ||
                (add_action(mboot, ACTION_WRITE, arg) < 0)
               )
            {
                return -1;
            }
            break;

        case 'n': /* no verify after write */
            mboot->verify = 0;
            break;

        case 'p':
            switch (*arg)
            {
                case '0':
                    mboot->progress_cb = progress_mode0_cb;
                    break;

                case '1':
                    mboot->progress_cb = progress_mode1_cb;
                    break;

                case '2':
                    mboot->progress_cb = progress_mode2_cb;
                    break;

                default:
                    fprintf(stderr, "invalid progress bar mode: '%s'\n", arg);
                    return -1;
            }
            break;
    }

    return 0;
}

/* *************************************************************************
 * main
 * ************************************************************************* */
int main(int argc, char *argv[])
{
    struct multiboot *mboot = NULL;

    char *progname = strrchr(argv[0], '/');
    progname = (progname != NULL) ? (progname +1) : argv[0];

    unsigned int i;
    for (i = 0; i < ARRAY_SIZE(prog_ops); i++)
    {
        struct multiboot_ops * ops = prog_ops[i];

        if (strcmp(progname, ops->exec_name) == 0)
        {
            mboot = ops->alloc();
            if (mboot == NULL)
            {
                fprintf(stderr, "failed to allocate '%s'\n",
                        progname);

                return -1;
            }
        }
    }

    if (mboot == NULL)
    {
        fprintf(stderr, "invalid progname\n");
        return -1;
    }

    mboot->verify      = 1;
    mboot->progress_cb = progress_mode1_cb;

    optarg_register(main_optargs, ARRAY_SIZE(main_optargs),
                    main_optarg_cb, (void *)mboot);

    int abort = optarg_parse(argc, argv);

    if ((abort == -1) ||
        (mboot->ops->open(mboot) != 0)
       )
    {
        return -1;
    }

    setbuf(stdout, NULL);

    struct mboot_action *action, *tmp;
    list_for_each_entry(action, &action_list, list)
    {
        abort = 1;
        if (action->mode == ACTION_READ)
        {
            int memsize = mboot->ops->get_memsize(mboot, action->memtype);
            if (memsize == 0)
            {
                break;
            }

            struct databuf *dbuf = dbuf_alloc(memsize);
            if (dbuf == NULL)
            {
                break;
            }

            int result = mboot->ops->read(mboot, dbuf, action->memtype);
            if (result != 0)
            {
                fprintf(stderr, "failed to read from device\n");
                dbuf_free(dbuf);
                break;
            }

            result = file_write(action->filename, dbuf);
            if (result != 0)
            {
                fprintf(stderr, "failed to write file '%s'\n", action->filename);
                dbuf_free(dbuf);
                break;
            }

            dbuf_free(dbuf);
            abort = 0;

        }
        else if (action->mode == ACTION_WRITE)
        {
            unsigned int size;
            int result;

            result = file_getsize(action->filename, &size);
            if (result != 0)
            {
                break;
            }

            struct databuf *dbuf = dbuf_alloc(size);
            if (dbuf == NULL)
            {
                break;
            }

            result = file_read(action->filename, dbuf);
            if (result != 0)
            {
                fprintf(stderr, "failed to read file '%s'\n", action->filename);
                dbuf_free(dbuf);
                break;
            }

            uint32_t memsize = mboot->ops->get_memsize(mboot, action->memtype);
            if ((memsize == 0) || (memsize < dbuf->length))
            {
                fprintf(stderr, "invalid memsize: 0x%04x > 0x%04x\n", dbuf->length, memsize);
                dbuf_free(dbuf);
                break;
            }

            result = mboot->ops->write(mboot, dbuf, action->memtype);
            if (result != 0)
            {
                fprintf(stderr, "failed to write to device\n");
                dbuf_free(dbuf);
                break;
            }

            if (mboot->verify &&
                (mboot->ops->verify != NULL)
               )
            {
                result = mboot->ops->verify(mboot, dbuf, action->memtype);
                if (result != 0)
                {
                    fprintf(stderr, "failed to verify\n");
                    dbuf_free(dbuf);
                    break;
                }
            }

            dbuf_free(dbuf);
            abort = 0;
        }
    }

    list_for_each_entry_safe(action, tmp, &action_list, list)
    {
        free(action->filename);
        free(action);
    }

    mboot->ops->close(mboot);
    mboot->ops->free(mboot);

    optarg_free();
    return abort;
} /* main */
