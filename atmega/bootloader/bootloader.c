/*
 * TWI/I2C Bootloader for ATmega8
 * Concept inspired by twiboot by Olaf Rempel <razzor@kopf-tisch.de>
 */

#include <avr/io.h>
#include <avr/boot.h>
#include <avr/pgmspace.h>

#define BOOTLOADER_VERSION          0x01
#define TWI_ADDRESS                 0x29
#define BOOTLOADER_START            0x1C00

/* Timer0: F_CPU / 1024, free-running overflow period = 256 * 1024 / F_CPU */
#define TIMER_DIVISOR               1024
#define TIMER_OVF_PER_SEC           (F_CPU / ((uint32_t)TIMER_DIVISOR * 256))

/* I2C protocol commands */
#define CMD_READ_INFO               0x01
#define CMD_SET_PAGE                0x02
#define CMD_WRITE_PAGE              0x03
#define CMD_READ_PAGE               0x04
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
#define BL_HOLD                     0x00
#define BL_JUMP_APP                 0x01

/* TWI ACK control helpers */
#define TWI_CLEAR_ACK(ctrl)         ((ctrl) &= ~(1<<TWEA))
#define TWI_SET_ACK(ctrl)           ((ctrl) |=  (1<<TWEA))

/* Pin definitions */
#define LCD_CONTROL                 (1<<PB2)
#define EN_5V_PIN                   (1<<PB6)
#define LED_WIFI_PIN                ((1<<PB3) | (1<<PB7))
#define RPI_DETECT                  (1<<PD1)
#define BTN_DISP                    (1<<PB0)

static uint8_t          bl_mode            = BL_HOLD;
static uint8_t          blink_fast         = 0;
static uint8_t          page_buf[SPM_PAGESIZE];
static uint16_t         flash_addr;
static volatile uint8_t page_write_pending = 0;
static volatile uint8_t page_load_pending  = 0;


static void load_page_to_buf(uint16_t addr)
{
    uint8_t i;
    for (i = 0; i < SPM_PAGESIZE; i++)
        page_buf[i] = pgm_read_byte_near(addr + i);
}


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
    uint16_t fill_addr = flash_addr;
    uint8_t  i;

    boot_page_erase(pagestart);
    boot_spm_busy_wait();

    for (i = 0; i < SPM_PAGESIZE; i += 2)
    {
        uint16_t word = page_buf[i] | ((uint16_t)page_buf[i + 1] << 8);
        boot_page_fill(fill_addr, word);
        fill_addr += 2;
    }

    boot_page_write(pagestart);
    boot_spm_busy_wait();
    boot_rww_enable();
}


static void twi_handle(void)
{
    static uint8_t cmd = 0;
    /* byte_cnt counts received bytes in the RX path and sent bytes in the TX path */
    static uint8_t byte_cnt;

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
                    /* valid commands; no immediate action on receipt of command byte */
                    case CMD_READ_INFO:
                    case CMD_SET_PAGE:
                    case CMD_WRITE_PAGE:
                    case CMD_READ_PAGE:
                        break;

                    case CMD_FINALIZE:
                        blink_fast = 1;
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

        /* master sent more data than expected; treat as end of transaction */
        case TWI_SR_DATA_NACK:
            /* fall through */

            case TWI_SR_STOP:
                if (page_write_pending)
                {
                    /* Flash write is deferred to the main loop to avoid holding
                     * SCL low for the full 4.5ms erase+program cycle. Keep TWEA
                     * cleared so the host's ACK poll sees NACK until we're done. */
                    TWI_CLEAR_ACK(twi_ctrl);
                }
                else
                {
                    if (cmd == CMD_SET_PAGE)
                        page_load_pending = 1;
                    byte_cnt = 0;
                    TWI_SET_ACK(twi_ctrl);
                }
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
                                    tx_data = page_buf[byte_cnt];
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
                                    /* unexpected TWI state; set TWSTO to reset the bus */
                                    twi_ctrl |= (1<<TWSTO);
                                    break;
    }

    TWCR = (1<<TWINT) | twi_ctrl;
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
    /* Outputs: PB2 (LCD_CONTROL), PB3/PB7 (LED_WIFI), PB6 (EN_5V); all others inputs with pull-ups */
    DDRB  = 0b11001100;
    PORTB = 0b00000001;
    DDRD  = 0b00000000;
    PORTD = 0b00000000;

    /* Timer0: F_CPU / 1024, free-running */
    TCCR0 = (1<<CS02) | (1<<CS00);

    /* TWI: set slave address, enable auto-ACK */
    TWAR  = (TWI_ADDRESS << 1);
    TWCR  = (1<<TWEA) | (1<<TWEN);

    /* --- BOOT ENTRY LOGIC --- */
    if (PINB & BTN_DISP)
    {
        /* Button not pressed: boot app if flash is not blank */
        if (!flash_is_blank())
            bl_mode = BL_JUMP_APP;
    }
    else
    {
        /* Button pressed: wait up to 1 second for release.
         * Releasing early boots the app; holding the full second stays in bootloader. */
        uint8_t ovf_count = 0;
        while (ovf_count < (uint8_t)TIMER_OVF_PER_SEC)
        {
            while (!(TIFR & (1<<TOV0)));
            TIFR = (1<<TOV0);
            ovf_count++;

            if (PINB & BTN_DISP)
            {
                bl_mode = BL_JUMP_APP;
                break;
            }
        }
    }

    /* Blank flash always forces bootloader mode regardless of button state */
    if (flash_is_blank())
        bl_mode = BL_HOLD;

    if (bl_mode == BL_HOLD)
        PORTB |= (LCD_CONTROL | EN_5V_PIN);

    /* Pre-buffer page 0 so it is ready before the host issues CMD_SET_PAGE(0). */
    load_page_to_buf(0);

    /* --- MAIN LOOP (I2C programming) --- */
    {
        uint8_t blink_div        = 0;
        uint8_t rpi_absent_ovf   = 0;
        while (bl_mode == BL_HOLD)
        {
            if (TWCR & (1<<TWINT))
                twi_handle();

            if (page_write_pending)
            {
                page_write_pending = 0;
                write_flash_page();
                TWCR = (1<<TWEN) | (1<<TWEA);
            }

            if (page_load_pending)
            {
                page_load_pending = 0;
                load_page_to_buf(flash_addr);
            }

            if (TIFR & (1<<TOV0))
            {
                TIFR = (1<<TOV0);

                if (PIND & RPI_DETECT)
                {
                    rpi_absent_ovf = 0;
                }
                else if (++rpi_absent_ovf >= (uint8_t)(2 * TIMER_OVF_PER_SEC))
                {
                    PORTB &= ~EN_5V_PIN;
                    rpi_absent_ovf = 0;
                }

                if (!(++blink_div & (blink_fast ? 0x03 : 0x0F)))
                    PORTB ^= LED_WIFI_PIN;
            }
        }
    }

    TWCR  = 0x00;
    TCCR0 = 0x00;

    jump_to_app();
}
