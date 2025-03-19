//Ines emulator code in C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

//Define a structure to hold the ines header
typedef struct {
    unsigned char prg_rom_size;
    unsigned char chr_rom_size;
    unsigned char flags6;
    unsigned char flags7;
    unsigned char prg_ram_size;
    unsigned char flags9;
    unsigned char flags10;
    unsigned char unused[5];
} INES_HEADER;

//Function to read the ines header
void read_ines_header(FILE* fp, INES_HEADER* hdr)
{
    fread(hdr, sizeof(INES_HEADER), 1, fp);
    if(hdr->prg_rom_size == 0)
        hdr->prg_rom_size = 0x10;
    if(hdr->chr_rom_size == 0)
        hdr->chr_rom_size = 0x08;
    if(hdr->prg_ram_size == 0)
        hdr->prg_ram_size = 0x00;
}

//Main function
int main(int argc, char* argv[])
{
    if (argc != 2) {
        printf("usage: %s <ines_file>\n", argv[0]);
        return 1;
    }

    //Open the file and read the header
    FILE* fp = fopen(argv[1], "rb");
    INES_HEADER hdr;
    read_ines_header(fp, &hdr);
    fclose(fp);

    //Print out the header data
    printf("PRG ROM SIZE: %d\n", hdr.prg_rom_size);
    printf("CHR ROM SIZE: %d\n", hdr.chr_rom_size);
    printf("PRG RAM SIZE: %d\n", hdr.prg_ram_size);

    return 0;
}
