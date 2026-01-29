def classify_columns(df, threshold=20):
    """
    데이터프레임의 컬럼을 범주형(cat)과 수치형(num)으로 자동 분류합니다.
    ID나 Index 성격의 컬럼은 수치형에서 제외합니다.
    """
    # 1. 대상 컬럼 선택 (수치형 + 문자열)
    # str은 pandas에서 보통 'object' 타입이므로 'object'를 포함합니다.
    target_cols = df.select_dtypes(include=['int', 'float', 'str', 'object']).columns.tolist()

    cat_columns = []
    num_columns = []
    index_columns = [] # 인덱스성 컬럼을 따로 관리하면 나중에 확인하기 좋습니다.

    for col in target_cols:
        # A. 인덱스/ID 컬럼 필터링 (이름에 id/index가 있거나, 모든 값이 유니크할 때)
        is_index_name = any(ext in col.lower() for ext in ['id', 'index', 'idx', '_no'])
        is_high_cardinality = (df[col].nunique() == len(df))
        
        if is_index_name or is_high_cardinality:
            index_columns.append(col)
            continue # index 리스트에 넣었으므로 다음 루프로 넘어감

        # B. 유니크 값 개수에 따른 분류
        if df[col].nunique() < threshold:
            cat_columns.append(col)
        else:
            num_columns.append(col)

    print(f"✅ 분류 완료: 범주형({len(cat_columns)}), 수치형({len(num_columns)}), 제외된 인덱스({len(index_columns)})")
    
    return cat_columns, num_columns, index_columns

def check_dependency(df, child_col, parent_col):
    """
    child_col(예: city)이 parent_col(예: region)에 완전히 종속되는지 확인합니다.
    """
    # child_col 값 하나당 parent_col 값이 몇 종류인지 계산
    counts = df.groupby(child_col)[parent_col].nunique()
    
    # 모든 child_col에 대해 parent_col 종류가 1개뿐인지 확인
    is_dependent = (counts <= 1).all()
    
    if is_dependent:
        print(f"✅ '{child_col}'은(는) '{parent_col}'에 의해 결정됩니다. (1:1 또는 N:1 관계)")
    else:
        # 관계가 깨지는 데이터 추출
        conflicts = counts[counts > 1]
        print(f"❌ '{child_col}' 중 일부가 여러 '{parent_col}'에 속해 있습니다.")
        print(f"--- 위반 사례 (처음 5개) ---\n{conflicts.head()}")
        
    return is_dependent

# def save_file(df, filepath):
#     """
#     데이터프레임을 지정된 경로에 CSV 파일로 저장합니다.
#     """
#     df.to_csv(filepath, index=False)
#     print(f"✅ 파일이 저장되었습니다: {filepath}")