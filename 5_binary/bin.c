#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>

#define SHM_KEY 0x1234
#define CHANNELS 1024
#define UPDATE_INTERVAL_US 16000
#define INPUT_FILE "t1.txt"

typedef struct {
    int active;
    float data[CHANNELS];
} SpectrumData;

int shmid = -1;
SpectrumData *shared = NULL;

void cleanup(int sig) {
    (void)sig;
    printf("\nStopping generator...\n");
    if (shared != NULL) shmdt(shared);
    if (shmid != -1) shmctl(shmid, IPC_RMID, NULL);
    exit(EXIT_SUCCESS);
}

int load_spectrum(const char *filename, float data[], int max_channels) {
    FILE *file = fopen(filename, "r");
    char line[256];
    int count = 0;
    if (!file) {
        fprintf(stderr, "Error opening %s: %s\n", filename, strerror(errno));
        return -1;
    }
    for (int i = 0; i < max_channels; i++) data[i] = 0.0f;
    while (fgets(line, sizeof(line), file)) {
        double energy, counts;
        if (sscanf(line, " %lf , %lf", &energy, &counts) == 2) {
            if (counts < 0) continue;
            if (count >= max_channels) break;
            data[count++] = (float)counts;
        }
    }
    fclose(file);
    return count;
}

int main(void) {
    float spectrum[CHANNELS];
    int points = load_spectrum(INPUT_FILE, spectrum, CHANNELS);
    if (points <= 0) {
        fprintf(stderr, "Error: No valid spectrum data.\n");
        return EXIT_FAILURE;
    }
    signal(SIGINT, cleanup);
    signal(SIGTERM, cleanup);
    shmid = shmget(SHM_KEY, sizeof(SpectrumData), IPC_CREAT | 0666);
    if (shmid == -1) {
        perror("shmget failed");
        return EXIT_FAILURE;
    }
    shared = (SpectrumData *)shmat(shmid, NULL, 0);
    if (shared == (void *)-1) {
        perror("shmat failed");
        shmctl(shmid, IPC_RMID, NULL);
        return EXIT_FAILURE;
    }
    shared->active = 1;
    for (int i = 0; i < CHANNELS; i++) shared->data[i] = spectrum[i];
    printf("Spectrum Generator running...\n");
    printf("Points loaded: %d\n", points);
    printf("Press Ctrl+C to stop.\n");
    while (1) {
        if (shared->active) {
            for (int i = 0; i < CHANNELS; i++) shared->data[i] = spectrum[i];
        }
        usleep(UPDATE_INTERVAL_US);
    }
    cleanup(0);
    return 0;
}
