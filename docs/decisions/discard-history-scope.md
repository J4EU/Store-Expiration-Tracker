# Discard History Scope

## 현재 선택

`discard_histories`에는 실제로 폐기한 수량이 0보다 큰 사건만 저장한다. `폐기 없음`은 실제 폐기 이력으로 저장하지 않고, 폐기 당시 소비기한 snapshot도 현재는 저장하지 않는다.

## 이유

이 데이터의 목적은 일반적인 BI나 판매 예측이 아니라, 실제 폐기 수량이 반복되는 상품을 확인해 현재 발주량이나 취급 유지 여부를 다시 검토할 근거를 남기는 것이다.

이 목적에는 언제, 어떤 상품이, 몇 개 실제로 폐기됐는지가 우선이다. 폐기 없음은 현재 소비기한을 종료한 확인 사건이지만 실제 폐기 수량 사건은 아니다. 이를 같은 이력에 넣으면 실제 폐기 횟수와 수량의 의미가 흐려진다.

폐기 당시 소비기한 snapshot은 운영 해석에는 도움이 될 수 있지만, 현재 목적의 필수 데이터는 아니다.

## 수용한 trade-off

- 현재 데이터만으로는 폐기 당시 소비기한이나 폐기 없음 확인 횟수를 분석할 수 없다.
- 현재 제품은 실제 폐기 데이터를 저장할 뿐, 이를 조회·집계하는 분석 API나 화면을 제공하지 않는다.

## 재검토 조건

- 소비기한 대비 폐기 시점 같은 운영 해석이 실제 판단에 필요해질 때
- 폐기 없음 자체를 별도의 운영 지표로 확인해야 할 때
- 실제 분석 기능을 도입하기 전에 필요한 질문과 데이터 범위를 다시 정의할 때

## References

- [Issue #6](https://github.com/J4EU/Store-Expiration-Tracker/issues/6)
- [PR #7](https://github.com/J4EU/Store-Expiration-Tracker/pull/7)
- [PR #8](https://github.com/J4EU/Store-Expiration-Tracker/pull/8)
- [Issue #10](https://github.com/J4EU/Store-Expiration-Tracker/issues/10)
- [PR #11](https://github.com/J4EU/Store-Expiration-Tracker/pull/11)
