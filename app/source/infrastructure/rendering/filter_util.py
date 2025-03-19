from datetime import datetime, date
import re
import locale
from markupsafe import Markup

# 한국어 로케일 설정 (시스템에 따라 다를 수 있음)
try:
    locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Korean_Korea.949')
    except locale.Error:
        pass  # 실패해도 계속 진행

def format_date(value, format='%Y-%m-%d'):
    """날짜를 지정된 형식으로 포맷팅합니다."""
    if value is None:
        return ""
        
    # 이미 date/datetime 객체인 경우
    if isinstance(value, (datetime, date)):
        return value.strftime(format)
        
    # 문자열인 경우 파싱 시도
    if isinstance(value, str):
        # 빈 문자열 체크
        if not value.strip():
            return ""
            
        # YYYY-MM-DD 형식 시도
        if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
                return dt.strftime(format)
            except ValueError:
                pass
                
        # YYYY.MM.DD 형식 시도
        if re.match(r'^\d{4}\.\d{2}\.\d{2}$', value):
            try:
                dt = datetime.strptime(value, '%Y.%m.%d')
                return dt.strftime(format)
            except ValueError:
                pass
                
        # ISO 형식 시도 (YYYY-MM-DDTHH:MM:SS)
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime(format)
        except ValueError:
            pass
    
    # 파싱 실패 시 원본 반환
    return str(value)

def format_korean_date(value):
    """날짜를 한국식으로 포맷팅 (YYYY년 MM월 DD일)"""
    formatted = format_date(value, '%Y년 %m월 %d일')
    return formatted

def format_date_range(start_date, end_date, format='%Y-%m-%d'):
    """두 날짜로 기간을 포맷팅"""
    start_str = format_date(start_date, format)
    end_str = format_date(end_date, format)
    
    if start_str and end_str:
        return f"{start_str} ~ {end_str}"
    elif start_str:
        return f"{start_str} ~"
    elif end_str:
        return f"~ {end_str}"
    else:
        return ""

def format_number(value, decimals=0, thousands_sep=','):
    """숫자를 천 단위 구분자가 있는 형식으로 포맷팅"""
    if value is None:
        return ""
        
    try:
        # 문자열을 숫자로 변환 시도
        if isinstance(value, str):
            value = value.replace(',', '')
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
                
        # 소수점 처리
        if decimals > 0:
            format_str = f"{{:,.{decimals}f}}"
            return format_str.format(float(value))
        else:
            # 정수 처리
            return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)

def number_to_korean(number):
    """숫자를 한글로 변환 (1234 -> 일천이백삼십사)"""
    
    if number == 0:
        return "영"
        
    # 1-9 한글 표현
    korean_number = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    # 자릿수 단위
    korean_unit = ["", "십", "백", "천"]
    # 만 단위
    korean_unit_man = ["", "만", "억", "조", "경"]
    
    result = ""
    num_str = str(number)
    num_len = len(num_str)
    
    # 4자리씩 끊어서 처리
    section_count = (num_len - 1) // 4 + 1
    
    for section in range(section_count):
        start_idx = num_len - (section + 1) * 4
        end_idx = num_len - section * 4
        if start_idx < 0:
            start_idx = 0
            
        current_section = num_str[start_idx:end_idx]
        current_section_len = len(current_section)
        
        section_result = ""
        has_value = False
        
        for i in range(current_section_len):
            digit = int(current_section[i])
            if digit == 0:
                continue
                
            has_value = True
            # 일십 -> 십, 일백 -> 백 처리
            if digit == 1 and i < current_section_len - 1:
                section_result += korean_unit[current_section_len - i - 1]
            else:
                section_result += korean_number[digit] + korean_unit[current_section_len - i - 1]
        
        if has_value:
            result = section_result + korean_unit_man[section] + result
            
    return result if result else "영"

def format_korean_currency(value):
    """숫자를 한글 금액으로 변환 (원 단위 포함)"""
    if value is None or value == "":
        return ""
        
    try:
        # 문자열이나 실수를 정수로 변환
        if isinstance(value, str):
            value = value.replace(',', '')
        number = int(float(value))
        
        if number == 0:
            return "영원"
            
        # 한글 변환
        korean = number_to_korean(abs(number))
        
        # 음수 처리
        if number < 0:
            korean = "마이너스 " + korean
            
        return korean + "원"
        
    except (ValueError, TypeError):
        return str(value)

def format_korean_currency_with_num(value):
    """숫자를 한글 금액으로 변환하고 숫자도 함께 표시"""
    if value is None or value == "":
        return ""
        
    try:
        # 숫자 포맷팅
        num_str = format_number(value)
        # 한글 금액 변환
        korean_str = format_korean_currency(value)
        
        return f"{korean_str} ({num_str}원)"
        
    except (ValueError, TypeError):
        return str(value)

def format_currency_aligned(value, show_symbol=True):
    """통화 금액을 정렬된 형식으로 반환"""
    if value is None or value == "":
        return ""
        
    try:
        # 숫자 포맷팅
        number = format_number(value)
        
        if show_symbol:
            # Markup으로 HTML 반환
            return Markup(
                '<span class="currency-container">'
                '<span class="currency-symbol">₩</span>'
                f'<span class="currency-amount">{number}</span>'
                '</span>'
            )
        else:
            return Markup(f'<span class="currency-amount">{number}</span>')
            
    except (ValueError, TypeError):
        return str(value)

def format_number_aligned(value):
    """숫자를 우측 정렬된 형식으로 반환"""
    if value is None or value == "":
        return ""
        
    try:
        number = format_number(value)
        return Markup(f'<span class="number-aligned">{number}</span>')
    except (ValueError, TypeError):
        return str(value)


    
