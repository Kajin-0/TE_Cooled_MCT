MODULE G3bInitialData
 USE DefUtils
 IMPLICIT NONE
 LOGICAL,SAVE :: loaded=.FALSE.
 REAL(KIND=dp),ALLOCATABLE,SAVE :: vals(:,:)
CONTAINS
 SUBROUTINE LoadInitial()
 INTEGER :: u,n,i
 IF(loaded) RETURN
 OPEN(NEWUNIT=u,FILE='InitialFields.dat',STATUS='old')
 READ(u,*)n;ALLOCATE(vals(n,2))
 DO i=1,n
 READ(u,*)vals(i,:)
 END DO
 CLOSE(u);loaded=.TRUE.
 END SUBROUTINE LoadInitial
END MODULE G3bInitialData
FUNCTION InitialT(Model,node,x) RESULT(v)
 USE G3bInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL LoadInitial();v=vals(node,1)
END FUNCTION InitialT
FUNCTION InitialPhi(Model,node,x) RESULT(v)
 USE G3bInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL LoadInitial();v=vals(node,2)
END FUNCTION InitialPhi
