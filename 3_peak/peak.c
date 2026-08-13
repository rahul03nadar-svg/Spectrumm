#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <time.h>

#define SHM_KEY 0x1234
#define CHANNELS 1024
#define INPUT_FILE "t2.txt"
#define UPDATE_INTERVAL_US 100000

typedef struct {
    int active;
    float data[CHANNELS];
} SpectrumData;

int shmid=-1;
SpectrumData *shared=NULL;

void cleanup(int sig) {
    (void)sig;
    printf("\nStopping generator...\n");
    if(shared!=NULL) shmdt(shared);
    if(shmid!=-1) shmctl(shmid,IPC_RMID,NULL);
    exit(EXIT_SUCCESS);
}

int load_spectrum(const char *filename,float data[]) {
    FILE *file=fopen(filename,"r");
    char line[256];
    int count=0;
    if(!file) {
        fprintf(stderr,"Error opening %s: %s\n",filename,strerror(errno));
        return -1;
    }
    for(int i=0;i<CHANNELS;i++) data[i]=0.0f;
    while(fgets(line,sizeof(line),file)&&count<CHANNELS) {
        double channel,counts;
        if(sscanf(line," %lf , %lf",&channel,&counts)==2) {
            if(counts>=0) data[count++]=(float)counts;
        }
    }
    fclose(file);
    return count;
}

int main(void) {
    float spectrum[CHANNELS];
    int points=load_spectrum(INPUT_FILE,spectrum);

    if(points<=0) {
        printf("Error:spectrum data found.\n");
        return 1;
    }

    signal(SIGINT,cleanup);
    signal(SIGTERM,cleanup);

    shmid=shmget(SHM_KEY,sizeof(SpectrumData),IPC_CREAT|0666);

    if(shmid==-1) {
        perror("shmget failed");
        return 1;
    }

    shared=(SpectrumData *)shmat(shmid,NULL,0);

    if(shared==(void *)-1) {
        perror("shmat failed");
        shmctl(shmid,IPC_RMID,NULL);
        return 1;
    }

    shared->active=1;
    srand(time(NULL));

    printf("Spectrum Generator running...\n");
    printf("Loaded %d channels.\n",points);
    printf("Shared Memory Key: 0x1234\n");
    printf("Press Ctrl+C to stop.\n");

    while(1) {
        if(shared->active) {
            for(int i=0;i<CHANNELS;i++) {
                float noise=((float)(rand()%11)-5.0f);
                shared->data[i]=spectrum[i]+noise;
                if(shared->data[i]<0) shared->data[i]=0;
            }
        }
        usleep(UPDATE_INTERVAL_US);
    }

    return 0;
}
