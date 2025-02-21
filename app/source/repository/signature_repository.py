from db import get_connection

@staticmethod
def get_file_path_by_user_id(user_id):
    """사용자 ID로 서명 이미지 파일 경로 조회"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT signature_path FROM employees WHERE id=%s;", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0]
        else:
            return None
    except Exception as e:
        print("데이터 조회 오류:", e)
        return None