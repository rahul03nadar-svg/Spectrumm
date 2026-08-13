#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>

#define SHARED_FILE "/dev/shm/detector_data"

typedef struct {
    int count;
    int running;
} SharedData;

int main() {
    int fd;
    SharedData *data;

    fd=open(SHARED_FILE,O_CREAT|O_RDWR,0666);
    if(fd==-1) {
        perror("Error opening shared memory");
        return 1;
    }

    if(ftruncate(fd,sizeof(SharedData))==-1) {
        perror("ftruncate failed");
        close(fd);
        return 1;
    }

    data=mmap(NULL,sizeof(SharedData),PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
    if(data==MAP_FAILED) {
        perror("mmap failed");
        close(fd);
        return 1;
    }

    srand(time(NULL));
    data->running=1;

    printf("Detector Producer Started\n");
    printf("Generating counts every 500 ms...\n");

    while(1) {
        if(data->running) {
            int random_count=100+rand()%1901;
            data->count=random_count;
            printf("Produced Count: %d\n",random_count);
            fflush(stdout);
        }
        usleep(500000);
    }

    munmap(data,sizeof(SharedData));
    close(fd);
    return 0;
}
