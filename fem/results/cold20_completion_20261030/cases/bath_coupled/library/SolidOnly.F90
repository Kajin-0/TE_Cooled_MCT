FUNCTION MCTHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(4)=[90.0_dp,148.0_dp,298.0_dp,400.0_dp]
 REAL(KIND=dp),PARAMETER :: yy(4)=[2.41_dp,1.61_dp,.973_dp,.790_dp]
 IF (.NOT.(T>=90.0_dp .AND. T<=400.0_dp)) CALL Fatal('CorrectedMCT','Outside local90..400K table')
 DO i=1,3
  IF(T<=tx(i+1)) EXIT
 END DO
 i=MIN(i,3);v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
END FUNCTION MCTHeat
FUNCTION JointHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n
 REAL(KIND=dp) :: T,v
 IF (.NOT.(T>=290.0_dp .AND. T<=320.0_dp)) CALL Fatal('CorrectedJoint','Outside numerical290..320K interval')
 v=35.0_dp
END FUNCTION JointHeat
