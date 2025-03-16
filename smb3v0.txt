#include <stdint.h>
#include <stdbool.h>

// PPU Registers
#define PPU_CTRL    (*(volatile uint8_t*)0x2000)  // PPU control register (write)&#8203;:contentReference[oaicite:0]{index=0}
#define PPU_MASK    (*(volatile uint8_t*)0x2001)  // PPU mask (enable/disable rendering)
#define PPU_STATUS  (*(volatile uint8_t*)0x2002)  // PPU status (read) – vblank status bit etc.
#define PPU_SCROLL  (*(volatile uint8_t*)0x2005)  // PPU scroll position (write twice for X/Y)
#define PPU_ADDR    (*(volatile uint8_t*)0x2006)  // PPU address pointer (write high then low)
#define PPU_DATA    (*(volatile uint8_t*)0x2007)  // PPU data port (read/write VRAM)

// APU and I/O Registers
#define APU_SOUND_CTRL   (*(volatile uint8_t*)0x4015) // Sound channels enable control&#8203;:contentReference[oaicite:1]{index=1}
#define APU_DMC_CTRL     (*(volatile uint8_t*)0x4010) // DMC control (disable DMC IRQ)
#define APU_FRAME_COUNTER (*(volatile uint8_t*)0x4017) // APU frame counter control (disable frame IRQ)

// Controller ports
#define JOY1            (*(volatile uint8_t*)0x4016)  // Controller 1 data port
#define JOY2            (*(volatile uint8_t*)0x4017)  // Controller 2 data port (also APU frame in bit7)

// MMC3 Mapper Registers (memory bank controller)&#8203;:contentReference[oaicite:2]{index=2}
#define MMC3_BANK_SELECT    (*(volatile uint8_t*)0x8000) // Bank select register (selects which bank to swap, and PRG mode via bit6)&#8203;:contentReference[oaicite:3]{index=3}
#define MMC3_BANK_DATA      (*(volatile uint8_t*)0x8001) // Bank data register (value to load into selected bank slot)
#define MMC3_MIRROR_REG     (*(volatile uint8_t*)0xA000) // Mirroring control (bit0: 0=horizontal,1=vertical)&#8203;:contentReference[oaicite:4]{index=4}
#define MMC3_RAM_ENABLE     (*(volatile uint8_t*)0xA001) // PRG RAM enable (bit7 enables PRG RAM at $6000-$7FFF)&#8203;:contentReference[oaicite:5]{index=5}
#define MMC3_IRQ_COUNTER    (*(volatile uint8_t*)0xC000) // IRQ scanline counter
#define MMC3_IRQ_LATCH      (*(volatile uint8_t*)0xC001) // IRQ latch value
#define MMC3_IRQ_DISABLE    (*(volatile uint8_t*)0xE000) // Disable IRQs (also resets counter)&#8203;:contentReference[oaicite:6]{index=6}
#define MMC3_IRQ_ENABLE     (*(volatile uint8_t*)0xE001) // Enable IRQs

// Useful constants
#define NMI_ENABLE    0x80  // Bit 7 of PPU_CTRL enables NMI on vblank
#define SPRITE_SIZE   0x20  // Bit 5 of PPU_CTRL selects sprite size (0=8x8,1=8x16). Here 0x20 means 8x16 sprites if set.
#define BG_PATTERN_TABLE 0x08 // Bit 3 of PPU_CTRL selects background pattern table (0x0000 or 0x1000). 0x08 means use 0x1000 for BG.
#define PPU_MASK_OFF  0x00  // Disable all rendering (used to turn screen off)
#define PPU_MASK_ON   0x1E  // Example value to turn on rendering (enable sprites/background visibility; 0x1E = show bg+sprites, no clipping)

// Game state mode values (from assembly comparisons)
#define MODE_OVERWORLD   0x00  // Overworld map mode
#define MODE_LEVEL       0x20  // In-level gameplay mode
#define MODE_ENTER_LEVEL 0x40  // Transition into a level
#define MODE_SWITCH_TURN 0x80  // Switch player turn / life lost / pause mode
#define MODE_ENDING      0xA0  // Victory or game ending mode

// Forward declarations of functions (defined later)
void NMI_Handler(void);           // NMI interrupt service routine (called every VBlank)
void updateOverworld(void);
void updateLevel(void);
void enterLevel(void);
void switchPlayerTurn(void);
void gameEnding(void);
