# water-quality	

## Preperation
❏ 테스트 시스템 사양은 다음과 같습니다. 
- Ubuntu 18.04
- Python 3.7.9
- Tensorflow-gpu 2.4.1
- CUDA 11.1
- cuDnn 8.0.4

❏ 데이터 수집 
본 튜토리얼은 한강의 가평 자동측정망을 대상으로 5가지의 항목 예측을 
시행합니다.
예측에 필요한 데이터 파일(.xlsx)을 준비합니다. 
예측 대상지점인 “가평”과 상류 2개의 지점인 “의암호”, “서상“ 의 자동측정망과 ”대성리“, ”청평댐3“, ”남이섬“, ”가평천3“, ”춘성교“, ”의암“, ”춘천“, ”춘천댐1“, ”춘천댐3” 의 수질측정망, “조종천3”, “청평”, “가평천3”, “춘성교”, “화천”의 총량측정망의 2013년 ~ 2020년 까지의 (총 136개의)엑셀 파일을 준비합니다.
> [data]->[han] 폴더에 측정망별로 엑셀파일이 존재합니다.     

## Install Libraries
필요 Library를 설치 합니다.    
 
```bash
$ pip install –r requirement.txt
```

## Run 
1. input.json 
[input] 폴더안의 input.json을 변경 합니다. 



<!--stackedit_data:
eyJoaXN0b3J5IjpbMjk3MzQwODcwXX0=
-->