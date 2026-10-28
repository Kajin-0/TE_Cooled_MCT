FUNCTION PElectric(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(2) = [ 2.0000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(2) = [ 7.1428571428571427e-06_dp, 7.1428571428571427e-06_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(2))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,1
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,1)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 v=1.0_dp/v
END FUNCTION PElectric

FUNCTION PHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(2) = [ 2.0000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(2) = [ 1.5000000000000000e+00_dp, 1.5000000000000000e+00_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(2))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,1
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,1)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION PHeat

FUNCTION PSeebeck(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(2) = [ 2.0000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(2) = [ 6.0000000000000002e-05_dp, 1.6000000000000001e-04_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(2))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,1
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,1)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION PSeebeck

FUNCTION NElectric(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(2) = [ 2.0000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(2) = [ 6.0422960725075530e-06_dp, 6.0422960725075530e-06_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(2))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,1
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,1)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 v=1.0_dp/v
END FUNCTION NElectric

FUNCTION NHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(2) = [ 2.0000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(2) = [ 1.5000000000000000e+00_dp, 1.5000000000000000e+00_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(2))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,1
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,1)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION NHeat

FUNCTION NSeebeck(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(2) = [ 2.0000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(2) = [ -1.7000000000000001e-04_dp, -1.7000000000000001e-04_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(2))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,1
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,1)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION NSeebeck
