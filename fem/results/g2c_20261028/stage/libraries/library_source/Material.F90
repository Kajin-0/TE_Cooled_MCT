FUNCTION PElectric(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(6) = [ 2.0000000000000000e+02_dp, 2.2000000000000000e+02_dp, 2.4000000000000000e+02_dp, 2.6000000000000000e+02_dp, 2.8000000000000000e+02_dp, 3.0000000000000000e+02_dp ]
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 6.0670581825577763e-06_dp, 7.0732840276780112e-06_dp, 8.1389316759689607e-06_dp, 9.3511427024375969e-06_dp, 1.0694094179453900e-05_dp, 1.2080611242485315e-05_dp ]
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
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 1.4159263225438823e+00_dp, 1.3321648422127959e+00_dp, 1.2574686836414648e+00_dp, 1.1940827743590623e+00_dp, 1.1374839658904956e+00_dp, 1.0990062885366549e+00_dp ]
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
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 1.6607875661298334e-04_dp, 1.7932142136212840e-04_dp, 1.9059486251571040e-04_dp, 1.9921988489389995e-04_dp, 2.0573924522476834e-04_dp, 2.1246254964304501e-04_dp ]
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
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 4.3718109221978405e-06_dp, 4.9321126360399514e-06_dp, 5.5704413787247722e-06_dp, 6.2326214329168184e-06_dp, 6.8845451315799307e-06_dp, 7.5432772425131382e-06_dp ]
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
 REAL(KIND=dp),PARAMETER :: yy(6) = [ 1.7444142695381821e+00_dp, 1.6538837131939097e+00_dp, 1.5746390725250115e+00_dp, 1.5067289937197432e+00_dp, 1.4473319978592614e+00_dp, 1.3992269984476857e+00_dp ]
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
 REAL(KIND=dp),PARAMETER :: yy(6) = [ -1.4584043006520551e-04_dp, -1.5623125457120540e-04_dp, -1.6573795758541176e-04_dp, -1.7456827715141068e-04_dp, -1.8244532605866015e-04_dp, -1.8957524436579554e-04_dp ]
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
