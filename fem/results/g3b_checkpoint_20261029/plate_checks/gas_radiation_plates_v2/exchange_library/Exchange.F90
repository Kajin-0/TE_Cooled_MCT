MODULE G3bNonlocal
 USE DefUtils
 IMPLICIT NONE
 INTEGER,SAVE :: n=0,nz=0,nlink=0,laststamp=-999999
 INTEGER,ALLOCATABLE,SAVE :: ptr(:),nodes(:),kind(:)
 REAL(KIND=dp),ALLOCATABLE,SAVE :: area(:),wt(:),rm(:,:),wm(:,:),gap(:,:),tw(:,:),tc(:,:),lg(:),lj(:),tp(:),power(:),prad(:),pgas(:),pgold(:),plead(:),pheat(:)
 REAL(KIND=dp),ALLOCATABLE,SAVE :: hf(:,:),hr(:,:),oldpower(:)
 INTEGER,SAVE :: nh=0
 REAL(KIND=dp),SAVE :: pressure,rg,gamma,acc,gs,ls,kk(3),lastnorm=-HUGE(1.0_dp),lastchange=-HUGE(1.0_dp)
 LOGICAL,SAVE :: initialized=.FALSE.,have_response=.FALSE.
CONTAINS
 SUBROUTINE EnsurePowers(Model)
  TYPE(Model_t) :: Model
  TYPE(Variable_t),POINTER :: temp,primary
  INTEGER :: u,i,j,k,it,ii,jj,info,piv(4)
  REAL(KIND=dp) :: gram(4,4),coeff(4,1),onesum,regular,rnorm
  REAL(KIND=dp),ALLOCATABLE :: rawpower(:),residual(:),candidate(:)
  REAL(KIND=dp) :: norm,change,t,kappa,cp,mu,pr,lambda,jump,g,q,joule
  IF (.NOT.initialized) THEN
   OPEN(NEWUNIT=u,FILE='ExchangeWeights.dat',STATUS='old',ACTION='read')
   READ(u,*)n,nz,nlink
   ALLOCATE(area(n),ptr(n+1),nodes(nz),wt(nz),kind(nlink),tw(n,nlink),tc(n,nlink),lg(nlink),lj(nlink),tp(n),power(n),prad(n),pgas(n),pgold(n),plead(n),pheat(n),rm(n,n),wm(n,n),gap(n,n))
   ALLOCATE(hf(n,4),hr(n,4),oldpower(n));oldpower=0
   READ(u,*)area
   READ(u,*)ptr
   READ(u,*)nodes
   READ(u,*)wt
   DO k=1,nlink
    READ(u,*)kind(k),lg(k),lj(k)
    READ(u,*)tw(:,k)
    READ(u,*)tc(:,k)
   END DO
   READ(u,*)pressure,rg,gamma,acc,gs,ls,kk
   CLOSE(u)
   OPEN(NEWUNIT=u,FILE='ExchangeMatrices.bin',FORM='unformatted',ACCESS='stream',STATUS='old',ACTION='read')
   READ(u)rm
   READ(u)wm
   READ(u)gap
   CLOSE(u);initialized=.TRUE.
  END IF
  primary => Model % Solver % Variable
  it=primary % NonlinIter;norm=primary % Norm;change=primary % NonlinChange
  IF(it==laststamp .AND. norm==lastnorm .AND. change==lastchange) RETURN
  temp => VariableGet(Model % Mesh % Variables,'Temperature')
  IF (.NOT.ASSOCIATED(temp)) CALL Fatal('G3bExchange','Missing global Temperature')
  IF (ANY(temp % Perm(nodes)<=0)) CALL Fatal('G3bExchange','Invalid endpoint/patch node mapping')
  DO i=1,n
   tp(i)=SUM(wt(ptr(i):ptr(i+1)-1)*temp % Values(temp % Perm(nodes(ptr(i):ptr(i+1)-1))))
  END DO
  prad=-MATMUL(rm,tp**4);pgas=0;pgold=0;plead=0;pheat=0
  IF(pressure>0) THEN
   cp=gamma/(gamma-1)*rg
   DO i=1,n
    DO j=i+1,n
     IF(wm(i,j)<=0) CYCLE
     t=.5_dp*(tp(i)+tp(j))
     IF(.NOT.(t>=200 .AND. t<=400)) CALL Fatal('G3bGas','Local mean outside NIST200..400 K')
     IF(t<=300) THEN
      kappa=kk(1)+(t-200)/100*(kk(2)-kk(1))
     ELSE
      kappa=kk(2)+(t-300)/100*(kk(3)-kk(2))
     END IF
     mu=kappa/(cp+1.25_dp*rg);pr=mu*cp/kappa;lambda=mu/pressure*SQRT(ACOS(-1.0_dp)*rg*t/2)
     jump=(2-acc)/acc*2*gamma/(gamma+1)*lambda/pr
     g=kappa*wm(i,j)/(gap(i,j)+2*jump);q=g*(tp(j)-tp(i));pgas(i)=pgas(i)+q;pgas(j)=pgas(j)-q
    END DO
   END DO
  END IF
  DO k=1,nlink
   q=lg(k)*(DOT_PRODUCT(tw(:,k),tp)-DOT_PRODUCT(tc(:,k),tp))
   IF(kind(k)==1) THEN
    pgold=pgold+gs*q*(tc(:,k)-tw(:,k))
   ELSE
    plead=plead+ls*q*(tc(:,k)-tw(:,k));pheat=pheat+.5_dp*ls*lj(k)*(tw(:,k)+tc(:,k))
   END IF
  END DO
  ALLOCATE(rawpower(n),residual(n),candidate(n))
  rawpower=prad+pgas+pgold+plead+pheat;residual=rawpower-oldpower;rnorm=SQRT(SUM(residual**2))
  IF(.NOT.have_response) THEN
   power=rawpower;have_response=.TRUE.
  ELSE
  IF(nh==4) THEN
   hf(:,1:3)=hf(:,2:4);hr(:,1:3)=hr(:,2:4)
  ELSE
   nh=nh+1
  END IF
  hf(:,nh)=rawpower;hr(:,nh)=residual
  IF(nh==1) THEN
   power=rawpower
  ELSE
   gram=0;coeff=0
   DO ii=1,nh
    coeff(ii,1)=1
    DO jj=1,nh
     gram(ii,jj)=DOT_PRODUCT(hr(:,ii),hr(:,jj))
    END DO
   END DO
   regular=MAX(1.0e-28_dp,MAXVAL(ABS(gram))*1.0e-12_dp)
   DO ii=1,nh
    gram(ii,ii)=gram(ii,ii)+regular
   END DO
   CALL DGESV(nh,1,gram,4,piv,coeff,4,info)
   onesum=SUM(coeff(1:nh,1))
   IF(info/=0 .OR. ABS(onesum)<1.0e-25_dp) THEN
    power=.4_dp*rawpower+.6_dp*oldpower
   ELSE
    coeff(1:nh,1)=coeff(1:nh,1)/onesum
    IF(SUM(ABS(coeff(1:nh,1)))>20.0_dp) THEN
     power=.4_dp*rawpower+.6_dp*oldpower
    ELSE
     candidate=MATMUL(hf(:,1:nh),coeff(1:nh,1));power=.9_dp*candidate+.1_dp*oldpower
    END IF
   END IF
  END IF
  END IF
  oldpower=power
  DEALLOCATE(rawpower,residual,candidate)
  OPEN(NEWUNIT=u,FILE='exchange-history.txt',POSITION='append',STATUS='unknown')
  WRITE(u,'(I8,8(1X,ES24.16))')it,MINVAL(tp),MAXVAL(tp),SUM(prad),SUM(pgas),SUM(pgold),SUM(plead),SUM(pheat),rnorm
  CLOSE(u)
  laststamp=it;lastnorm=norm;lastchange=change
 END SUBROUTINE EnsurePowers
END MODULE G3bNonlocal
FUNCTION Flux20000(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(1)/area(1)
END FUNCTION Flux20000
FUNCTION Flux20001(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(2)/area(2)
END FUNCTION Flux20001
