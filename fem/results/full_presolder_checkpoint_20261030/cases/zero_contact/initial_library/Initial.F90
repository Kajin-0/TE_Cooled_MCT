MODULE JointInitialData
 USE DefUtils
 LOGICAL,SAVE :: loaded=.FALSE.
 REAL(KIND=dp),ALLOCATABLE,SAVE :: a(:,:)
CONTAINS
 SUBROUTINE Load()
 INTEGER :: u,n,i
 IF(loaded) RETURN
 OPEN(NEWUNIT=u,FILE='InitialFields.dat',STATUS='old')
 READ(u,*)n
 ALLOCATE(a(n,2))
 DO i=1,n
 READ(u,*)a(i,:)
 END DO
 CLOSE(u)
 loaded=.TRUE.
 END SUBROUTINE
END MODULE
FUNCTION JointInitialT(Model,node,x) RESULT(v)
 USE JointInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL Load()
 v=a(node,1)
END FUNCTION
FUNCTION JointInitialPhi(Model,node,x) RESULT(v)
 USE JointInitialData
 TYPE(Model_t) :: Model
 INTEGER :: node
 REAL(KIND=dp) :: x,v
 CALL Load()
 v=a(node,2)
END FUNCTION
