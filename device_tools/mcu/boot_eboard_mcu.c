#include <termio.h>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <errno.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>

void print_hex( uint8_t* buf, int len )
{
    for( int i = 0; i < len; i++ )
    {
        printf("%02X", buf[i]);
    }
}

/* Bootloader start code to trigger execution of Klipper firmware on Eboard-MCU for Flashforge 5M */
int main()
{
    // Setup serial port
    const char* tty = "/dev/ttyS1";
    int fd = open( tty, O_RDWR );
    if( fd < 0 )
    {
        printf( "Serial: open (%s) failed: %s\n", tty, strerror( errno ) );
        return -1;
    }

    struct termios termios_p;
    if( tcgetattr( fd, &termios_p ) != 0 )
    {
        printf( "Serial: tcgetattr failed: %s\n", strerror( errno ) );
        return 1;
    }

    cfmakeraw( &termios_p );
    cfsetispeed( &termios_p, B115200 );
    cfsetospeed( &termios_p, B115200 );

    if( tcsetattr( fd, 0, &termios_p ) != 0 )
    {
        printf("Serial: tcsetattr failed: %s\n", strerror( errno ));
        return 1;
    }

    // Actual initialization starts here
    uint8_t buf[64];
    printf("Waiting for MCU to become ready ...\n");
    for( int i = 0; i < 15; i++ )
    {
        int len = read( fd, buf, 32 );
        if( len <= 0 )
            break;  // EOF or error

        // MCU bootloader sents 'Ready.' in a loop when started
        printf("Recv: ");
        print_hex( buf, len );
        printf("\n");

        buf[len] = 0;
        if( strstr( (char*)buf, "Ready." ) != 0 )
        {
            printf("Eboard MCU sent 'Ready.'\n");
            break;
        }
    }

    // Tell MCU to start execution of firmware with cmd 'A' 0x41
    uint8_t go_cmd = 'A';
    for( int i = 0; i < 15; i++ )
    {
        write( fd, &go_cmd, 1 );
        printf("Send: %02X\n", go_cmd);
        int len  = read(  fd, &buf, 32 );
        if( len <= 0 )
            return 1; // EOF or error

        // MCU acknowledges cmd with byte 0x06 (Ascii ACK)
        printf("Recv: %02X\n", buf[0]);
        if( buf[0] == '\x06' )
        {
            printf("Application is starting.\n");
            break;
        }
    }

    close(fd);
    return 0;
}
