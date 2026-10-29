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
FUNCTION Flux20002(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(3)/area(3)
END FUNCTION Flux20002
FUNCTION Flux20003(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(4)/area(4)
END FUNCTION Flux20003
FUNCTION Flux20004(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(5)/area(5)
END FUNCTION Flux20004
FUNCTION Flux20005(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(6)/area(6)
END FUNCTION Flux20005
FUNCTION Flux20006(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(7)/area(7)
END FUNCTION Flux20006
FUNCTION Flux20007(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(8)/area(8)
END FUNCTION Flux20007
FUNCTION Flux20008(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(9)/area(9)
END FUNCTION Flux20008
FUNCTION Flux20009(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(10)/area(10)
END FUNCTION Flux20009
FUNCTION Flux20010(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(11)/area(11)
END FUNCTION Flux20010
FUNCTION Flux20011(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(12)/area(12)
END FUNCTION Flux20011
FUNCTION Flux20012(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(13)/area(13)
END FUNCTION Flux20012
FUNCTION Flux20013(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(14)/area(14)
END FUNCTION Flux20013
FUNCTION Flux20014(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(15)/area(15)
END FUNCTION Flux20014
FUNCTION Flux20015(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(16)/area(16)
END FUNCTION Flux20015
FUNCTION Flux20016(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(17)/area(17)
END FUNCTION Flux20016
FUNCTION Flux20017(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(18)/area(18)
END FUNCTION Flux20017
FUNCTION Flux20018(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(19)/area(19)
END FUNCTION Flux20018
FUNCTION Flux20019(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(20)/area(20)
END FUNCTION Flux20019
FUNCTION Flux20020(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(21)/area(21)
END FUNCTION Flux20020
FUNCTION Flux20021(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(22)/area(22)
END FUNCTION Flux20021
FUNCTION Flux20022(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(23)/area(23)
END FUNCTION Flux20022
FUNCTION Flux20023(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(24)/area(24)
END FUNCTION Flux20023
FUNCTION Flux20024(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(25)/area(25)
END FUNCTION Flux20024
FUNCTION Flux20025(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(26)/area(26)
END FUNCTION Flux20025
FUNCTION Flux20026(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(27)/area(27)
END FUNCTION Flux20026
FUNCTION Flux20027(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(28)/area(28)
END FUNCTION Flux20027
FUNCTION Flux20028(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(29)/area(29)
END FUNCTION Flux20028
FUNCTION Flux20029(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(30)/area(30)
END FUNCTION Flux20029
FUNCTION Flux20030(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(31)/area(31)
END FUNCTION Flux20030
FUNCTION Flux20031(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(32)/area(32)
END FUNCTION Flux20031
FUNCTION Flux20032(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(33)/area(33)
END FUNCTION Flux20032
FUNCTION Flux20033(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(34)/area(34)
END FUNCTION Flux20033
FUNCTION Flux20034(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(35)/area(35)
END FUNCTION Flux20034
FUNCTION Flux20035(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(36)/area(36)
END FUNCTION Flux20035
FUNCTION Flux20036(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(37)/area(37)
END FUNCTION Flux20036
FUNCTION Flux20037(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(38)/area(38)
END FUNCTION Flux20037
FUNCTION Flux20038(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(39)/area(39)
END FUNCTION Flux20038
FUNCTION Flux20039(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(40)/area(40)
END FUNCTION Flux20039
FUNCTION Flux20040(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(41)/area(41)
END FUNCTION Flux20040
FUNCTION Flux20041(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(42)/area(42)
END FUNCTION Flux20041
FUNCTION Flux20042(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(43)/area(43)
END FUNCTION Flux20042
FUNCTION Flux20043(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(44)/area(44)
END FUNCTION Flux20043
FUNCTION Flux20044(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(45)/area(45)
END FUNCTION Flux20044
FUNCTION Flux20045(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(46)/area(46)
END FUNCTION Flux20045
FUNCTION Flux20046(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(47)/area(47)
END FUNCTION Flux20046
FUNCTION Flux20047(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(48)/area(48)
END FUNCTION Flux20047
FUNCTION Flux20048(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(49)/area(49)
END FUNCTION Flux20048
FUNCTION Flux20049(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(50)/area(50)
END FUNCTION Flux20049
FUNCTION Flux20050(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(51)/area(51)
END FUNCTION Flux20050
FUNCTION Flux20051(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(52)/area(52)
END FUNCTION Flux20051
FUNCTION Flux20052(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(53)/area(53)
END FUNCTION Flux20052
FUNCTION Flux20053(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(54)/area(54)
END FUNCTION Flux20053
FUNCTION Flux20054(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(55)/area(55)
END FUNCTION Flux20054
FUNCTION Flux20055(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(56)/area(56)
END FUNCTION Flux20055
FUNCTION Flux20056(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(57)/area(57)
END FUNCTION Flux20056
FUNCTION Flux20057(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(58)/area(58)
END FUNCTION Flux20057
FUNCTION Flux20058(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(59)/area(59)
END FUNCTION Flux20058
FUNCTION Flux20059(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(60)/area(60)
END FUNCTION Flux20059
FUNCTION Flux20060(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(61)/area(61)
END FUNCTION Flux20060
FUNCTION Flux20061(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(62)/area(62)
END FUNCTION Flux20061
FUNCTION Flux20062(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(63)/area(63)
END FUNCTION Flux20062
FUNCTION Flux20063(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(64)/area(64)
END FUNCTION Flux20063
FUNCTION Flux20064(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(65)/area(65)
END FUNCTION Flux20064
FUNCTION Flux20065(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(66)/area(66)
END FUNCTION Flux20065
FUNCTION Flux20066(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(67)/area(67)
END FUNCTION Flux20066
FUNCTION Flux20067(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(68)/area(68)
END FUNCTION Flux20067
FUNCTION Flux20068(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(69)/area(69)
END FUNCTION Flux20068
FUNCTION Flux20069(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(70)/area(70)
END FUNCTION Flux20069
FUNCTION Flux20070(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(71)/area(71)
END FUNCTION Flux20070
FUNCTION Flux20071(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(72)/area(72)
END FUNCTION Flux20071
FUNCTION Flux20072(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(73)/area(73)
END FUNCTION Flux20072
FUNCTION Flux20073(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(74)/area(74)
END FUNCTION Flux20073
FUNCTION Flux20074(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(75)/area(75)
END FUNCTION Flux20074
FUNCTION Flux20075(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(76)/area(76)
END FUNCTION Flux20075
FUNCTION Flux20076(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(77)/area(77)
END FUNCTION Flux20076
FUNCTION Flux20077(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(78)/area(78)
END FUNCTION Flux20077
FUNCTION Flux20078(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(79)/area(79)
END FUNCTION Flux20078
FUNCTION Flux20079(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(80)/area(80)
END FUNCTION Flux20079
FUNCTION Flux20080(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(81)/area(81)
END FUNCTION Flux20080
FUNCTION Flux20081(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(82)/area(82)
END FUNCTION Flux20081
FUNCTION Flux20082(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(83)/area(83)
END FUNCTION Flux20082
FUNCTION Flux20083(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(84)/area(84)
END FUNCTION Flux20083
FUNCTION Flux20084(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(85)/area(85)
END FUNCTION Flux20084
FUNCTION Flux20085(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(86)/area(86)
END FUNCTION Flux20085
FUNCTION Flux20086(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(87)/area(87)
END FUNCTION Flux20086
FUNCTION Flux20087(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(88)/area(88)
END FUNCTION Flux20087
FUNCTION Flux20088(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(89)/area(89)
END FUNCTION Flux20088
FUNCTION Flux20089(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(90)/area(90)
END FUNCTION Flux20089
FUNCTION Flux20090(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(91)/area(91)
END FUNCTION Flux20090
FUNCTION Flux20091(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(92)/area(92)
END FUNCTION Flux20091
FUNCTION Flux20092(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(93)/area(93)
END FUNCTION Flux20092
FUNCTION Flux20093(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(94)/area(94)
END FUNCTION Flux20093
FUNCTION Flux20094(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(95)/area(95)
END FUNCTION Flux20094
FUNCTION Flux20095(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(96)/area(96)
END FUNCTION Flux20095
FUNCTION Flux20096(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(97)/area(97)
END FUNCTION Flux20096
FUNCTION Flux20097(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(98)/area(98)
END FUNCTION Flux20097
FUNCTION Flux20098(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(99)/area(99)
END FUNCTION Flux20098
FUNCTION Flux20099(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(100)/area(100)
END FUNCTION Flux20099
FUNCTION Flux20100(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(101)/area(101)
END FUNCTION Flux20100
FUNCTION Flux20101(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(102)/area(102)
END FUNCTION Flux20101
FUNCTION Flux20102(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(103)/area(103)
END FUNCTION Flux20102
FUNCTION Flux20103(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(104)/area(104)
END FUNCTION Flux20103
FUNCTION Flux20104(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(105)/area(105)
END FUNCTION Flux20104
FUNCTION Flux20105(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(106)/area(106)
END FUNCTION Flux20105
FUNCTION Flux20106(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(107)/area(107)
END FUNCTION Flux20106
FUNCTION Flux20107(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(108)/area(108)
END FUNCTION Flux20107
FUNCTION Flux20108(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(109)/area(109)
END FUNCTION Flux20108
FUNCTION Flux20109(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(110)/area(110)
END FUNCTION Flux20109
FUNCTION Flux20110(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(111)/area(111)
END FUNCTION Flux20110
FUNCTION Flux20111(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(112)/area(112)
END FUNCTION Flux20111
FUNCTION Flux20112(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(113)/area(113)
END FUNCTION Flux20112
FUNCTION Flux20113(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(114)/area(114)
END FUNCTION Flux20113
FUNCTION Flux20114(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(115)/area(115)
END FUNCTION Flux20114
FUNCTION Flux20115(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(116)/area(116)
END FUNCTION Flux20115
FUNCTION Flux20116(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(117)/area(117)
END FUNCTION Flux20116
FUNCTION Flux20117(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(118)/area(118)
END FUNCTION Flux20117
FUNCTION Flux20118(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(119)/area(119)
END FUNCTION Flux20118
FUNCTION Flux20119(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(120)/area(120)
END FUNCTION Flux20119
FUNCTION Flux20120(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(121)/area(121)
END FUNCTION Flux20120
FUNCTION Flux20121(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(122)/area(122)
END FUNCTION Flux20121
FUNCTION Flux20122(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(123)/area(123)
END FUNCTION Flux20122
FUNCTION Flux20123(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(124)/area(124)
END FUNCTION Flux20123
FUNCTION Flux20124(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(125)/area(125)
END FUNCTION Flux20124
FUNCTION Flux20125(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(126)/area(126)
END FUNCTION Flux20125
FUNCTION Flux20126(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(127)/area(127)
END FUNCTION Flux20126
FUNCTION Flux20127(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(128)/area(128)
END FUNCTION Flux20127
FUNCTION Flux20128(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(129)/area(129)
END FUNCTION Flux20128
FUNCTION Flux20129(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(130)/area(130)
END FUNCTION Flux20129
FUNCTION Flux20130(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(131)/area(131)
END FUNCTION Flux20130
FUNCTION Flux20131(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(132)/area(132)
END FUNCTION Flux20131
FUNCTION Flux20132(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(133)/area(133)
END FUNCTION Flux20132
FUNCTION Flux20133(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(134)/area(134)
END FUNCTION Flux20133
FUNCTION Flux20134(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(135)/area(135)
END FUNCTION Flux20134
FUNCTION Flux20135(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(136)/area(136)
END FUNCTION Flux20135
FUNCTION Flux20136(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(137)/area(137)
END FUNCTION Flux20136
FUNCTION Flux20137(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(138)/area(138)
END FUNCTION Flux20137
FUNCTION Flux20138(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(139)/area(139)
END FUNCTION Flux20138
FUNCTION Flux20139(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(140)/area(140)
END FUNCTION Flux20139
FUNCTION Flux20140(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(141)/area(141)
END FUNCTION Flux20140
FUNCTION Flux20141(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(142)/area(142)
END FUNCTION Flux20141
FUNCTION Flux20142(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(143)/area(143)
END FUNCTION Flux20142
FUNCTION Flux20143(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(144)/area(144)
END FUNCTION Flux20143
FUNCTION Flux20144(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(145)/area(145)
END FUNCTION Flux20144
FUNCTION Flux20145(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(146)/area(146)
END FUNCTION Flux20145
FUNCTION Flux20146(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(147)/area(147)
END FUNCTION Flux20146
FUNCTION Flux20147(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(148)/area(148)
END FUNCTION Flux20147
FUNCTION Flux20148(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(149)/area(149)
END FUNCTION Flux20148
FUNCTION Flux20149(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(150)/area(150)
END FUNCTION Flux20149
FUNCTION Flux20150(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(151)/area(151)
END FUNCTION Flux20150
FUNCTION Flux20151(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(152)/area(152)
END FUNCTION Flux20151
FUNCTION Flux20152(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(153)/area(153)
END FUNCTION Flux20152
FUNCTION Flux20153(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(154)/area(154)
END FUNCTION Flux20153
FUNCTION Flux20154(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(155)/area(155)
END FUNCTION Flux20154
FUNCTION Flux20155(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(156)/area(156)
END FUNCTION Flux20155
FUNCTION Flux20156(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(157)/area(157)
END FUNCTION Flux20156
FUNCTION Flux20157(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(158)/area(158)
END FUNCTION Flux20157
FUNCTION Flux20158(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(159)/area(159)
END FUNCTION Flux20158
FUNCTION Flux20159(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(160)/area(160)
END FUNCTION Flux20159
FUNCTION Flux20160(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(161)/area(161)
END FUNCTION Flux20160
FUNCTION Flux20161(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(162)/area(162)
END FUNCTION Flux20161
FUNCTION Flux20162(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(163)/area(163)
END FUNCTION Flux20162
FUNCTION Flux20163(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(164)/area(164)
END FUNCTION Flux20163
FUNCTION Flux20164(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(165)/area(165)
END FUNCTION Flux20164
FUNCTION Flux20165(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(166)/area(166)
END FUNCTION Flux20165
FUNCTION Flux20166(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(167)/area(167)
END FUNCTION Flux20166
FUNCTION Flux20167(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(168)/area(168)
END FUNCTION Flux20167
FUNCTION Flux20168(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(169)/area(169)
END FUNCTION Flux20168
FUNCTION Flux20169(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(170)/area(170)
END FUNCTION Flux20169
FUNCTION Flux20170(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(171)/area(171)
END FUNCTION Flux20170
FUNCTION Flux20171(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(172)/area(172)
END FUNCTION Flux20171
FUNCTION Flux20172(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(173)/area(173)
END FUNCTION Flux20172
FUNCTION Flux20173(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(174)/area(174)
END FUNCTION Flux20173
FUNCTION Flux20174(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(175)/area(175)
END FUNCTION Flux20174
FUNCTION Flux20175(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(176)/area(176)
END FUNCTION Flux20175
FUNCTION Flux20176(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(177)/area(177)
END FUNCTION Flux20176
FUNCTION Flux20177(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(178)/area(178)
END FUNCTION Flux20177
FUNCTION Flux20178(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(179)/area(179)
END FUNCTION Flux20178
FUNCTION Flux20179(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(180)/area(180)
END FUNCTION Flux20179
FUNCTION Flux20180(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(181)/area(181)
END FUNCTION Flux20180
FUNCTION Flux20181(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(182)/area(182)
END FUNCTION Flux20181
FUNCTION Flux20182(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(183)/area(183)
END FUNCTION Flux20182
FUNCTION Flux20183(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(184)/area(184)
END FUNCTION Flux20183
FUNCTION Flux20184(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(185)/area(185)
END FUNCTION Flux20184
FUNCTION Flux20185(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(186)/area(186)
END FUNCTION Flux20185
FUNCTION Flux20186(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(187)/area(187)
END FUNCTION Flux20186
FUNCTION Flux20187(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(188)/area(188)
END FUNCTION Flux20187
FUNCTION Flux20188(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(189)/area(189)
END FUNCTION Flux20188
FUNCTION Flux20189(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(190)/area(190)
END FUNCTION Flux20189
FUNCTION Flux20190(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(191)/area(191)
END FUNCTION Flux20190
FUNCTION Flux20191(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(192)/area(192)
END FUNCTION Flux20191
FUNCTION Flux20192(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(193)/area(193)
END FUNCTION Flux20192
FUNCTION Flux20193(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(194)/area(194)
END FUNCTION Flux20193
FUNCTION Flux20194(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(195)/area(195)
END FUNCTION Flux20194
FUNCTION Flux20195(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(196)/area(196)
END FUNCTION Flux20195
FUNCTION Flux20196(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(197)/area(197)
END FUNCTION Flux20196
FUNCTION Flux20197(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(198)/area(198)
END FUNCTION Flux20197
FUNCTION Flux20198(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(199)/area(199)
END FUNCTION Flux20198
FUNCTION Flux20199(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(200)/area(200)
END FUNCTION Flux20199
FUNCTION Flux20200(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(201)/area(201)
END FUNCTION Flux20200
FUNCTION Flux20201(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(202)/area(202)
END FUNCTION Flux20201
FUNCTION Flux20202(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(203)/area(203)
END FUNCTION Flux20202
FUNCTION Flux20203(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(204)/area(204)
END FUNCTION Flux20203
FUNCTION Flux20204(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(205)/area(205)
END FUNCTION Flux20204
FUNCTION Flux20205(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(206)/area(206)
END FUNCTION Flux20205
FUNCTION Flux20206(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(207)/area(207)
END FUNCTION Flux20206
FUNCTION Flux20207(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(208)/area(208)
END FUNCTION Flux20207
FUNCTION Flux20208(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(209)/area(209)
END FUNCTION Flux20208
FUNCTION Flux20209(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(210)/area(210)
END FUNCTION Flux20209
FUNCTION Flux20210(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(211)/area(211)
END FUNCTION Flux20210
FUNCTION Flux20211(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(212)/area(212)
END FUNCTION Flux20211
FUNCTION Flux20212(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(213)/area(213)
END FUNCTION Flux20212
FUNCTION Flux20213(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(214)/area(214)
END FUNCTION Flux20213
FUNCTION Flux20214(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(215)/area(215)
END FUNCTION Flux20214
FUNCTION Flux20215(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(216)/area(216)
END FUNCTION Flux20215
FUNCTION Flux20216(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(217)/area(217)
END FUNCTION Flux20216
FUNCTION Flux20217(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(218)/area(218)
END FUNCTION Flux20217
FUNCTION Flux20218(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(219)/area(219)
END FUNCTION Flux20218
FUNCTION Flux20219(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(220)/area(220)
END FUNCTION Flux20219
FUNCTION Flux20220(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(221)/area(221)
END FUNCTION Flux20220
FUNCTION Flux20221(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(222)/area(222)
END FUNCTION Flux20221
FUNCTION Flux20222(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(223)/area(223)
END FUNCTION Flux20222
FUNCTION Flux20223(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(224)/area(224)
END FUNCTION Flux20223
FUNCTION Flux20224(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(225)/area(225)
END FUNCTION Flux20224
FUNCTION Flux20225(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(226)/area(226)
END FUNCTION Flux20225
FUNCTION Flux20226(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(227)/area(227)
END FUNCTION Flux20226
FUNCTION Flux20227(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(228)/area(228)
END FUNCTION Flux20227
FUNCTION Flux20228(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(229)/area(229)
END FUNCTION Flux20228
FUNCTION Flux20229(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(230)/area(230)
END FUNCTION Flux20229
FUNCTION Flux20230(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(231)/area(231)
END FUNCTION Flux20230
FUNCTION Flux20231(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(232)/area(232)
END FUNCTION Flux20231
FUNCTION Flux20232(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(233)/area(233)
END FUNCTION Flux20232
FUNCTION Flux20233(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(234)/area(234)
END FUNCTION Flux20233
FUNCTION Flux20234(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(235)/area(235)
END FUNCTION Flux20234
FUNCTION Flux20235(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(236)/area(236)
END FUNCTION Flux20235
FUNCTION Flux20236(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(237)/area(237)
END FUNCTION Flux20236
FUNCTION Flux20237(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(238)/area(238)
END FUNCTION Flux20237
FUNCTION Flux20238(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(239)/area(239)
END FUNCTION Flux20238
FUNCTION Flux20239(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(240)/area(240)
END FUNCTION Flux20239
FUNCTION Flux20240(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(241)/area(241)
END FUNCTION Flux20240
FUNCTION Flux20241(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(242)/area(242)
END FUNCTION Flux20241
FUNCTION Flux20242(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(243)/area(243)
END FUNCTION Flux20242
FUNCTION Flux20243(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(244)/area(244)
END FUNCTION Flux20243
FUNCTION Flux20244(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(245)/area(245)
END FUNCTION Flux20244
FUNCTION Flux20245(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(246)/area(246)
END FUNCTION Flux20245
FUNCTION Flux20246(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(247)/area(247)
END FUNCTION Flux20246
FUNCTION Flux20247(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(248)/area(248)
END FUNCTION Flux20247
FUNCTION Flux20248(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(249)/area(249)
END FUNCTION Flux20248
FUNCTION Flux20249(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(250)/area(250)
END FUNCTION Flux20249
FUNCTION Flux20250(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(251)/area(251)
END FUNCTION Flux20250
FUNCTION Flux20251(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(252)/area(252)
END FUNCTION Flux20251
FUNCTION Flux20252(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(253)/area(253)
END FUNCTION Flux20252
FUNCTION Flux20253(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(254)/area(254)
END FUNCTION Flux20253
FUNCTION Flux20254(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(255)/area(255)
END FUNCTION Flux20254
FUNCTION Flux20255(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(256)/area(256)
END FUNCTION Flux20255
FUNCTION Flux20256(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(257)/area(257)
END FUNCTION Flux20256
FUNCTION Flux20257(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(258)/area(258)
END FUNCTION Flux20257
FUNCTION Flux20258(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(259)/area(259)
END FUNCTION Flux20258
FUNCTION Flux20259(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(260)/area(260)
END FUNCTION Flux20259
FUNCTION Flux20260(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(261)/area(261)
END FUNCTION Flux20260
FUNCTION Flux20261(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(262)/area(262)
END FUNCTION Flux20261
FUNCTION Flux20262(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(263)/area(263)
END FUNCTION Flux20262
FUNCTION Flux20263(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(264)/area(264)
END FUNCTION Flux20263
FUNCTION Flux20264(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(265)/area(265)
END FUNCTION Flux20264
FUNCTION Flux20265(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(266)/area(266)
END FUNCTION Flux20265
FUNCTION Flux20266(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(267)/area(267)
END FUNCTION Flux20266
FUNCTION Flux20267(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(268)/area(268)
END FUNCTION Flux20267
FUNCTION Flux20268(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(269)/area(269)
END FUNCTION Flux20268
FUNCTION Flux20269(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(270)/area(270)
END FUNCTION Flux20269
FUNCTION Flux20270(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(271)/area(271)
END FUNCTION Flux20270
FUNCTION Flux20271(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(272)/area(272)
END FUNCTION Flux20271
FUNCTION Flux20272(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(273)/area(273)
END FUNCTION Flux20272
FUNCTION Flux20273(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(274)/area(274)
END FUNCTION Flux20273
FUNCTION Flux20274(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(275)/area(275)
END FUNCTION Flux20274
FUNCTION Flux20275(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(276)/area(276)
END FUNCTION Flux20275
FUNCTION Flux20276(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(277)/area(277)
END FUNCTION Flux20276
FUNCTION Flux20277(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(278)/area(278)
END FUNCTION Flux20277
FUNCTION Flux20278(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(279)/area(279)
END FUNCTION Flux20278
FUNCTION Flux20279(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(280)/area(280)
END FUNCTION Flux20279
FUNCTION Flux20280(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(281)/area(281)
END FUNCTION Flux20280
FUNCTION Flux20281(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(282)/area(282)
END FUNCTION Flux20281
FUNCTION Flux20282(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(283)/area(283)
END FUNCTION Flux20282
FUNCTION Flux20283(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(284)/area(284)
END FUNCTION Flux20283
FUNCTION Flux20284(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(285)/area(285)
END FUNCTION Flux20284
FUNCTION Flux20285(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(286)/area(286)
END FUNCTION Flux20285
FUNCTION Flux20286(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(287)/area(287)
END FUNCTION Flux20286
FUNCTION Flux20287(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(288)/area(288)
END FUNCTION Flux20287
FUNCTION Flux20288(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(289)/area(289)
END FUNCTION Flux20288
FUNCTION Flux20289(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(290)/area(290)
END FUNCTION Flux20289
FUNCTION Flux20290(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(291)/area(291)
END FUNCTION Flux20290
FUNCTION Flux20291(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(292)/area(292)
END FUNCTION Flux20291
FUNCTION Flux20292(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(293)/area(293)
END FUNCTION Flux20292
FUNCTION Flux20293(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(294)/area(294)
END FUNCTION Flux20293
FUNCTION Flux20294(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(295)/area(295)
END FUNCTION Flux20294
FUNCTION Flux20295(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(296)/area(296)
END FUNCTION Flux20295
FUNCTION Flux20296(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(297)/area(297)
END FUNCTION Flux20296
FUNCTION Flux20297(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(298)/area(298)
END FUNCTION Flux20297
FUNCTION Flux20298(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(299)/area(299)
END FUNCTION Flux20298
FUNCTION Flux20299(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(300)/area(300)
END FUNCTION Flux20299
FUNCTION Flux20300(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(301)/area(301)
END FUNCTION Flux20300
FUNCTION Flux20301(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(302)/area(302)
END FUNCTION Flux20301
FUNCTION Flux20302(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(303)/area(303)
END FUNCTION Flux20302
FUNCTION Flux20303(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(304)/area(304)
END FUNCTION Flux20303
FUNCTION Flux20304(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(305)/area(305)
END FUNCTION Flux20304
FUNCTION Flux20305(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(306)/area(306)
END FUNCTION Flux20305
FUNCTION Flux20306(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(307)/area(307)
END FUNCTION Flux20306
FUNCTION Flux20307(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(308)/area(308)
END FUNCTION Flux20307
FUNCTION Flux20308(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(309)/area(309)
END FUNCTION Flux20308
FUNCTION Flux20309(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(310)/area(310)
END FUNCTION Flux20309
FUNCTION Flux20310(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(311)/area(311)
END FUNCTION Flux20310
FUNCTION Flux20311(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(312)/area(312)
END FUNCTION Flux20311
FUNCTION Flux20312(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(313)/area(313)
END FUNCTION Flux20312
FUNCTION Flux20313(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(314)/area(314)
END FUNCTION Flux20313
FUNCTION Flux20314(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(315)/area(315)
END FUNCTION Flux20314
FUNCTION Flux20315(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(316)/area(316)
END FUNCTION Flux20315
FUNCTION Flux20316(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(317)/area(317)
END FUNCTION Flux20316
FUNCTION Flux20317(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(318)/area(318)
END FUNCTION Flux20317
FUNCTION Flux20318(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(319)/area(319)
END FUNCTION Flux20318
FUNCTION Flux20319(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(320)/area(320)
END FUNCTION Flux20319
FUNCTION Flux20320(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(321)/area(321)
END FUNCTION Flux20320
FUNCTION Flux20321(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(322)/area(322)
END FUNCTION Flux20321
FUNCTION Flux20322(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(323)/area(323)
END FUNCTION Flux20322
FUNCTION Flux20323(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(324)/area(324)
END FUNCTION Flux20323
FUNCTION Flux20324(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(325)/area(325)
END FUNCTION Flux20324
FUNCTION Flux20325(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(326)/area(326)
END FUNCTION Flux20325
FUNCTION Flux20326(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(327)/area(327)
END FUNCTION Flux20326
FUNCTION Flux20327(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(328)/area(328)
END FUNCTION Flux20327
FUNCTION Flux20328(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(329)/area(329)
END FUNCTION Flux20328
FUNCTION Flux20329(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(330)/area(330)
END FUNCTION Flux20329
FUNCTION Flux20330(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(331)/area(331)
END FUNCTION Flux20330
FUNCTION Flux20331(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(332)/area(332)
END FUNCTION Flux20331
FUNCTION Flux20332(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(333)/area(333)
END FUNCTION Flux20332
FUNCTION Flux20333(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(334)/area(334)
END FUNCTION Flux20333
FUNCTION Flux20334(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(335)/area(335)
END FUNCTION Flux20334
FUNCTION Flux20335(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(336)/area(336)
END FUNCTION Flux20335
FUNCTION Flux20336(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(337)/area(337)
END FUNCTION Flux20336
FUNCTION Flux20337(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(338)/area(338)
END FUNCTION Flux20337
FUNCTION Flux20338(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(339)/area(339)
END FUNCTION Flux20338
FUNCTION Flux20339(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(340)/area(340)
END FUNCTION Flux20339
FUNCTION Flux20340(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(341)/area(341)
END FUNCTION Flux20340
FUNCTION Flux20341(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(342)/area(342)
END FUNCTION Flux20341
FUNCTION Flux20342(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(343)/area(343)
END FUNCTION Flux20342
FUNCTION Flux20343(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(344)/area(344)
END FUNCTION Flux20343
FUNCTION Flux20344(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(345)/area(345)
END FUNCTION Flux20344
FUNCTION Flux20345(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(346)/area(346)
END FUNCTION Flux20345
FUNCTION Flux20346(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(347)/area(347)
END FUNCTION Flux20346
FUNCTION Flux20347(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(348)/area(348)
END FUNCTION Flux20347
FUNCTION Flux20348(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(349)/area(349)
END FUNCTION Flux20348
FUNCTION Flux20349(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(350)/area(350)
END FUNCTION Flux20349
FUNCTION Flux20350(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(351)/area(351)
END FUNCTION Flux20350
FUNCTION Flux20351(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(352)/area(352)
END FUNCTION Flux20351
FUNCTION Flux20352(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(353)/area(353)
END FUNCTION Flux20352
FUNCTION Flux20353(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(354)/area(354)
END FUNCTION Flux20353
FUNCTION Flux20354(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(355)/area(355)
END FUNCTION Flux20354
FUNCTION Flux20355(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(356)/area(356)
END FUNCTION Flux20355
FUNCTION Flux20356(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(357)/area(357)
END FUNCTION Flux20356
FUNCTION Flux20357(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(358)/area(358)
END FUNCTION Flux20357
FUNCTION Flux20358(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(359)/area(359)
END FUNCTION Flux20358
FUNCTION Flux20359(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(360)/area(360)
END FUNCTION Flux20359
FUNCTION Flux20360(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(361)/area(361)
END FUNCTION Flux20360
FUNCTION Flux20361(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(362)/area(362)
END FUNCTION Flux20361
FUNCTION Flux20362(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(363)/area(363)
END FUNCTION Flux20362
FUNCTION Flux20363(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(364)/area(364)
END FUNCTION Flux20363
FUNCTION Flux20364(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(365)/area(365)
END FUNCTION Flux20364
FUNCTION Flux20365(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(366)/area(366)
END FUNCTION Flux20365
FUNCTION Flux20366(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(367)/area(367)
END FUNCTION Flux20366
FUNCTION Flux20367(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(368)/area(368)
END FUNCTION Flux20367
FUNCTION Flux20368(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(369)/area(369)
END FUNCTION Flux20368
FUNCTION Flux20369(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(370)/area(370)
END FUNCTION Flux20369
FUNCTION Flux20370(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(371)/area(371)
END FUNCTION Flux20370
FUNCTION Flux20371(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(372)/area(372)
END FUNCTION Flux20371
FUNCTION Flux20372(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(373)/area(373)
END FUNCTION Flux20372
FUNCTION Flux20373(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(374)/area(374)
END FUNCTION Flux20373
FUNCTION Flux20374(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(375)/area(375)
END FUNCTION Flux20374
FUNCTION Flux20375(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(376)/area(376)
END FUNCTION Flux20375
FUNCTION Flux20376(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(377)/area(377)
END FUNCTION Flux20376
FUNCTION Flux20377(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(378)/area(378)
END FUNCTION Flux20377
FUNCTION Flux20378(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(379)/area(379)
END FUNCTION Flux20378
FUNCTION Flux20379(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(380)/area(380)
END FUNCTION Flux20379
FUNCTION Flux20380(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(381)/area(381)
END FUNCTION Flux20380
FUNCTION Flux20381(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(382)/area(382)
END FUNCTION Flux20381
FUNCTION Flux20382(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(383)/area(383)
END FUNCTION Flux20382
FUNCTION Flux20383(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(384)/area(384)
END FUNCTION Flux20383
FUNCTION Flux20384(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(385)/area(385)
END FUNCTION Flux20384
FUNCTION Flux20385(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(386)/area(386)
END FUNCTION Flux20385
FUNCTION Flux20386(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(387)/area(387)
END FUNCTION Flux20386
FUNCTION Flux20387(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(388)/area(388)
END FUNCTION Flux20387
FUNCTION Flux20388(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(389)/area(389)
END FUNCTION Flux20388
FUNCTION Flux20389(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(390)/area(390)
END FUNCTION Flux20389
FUNCTION Flux20390(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(391)/area(391)
END FUNCTION Flux20390
FUNCTION Flux20391(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(392)/area(392)
END FUNCTION Flux20391
FUNCTION Flux20392(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(393)/area(393)
END FUNCTION Flux20392
FUNCTION Flux20393(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(394)/area(394)
END FUNCTION Flux20393
FUNCTION Flux20394(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(395)/area(395)
END FUNCTION Flux20394
FUNCTION Flux20395(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(396)/area(396)
END FUNCTION Flux20395
FUNCTION Flux20396(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(397)/area(397)
END FUNCTION Flux20396
FUNCTION Flux20397(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(398)/area(398)
END FUNCTION Flux20397
FUNCTION Flux20398(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(399)/area(399)
END FUNCTION Flux20398
FUNCTION Flux20399(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(400)/area(400)
END FUNCTION Flux20399
FUNCTION Flux20400(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(401)/area(401)
END FUNCTION Flux20400
FUNCTION Flux20401(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(402)/area(402)
END FUNCTION Flux20401
FUNCTION Flux20402(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(403)/area(403)
END FUNCTION Flux20402
FUNCTION Flux20403(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(404)/area(404)
END FUNCTION Flux20403
FUNCTION Flux20404(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(405)/area(405)
END FUNCTION Flux20404
FUNCTION Flux20405(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(406)/area(406)
END FUNCTION Flux20405
FUNCTION Flux20406(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(407)/area(407)
END FUNCTION Flux20406
FUNCTION Flux20407(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(408)/area(408)
END FUNCTION Flux20407
FUNCTION Flux20408(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(409)/area(409)
END FUNCTION Flux20408
FUNCTION Flux20409(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(410)/area(410)
END FUNCTION Flux20409
FUNCTION Flux20410(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(411)/area(411)
END FUNCTION Flux20410
FUNCTION Flux20411(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(412)/area(412)
END FUNCTION Flux20411
FUNCTION Flux20412(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(413)/area(413)
END FUNCTION Flux20412
FUNCTION Flux20413(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(414)/area(414)
END FUNCTION Flux20413
FUNCTION Flux20414(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(415)/area(415)
END FUNCTION Flux20414
FUNCTION Flux20415(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(416)/area(416)
END FUNCTION Flux20415
FUNCTION Flux20416(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(417)/area(417)
END FUNCTION Flux20416
FUNCTION Flux20417(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(418)/area(418)
END FUNCTION Flux20417
FUNCTION Flux20418(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(419)/area(419)
END FUNCTION Flux20418
FUNCTION Flux20419(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(420)/area(420)
END FUNCTION Flux20419
FUNCTION Flux20420(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(421)/area(421)
END FUNCTION Flux20420
FUNCTION Flux20421(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(422)/area(422)
END FUNCTION Flux20421
FUNCTION Flux20422(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(423)/area(423)
END FUNCTION Flux20422
FUNCTION Flux20423(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(424)/area(424)
END FUNCTION Flux20423
FUNCTION Flux20424(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(425)/area(425)
END FUNCTION Flux20424
FUNCTION Flux20425(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(426)/area(426)
END FUNCTION Flux20425
FUNCTION Flux20426(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(427)/area(427)
END FUNCTION Flux20426
FUNCTION Flux20427(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(428)/area(428)
END FUNCTION Flux20427
FUNCTION Flux20428(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(429)/area(429)
END FUNCTION Flux20428
FUNCTION Flux20429(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(430)/area(430)
END FUNCTION Flux20429
FUNCTION Flux20430(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(431)/area(431)
END FUNCTION Flux20430
FUNCTION Flux20431(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(432)/area(432)
END FUNCTION Flux20431
FUNCTION Flux20432(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(433)/area(433)
END FUNCTION Flux20432
FUNCTION Flux20433(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(434)/area(434)
END FUNCTION Flux20433
FUNCTION Flux20434(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(435)/area(435)
END FUNCTION Flux20434
FUNCTION Flux20435(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(436)/area(436)
END FUNCTION Flux20435
FUNCTION Flux20436(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(437)/area(437)
END FUNCTION Flux20436
FUNCTION Flux20437(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(438)/area(438)
END FUNCTION Flux20437
FUNCTION Flux20438(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(439)/area(439)
END FUNCTION Flux20438
FUNCTION Flux20439(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(440)/area(440)
END FUNCTION Flux20439
FUNCTION Flux20440(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(441)/area(441)
END FUNCTION Flux20440
FUNCTION Flux20441(Model,node,T) RESULT(v)
 USE G3bNonlocal
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: T,v
 CALL EnsurePowers(Model)
 v=power(442)/area(442)
END FUNCTION Flux20441
