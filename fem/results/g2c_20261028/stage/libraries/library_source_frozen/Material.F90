FUNCTION PElectric(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 1.2080611242485315e-05_dp, 1.2080611242485315e-05_dp, 1.2080611242485315e-05_dp, 1.2080611242485315e-05_dp, 1.2080611242485315e-05_dp, 1.2080611242485315e-05_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(6))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,5
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,5)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 v=1.0_dp/v
END FUNCTION PElectric

FUNCTION PHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 1.0990062885366549e+00_dp, 1.0990062885366549e+00_dp, 1.0990062885366549e+00_dp, 1.0990062885366549e+00_dp, 1.0990062885366549e+00_dp, 1.0990062885366549e+00_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(6))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,5
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,5)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION PHeat

FUNCTION PSeebeck(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 2.1246254964304501e-04_dp, 2.1246254964304501e-04_dp, 2.1246254964304501e-04_dp, 2.1246254964304501e-04_dp, 2.1246254964304501e-04_dp, 2.1246254964304501e-04_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(6))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,5
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,5)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION PSeebeck

FUNCTION NElectric(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 7.5432772425131382e-06_dp, 7.5432772425131382e-06_dp, 7.5432772425131382e-06_dp, 7.5432772425131382e-06_dp, 7.5432772425131382e-06_dp, 7.5432772425131382e-06_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(6))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,5
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,5)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 v=1.0_dp/v
END FUNCTION NElectric

FUNCTION NHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 1.3992269984476857e+00_dp, 1.3992269984476857e+00_dp, 1.3992269984476857e+00_dp, 1.3992269984476857e+00_dp, 1.3992269984476857e+00_dp, 1.3992269984476857e+00_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(6))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,5
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,5)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION NHeat

FUNCTION NSeebeck(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ -1.8957524436579554e-04_dp, -1.8957524436579554e-04_dp, -1.8957524436579554e-04_dp, -1.8957524436579554e-04_dp, -1.8957524436579554e-04_dp, -1.8957524436579554e-04_dp ]
 IF (.NOT.(T >= tx(1) .AND. T <= tx(6))) THEN
   WRITE(*,*) "Rejected local T:",T
   CALL Fatal("G2cMaterial", "Local temperature outside qualified profile interval; extrapolation refused")
 END IF
 DO i=1,5
   IF (T <= tx(i+1)) EXIT
 END DO
 i=MIN(i,5)
 v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
 
END FUNCTION NSeebeck
