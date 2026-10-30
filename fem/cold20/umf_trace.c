#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static double tick(clockid_t id){struct timespec t;clock_gettime(id,&t);return t.tv_sec+t.tv_nsec*1e-9;}
typedef void (*symfn)(void*,void*,void*,void*,void*,void*,void*,double*);
typedef void (*numfn)(void*,void*,void*,void*,void*,void*,double*);
void umf4_l_sym(void*m,void*n,void*ap,void*ai,void*ax,void*s,void*c,double*i){
    symfn f=(symfn)dlsym(RTLD_NEXT,"umf4_l_sym");if(!f)abort();
    double w=tick(CLOCK_MONOTONIC),p=tick(CLOCK_PROCESS_CPUTIME_ID);f(m,n,ap,ai,ax,s,c,i);
    fprintf(stderr,"COLD20_UMF symbolic wall=%.9g cpu=%.9g status=%.0f estimated_peak_bytes=%.0f\n",tick(CLOCK_MONOTONIC)-w,tick(CLOCK_PROCESS_CPUTIME_ID)-p,i[0],i[21]*i[3]);fflush(stderr);
}
void umf4_l_num(void*ap,void*ai,void*ax,void*s,void*n,void*c,double*i){
    numfn f=(numfn)dlsym(RTLD_NEXT,"umf4_l_num");if(!f)abort();
    double w=tick(CLOCK_MONOTONIC),p=tick(CLOCK_PROCESS_CPUTIME_ID);f(ap,ai,ax,s,n,c,i);
    fprintf(stderr,"COLD20_UMF numeric wall=%.9g cpu=%.9g status=%.0f peak_bytes=%.0f L_nnz=%.0f U_nnz=%.0f flops=%.0f\n",tick(CLOCK_MONOTONIC)-w,tick(CLOCK_PROCESS_CPUTIME_ID)-p,i[0],i[41]*i[3],i[43],i[44],i[42]);fflush(stderr);
}
