# PaGNet_v4 IEEE Access 투고 가능성 리뷰

- **검토 원고:** `PaGNet_v4.pdf`
- **검토 관점:** IEEE Access 투고 전 사전심사 관점의 냉정한 technical / editorial review
- **핵심 질문:** 지금 투고 가능한가, 리비전이 온다면 어떤 방향인가, 리젝이면 어떤 사유가 가장 유력한가

---

## 1. 한 줄 판정

**지금 바로 투고는 가능하지만, 그대로 제출하는 것은 추천하지 않는다.**

현재 버전은 논문 구조와 실험 설계가 이미 상당히 갖춰져 있으므로 단순한 초안 수준은 아니다. 그러나 IEEE Access reviewer 관점에서는 몇 가지 핵심 리스크가 뚜렷하다. 특히 **설명가능성 주장**, **single temporal split**, **CETR에서 blended PaGNet이 자기 branch보다 약한 문제**, **panel-flatten 이후 architecture gain이 작다는 점**, **일부 수치 서술 불일치**가 그대로 제출 시 reject-resubmission을 유도할 가능성이 크다.

내 판단상 현재 상태의 가장 가능성 높은 판정은 다음이다.

| 판정 가능성 | 현재 원고 기준 예상 |
|---|---:|
| Desk reject | 낮음~중간 |
| Peer review 진입 | 가능성 있음 |
| Accept without substantial update | 낮음 |
| Reject, updates required before resubmission | 가장 가능성 높음 |
| 완전 reject | 중간 이하이나 가능 |

**최종 권고:** 바로 제출하지 말고, 최소 1–2주 정도의 targeted revision 후 제출하는 것이 안전하다. 3–4주를 들여 rolling split, feature-level explainability, 수치 불일치 정리까지 하면 투고 경쟁력이 크게 올라간다.

---

## 2. 전체 평가 요약

| 항목 | 현재 평가 | 리스크 수준 | 조치 필요도 |
|---|---|---:|---:|
| IEEE Access scope | ML + applied finance/accounting로 대체로 적합 | 낮음 | 중간 |
| 논문 구조 | Introduction–Related Work–Method–Experiment–Discussion 구조 양호 | 낮음 | 낮음 |
| 실험 설계 | leakage-free protocol, FS1–FS4, baselines, ablation이 강점 | 낮음~중간 | 중간 |
| 신규성 | hybrid 자체는 incremental, panel-flatten diagnostic framing은 강점 | 중간 | 높음 |
| 설명가능성 | branch-level diagnostic은 있으나 feature-level driver traceability 부족 | 높음 | 매우 높음 |
| robustness | 단일 temporal split, K=3 고정 | 높음 | 높음 |
| 결과 해석 | FS1/FS2 framing은 좋으나 일부 claim이 실험보다 강함 | 중간~높음 | 높음 |
| 형식/행정 | funding placeholder, abstract length, data/code availability 보완 필요 | 높음 | 매우 높음 |

---

## 3. 논문의 강점

### 3.1 Leakage-free evaluation protocol이 강하다

원고는 `t -> t+1` 예측 문제를 명확히 정의하고, target year 정보가 feature에 들어가지 않도록 train/validation/test를 시간 기준으로 나누었다. 특히 2020, 2022 buffer year를 둔 점은 reviewer에게 “temporal leakage를 신경 썼다”는 인상을 준다.

이 부분은 반드시 유지해야 한다. IEEE Access reviewer가 실험의 신뢰성을 볼 때 가장 먼저 확인할 지점이기 때문이다.

### 3.2 Panel-flatten control은 이 논문의 가장 좋은 방어 카드다

원고의 가장 강한 contribution은 단순히 PaGNet이 성능이 좋다는 것이 아니라, **multi-year information access 효과와 architecture 효과를 분리하려는 panel-flatten control**이다.

일반적인 panel/tabular 논문은 multi-year history를 넣고 성능이 오르면 그것을 architecture gain처럼 주장하는 경우가 많다. 이 원고는 IID baseline들에게도 K=3년 정보를 flatten해서 주고, 그 이후에도 PaGNet이 남기는 residual gain을 본다. 이 설계는 reviewer가 “정보를 더 많이 줬기 때문에 이긴 것 아니냐”라고 공격할 때 강력한 방어가 된다.

단, panel-flatten 이후 architecture increment가 크지는 않다. 따라서 이 결과는 “압도적 SOTA”가 아니라 **정직한 attribution / diagnostic framework**로 포지셔닝해야 한다.

### 3.3 FS3/FS4를 과장하지 않는 AR(1) ceiling 분석이 좋다

FS3/FS4에서는 lagged target이 들어가면서 TSTA/TSDA가 거의 AR(1) ceiling에 도달한다. 원고는 이를 모델 성능으로 과장하지 않고, naive AR(1) baseline과 비교하여 architecture difference가 압축된다고 설명한다.

이건 좋은 과학적 태도다. reviewer 입장에서도 “저자들이 자기 모델의 한계를 알고 있다”는 인상을 준다.

### 3.4 Branch-target heterogeneity는 논문을 살릴 수 있는 핵심 스토리다

PaGNet의 핵심은 “모든 target에서 무조건 이긴다”가 아니라, target별로 어떤 signal source를 신뢰하는지가 다르다는 점이다.

- TSTA/TSDA: LightGBM branch 중심
- GETR: Panel-MLP branch 활용
- CETR: noisy target이며 branch selection mismatch가 드러남

이 framing은 좋다. 단, 현재는 `lambda*`를 너무 강하게 “driver traceability”처럼 말하고 있어 위험하다. “branch-level trust diagnostic”으로 낮추고, feature-level explanation을 추가하면 훨씬 설득력이 생긴다.

---

## 4. 가장 큰 리젝 리스크

## 4.1 리스크 1: 설명가능성 주장이 evidence보다 강하다

현재 abstract와 introduction은 다음과 같은 강한 표현을 사용한다.

- “source of every prediction inspectable”
- “each flag be traceable to an identifiable driver”
- “transparent about which signal drives each proxy”

문제는 실제 실험에서 보여주는 설명가능성은 대부분 **branch-level blend weight**다. 즉, `lambda*`는 “LightGBM branch를 더 신뢰했는가, Panel-MLP branch를 더 신뢰했는가”를 보여준다. 하지만 reviewer가 audit screening 문맥에서 기대하는 설명가능성은 보통 다음 수준이다.

- 어떤 재무변수가 예측을 밀어 올렸는가?
- 어떤 3년 trend가 risk flag를 만들었는가?
- 특정 firm-year에서 model output이 어떤 feature contribution으로 구성되는가?
- attention weight 또는 temporal aggregate가 실제 economic driver와 연결되는가?

따라서 현 상태에서는 다음과 같은 reviewer comment가 나올 가능성이 높다.

> The claimed inspectability is not sufficiently demonstrated. The blend weight only indicates branch reliance, not the feature-level or economic driver of an individual prediction.

### 수정 방향

원고에 최소 하나 이상의 feature-level explainability 분석을 넣어야 한다.

권장 추가 분석:

1. **LightGBM branch SHAP analysis**  
   target별 top-15 panel-temporal aggregate feature를 제시한다. 예: `last`, `mean`, `std`, `delta_prev`, `delta_mean` 단위로 보여주면 architecture와 잘 맞는다.

2. **Local case study**  
   test set에서 CETR, GETR, TSTA, TSDA 각각 high-risk prediction firm-year 1개씩 골라, prediction, branch weight, top feature drivers, 3-year history trajectory를 한 figure/table로 보여준다.

3. **Panel-MLP branch attribution**  
   Integrated Gradients, occlusion importance, permutation importance 중 하나를 사용한다. attention weight는 explanation이라고 과장하지 말고 “temporal reliance indicator” 정도로 제한한다.

4. **lambda stability**  
   seed별, split별 `lambda*` 분산을 boxplot으로 제시한다. 현재는 평균 중심이라 diagnostic의 안정성이 충분히 검증되지 않았다.

---

## 4.2 리스크 2: single temporal split만으로 robustness가 부족하다

현재 원고는 primary split을 하나 사용한다.

- Train: input year 2011–2019
- Validation: input year 2021
- Test: input year 2023
- Buffer: 2020, 2022

이 설계는 leakage 방지 측면에서는 좋지만, reviewer는 다음 질문을 할 수 있다.

> Are the reported gains specific to the 2024 target year? How stable are the results across temporal splits?

특히 panel-flatten 이후 architecture increment가 `+0.004 ~ +0.018 R²` 수준으로 작다고 원고 스스로 말하고 있기 때문에, single split만으로는 이 작은 차이를 강하게 주장하기 어렵다.

### 수정 방향

최소 3개의 rolling-origin split을 추가하는 것이 좋다.

예시:

| Split | Train | Validation | Test |
|---|---|---|---|
| A | ≤2017 | 2019 | 2021 |
| B | ≤2018 | 2020 | 2022 |
| C | ≤2019 | 2021 | 2023 |

추가로 다음을 제시하면 좋다.

- split별 R²/RMSE 평균 및 표준편차
- paired bootstrap confidence interval
- PaGNet vs best panel-flatten baseline의 paired difference
- seed std뿐 아니라 temporal split std

이 실험을 넣으면 “single dataset/single split overfitting” 공격을 상당히 줄일 수 있다.

---

## 4.3 리스크 3: CETR에서 proposed blended PaGNet이 자기 NN branch보다 약하다

현재 가장 취약한 technical point는 CETR이다.

원고의 결과를 보면 CETR에서는 Panel-MLP branch가 blended PaGNet보다 더 좋다.

예시:

| Setting | Model | CETR R² |
|---|---|---:|
| FS1 Raw+Derived | PaGNet-NN | +0.0436 |
| FS1 Raw+Derived | Blended PaGNet | −0.0340 |
| FS2 | PaGNet-NN | +0.1274 |
| FS2 | Blended PaGNet | +0.0838 |
| FS2 learned-blender table | Panel-MLP branch | +0.1457 |
| FS2 learned-blender table | Grid blend | +0.0835 |

저자들은 이를 validation-test distribution shift로 설명하고 있다. 이 설명은 정직하고 나쁘지 않다. 하지만 reviewer는 다음을 물을 수 있다.

> If the diagnostic shows that the default blended model is suboptimal for CETR, why is the blended PaGNet still the proposed model?

### 수정 방향 A: PaGNet-Routed 제안

PaGNet을 단일 blended predictor가 아니라, validation-only diagnostic에 기반한 **target-wise routing framework**로 재정의하는 방법이 있다.

예:

- CETR: Panel-MLP branch 사용
- TSTA/TSDA: LightGBM branch 사용
- GETR: blended 또는 Panel-MLP branch 사용

단, test 결과를 보고 route를 정하면 안 된다. route rule은 validation split 또는 rolling validation에서 사전에 정해야 한다.

### 수정 방향 B: Claim을 낮추기

현재 full PaGNet을 유지하려면 “PaGNet is best single pipeline” 식의 표현을 줄이고 다음처럼 말해야 한다.

> PaGNet provides a unified blended forecast and exposes when branch-specific deployment is preferable.

즉, CETR에서 full blend가 최선이 아니라는 점을 weakness가 아니라 diagnostic value로 해석해야 한다.

내 추천은 **A와 B의 절충**이다. main model은 blended PaGNet으로 유지하되, deployment guidance에서 `PaGNet-Routed` 또는 `branch-specific deployment`를 명시하고, appendix에 validation-only routing 결과를 추가하는 것이 좋다.

---

## 4.4 리스크 4: architecture novelty가 incremental로 보일 수 있다

GBDT + NN hybrid, validation blending, multi-task MLP, attention pooling은 각각 기존 연구가 많다. reviewer는 다음처럼 볼 수 있다.

> The architecture is an incremental combination of known components.

따라서 novelty를 “새로운 블록을 만들었다”가 아니라 다음 세 가지로 재정렬해야 한다.

1. **Panel multi-target setting으로 hybrid를 확장**  
   firm-year short panel과 multiple tax proxies를 동시에 다룬다.

2. **Branch weight를 diagnostic으로 해석**  
   `lambda*`를 단순 ensemble weight가 아니라 target별 signal source readout으로 사용한다.

3. **Panel-flatten control로 information vs architecture를 분리**  
   이 논문의 가장 설득력 있는 methodological contribution이다.

반대로 다음 표현은 줄이는 것이 좋다.

- “no single-family model can produce”
- “every prediction inspectable”
- “first to cleanly separate”
- “transparent about which signal drives each proxy”

더 안전한 표현:

- “branch-level trust diagnostic”
- “information-equalized panel control”
- “controlled decomposition of information access and architecture effect”
- “feature-level traceability is further examined through SHAP/local case studies”

---

## 4.5 리스크 5: 내부 수치 서술 불일치

현재 원고에는 reviewer가 쉽게 잡을 수 있는 수치 불일치가 있다. 이건 반드시 제출 전 수정해야 한다.

### Panel-flatten win count 불일치

Section IV-D에서는 panel-flatten 결과를 다음처럼 설명한다.

- PaGNet wins **19 of 24** cells

그런데 Discussion/Conclusion 쪽에서는 다음처럼 보인다.

- PaGNet matches/exceeds on **21 of 24** information-equalized panel-flatten cells

Table 4 기준으로는 **19/24가 맞다.**

FS1에서는 GETR 3개 metric에서 PaGNet이 FT-Transformer(panel)에 밀리고, FS2에서는 GETR RMSE/R² 2개 metric에서 밀린다. 따라서 총 loss가 5개이고, win은 19개다.

### FS2 win count 불일치

Section IV-C에서는 best PaGNet variant가 strongest baseline을 **10 of 12** cells에서 이긴다고 말한다. 그런데 Discussion/Conclusion에서는 blended PaGNet이 **11 of 12 FS2 cells**에서 이긴다고 쓰여 있다.

Table 3 기준으로는 GETR RMSE와 GETR R²에서 FT-Transformer가 PaGNet보다 좋으므로 **10/12가 맞다.**

### 수정 지시

모든 곳에서 다음처럼 통일하는 것이 안전하다.

- FS1 Raw+Derived: `9/12` 유지 가능
- FS2: `10/12`
- Panel-flatten FS1+FS2: `19/24`

이 불일치는 작아 보이지만 reviewer에게는 “저자들이 자기 표를 정확히 읽지 않았다”는 나쁜 신호가 된다.

---

## 4.6 리스크 6: 형식/행정 문제

### Funding placeholder

첫 페이지에 다음 문구가 남아 있다.

> This work was supported in part by [funding information to be added].

이건 투고 전 반드시 제거해야 한다. 지원이 있으면 정확한 funder/grant number를 넣고, 없으면 no specific funding statement로 정리해야 한다.

### Abstract 길이

현재 abstract는 약 **328 words** 수준으로 보인다. IEEE Access template 기준 abstract는 보통 **150–250 words** 범위로 맞추는 것이 안전하다. 현재 abstract는 내용이 많고 좋지만 너무 길다.

### KoTaP 논문과의 self-overlap disclosure

본 논문은 KoTaP dataset paper를 기반으로 한다. 따라서 다음을 명확히 해야 한다.

- KoTaP 논문은 dataset descriptor / benchmark protocol 중심
- 본 논문은 PaGNet architecture, branch diagnostic, panel-flatten decomposition 중심
- 문장 재사용이 있으면 반드시 줄이고, cover letter에 차이를 설명

### Data/code availability

현재 reproducibility 측면에서 code/data availability statement가 더 명확해야 한다. IEEE Access reviewer는 ML 논문에서 재현 가능성을 자주 본다.

추천 문장:

> The KoTaP dataset is available through the corresponding data publication. Code for preprocessing, model training, panel-flatten controls, and evaluation scripts will be released upon publication / is available at [repository].

가능하면 익명 GitHub 또는 Zenodo/OSF 링크를 준비하는 것이 좋다.

---

## 5. 예상 reviewer comment

### Reviewer 1: Machine learning / tabular learning 관점

예상 코멘트:

> The proposed architecture combines known components: LightGBM, MLP, attention pooling, multi-task learning, and validation blending. The novelty over existing GBDT–NN hybrids is not sufficiently clear.

> The panel-flatten control shows that the remaining architecture gain is small. Statistical significance and temporal robustness should be reported.

대응:

- contribution을 architecture novelty가 아니라 panel multi-target diagnostic framework로 재정렬
- rolling-origin split 추가
- paired bootstrap CI 추가
- K sensitivity 추가
- tuned baseline 또는 constrained-budget tuning fairness 명시

---

### Reviewer 2: Explainability / responsible AI 관점

예상 코멘트:

> The paper motivates audit screening and traceability, but the explanation is only at the branch level. The model does not identify the economic drivers of individual predictions.

대응:

- LightGBM SHAP global feature importance 추가
- firm-year local explanation 추가
- attention/occlusion analysis 추가
- “explainable”을 “branch-level diagnostic + feature-level post-hoc explanation”으로 정리

---

### Reviewer 3: Accounting / tax avoidance 관점

예상 코멘트:

> The four targets are proxies, not direct observations of tax avoidance. The paper should avoid implying that the model predicts actual tax avoidance behavior.

대응:

- “tax avoidance proxy forecasting” 표현 유지
- “not direct detection of illegal tax avoidance” 명시
- ETR proxies와 accrual proxies의 construct 차이 설명 강화
- audit screening은 prioritization aid이지 final enforcement decision이 아님을 명시

---

### Associate Editor / Admin 관점

예상 코멘트:

> The manuscript contains placeholder funding text, an overlong abstract, and possible overlap with the KoTaP data paper. Please correct before review.

대응:

- funding placeholder 제거
- abstract 250 words 이하로 축약
- KoTaP 논문과 차별점 cover letter에 명시
- code/data availability 추가
- 수치 불일치 전부 수정

---

## 6. 권장 리비전 우선순위

## Priority 0: 제출 전 즉시 수정할 것

1. Funding placeholder 제거
2. Abstract 150–250 words로 축약
3. `19/24`, `10/12`, `11/12`, `21/24` 등 수치 불일치 수정
4. “every prediction inspectable”, “identifiable driver” 표현 완화
5. Data/code availability statement 추가
6. KoTaP paper와의 차별점 명시
7. Reference formatting / DOI / publication metadata 확인

이 단계는 하루 안에 처리 가능하지만, 하지 않으면 매우 나쁜 인상을 준다.

---

## Priority 1: accept 가능성을 실질적으로 올리는 수정

1. **Feature-level explanation 추가**
   - SHAP global top features
   - local case study 4개 target
   - branch weight + feature driver 연결

2. **Rolling temporal split 추가**
   - 최소 3 split
   - 평균/표준편차/CI 제시

3. **K sensitivity 추가**
   - K=1,2,3,4 비교
   - K=3 선택 근거 강화

4. **CETR routing / robust blender 정리**
   - PaGNet-Routed 또는 branch-specific deployment rule 추가
   - validation-only rule임을 명시

5. **Statistical testing**
   - paired bootstrap 또는 Diebold-Mariano류 test보다, 이 setting에서는 paired bootstrap CI가 더 직관적

---

## Priority 2: 시간이 있으면 추가하면 좋은 수정

1. Industry-wise performance heterogeneity
2. Firm-size subgroup analysis
3. Loss-near firms / denominator instability analysis for ETR proxies
4. External validation 또는 post-2024 확장 데이터가 가능하면 추가
5. Code repository와 model card / reproducibility checklist

---

## 7. Suggested abstract revision 방향

현재 abstract는 너무 많은 것을 담고 있다. 특히 다음 요소를 줄여야 한다.

- Oversight motivation의 세부 문장
- “no single-family model can produce” 같은 강한 novelty claim
- 성능 숫자를 너무 많이 나열하는 부분
- panel-flatten 결과의 상세 수치

### 예시 abstract 초안

아래는 250 words 이하로 줄인 예시다. 실제 투고 전 숫자와 표현은 최종 table 기준으로 다시 맞춰야 한다.

> Forecasting corporate tax avoidance proxies from firm-year panel data requires using short multi-year histories while avoiding look-ahead leakage and retaining interpretable signals for screening. We propose PaGNet, a panel-aware GBDT–neural hybrid for one-year-ahead prediction of four tax avoidance proxies: CETR, GETR, TSTA, and TSDA. PaGNet combines a LightGBM branch built on K=3 panel-temporal aggregate features with a multi-task Panel-MLP branch using attention-pooled temporal aggregation. The two branches are fused by a per-target validation-optimal blender with no trainable fusion parameters. The resulting blend weights provide a branch-level trust diagnostic, indicating whether each proxy relies more on tree-based temporal aggregation or neural multi-target representation sharing. On the KoTaP panel of Korean listed firms, PaGNet is evaluated under a leakage-free temporal protocol across four feature regimes and six tabular baselines. In the deployment-realistic FS1 and FS2 regimes, where prior-year target proxies are unavailable, PaGNet yields the strongest overall performance on the predictable accrual targets and remains competitive on ETR targets. A panel-flatten control shows that most accrual-target gains come from multi-year information access, while PaGNet adds a smaller but consistent architectural refinement. An AR(1) analysis further shows that lagged-target regimes saturate accrual prediction and compress architecture differences. These results position PaGNet not as a universally superior tabular learner, but as a controlled and diagnostically useful framework for panel-based tax proxy forecasting.

---

## 8. Contribution 재정렬 제안

현재 contribution은 좋지만 약간 과장되어 보일 수 있다. 아래처럼 정리하면 reviewer 방어가 쉬워진다.

### 기존 framing의 위험

- “우리가 새로운 hybrid architecture를 제안했고 대부분 이긴다”처럼 읽힘
- GBDT–NN hybrid 자체의 novelty가 약하다는 공격을 받을 수 있음
- interpretability claim이 feature-level evidence 없이 강하게 보임

### 추천 framing

1. **Panel-aware hybrid forecasting framework**  
   짧은 firm-year panel에서 GBDT temporal aggregates와 multi-task neural branch를 결합한다.

2. **Branch-level diagnostic for target heterogeneity**  
   `lambda*`를 통해 proxy별 signal source가 다름을 보여준다.

3. **Information-versus-architecture decomposition**  
   panel-flatten control로 multi-year information access와 architecture effect를 분리한다.

4. **Deployment-realistic evaluation**  
   FS1/FS2를 핵심 regime으로 두고, FS3/FS4는 AR(1) ceiling으로 해석한다.

---

## 9. 리젝 사유가 된다면 가장 유력한 순서

### 1순위: 설명가능성/traceability claim 불충분

현재 가장 위험하다. Audit screening을 motivation으로 쓰려면 branch-level weight 이상의 driver evidence가 필요하다.

### 2순위: robustness 부족

단일 temporal split과 K=3 fixed setting은 reviewer가 쉽게 공격할 수 있다.

### 3순위: architecture contribution이 incremental

Panel-flatten 이후 residual gain이 작다. 이를 “작지만 일관된 refinement”로 정직하게 말해야 한다.

### 4순위: proposed model이 target별 최적 branch보다 약함

특히 CETR에서 Panel-MLP branch가 full blend보다 낫다. deployment rule 또는 claim 조정이 필요하다.

### 5순위: manuscript polish / administrative issues

funding placeholder, abstract length, internal count inconsistency는 기술적 완성도 이전의 기본 문제다.

---

## 10. 투고 전 체크리스트

### Manuscript text

- [ ] Abstract 250 words 이하
- [ ] Funding placeholder 제거
- [ ] 수치 claim 전부 table과 cross-check
- [ ] `19/24`, `10/12` 등 win count 통일
- [ ] “every prediction inspectable” 표현 완화
- [ ] “feature-level explanation” 또는 claim downgrade
- [ ] “tax avoidance proxy”와 actual tax avoidance 구분
- [ ] KoTaP paper와 차별점 명시
- [ ] Code/data availability statement 추가

### Experiments

- [ ] Rolling-origin split 추가
- [ ] K sensitivity 추가
- [ ] SHAP/global feature attribution 추가
- [ ] Local case study 추가
- [ ] lambda stability plot 추가
- [ ] paired bootstrap CI 추가
- [ ] CETR routing 또는 robust blender discussion 강화

### Cover letter

- [ ] IEEE Access scope 적합성 설명
- [ ] KoTaP dataset paper와 본 논문의 차별성 설명
- [ ] Contribution을 architecture SOTA가 아니라 diagnostic panel-tabular framework로 설명
- [ ] Data/code release 계획 명시

---

## 11. 최종 투고 전략

### 전략 A: 빠른 투고형 revision

소요: 3–5일

할 일:

- abstract 축약
- funding/수치 불일치/표현 수정
- claim downgrade
- data/code statement 추가
- cover letter 보강

예상 효과:

- admin/editorial risk는 낮아짐
- 하지만 reviewer 단계에서 robustness/explainability 지적은 여전히 강하게 들어올 수 있음

판정 예상:

- Reject-resubmit 가능성이 여전히 높음

---

### 전략 B: 안전한 투고형 revision

소요: 2–3주

할 일:

- 전략 A 전부
- SHAP + local case study
- rolling split 3개
- K sensitivity
- lambda stability
- CETR routing discussion

예상 효과:

- “설명가능성 부족”, “single split”, “incremental architecture” 공격을 상당히 줄일 수 있음

판정 예상:

- Peer review에서 reject-resubmit이 오더라도 resubmission acceptance 가능성이 높아짐
- 운이 좋으면 accept with minor updates에 가까운 결과도 기대 가능

---

### 전략 C: 강한 revision

소요: 4주 이상

할 일:

- 전략 B 전부
- PaGNet-Routed 정식 variant 추가
- distributionally robust blender 또는 rolling-validation blender 추가
- industry/firm-size subgroup analysis
- reproducibility package 준비

예상 효과:

- 논문이 단순 hybrid model에서 “deployment-aware diagnostic framework”로 강해짐

판정 예상:

- IEEE Access뿐 아니라 더 selective한 applied ML / accounting analytics venue도 고려 가능

---

## 12. 최종 결론

현재 원고는 **투고 가능한 수준의 골격은 이미 갖췄다.** 특히 leakage-free protocol, panel-flatten control, AR(1) ceiling analysis는 좋은 설계다. 그러나 지금 상태로는 claim이 실험 evidence보다 조금 앞서 있으며, 몇 가지 manuscript-level 오류가 reviewer 신뢰를 떨어뜨릴 수 있다.

가장 중요한 수정 방향은 다음 한 문장으로 요약된다.

> PaGNet을 “압도적으로 우월한 새 tabular learner”로 주장하지 말고, “leakage-free panel evaluation에서 information access와 architecture effect를 분리하고, proxy별 branch-level trust diagnostic을 제공하는 deployment-aware forecasting framework”로 재정렬해야 한다.

이 방향으로 수정하면 IEEE Access 투고 경쟁력은 충분히 있다. 반대로 현재 claim과 수치 불일치를 그대로 두고 제출하면, 기술적 merit가 있음에도 **Reject, updates required before resubmission**이 가장 그럴듯한 결과다.
