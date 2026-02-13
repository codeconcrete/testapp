import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import datetime
import math
import streamlit.components.v1 as components

import re

# 1. 화면 디자인 및 CSS (A4 출력용 스타일 포함)
def parse_to_list(text_data):
    if isinstance(text_data, list):
        return text_data
    if not text_data:
        return []
    return [item.strip() for item in text_data.split(',') if item.strip()]

def clean_item_list(items):
    """모든 항목에서 괄호 내용 제거 및 특수 치환"""
    cleaned = []
    for item in items:
        # Remove text in parentheses: "굴착기(백호우)" -> "굴착기", "안전모(턱끈포함)" -> "안전모"
        new_item = re.sub(r'\([^)]*\)', '', item).strip()
        
        # Specific replacements
        if "안전대" in new_item and "벨트" not in new_item:
            new_item = "전체식 안전벨트"
        
        if new_item:
            cleaned.append(new_item)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(cleaned))

st.set_page_config(page_title="스마트 위험성평가", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #1a1a1a; color: #ffffff; }
    h1, h2, h3, p, div { font-family: 'Noto Sans KR', sans-serif; }
    .stTextInput input { background-color: #333333 !important; color: white !important; }
    .stTextInput input::placeholder { color: #aaaaaa !important; opacity: 1; }
    .stTextInput label, .stMultiSelect label, .stTextInput label p, .stMultiSelect label p { color: #ffffff !important; }
    div.stButton > button {
        background-color: #0085ff; color: white; border: none;
        border-radius: 5px; padding: 10px 20px; font-weight: bold; width: 100%;
    }
    
    /* Table styling - only for the report tables */
    .safety-table {
        width: 100% !important; 
        table-layout: fixed !important;
        border-collapse: collapse;
        font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
        font-size: 10pt;
        margin-bottom: 5px;
        color: #000000;
    }
    .safety-table th, .safety-table td {
        border: 1px solid #000000;
        padding: 2px;
        text-align: center;
        vertical-align: middle;
        background-color: #ffffff;
        color: #000000;
        word-break: break-all;
    }
    .safety-table th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    .left-align {
        text-align: left !important;
        padding-left: 5px;
    }
    
    /* Screen A4 Preview Container */
    .a4-page {
        width: 297mm;
        height: 210mm;
        padding: 10mm;
        margin: 0 auto;
        background: white;
        color: black;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        box-sizing: border-box;
        border: 1px solid #ddd;
        display: block;
    }
    
    /* PRINT SETTINGS */
    @media print {
        @page {
            size: 297mm 210mm;
            margin: 0;
        }
        
        body > * { display: none !important; }
        
        body > div[data-testid="stAppViewBlockContainer"],
        body > div,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMainBlockContainer"],
        .block-container,
        .print-container {
            display: block !important;
        }
        
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"],
        [data-testid="stBottom"], [data-testid="stDecoration"], .stInfo, .stButton,
        .stDivider, footer, hr, .no-print {
            display: none !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        
        html, body, .stApp, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stMainBlockContainer"],
        .block-container {
            margin: 0 !important;
            padding: 0 !important;
            background: white !important;
            max-width: none !important;
            width: 100% !important;
        }
        
        .print-container {
            display: block !important;
            width: 100% !important;
        }
        
        .a4-page {
            width: 297mm !important;
            height: 210mm !important;
            padding: 10mm !important;
            margin: 0 !important;
            box-shadow: none !important;
            border: none !important;
            page-break-after: always;
            page-break-inside: avoid;
            box-sizing: border-box;
            background: white !important;
            overflow: hidden !important;
        }
        
        .a4-page:last-child {
            page-break-after: auto;
        }
        
        .safety-table {
            width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

today_str = datetime.datetime.now().strftime("%Y.%m.%d")

# Helper function for Header
def create_header_html(task_name, location, protectors, safety_equip, tools, materials, writer, action_taker, reviewer, checker, approver, today_str):
    return f'''
<div style="text-align:right; font-size:10px; margin-bottom:5px; color:black;">(보존기간 : 3년)</div>
<table class="safety-table" style="width: 100%; table-layout: fixed;">
    <colgroup>
        <col style="width: 15%;">
        <col style="width: 35%;">
        <col style="width: 10%;">
        <col style="width: 15%;">
        <col style="width: 10%;">
        <col style="width: 15%;">
    </colgroup>
    <tr>
        <th>단위 작업명</th>
        <td class="left-align" colspan="5" style="color: blue; font-weight: bold; font-size:14px;">{task_name}</td>
    </tr>
    <tr>
        <th>보 호 구</th>
        <td class="left-align">{', '.join(protectors)}</td>
        <th>작 업 구 역</th>
        <td colspan="3">{location}</td>
    </tr>
    <tr>
        <th>안 전 장 비</th>
        <td class="left-align">{', '.join(safety_equip)}</td>
        <th>작성자</th>
        <td>{writer}</td>
        <th>작성일</th>
        <td>{today_str}</td>
    </tr>
    <tr>
        <th>공구 및 장비</th>
        <td class="left-align">{', '.join(tools)}</td>
        <th>검토자</th>
        <td>{reviewer}</td>
        <th>검토일</th>
        <td>{today_str}</td>
    </tr>
    <tr>
        <th>준비 자료</th>
        <td class="left-align">{', '.join(materials)}</td>
        <th>승인자</th>
        <td>{approver}</td>
        <th>승인일</th>
        <td>{today_str}</td>
    </tr>
    <tr>
        <th>조치자</th>
        <td class="left-align">{action_taker}</td>
        <th>이행상태 확인</th>
        <td colspan="3">{checker}</td>
    </tr>
</table>
'''

st.title("🛡️ AI 건설 위험성평가 생성기")
st.caption(f"시스템 버전: {genai.__version__} (Gemini 1.5 Flash 엔진)")

# 2. API 키 가져오기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = st.text_input("API 키 입력", type="password")

# 2-1. safety_data.json에서 작업 데이터 인덱스 구축 (키워드 매칭용)
@st.cache_data
def load_safety_index():
    """safety_data.json의 모든 단위작업을 인덱싱하여 키워드 매칭이 가능하게 함"""
    try:
        with open('safety_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return [], {}
    
    index = []  # [{name, keywords, data, division, work_type, path}, ...]
    all_vocab = {"protectors": set(), "safety_equip": set(), "tools": set(), "docs": set()}
    
    # 키워드 추출 함수: 번호/괄호 제거 후 핵심 단어만 추출
    def extract_keywords(text):
        # 번호 제거: "1) 가설공사" -> "가설공사", "(7) 콘크리트 타설 및 양생" -> "콘크리트 타설 및 양생"
        cleaned = re.sub(r'^\d+\)\s*', '', text)
        cleaned = re.sub(r'^\(\d+\)\s*', '', cleaned)
        # 공백, 특수문자로 분리
        words = re.split(r'[\s,/·및\-_]+', cleaned)
        # 의미있는 단어만 (1글자 이상)
        keywords = set()
        for w in words:
            w = w.strip()
            if len(w) >= 1:
                keywords.add(w.lower())
        return keywords
    
    # 동의어 매핑 (사용자가 입력할 수 있는 다양한 표현 대응)
    synonym_map = {
        'mat': ['콘크리트', '타설', 'mat'],
        '타설': ['콘크리트', '타설', '양생'],
        '콘크리트': ['콘크리트', '타설', 'conc', 'rc'],
        '비계': ['비계', '가설', '스캐폴딩'],
        '용접': ['용접', '화기'],
        '배관': ['배관', '파이프', 'pipe'],
        '도장': ['도장', '페인트', '방청'],
        '철근': ['철근', '배근', 'conc', 'rc'],
        '토공': ['토공', '굴착', '되메우기', '터파기'],
        '굴착': ['토공', '굴착', '터파기'],
        '방수': ['방수', '우레탄', '아스팔트', '시트'],
        '거푸집': ['거푸집', '폼', '형틀', '탈형'],
        '양중': ['양중', '크레인', '인양'],
        '크레인': ['양중', '크레인', '인양'],
        '해체': ['해체', '철거', '잔재물'],
        '전기': ['전기', '배선', '케이블'],
        '철골': ['철골', '강구조', 'steel'],
        '포장': ['포장', '아스팔트', '아스콘'],
    }
    
    for division_name, division_data in data.items():
        if not isinstance(division_data, dict):
            continue
        for work_type_name, work_type_data in division_data.items():
            if not isinstance(work_type_data, dict):
                continue
            for unit_work_name, unit_work_data in work_type_data.items():
                if not isinstance(unit_work_data, dict) or "protectors" not in unit_work_data:
                    continue
                
                keywords = extract_keywords(unit_work_name)
                keywords.update(extract_keywords(work_type_name))
                
                entry = {
                    "name": unit_work_name,
                    "keywords": keywords,
                    "data": {
                        "protectors": unit_work_data.get("protectors", ""),
                        "safety_equip": unit_work_data.get("safety_equip", ""),
                        "tools": unit_work_data.get("tools", ""),
                        "docs": unit_work_data.get("docs", ""),
                    },
                    "risks": unit_work_data.get("risks", []),
                    "division": division_name,
                    "work_type": work_type_name,
                    "path": f"{division_name} > {work_type_name} > {unit_work_name}"
                }
                index.append(entry)
                
                # 전체 용어 수집 (프롬프트 참고용)
                for item in unit_work_data.get("protectors", "").split(','):
                    cleaned = re.sub(r'\([^)]*\)', '', item).strip()
                    if cleaned:
                        all_vocab["protectors"].add(cleaned)
                for item in unit_work_data.get("safety_equip", "").split(','):
                    if item.strip():
                        all_vocab["safety_equip"].add(item.strip())
                for item in unit_work_data.get("tools", "").split(','):
                    if item.strip():
                        all_vocab["tools"].add(item.strip())
                for item in unit_work_data.get("docs", "").split(','):
                    if item.strip():
                        all_vocab["docs"].add(item.strip())
    
    vocab_sorted = {k: sorted(v) for k, v in all_vocab.items()}
    return index, vocab_sorted, synonym_map

def find_best_match(task_name, index, synonym_map):
    """사용자 입력 작업명과 가장 유사한 safety_data.json 항목 찾기"""
    if not task_name or not index:
        return None, 0
    
    # 사용자 입력 키워드 추출
    user_words_raw = re.split(r'[\s,/·및\-_]+', task_name.strip())
    user_keywords = set()
    for w in user_words_raw:
        w = w.strip().lower()
        if len(w) >= 1:
            user_keywords.add(w)
            # 동의어 확장
            for syn_key, syn_values in synonym_map.items():
                if syn_key in w or w in syn_key:
                    user_keywords.update(syn_values)
    
    best_match = None
    best_score = 0
    
    for entry in index:
        entry_keywords = entry["keywords"]
        # 확장된 entry 키워드 (동의어 포함)
        expanded_entry = set(entry_keywords)
        for kw in entry_keywords:
            for syn_key, syn_values in synonym_map.items():
                if syn_key in kw or kw in syn_key:
                    expanded_entry.update(syn_values)
        
        # 교집합 기반 점수 계산
        overlap = user_keywords & expanded_entry
        if not overlap:
            continue
        
        # 점수 = 겹치는 키워드 수 / 사용자 키워드 수 (0~1) 
        score = len(overlap) / max(len(user_keywords), 1)
        
        # 직접 키워드 매칭 보너스 (원본 키워드끼리 겹치면 가산점)
        direct_overlap = set(w.lower() for w in user_words_raw if len(w.strip()) >= 1) & entry_keywords
        score += len(direct_overlap) * 0.3
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    return best_match, best_score

safety_index, ref_vocab, synonym_map = load_safety_index()
ref_vocab_text = f"""[현장 표준 용어 참고 - 반드시 아래 용어를 우선 사용하세요]
- 보호구 용어: {', '.join(ref_vocab.get('protectors', [])[:30])}
- 안전장비 용어: {', '.join(ref_vocab.get('safety_equip', [])[:30])}
- 공구/장비 용어: {', '.join(ref_vocab.get('tools', [])[:30])}
- 준비자료 용어: {', '.join(ref_vocab.get('docs', [])[:20])}
"""

# 3. 작업 정보 입력 (1단계)
st.markdown("### 1. 작업 개요 및 위험 특성")
col1, col2 = st.columns(2)
with col1:
    task_name = st.text_input("작업명", placeholder="예: 외부 비계 해체 작업")
    # 주요 위험 요인 선택
    risk_factors = st.multiselect(
        "해당되는 위험 작업 특성을 모두 선택하세요 (자동 추천에 반영)",
        ["일반작업 (해당 없음)", "고소작업 (추락 위험)", "화기작업 (화재 발생)", "밀폐공간 (질식 위험)", 
         "전기작업 (감전 위험)", "중량물 취급 (근골격계/낙하)", "화학물질 취급", 
         "건설기계 사용", "해체/철거 작업"]
    )

with col2:
    location = st.text_input("작업 위치", placeholder="예: 105동 외부 지상 3층~5층")
    risk_context_manual = st.text_input("기타 위험 특성 (직접 입력)", placeholder="예: 강풍 예상, 야간 작업, 인접 장비 동시 작업 등")

# 초안 생성 버튼
if "draft_generated" not in st.session_state:
    st.session_state.draft_generated = False

analyze_btn = st.button("📋 작업 정보 분석 및 장비 추천받기 (1단계)", use_container_width=True)

if analyze_btn:
    if not task_name:
        st.error("작업명을 입력해주세요.")
    elif not api_key:
        st.error("API 키를 먼저 입력해주세요.")
    else:
        # safety_data.json에서 유사 작업 검색 (참고용)
        matched_entry, match_score = find_best_match(task_name, safety_index, synonym_map)
        
        # 매칭된 데이터를 참고자료로 구성
        ref_data_text = ""
        if matched_entry and match_score >= 0.3:
            md = matched_entry["data"]
            ref_data_text = f"""
                [참고: 유사 작업 표준 데이터 - "{matched_entry['name']}"]
                아래는 유사한 작업의 표준 데이터입니다. 하지만 사용자의 실제 작업명은 "{task_name}"이므로,
                작업 내용에 맞게 적절히 참고만 하고, 작업명에 맞지 않는 항목은 제외하거나 교체하세요.
                - 참고 보호구: {md.get('protectors', '')}
                - 참고 안전장비: {md.get('safety_equip', '')}
                - 참고 공구/장비: {md.get('tools', '')}
                - 참고 준비자료: {md.get('docs', '')}
            """
        
        with st.spinner("작업 특성을 분석하여 안전 장비를 추천 중입니다... 🤖"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
                
                req_prompt = f"""
                    건설 안전 전문가로서 다음 작업에 필요한 장비와 준비물을 제안하세요.
                    
                    [작업 정보]
                    - 작업명: {task_name}
                    - 장소: {location}
                    - 위험 특성: {', '.join(risk_factors)}
                    - 기타: {risk_context_manual}
                    
                    {ref_vocab_text}
                    {ref_data_text}
                    
                    [요청 사항]
                    **작업명 "{task_name}"에 정확히 맞는** 장비와 준비물을 추천하세요.
                    참고 데이터가 있더라도, 실제 작업 내용과 맞지 않으면 무시하고 작업명에 맞게 새로 작성하세요.
                    위 '현장 표준 용어'에 해당 항목이 있으면 반드시 그 용어를 그대로 사용하세요.
                    1. 보호구 (필수 및 권장)
                    2. 안전장비 (시설물 포함)
                    3. 사용 공구/장비
                    4. 준비자료 (허가서 등)
                    
                    [중요 규칙]
                    - 모든 항목명에 괄호 안 부가설명을 넣지 마세요.
                      예: "안전모" (O), "안전모(턱끈포함)" (X), "굴착기" (O), "굴착기(백호우)" (X)
                    - "안전대" 대신 반드시 "전체식 안전벨트"로 작성하세요.
                    - 공구/장비명은 현장에서 실제 사용하는 용어를 쓰세요.
                      예: "바이브레이터" (O), "고주파진동기" (X)
                    - 소화기는 화기작업(용접, 가스절단, 도장 등)에만 포함하세요. 콘크리트 타설, 자재반입 등 일반 작업에는 소화기를 넣지 마세요.
                    - 작업명에 맞는 실제 장비를 추천하세요:
                      * 콘크리트/MAT 타설: 공구→레미콘, 펌프카, 바이브레이터 / 안전장비→반사경, 스토퍼, 라바콘
                      * 자재반입/하역/운반: 공구→지게차, 카고트럭, 슬링벨트, 샤클, 와이어로프 / 안전장비→신호봉, 라바콘
                      * 철근작업: 공구→절단기, 절곡기(밴딩기), 수공구
                      * 비계/가설: 공구→비계자재, 수공구, 전동공구 / 안전장비→안전네트, 추락방지망
                    - 해당 작업에 실제로 사용하지 않는 장비는 절대 포함하지 마세요.
                    
                    [JSON 포맷]
                    {{
                        "protectors": "안전모, 안전화, ...",
                        "safety_equip": "CCTV, 라바콘, ...",
                        "tools": "...",
                        "docs": "..."
                    }}
                    """
                
                response = model.generate_content(req_prompt)
                draft_data = json.loads(response.text)
                
                # 세션에 저장
                st.session_state.draft_data = draft_data
                st.session_state.matched_entry = matched_entry if (matched_entry and match_score >= 0.3) else None
                st.session_state.draft_generated = True
                
                if matched_entry and match_score >= 0.3:
                    st.success(f"📂 유사 작업 **{matched_entry['name']}**을 참고하여 AI가 **{task_name}**에 맞게 추천했습니다.")
                else:
                    st.info("🤖 AI가 작업 내용을 분석하여 추천했습니다.")
                
            except Exception as e:
                st.error(f"분석 실패: {e}")

# 2단계: 추천 결과 확인 및 수정
if st.session_state.draft_generated:
    st.markdown("### 2. 추천 장비 및 준비물 확인 (수정 가능)")
    matched = st.session_state.get('matched_entry')
    if matched:
        st.success(f"📂 유사 작업 **{matched.get('name', '')}** 참고 — AI가 **{task_name}**에 맞게 추천한 결과입니다. 수정 가능합니다.")
    else:
        st.info("🤖 AI가 추천한 내용입니다. 현장 상황에 맞게 수정하세요.")
    
    draft = st.session_state.draft_data
    
    # 공통 기본값 (safety_data.json 분석 기반 - 대부분의 작업에 공통)
    common_defaults = {
        "protectors": ["안전모", "안전화"],
        "safety_equip": [],
        "tools": [],
        "docs": ["TBM", "안전작업 허가서"],
    }
    
    col3, col4 = st.columns(2)
    with col3:
        protectors_list = clean_item_list(parse_to_list(draft.get("protectors", "")))
        for d_item in common_defaults["protectors"]:
            if d_item not in protectors_list:
                protectors_list.insert(0, d_item)
        prot_defaults = [p for p in protectors_list if p in common_defaults["protectors"] or p in clean_item_list(parse_to_list(draft.get("protectors", "")))]
        protectors_selected = st.multiselect("보호구", options=protectors_list, default=prot_defaults)
        protectors_extra = st.text_input("보호구 추가 입력", placeholder="예: 방열복, 절연장갑 (쉼표로 구분)", key="prot_extra")
        protectors = protectors_selected + [x.strip() for x in protectors_extra.split(',') if x.strip()]

        tools_list = clean_item_list(parse_to_list(draft.get("tools", "")))
        for d_item in common_defaults["tools"]:
            if d_item not in tools_list:
                tools_list.insert(0, d_item)
        tools_selected = st.multiselect("사용 공구/장비", options=tools_list, default=tools_list)
        tools_extra = st.text_input("공구/장비 추가 입력", placeholder="예: 지게차, 슬링벨트 (쉼표로 구분)", key="tools_extra")
        tools = tools_selected + [x.strip() for x in tools_extra.split(',') if x.strip()]
    
    with col4:
        safety_equip_list = clean_item_list(parse_to_list(draft.get("safety_equip", "")))
        for d_item in common_defaults["safety_equip"]:
            if d_item not in safety_equip_list:
                safety_equip_list.insert(0, d_item)
        safety_equip_selected = st.multiselect("안전장비/시설", options=safety_equip_list, default=safety_equip_list)
        safety_extra = st.text_input("안전장비 추가 입력", placeholder="예: 안전난간, 경광등 (쉼표로 구분)", key="equip_extra")
        safety_equip = safety_equip_selected + [x.strip() for x in safety_extra.split(',') if x.strip()]

        materials_list = clean_item_list(parse_to_list(draft.get("docs", "")))
        for d_item in common_defaults["docs"]:
            if d_item not in materials_list:
                materials_list.insert(0, d_item)
        docs_defaults = [d for d in materials_list if d in common_defaults["docs"] or d in parse_to_list(draft.get("docs", ""))]
        materials_selected = st.multiselect("준비자료/허가서", options=materials_list, default=docs_defaults)
        materials_extra = st.text_input("준비자료 추가 입력", placeholder="예: 밀폐공간작업허가서 (쉼표로 구분)", key="docs_extra")
        materials = materials_selected + [x.strip() for x in materials_extra.split(',') if x.strip()]
        
    # 추가 입력 필드 (결재란 및 조치자 등) - A4 출력용
    st.markdown("##### ✍️ 추가 정보 입력 (결재란 및 담당자)")
    col_add1, col_add2, col_add3 = st.columns(3)
    with col_add1:
        writer_name = st.text_input("작성자", value="관리감독자")
        action_taker = st.text_input("조치자", value="공급사 관리감독자")
    with col_add2:
        reviewer_name = st.text_input("검토자", value="안전관리자")
        checker_name = st.text_input("이행상태 확인자", value="시공사 관리감독자")
    with col_add3:
        approver_name = st.text_input("승인자", value="현장소장")

    st.markdown("---")
    generate_final_btn = st.button("🚀 위험성평가표 최종 생성하기 (2단계)", use_container_width=True)

    if generate_final_btn:
        with st.spinner("최종 위험성평가표를 생성하고 있습니다... 🛡️"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    'gemini-flash-latest', 
                    generation_config={"response_mime_type": "application/json"}
                )

                prompt = f"""
                건설 안전 기술사로서 아래 작업에 대한 위험성평가표(JSA)를 작성하세요.
                
                [작업 정보]
                - 작업명: {task_name}
                - 작업 위치: {location}
                - 위험 특성: {', '.join(risk_factors)} / {risk_context_manual}
                - 보호구: {', '.join(protectors)}
                - 안전장비: {', '.join(safety_equip)}
                - 사용장비: {', '.join(tools)}
                - 준비자료: {', '.join(materials)}
                
                {ref_vocab_text}
                {''.join([
                    chr(10) + '                [참고: 표준 데이터의 유사 작업 위험성평가 예시 - 아래 내용을 참고하여 비슷한 톤과 표현으로 작성하세요]' + chr(10) +
                    chr(10).join([
                        f"                - 단계: {r.get('step','')}, 위험요인: {r.get('factor','')}, 대책: {r.get('measure','')}"
                        for r in st.session_state.get('matched_entry', {}).get('risks', [])[:6]
                    ])
                ] if st.session_state.get('matched_entry') and st.session_state.get('matched_entry', {}).get('risks') else [])}
                
                [작업 규칙]
                1. '작업준비' -> '본작업' -> '작업종료/정리' 3단계를 기본으로 하되, **'본작업'은 반드시 구체적인 단위 작업명으로 세분화해서 작성하세요.** (예: '본작업: 펌프카 설치', '본작업: 타설 진행')
                2. '작업준비' 단계의 맨 첫 번째 행은 반드시 '작업자 개인 보호구 및 복장 상태 확인'에 대한 내용이어야 합니다.
                3. 각 위험요인별 '대책'은 실질적인 내용으로 반드시 2개~5개 사이로 다르게 작성하세요. (줄바꿈은 반드시 '\\n' 문자를 사용하세요. 실제 엔터키 사용 금지)
                4. [중요] 위험성은 빈도(1~5)와 강도(1~4)의 곱으로 계산하되, 계산된 '위험성' 수치가 절대 8을 초과하지 않도록 빈도와 강도를 조절하세요. (위험성 <= 8)
                5. 반드시 JSON 포맷으로만 출력하세요. (Markdown 코드 블록 없이 순수 JSON만 출력)
                6. [중요] 위 '현장 표준 용어'에 있는 표현을 우선적으로 사용하세요. 현장 실무 용어를 그대로 쓰세요.
                7. [중요] **반드시 최소 12개 이상, 최대 20개 이하의 위험요인 항목**을 생성하세요.
                   - '작업준비': 3~4개
                   - '본작업: (세부단계1)': 3~5개
                   - '본작업: (세부단계2)': 3~5개 (필요시 세부단계 추가)
                   - '작업종료/정리': 2~3개
                8. [중요] **위험요인은 반드시 1가지 위험만 기술하세요.** 여러 위험을 "및", "또는"으로 묶지 마세요.
                   - 잘못된 예: "체인 이탈 또는 파손으로 인한 낙하 및 깔림 위험" (X)
                   - 올바른 예: "체인 이탈로 인한 자재 낙하 위험" (O) → 별도 행: "인양 자재에 의한 작업자 깔림 위험" (O)
                   각 위험요인에 대해 그에 맞는 구체적인 대책을 작성하세요.
                
                [JSON 예시]
                [
                    {{"단계": "1) 작업준비", "위험요인": "...", "대책": "...", "빈도": 2, "강도": 3}},
                    {{"단계": "2) 본작업: ...", "위험요인": "...", "대책": "...", "빈도": 2, "강도": 3}}
                ]
                """
                
                response = model.generate_content(prompt)
                
                # JSON 파싱 전처리
                text = response.text
                if "```json" in text:
                    text = text.replace("```json", "").replace("```", "")
                text = text.strip()
                
                data = json.loads(text, strict=False)
                df = pd.DataFrame(data)
                df["위험성"] = df["빈도"] * df["강도"]
                df["등급"] = df["위험성"].apply(lambda x: "🔴 상" if x>=6 else ("🟡 중" if x>=3 else "🟢 하"))
                
                st.session_state.result_df = df
                st.success("최종 생성 완료! 아래 결과를 확인하세요.")

            except Exception as e:
                st.error(f"생성 중 오류 발생: {e}")

if 'result_df' in st.session_state:
    st.divider()
    
    # 3. 결과 수정 및 확정 (통합 카드 뷰)
    st.divider()
    st.markdown("### 📝 위험성평가 수정 및 확정")
    st.info("각 항목을 직접 수정하세요. 내용은 하단 A4 미리보기에 실시간으로 반영됩니다.")
    
    if 'result_df' not in st.session_state or st.session_state.result_df.empty:
        st.warning("데이터가 없습니다.")
    else:
        # DataFrame을 리스트 딕셔너리로 변환하여 처리 (삭제/추가 용이성)
        # 세션 스테이트에 'rows'가 없으면 초기화
        if 'rows_data' not in st.session_state:
            st.session_state.rows_data = st.session_state.result_df.to_dict('records')
            
        rows = st.session_state.rows_data
        
        # 행 추가 버튼 (상단)
        col_add_top, _ = st.columns([1, 5])
        if col_add_top.button("➕ 새 항목 추가", key="add_row_top"):
            new_row = {
                "단계": "1) 작업준비", 
                "위험요인": "새로운 위험요인 입력", 
                "대책": "대책을 입력하세요.", 
                "빈도": 1, "강도": 1, "위험성": 1, "등급": "🟢 하"
            }
            rows.insert(0, new_row)
            st.rerun()

        # 각 행을 카드 형태로 출력
        rows_to_delete = []
        
        for idx, row in enumerate(rows):
            with st.container(border=True):
                # Header: 단계 & 삭제 버튼
                c1, c2, c3 = st.columns([2, 6, 1])
                with c1:
                    new_step = st.text_input(f"작업단계 #{idx+1}", value=row.get('단계', ''), key=f"step_{idx}")
                    row['단계'] = new_step
                with c2:
                    st.empty() # Spacer
                with c3:
                    if st.button("🗑️ 삭제", key=f"del_{idx}", type="secondary"):
                        rows_to_delete.append(idx)
                
                # Content: 위험요인 & 대책
                c_factor, c_measure = st.columns([1, 1])
                with c_factor:
                    new_factor = st.text_area("유해위험요인", value=row.get('위험요인', ''), key=f"factor_{idx}", height=100)
                    row['위험요인'] = new_factor
                with c_measure:
                    new_measure = st.text_area("위험 제거 및 감소 대책 (줄바꿈 가능)", value=row.get('대책', ''), key=f"measure_{idx}", height=100)
                    row['대책'] = new_measure
                
                # Footer: 빈도/강도/위험성
                c_freq, c_sev, c_risk, c_grade = st.columns(4)
                with c_freq:
                    new_freq = st.number_input("빈도", min_value=1, max_value=5, value=int(row.get('빈도', 1)), key=f"freq_{idx}")
                    row['빈도'] = new_freq
                with c_sev:
                    new_sev = st.number_input("강도", min_value=1, max_value=4, value=int(row.get('강도', 1)), key=f"sev_{idx}")
                    row['강도'] = new_sev
                with c_risk:
                    risk_val = new_freq * new_sev
                    row['위험성'] = risk_val
                    st.metric("위험성", risk_val)
                with c_grade:
                    grade = "🔴 상" if risk_val>=6 else ("🟡 중" if risk_val>=3 else "🟢 하")
                    row['등급'] = grade
                    st.metric("등급", grade)

        # 삭제 처리
        if rows_to_delete:
            for del_idx in sorted(rows_to_delete, reverse=True):
                del rows[del_idx]
            st.rerun()
            
        # 데이터프레임 동기화 (출력 로직이 DF를 쓰므로)
        st.session_state.result_df = pd.DataFrame(rows)

    # 여기서부터 A4 출력 로직으로 대체
    st.divider()
    st.markdown("### 📋 위험성평가 결과 (A4 출력용)")
    
    df = st.session_state.result_df
    
    # Flatten Data for Pagination
    grouped_df = df.groupby('단계', sort=False)
    flat_data = []
    
    for step_name, group in grouped_df:
        first_in_group = True
        for idx, row in group.iterrows():
            item = row.to_dict()
            item['is_first'] = first_in_group
            item['step_name'] = step_name
            item['group_size'] = len(group)
            flat_data.append(item)
            first_in_group = False
            
    # Dynamic Pagination Logic (Height-based)
    pages = []
    current_page = []
    
    current_height = 0
    # Capacity in "lines" (Heuristic)
    # Page 1 has header, so less space. Page N has full space.
    # Adjusted capacities to reduce empty space (Optimized for A4)
    PAGE_1_CAPACITY = 22.0  # Increased from 16
    PAGE_N_CAPACITY = 32.0  # Increased from 25
    
    limit = PAGE_1_CAPACITY
    
    def count_view_lines(text, chars_per_line):
        """줄바꿈과 자동 줄바꿈(wrapping)을 모두 고려한 줄 수 계산"""
        if not text:
            return 1
        lines = str(text).split('\n')
        total = 0
        for line in lines:
            length = len(line)
            if length == 0:
                total += 1
            else:
                total += math.ceil(length / chars_per_line)
        return total

    def split_text_to_fit(text, max_lines, chars_per_line):
        """주어진 줄 수(max_lines)에 맞춰 텍스트를 앞부분(head)과 뒷부분(tail)으로 분리"""
        if not text:
            return "", ""
        
        raw_lines = str(text).split('\n')
        head_lines = []
        tail_lines = []
        
        current_lines = 0
        
        for i, line in enumerate(raw_lines):
            line_len = len(line)
            line_cost = 1 if line_len == 0 else math.ceil(line_len / chars_per_line)
            
            if current_lines + line_cost <= max_lines:
                head_lines.append(line)
                current_lines += line_cost
            else:
                # 이 줄에서 잘라야 함
                remaining_lines_capacity = max_lines - current_lines
                if remaining_lines_capacity > 0 and line_len > chars_per_line:
                    # chars_per_line 만큼씩 잘라서 head에 추가
                    split_idx = int(remaining_lines_capacity * chars_per_line)
                    if split_idx < line_len:
                        head_lines.append(line[:split_idx])
                        tail_lines.append(line[split_idx:])
                        tail_lines.extend(raw_lines[i+1:])
                        break
                    else:
                        tail_lines.extend(raw_lines[i:])
                        break
                else:
                    tail_lines.extend(raw_lines[i:])
                    break
        
        return "\n".join(head_lines), "\n".join(tail_lines)

    # Process items as a queue
    queue = flat_data.copy()
    
    while queue:
        item = queue.pop(0)
        
        measure_text = str(item.get('대책', ''))
        factor_text = str(item.get('위험요인', ''))
        
        lines_measure = count_view_lines(measure_text, 28)
        lines_factor = count_view_lines(factor_text, 20)
        row_height = max(1.2, lines_measure, lines_factor)
        
        if current_height + row_height <= limit:
            current_page.append(item)
            current_height += row_height
        else:
            # Overflow
            remaining_space = limit - current_height
            
            # If remaining space is reasonable (e.g. > 3 lines), try logic split
            if remaining_space >= 3.0:
                # Split Attempt
                head_meas, tail_meas = split_text_to_fit(measure_text, int(remaining_space), 28)
                head_fact, tail_fact = split_text_to_fit(factor_text, int(remaining_space), 20)
                
                if not head_meas and not head_fact:
                    # Split failed or empty, just page break
                    pages.append(current_page)
                    current_page = [item]
                    current_height = row_height
                    limit = PAGE_N_CAPACITY
                else:
                    # Create Head Item
                    item_head = item.copy()
                    item_head['대책'] = head_meas
                    item_head['위험요인'] = head_fact
                    
                    # Create Tail Item
                    item_tail = item.copy()
                    item_tail['대책'] = tail_meas if tail_meas else "(대책 내용 계속)"
                    # 유해위험요인이 짧아서 1페이지에 다 들어갔더라도, 2페이지에서 어떤 항목인지 알 수 있게 표시
                    item_tail['위험요인'] = tail_fact if tail_fact else f"{factor_text} (계속)"
                    item_tail['is_first'] = False # Tail is continuation
                    
                    current_page.append(item_head)
                    
                    # Page Break
                    pages.append(current_page)
                    current_page = []
                    current_height = 0
                    limit = PAGE_N_CAPACITY
                    
                    # Push Tail back to Front of Queue
                    queue.insert(0, item_tail)
            else:
                # Not enough space to split gracefully
                pages.append(current_page)
                current_page = [item]
                current_height = row_height
                limit = PAGE_N_CAPACITY
            
    if current_page:
        pages.append(current_page)
        
    # Build HTML string
    full_html = ""
    
    for p_idx, page_rows in enumerate(pages):
        is_first_page = (p_idx == 0)
        
        full_html += '<div class="a4-page">'
        
        if is_first_page:
            full_html += create_header_html(
                task_name, location, protectors, safety_equip, tools, materials,
                writer_name, action_taker, reviewer_name, checker_name, approver_name, today_str
            )
        else:
            full_html += f'<div style="text-align:right; font-size:10px; margin-bottom:5px; color:black;">공종별 위험성평가표 ({p_idx+1}/{len(pages)})</div>'

        full_html += '''
<table class="safety-table" style="width: 100%; table-layout: fixed;">
    <colgroup>
        <col style="width: 15%;">
        <col style="width: 25%;">
        <col style="width: 35%;">
        <col style="width: 5%;">
        <col style="width: 5%;">
        <col style="width: 5%;">
        <col style="width: 10%;">
    </colgroup>
    <thead>
        <tr>
            <th rowspan="2">작업단계 (STEP)</th>
            <th rowspan="2">유해위험요인</th>
            <th rowspan="2">위험 제거 및 감소 대책</th>
            <th colspan="3">위험성평가</th>
            <th rowspan="2">조치<br>확인</th>
        </tr>
        <tr>
            <th>빈도</th>
            <th>강도</th>
            <th>위험도</th>
        </tr>
    </thead>
    <tbody>
'''
        # Body Generation - With rowspan per page
        # Group rows by step_name within this page
        from collections import OrderedDict
        step_groups = OrderedDict()
        for item in page_rows:
            sn = item['step_name']
            if sn not in step_groups:
                step_groups[sn] = []
            step_groups[sn].append(item)
        
        for step_name, items in step_groups.items():
            row_count = len(items)
            first_row = True
            
            for item in items:
                factor = item["위험요인"].replace('\n', '<br>')
                measure = item["대책"].replace('\n', '<br>')
                
                # Grade Color
                grade_val = item['등급'].strip()
                grade_display = grade_val
                if "상" in grade_val:
                    grade_display = f'<span style="color:red; font-weight:bold;">{grade_val}</span>'
                elif "중" in grade_val:
                    grade_display = f'<span style="color:#d35400; font-weight:bold;">{grade_val}</span>'
                elif "하" in grade_val:
                    grade_display = f'<span style="color:green; font-weight:bold;">{grade_val}</span>'
                
                full_html += "<tr>"
                
                if first_row:
                    step_display = step_name
                    if not item['is_first']:
                        step_display += "<br>(계속)"
                    full_html += f'<td rowspan="{row_count}" style="background-color: #f9f9f9; font-weight:bold; vertical-align: middle;">{step_display}</td>'
                
                full_html += f'<td class="left-align">{factor}</td>'
                full_html += f'<td class="left-align" style="white-space: pre-wrap;">{measure}</td>'
                full_html += f'<td>{item["빈도"]}</td>'
                full_html += f'<td>{item["강도"]}</td>'
                full_html += f'<td>{item["위험성"]}<br>{grade_display}</td>'
                full_html += f'<td></td>'
                
                full_html += "</tr>"
                first_row = False
                
        full_html += "</tbody></table></div>"
        
        if not is_first_page:
            full_html += '<div class="page-break"></div>'

    # Store HTML in session state for printing
    st.session_state['print_html'] = full_html
    
    # Wrap in print-container for clean printing
    wrapped_html = f'<div class="print-container" id="printContent">{full_html}</div>'
    
    # Render HTML
    st.markdown(wrapped_html, unsafe_allow_html=True)
    
    # Print Button - Opens new window with only report content
    col_p1, col_p2 = st.columns([1, 4])
    with col_p1:
        # Use session state to track print requests
        if 'print_count' not in st.session_state:
            st.session_state.print_count = 0
            
        if st.button("🖨️ 인쇄 / PDF 저장", type="primary", key=f"print_btn_{st.session_state.print_count}"):
            st.session_state.print_count += 1
            
            # Clean up HTML - remove page-break divs
            clean_html = full_html.replace('<div class="page-break"></div>', '')
            
            # JavaScript to open new window and print
            js_code = f'''
            <script>
                var printWindow = window.open('', 'PrintWindow', 'width=1100,height=800');
                if (printWindow) {{
                    var htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>위험성평가표</title>
    <style>
        @page {{ size: A4 landscape; margin: 5mm; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Malgun Gothic', sans-serif; background: white; }}
        .a4-page {{ 
            width: 287mm; 
            padding: 5mm; 
            margin: 0;
            page-break-after: always;
            page-break-inside: avoid;
        }}
        .a4-page:last-child {{ page-break-after: auto; }}
        .page-break {{ display: none; }}
        .safety-table {{ 
            width: 100%; border-collapse: collapse; font-size: 10px; 
        }}
        .safety-table th, .safety-table td {{ 
            border: 1px solid #000; padding: 3px; text-align: center; 
            vertical-align: middle; 
        }}
        .safety-table th {{ background-color: #f0f0f0; font-weight: bold; }}
        .left-align {{ text-align: left !important; padding-left: 5px; }}
        .info-table {{ 
            width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 10px;
        }}
        .info-table td {{ border: 1px solid #000; padding: 2px 5px; }}
    </style>
</head>
<body>
{clean_html}
</body>
</html>`;
                    printWindow.document.open();
                    printWindow.document.write(htmlContent);
                    printWindow.document.close();
                    printWindow.focus();
                    setTimeout(function() {{
                        printWindow.print();
                    }}, 300);
                }} else {{
                    alert('팝업이 차단되었습니다. 팝업 차단을 해제해 주세요.');
                }}
            </script>
            '''
            st.components.v1.html(js_code, height=0, width=0)
            st.rerun()
    with col_p2:
        st.info("👆 버튼을 누르면 **새 창**이 열리고 인쇄 다이얼로그가 나타납니다. '레이아웃'을 **가로**로 설정하세요!")
