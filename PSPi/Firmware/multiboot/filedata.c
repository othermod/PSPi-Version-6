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

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "filedata.h"

#define FILETYPE_UNKNOWN	0
#define FILETYPE_BINARY		1
#define FILETYPE_INTELHEX	2

/* *************************************************************************
 * dbuf_alloc
 * ************************************************************************* */
struct databuf * dbuf_alloc(uint32_t size)
{
    struct databuf *dbuf = malloc(sizeof(struct databuf) + size);
    if (dbuf == NULL)
    {
        perror("dbuf_alloc");
        return NULL;
    }

    memset(dbuf->data, 0xFF, size);
    dbuf->size = size;
    dbuf->length = 0;
    return dbuf;
} /* dbuf_alloc */


/* *************************************************************************
 * dbuf_free
 * ************************************************************************* */
void dbuf_free(struct databuf *dbuf)
{
    free(dbuf);
} /* dbuf_free */


/* *************************************************************************
 * dbuf_dump
 * ************************************************************************* */
static void dbuf_dump(struct databuf *dbuf)
{
    uint32_t pos = 0;
    int oldskip = 0;

    while (pos < dbuf->length)
    {
        char buf[128];
        int j, i = 0;

        int skip = 1;
        for (j = 0; j < 16; j++)
        {
            if (pos + j < dbuf->length)
            {
                i += sprintf(buf + i, "%02X", dbuf->data[pos + j]);
            } else {
                i += sprintf(buf + i, "  ");
            }

            if (j % 2)
            {
                buf[i++] = ' ';
            }
        }

        for (j = 0; j < 16; j++)
        {
            if (pos + j < dbuf->length)
            {
                unsigned char val = dbuf->data[pos + j];

                if (val >= 0x20 && val < 0x7F)
                {
                    buf[i++] = val;
                } else {
                    buf[i++] = '.';
                }

                if (val != 0xFF)
                {
                    skip = 0;
                }
            }
            else
            {
                buf[i++] = ' ';
            }
        }

        if ((pos == 0) ||
            ((pos + 16) >= dbuf->length) ||
            (skip == 0)
           )
        {
            buf[i++] = '\0';
            printf("%04X: %s\r\n", pos, buf);
            oldskip = 0;

        }
        else if ((skip == 1) &&
                 (oldskip == 0)
                )
        {
            printf("****\n");
            oldskip = 1;
        }

        pos += 16;
    }
} /* dbuf_dump */


/* *************************************************************************
 * binfile_getsize
 * ************************************************************************* */
static int binfile_getsize(const char *filename, uint32_t *size)
{
    int fd = open(filename, O_RDONLY);
    if (fd < 0)
    {
        perror("binfile_getsize(): open()");
        return -1;
    }

    struct stat filestat;
    if (fstat(fd, &filestat) < 0)
    {
        perror("binfile_getsize(): fstat()");
        close(fd);
        return -1;
    }

    *size = filestat.st_size;

    close(fd);
    return 0;
} /* binfile_getsize */


/* *************************************************************************
 * binfile_read
 * ************************************************************************* */
static int binfile_read(const char *filename, struct databuf *dbuf)
{
    int fd = open(filename, O_RDONLY);
    if (fd < 0)
    {
        perror("binfile_read(): open()");
        return -1;
    }

    ssize_t readsize = read(fd, dbuf->data, dbuf->size);
    if (readsize <= 0)
    {
        perror("binfile_read(): read()");
        close(fd);
        return -1;
    }

    dbuf->length = readsize;

    close(fd);
    return 0;
} /* binfile_read */


/* *************************************************************************
 * binfile_write
 * ************************************************************************* */
static int binfile_write(const char *filename, struct databuf *dbuf)
{
    int fd = open(filename, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0)
    {
        perror("binfile_write(): open()");
        return -1;
    }

    ssize_t writesize = write(fd, dbuf->data, dbuf->length);
    if (writesize != dbuf->length)
    {
        perror("binfile_write(): write()");
        close(fd);
        return -1;
    }

    close(fd);
    return 0;
} /* binfile_write */


struct ihex_record
{
    uint8_t byte_count;
    uint16_t address;
    uint8_t type;

    uint8_t *data;
    uint8_t chksum;
};


/* *************************************************************************
 * hex2byte
 * ************************************************************************* */
static uint8_t hex2byte(const char *ptr)
{
    int i;
    uint8_t result = 0;

    for (i = 0; i < 2; i++)
    {
        result <<= 4;
        result |= (ptr[i] >= '0' && ptr[i] <= '9') ? (ptr[i] - '0')
                                                   : (((ptr[i] & 0xDF) >= 'A' && (ptr[i] & 0xDF) <= 'F') ? (ptr[i] - 'A' + 0x0A)
                                                                                                         : 0x00);
    }

    return result;
} /* hex2byte */


/* *************************************************************************
 * hexfile_getrecord
 * ************************************************************************* */
static int hexfile_getrecord(FILE *stream, struct ihex_record *record)
{
    char *hexline = NULL;
    size_t size;

    ssize_t length = getline(&hexline, &size, stream);
    if (length == -1)
    {
        if (!feof(stream))
        {
            perror("hexfile_getrecord(): getline()");
        }

        return -1;
    }

    if (length < 12)
    {
        fprintf(stderr, "record too short (%ld)\n", length);
        free(hexline);
        return -1;
    }

    int pos = 0;
    if (hexline[pos] != ':')
    {
        fprintf(stderr, "invalid startcode\n");
        free(hexline);
        return -1;
    }

    pos++;

    uint8_t chksum = 0x00;

    record->byte_count = hex2byte(&hexline[pos]);
    chksum += record->byte_count;
    pos += 2;

    if (record->byte_count > 0)
    {
        record->data = malloc(record->byte_count);
        if (record->data == NULL)
        {
            perror("hexfile_getrecord(): malloc()");
            free(hexline);
            return -1;
        }
    }

    uint8_t hiaddr = hex2byte(&hexline[pos]);
    uint8_t loaddr = hex2byte(&hexline[pos +2]);
    record->address = (hiaddr << 8) + loaddr;
    chksum += hiaddr + loaddr;
    pos += 4;

    record->type = hex2byte(&hexline[pos]);
    chksum += record->type;
    pos += 2;

    int i;
    for (i = 0; i < record->byte_count; i++)
    {
        record->data[i] = hex2byte(&hexline[pos]);
        chksum += record->data[i];
        pos += 2;
    }

    record->chksum = hex2byte(&hexline[pos]);
    chksum += record->chksum;
    pos += 2;

    if (chksum != 0x00)
    {
        fprintf(stderr, "invalid checksum (0x%02X)\n", chksum);
        if (record->byte_count > 0)
        {
            free(record->data);
        }

        free(hexline);
        return -1;
    }

    free(hexline);
    return 0;
} /* hexfile_getrecord */


/* *************************************************************************
 * hexfile_putrecord
 * ************************************************************************* */
static int hexfile_putrecord(FILE *stream, struct ihex_record *record)
{
    uint8_t chksum = record->byte_count;
    chksum += (record->address >> 8) & 0xFF;
    chksum += (record->address & 0xFF);
    chksum += record->type;

    int i, len = 0;
    char buf[64];

    buf[0] = '\0';
    for (i = 0; i < record->byte_count; i++)
    {
        len += snprintf(buf + len, sizeof(buf) - len, "%02X", record->data[i]);
        chksum += record->data[i];
    }

    fprintf(stream, ":%02X%04X%02X%s%02X\n",
            record->byte_count,
            record->address,
            record->type,
            buf,
            (uint8_t)(0x100 - chksum));

    return -1;
} /* hexfile_putrecord */


/* *************************************************************************
 * hexfile_getsize
 * ************************************************************************* */
static int hexfile_getsize(const char *filename, uint32_t *size)
{
    /* unused parameter */
    (void)filename;

    *size = 0x10000;
    return 0;
} /* hexfile_getsize */


/* *************************************************************************
 * hexfile_read
 * ************************************************************************* */
static int hexfile_read(const char *filename, struct databuf *dbuf)
{
    FILE *stream = fopen(filename, "r");
    if (stream == NULL)
    {
        perror("hexfile_read(): fopen()");
        return -1;
    }

    while (1)
    {
        struct ihex_record record;
        memset(&record, 0x00, sizeof(struct ihex_record));

        int result = hexfile_getrecord(stream, &record);
        if (result == -1)
        {
            break;
        }

        if (record.type == 0x00)
        {
            if ((record.address > dbuf->size) ||
                (record.address + record.byte_count > dbuf->size)
               )
            {
                fprintf(stderr, "hexfile_read(): data out of bounds\n");
                break;
            }

            memcpy(&dbuf->data[record.address], record.data, record.byte_count);
            dbuf->length = record.address + record.byte_count;
        }
    }

    fclose(stream);
    return 0;
} /* hexfile_read */


/* *************************************************************************
 * hexfile_write
 * ************************************************************************* */
static int hexfile_write(const char *filename, struct databuf *dbuf)
{
    FILE *stream = fopen(filename, "w");
    if (stream == NULL)
    {
        perror("hexfile_write(): fopen()");
        return -1;
    }

    uint32_t i;
    uint32_t addr_min = dbuf->length;
    uint32_t addr_max = 0;
    for (i = 0; i < dbuf->length; i++)
    {
        if (dbuf->data[i] == 0xFF)
        {
            continue;
        }

        if (addr_min > i)
        {
            addr_min = i;
        }

        if (addr_max < i)
        {
            addr_max = i;
        }
    }

    if (addr_min >= addr_max)
    {
        addr_min = 0;
        addr_max = dbuf->length;
    }

    addr_min = addr_min & ~0x0F;
    addr_max = (addr_max + 0x0F) & ~0x0F;

    struct ihex_record record;
    for (i = addr_min; i < addr_max; i += 0x10)
    {
        record.byte_count = 0x10;
        record.address = i;
        record.type = 0x00;
        record.data = &dbuf->data[i];

        hexfile_putrecord(stream, &record);
    }

    record.byte_count = 0x00;
    record.address = addr_min;
    record.type = 0x01;
    record.data = NULL;
    hexfile_putrecord(stream, &record);

    fclose(stream);
    return 0;
} /* hexfile_write */


/* *************************************************************************
 * get_filetype
 * ************************************************************************* */
static int get_filetype(const char *filename)
{
    const char *ext = filename + (strlen(filename) -4);

    if (ext < filename)
    {
        return FILETYPE_UNKNOWN;
    }

    if (strncmp(ext, ".bin", 4) == 0)
    {
        return FILETYPE_BINARY;
    }

    if (strncmp(ext, ".hex", 4) == 0)
    {
        return FILETYPE_INTELHEX;
    }

    return FILETYPE_UNKNOWN;
} /* get_filetype */


/* *************************************************************************
 * file_getsize
 * ************************************************************************* */
int file_getsize(const char *filename, uint32_t *size)
{
    switch (get_filetype(filename))
    {
        case FILETYPE_BINARY:
            return binfile_getsize(filename, size);

        case FILETYPE_INTELHEX:
            return hexfile_getsize(filename, size);

        default:
            return -1;
    }
} /* file_getsize */


/* *************************************************************************
 * file_read
 * ************************************************************************* */
int file_read(const char *filename, struct databuf *dbuf)
{
    switch (get_filetype(filename))
    {
        case FILETYPE_BINARY:
            return binfile_read(filename, dbuf);

        case FILETYPE_INTELHEX:
            return hexfile_read(filename, dbuf);

        default:
            return -1;
    }
} /* file_read */


/* *************************************************************************
 * file_write
 * ************************************************************************* */
int file_write(const char *filename, struct databuf *dbuf)
{
    if (strncmp(filename, "-", 1) == 0)
    {
        dbuf_dump(dbuf);
        return 0;
    }

    switch (get_filetype(filename))
    {
        case FILETYPE_BINARY:
            return binfile_write(filename, dbuf);

        case FILETYPE_INTELHEX:
            return hexfile_write(filename, dbuf);

        default:
            return -1;
    }
} /* file_write */
