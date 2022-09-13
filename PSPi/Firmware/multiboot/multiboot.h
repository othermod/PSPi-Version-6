#ifndef _MULTIBOOT_H_
#define _MULTIBOOT_H_

#include <stdint.h>
#include "filedata.h"

struct multiboot
{
    struct multiboot_ops *ops;
    void *privdata;

    int verify;
    void (* progress_cb)(const char *msg, int pos, int max);
};

struct multiboot_ops
{
    const char * exec_name;

    struct multiboot * (* alloc)(void);
    void (* free)(struct multiboot *mboot);

    int (* get_memtype)(struct multiboot *mboot, const char *memname);
    uint32_t (* get_memsize)(struct multiboot *mboot, int memtype);

    int (* open)(struct multiboot *mboot);
    int (* close)(struct multiboot *mboot);

    int (* read)(struct multiboot *mboot, struct databuf *dbuf, int memtype);
    int (* verify)(struct multiboot *mboot, struct databuf *dbuf, int memtype);
    int (* write)(struct multiboot *mboot, struct databuf *dbuf, int memtype);
};

extern struct multiboot_ops twi_ops;
extern struct multiboot_ops mpm_ops;
extern struct multiboot_ops funk_ops;
extern struct multiboot_ops eprog_ops;
extern struct multiboot_ops butterfly_ops;

#endif /* _MULTIBOOT_H_ */
