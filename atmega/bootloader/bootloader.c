/*
 * TWI/I2C Bootloader for ATmega8
 * Concept inspired by twiboot by Olaf Rempel <razzor@kopf-tisch.de>
 */

#include <avr/io.h>
#include <avr/boot.h>
#include <avr/pgmspace.h>

#define BOOTLOADER_VERSION          0x01

#define TWI_ADDRESS                 0x29

#define TIMER_DIVISOR               1024
#define TIMER_IRQFREQ_MS            25
#define TIMEOUT_MS                  1000

#define TIMER_MSEC2TICKS(x)         ((x * F_CPU) / (TIMER_DIVISOR * 1000ULL))
#define TIMER_MSEC2IRQCNT(x)        (x / TIMER_IRQFREQ_MS)
#define TIMER_RELOAD_VALUE          (0xFF - TIMER_MSEC2TICKS(TIMER_IRQFREQ_MS))

/* I2C protocol commands */
#define CMD_ABORT_TIMEOUT           0x00
#define CMD_READ_INFO               0x01
#define CMD_SET_PAGE             0x02
#define CMD_WRITE_PAGE              0x03
#define CMD_READ_PAGE              0x04
#define CMD_FINALIZE                0x05

/* TWI slave receiver status codes (ATmega8 datasheet table 22-2) */
#define TWI_SR_SLA_ACK              0x60    /* SLA+W received, ACK returned */
#define TWI_SR_DATA_ACK             0x80    /* data received, ACK returned */
#define TWI_SR_DATA_NACK            0x88    /* data received, NACK returned */
#define TWI_SR_STOP                 0xA0    /* STOP or repeated START received */

/* TWI slave transmitter status codes (ATmega8 datasheet table 22-3) */
#define TWI_ST_SLA_ACK              0xA8    /* SLA+R received, ACK returned */
#define TWI_ST_DATA_ACK             0xB8    /* data sent, ACK received */
#define TWI_ST_DATA_NACK            0xC0    /* data sent, NACK received */
#define TWI_ST_LAST_ACK             0xC8    /* last data byte sent, ACK received */

/* bootloader run modes */
#define BL_RUNNING                  0x00
#define BL_BOOT_APP                 0x01

/* TWI ACK control helpers */
#define TWI_CLEAR_ACK(ctrl)         ((ctrl) &= ~(1<<TWEA))
#define TWI_SET_ACK(ctrl)           ((ctrl) |=  (1<<TWEA))

static uint8_t  bl_mode        = BL_RUNNING;
static uint8_t  timeout_ticks  = TIMER_MSEC2IRQCNT(TIMEOUT_MS);
static uint8_t  button_override = 0;

static uint8_t  page_buf[SPM_PAGESIZE];
static uint16_t flash_addr;


static uint8_t flash_is_blank(void)
{
    uint16_t i;
    for (i = 0; i < BOOTLOADER_START; i++)
    {
        if (pgm_read_byte_near(i) != 0xFF)
            return 0;
    }
    return 1;
}


static void write_flash_page(void)
{
    uint16_t pagestart = flash_addr;
    uint8_t  i;

    boot_page_erase(pagestart);
    boot_spm_busy_wait();

    /* fill page buffer word by word; flash_addr advances as a side effect */
    for (i = 0; i < SPM_PAGESIZE; i += 2)
    {
        uint16_t word = page_buf[i] | ((uint16_t)page_buf[i + 1] << 8);
        boot_page_fill(flash_addr, word);
        flash_addr += 2;
    }

    boot_page_write(pagestart);
    boot_spm_busy_wait();
    boot_rww_enable();
}


static void twi_handle(void)
{
    static uint8_t cmd = CMD_ABORT_TIMEOUT;
    /* byte_cnt counts received bytes in the RX path and sent bytes in the TX path */
    static uint8_t byte_cnt;
    static uint8_t page_write_pending;

    uint8_t twi_ctrl   = TWCR;
    uint8_t twi_status = TWSR & 0xF8;

    switch (twi_status)
    {
        case TWI_SR_SLA_ACK:
            byte_cnt           = 0;
            page_write_pending = 0;
            break;

        case TWI_SR_DATA_ACK:
        {
            uint8_t rx_data = TWDR;

            if (byte_cnt == 0)
            {
                cmd = rx_data;
                switch (cmd)
                {
                    case CMD_ABORT_TIMEOUT:
                        timeout_ticks = 0;
                        PORTC |= (1<<PC3);
                        break;

                    case CMD_FINALIZE:
                        bl_mode = BL_BOOT_APP;
                        break;

                    /* valid commands; no immediate action on receipt of command byte */
                    case CMD_READ_INFO:
                    case CMD_SET_PAGE:
                    case CMD_WRITE_PAGE:
                    case CMD_READ_PAGE:
                        break;

                    default:
                        TWI_CLEAR_ACK(twi_ctrl);
                        break;
                }
            }
            else
            {
                switch (cmd)
                {
                    case CMD_SET_PAGE:
                        if (byte_cnt == 1)
                        {
                            if (rx_data >= (BOOTLOADER_START / SPM_PAGESIZE))
                                TWI_CLEAR_ACK(twi_ctrl);
                            else
                                flash_addr = (uint16_t)rx_data * SPM_PAGESIZE;
                        }
                        break;

                    case CMD_WRITE_PAGE:
                    {
                        uint8_t buf_pos = byte_cnt - 1;
                        page_buf[buf_pos] = rx_data;
                        if (buf_pos >= (SPM_PAGESIZE - 1))
                        {
                            page_write_pending = 1;
                            TWI_CLEAR_ACK(twi_ctrl);
                        }
                        break;
                    }

                    default:
                        break;
                }
            }

            byte_cnt++;
            break;
        }

        /* master sent more data than expected — treat as end of transaction */
        case TWI_SR_DATA_NACK:
            /* fall through */

        case TWI_SR_STOP:
            if (page_write_pending)
            {
                page_write_pending = 0;
                /* hold off ACK while flash write is in progress */
                TWI_CLEAR_ACK(twi_ctrl);
                TWCR = (1<<TWINT) | twi_ctrl;
                write_flash_page();
            }
            byte_cnt = 0;
            TWI_SET_ACK(twi_ctrl);
            break;

        case TWI_ST_SLA_ACK:
            byte_cnt = 0;
            /* fall through */

        case TWI_ST_DATA_ACK:
        {
            uint8_t tx_data = 0xFF;

            switch (cmd)
            {
                case CMD_READ_INFO:
                    switch (byte_cnt)
                    {
                        case 0: tx_data = SIGNATURE_0;                     break;
                        case 1: tx_data = SIGNATURE_1;                     break;
                        case 2: tx_data = SIGNATURE_2;                     break;
                        case 3: tx_data = BOOTLOADER_VERSION;              break;
                        case 4: tx_data = BOOTLOADER_START / SPM_PAGESIZE; break;
                        default: tx_data = 0xFF;                           break;
                    }
                    break;

                case CMD_READ_PAGE:
                    tx_data = pgm_read_byte_near(flash_addr++);
                    if (byte_cnt >= SPM_PAGESIZE - 1)
                        TWI_CLEAR_ACK(twi_ctrl);
                    break;

                default:
                    break;
            }

            TWDR = tx_data;
            byte_cnt++;
            break;
        }

        case TWI_ST_DATA_NACK:
        case TWI_ST_LAST_ACK:
            TWI_SET_ACK(twi_ctrl);
            break;

        default:
            /* unexpected TWI state — set TWSTO to reset the bus */
            twi_ctrl |= (1<<TWSTO);
            break;
    }

    TWCR = (1<<TWINT) | twi_ctrl;
}


static void timer_tick(void)
{
    TCNT0 = TIMER_RELOAD_VALUE;

    /* if button was held at boot but has since been released, disqualify */
    if (button_override && (PINC & (1<<PC2)))
        button_override = 0;

    if (timeout_ticks > 1)
    {
        timeout_ticks--;
    }
    else if (timeout_ticks == 1)
    {
        timeout_ticks = 0;

        if (button_override || flash_is_blank())
            PORTC |= (1<<PC3);  /* hold active — button override or blank firmware */
        else
            bl_mode = BL_BOOT_APP;
    }
}


static void (*jump_to_app)(void) __attribute__((noreturn)) = (void *)0x0000;


void init1(void) __attribute__((naked, section(".init1")));
void init1(void)
{
    asm volatile ("clr __zero_reg__");
    SP = RAMEND;
}


int main(void) __attribute__((OS_main, section(".init9")));
int main(void)
{
    /* PC3: output, initially low — driven high when bootloader holds active */
    DDRC  |= (1<<PC3);
    PORTC &= ~(1<<PC3);

    /* PC2: input with pull-up — held at power-on forces bootloader to stay active */
    DDRC  &= ~(1<<PC2);
    PORTC |=  (1<<PC2);
    button_override = !(PINC & (1<<PC2));

    /* Timer0: F_CPU / 1024 */
    TCCR0 = (1<<CS02) | (1<<CS00);

    /* TWI: set slave address, enable auto-ACK */
    TWAR = (TWI_ADDRESS << 1);
    TWCR = (1<<TWEA) | (1<<TWEN);

    while (bl_mode == BL_RUNNING)
    {
        if (TWCR & (1<<TWINT))
            twi_handle();

        if (TIFR & (1<<TOV0))
        {
            timer_tick();
            TIFR = (1<<TOV0);
        }
    }

    TWCR  = 0x00;
    TCCR0 = 0x00;

    jump_to_app();
}
