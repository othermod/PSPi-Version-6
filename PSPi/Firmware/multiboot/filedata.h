#ifndef _FILEDATA_H_
#define _FILEDATA_H_

#include <stdint.h>

struct databuf {
    uint32_t size;      // allocation size
    uint32_t length;    // used size
    uint8_t data[0];
};

struct databuf * dbuf_alloc(uint32_t size);
void dbuf_free(struct databuf *dbuf);

int file_getsize(const char *filename, uint32_t *size);
int file_read(const char *filename, struct databuf *dbuf);
int file_write(const char *filename, struct databuf *dbuf);

#endif /* _FILEDATA_H_ */
