#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <time.h>

#define SHM_KEY 0x1234
#define CHANNELS 1024

typedef struct {
    int active;         
    float data[CHANNELS];
} SpectrumData;

int main() {
    int shmid = shmget(SHM_KEY, sizeof(SpectrumData), IPC_CREAT | 0666);
    if (shmid < 0) {
        perror("shmget failed");
        return 1;
    }

    SpectrumData *shared = (SpectrumData *)shmat(shmid, NULL, 0);
    if (shared == (void *)-1) {
        perror("shmat failed");
        return 1;
    }

    shared->active = 1; 
    srand(time(NULL));

    printf("Spectrum Generator running... \n");

    while (1) {
        if (shared->active) {
            for (int i = 0; i < CHANNELS; i++) {
                shared->data[i] = (rand() % 100) + (i % 50); 
            }
        }
        usleep(16000); 
    }

    shmdt(shared);
    return 0;
}
