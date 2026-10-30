#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
_Static_assert(sizeof(int64_t)==8,"pinned64bit UMFPACK index ABI");
static int64_t dimension=0,*saved_ap=NULL,*saved_ai=NULL;
static double *saved_ax=NULL;
static void *saved_numeric=NULL;
static double cpu(void){struct timespec t;clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&t);return t.tv_sec+t.tv_nsec*1e-9;}
typedef void (*symfn)(void*,void*,void*,void*,void*,void*,void*,double*);
typedef void (*numfn)(void*,void*,void*,void*,void*,void*,double*);
typedef void (*solrfn)(void*,void*,void*,void*,void*,void*,void*,void*,double*);
void umf4_l_sym(void*m,void*n,void*ap,void*ai,void*ax,void*s,void*c,double*i){
    symfn f=(symfn)dlsym(RTLD_NEXT,"umf4_l_sym");if(!f)abort();
    dimension=*(int64_t*)n;if(dimension!=*(int64_t*)m || dimension<=0)abort();
    double t=cpu();f(m,n,ap,ai,ax,s,c,i);
    fprintf(stderr,"COLD20_REFINE symbolic_cpu=%.9g status=%.0f\n",cpu()-t,i[0]);fflush(stderr);
}
void umf4_l_num(void*ap,void*ai,void*ax,void*s,void*n,void*c,double*i){
    numfn f=(numfn)dlsym(RTLD_NEXT,"umf4_l_num");if(!f||dimension<=0)abort();
    int64_t nz=((int64_t*)ap)[dimension];if(nz<=0)abort();
    free(saved_ap);free(saved_ai);free(saved_ax);
    saved_ap=malloc((dimension+1)*sizeof(int64_t));saved_ai=malloc(nz*sizeof(int64_t));saved_ax=malloc(nz*sizeof(double));
    if(!saved_ap||!saved_ai||!saved_ax)abort();
    memcpy(saved_ap,ap,(dimension+1)*sizeof(int64_t));memcpy(saved_ai,ai,nz*sizeof(int64_t));memcpy(saved_ax,ax,nz*sizeof(double));
    double t=cpu();f(ap,ai,ax,s,n,c,i);saved_numeric=*(void**)n;
    fprintf(stderr,"COLD20_REFINE numeric_cpu=%.9g status=%.0f peak_bytes=%.0f L_nnz=%.0f U_nnz=%.0f\n",cpu()-t,i[0],i[41]*i[3],i[43],i[44]);fflush(stderr);
}
void umf4_l_sol(void*sys,void*x,void*b,void*n,void*c,double*i){
    solrfn f=(solrfn)dlsym(RTLD_NEXT,"umf4_l_solr");
    if(!f||!saved_ap||saved_numeric!=*(void**)n)abort();
    double *control=(double*)c,previous=control[7],t=cpu();control[7]=4;
    f(sys,saved_ap,saved_ai,saved_ax,x,b,n,c,i);control[7]=previous;
    fprintf(stderr,"COLD20_REFINE solve_cpu=%.9g status=%.0f steps=%.0f attempted=%.0f omega1=%.9g omega2=%.9g\n",cpu()-t,i[0],i[80],i[81],i[82],i[83]);fflush(stderr);
}
