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

#include <stdint.h>

#include "chipinfo_avr.h"

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))

static avr_chipinfo_t chips[] =
{
    { { 0x1E, 0x93, 0x07 }, "ATmega8",      0x2000, 0x200 },
    { { 0x1E, 0x93, 0x0A }, "ATmega88",     0x2000, 0x200 },
    { { 0x1E, 0x93, 0x0B }, "ATtiny85",     0x2000, 0x200 },
    { { 0x1E, 0x94, 0x06 }, "ATmega168",    0x4000, 0x200 },
    { { 0x1E, 0x95, 0x02 }, "ATmega32",     0x8000, 0x400 },
    { { 0x1E, 0x95, 0x0F }, "ATmega328p",   0x8000, 0x400 },
    { { 0x1E, 0x95, 0x87 }, "ATmega32u4",   0x8000, 0x400 },
};

/* *************************************************************************
 * chipinfo_get_by_signature
 * ************************************************************************* */
const avr_chipinfo_t * chipinfo_get_by_signature(const uint8_t *sig)
{
    unsigned int i;

    for (i = 0; i < ARRAY_SIZE(chips); i++)
    {
        avr_chipinfo_t *chip = &chips[i];

        if ((chip->sig[0] == sig[0]) &&
            (chip->sig[1] == sig[1]) &&
            (chip->sig[2] == sig[2])
           )
        {
            return chip;
        }
    }

    return NULL;
} /* chipinfo_get_by_signature */


/* *************************************************************************
 * chipinfo_get_avr_name
 * ************************************************************************* */
const char * chipinfo_get_avr_name(const uint8_t *sig)
{
    const avr_chipinfo_t * p_chipinfo;

    p_chipinfo = chipinfo_get_by_signature(sig);

    return (p_chipinfo != NULL) ? p_chipinfo->name : "unknown";
} /* chipinfo_get_avr_name */
