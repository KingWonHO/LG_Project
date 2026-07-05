# 분석 리포트

- 파일: DZ150A1Q_7번트립발생.xlsx
- 판정: FAIL
- Trip: 2회
- 모델: gemma3:4b

## 요약

결과: FAIL
판정: Trip 발생은 2회이며, AVERAGE_TORQUE_OVER, WINDING_TEMPERATURE_OVER Trip이 발생했습니다.
해석: 평균토크가 허용 수준 이상으로 지속될 때 또는 추정 권선온도가 기준 이상으로 상승할 때 발생하는 Trip입니다.
조치: 부하 영향도를 확인하고 HW영향 여부 및 제어품질 불량 여부를 확인해야 합니다.

## RAG 참고 자료

[유사 Trip Code 참고 자료]
- AVERAGE_TORQUE_OVER (토크 Trip): [AVERAGE_TORQUE_OVER] 토크 Trip
평균토크가 Compressor 허용 수준 이상으로 지속될 때 발생하는 Trip이다.
조치: [] [] [] [] 
- FO_SIGNAL (FO Trip): [FO_SIGNAL] FO Trip
IPM 또는 인버터 보호 신호인 FO Signal에 의해 발생하는 Trip이다.
조치: [] ['부하(Power, Imag, LeadA_total, Hz_Real떨림)영향도를 확인하고 HW영향인지, 제어품질 불량인지 확인하여 조치한다.'] ['과부하, 고토크의 운전 상태일 경우 6번 전류트립과 번갈아 가며 나타날 수 있다
- POWER_OVERLOAD (파워 Trip): [POWER_OVERLOAD] 파워 Trip
Compressor 출력 Power가 기준 이상으로 지속될 때 발생하는 Trip이다.
조치: [] [] [] [] 
- WINDING_TEMPERATURE_OVER (권선온도 Trip): [WINDING_TEMPERATURE_OVER] 권선온도 Trip
추정권선온도가 기준 이상으로 상승할 때 발생하는 Trip이다.
조치: [] [] [] [] 
- OVERCURRENT_SHUNT (과전류 Trip): [OVERCURRENT_SHUNT] 과전류 Trip
Compressor 구동 전류가 내부 기준 이상으로 상승한 경우 발생하는 Trip이다.
조치: [] [] [] [] 
