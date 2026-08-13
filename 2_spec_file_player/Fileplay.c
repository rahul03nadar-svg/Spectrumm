#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <string.h>

#define SHM_KEY 0x1234
#define CHANNELS 1024

typedef struct {
    int control_state;  
    float data[CHANNELS];
} SpectrumShared;

int main() {
    // Connect to Shared Memory
    int shmid = shmget(SHM_KEY, sizeof(SpectrumShared), IPC_CREAT | 0666);
    if (shmid < 0) {
        perror("shmget failed");
        return 1;
    }

    SpectrumShared *shared = (SpectrumShared *)shmat(shmid, NULL, 0);
    if (shared == (void *)-1) {
        perror("shmat failed");
        return 1;
    }

   
    shared->control_state = 1;
    memset(shared->data, 0, sizeof(shared->data));


    float file_x[2000];
    float file_y[2000];
    int total_lines = 0;


    FILE *file = fopen("t1.txt", "r");
    if (!file) {
        printf("Error: Missing t1.txt in this folder!\n");
        return 1;
    }

    while (fscanf(file, "%f,%f", &file_x[total_lines], &file_y[total_lines]) == 2) {
        total_lines++;
        if (total_lines >= 2000) break; 
    }
    fclose(file);
    printf("Successfully loaded %d spectrum data entries into memory.\n", total_lines);

    int current_index = 0;

    while (1) {
        // Handle User Request: RESTART
        if (shared->control_state == 2) {
            current_index = 0;
            shared->control_state = 1; // Reset back to active play state
            printf("[System] Playback restarted from beginning.\n");
        }

        // Handle User Request: PLAYING
        if (shared->control_state == 1) {

            for (int i = 0; i < CHANNELS; i++) {
                int data_lookup = (current_index + i) % total_lines;
                shared->data[i] = file_y[data_lookup];
            }

            printf("Streaming spectrum frame offset: %d / %d\n", current_index, total_lines);
            
            current_index = (current_index + 20) % total_lines; 
        } else {
        }

        sleep(1);
    }

    shmdt(shared);
    return 0;
}

