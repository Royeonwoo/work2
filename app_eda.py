import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, Page_Login=None, Page_Register=None, Page_FindPW=None):
        st.title("지역별 인구 분석 웹앱")
        st.markdown("""
        이 웹 애플리케이션은 population_trends.csv 데이터를 기반으로 지역별 인구 변화를 시각적으로 분석합니다.

        - **파일 업로드:** population_trends.csv 파일을 업로드하세요.
        - **탭 기반 분석:** 기초 통계, 연도별 추이, 지역별 분석 등 다양한 시각화 탭을 제공합니다.
        - **활용 기술:** Streamlit, pandas, matplotlib, seaborn, ChatGPT
        - **배포:** GitHub와 Streamlit Cloud를 통해 배포 예정
        """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 지역별 인구 분석 EDA")
        uploaded_file = st.file_uploader("📂 population_trends.csv 파일 업로드", type="csv")

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            # 전처리 - '세종' 지역 결측치 '-' → 0 치환
            df.replace("-", 0, inplace=True)
            if '지역' in df.columns:
                df[df['지역'].str.contains("세종")] = df[df['지역'].str.contains("세종")].replace("-", 0)

            # 숫자형 변환
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            df['지역영문'] = df['지역'].map(region_map)

            tabs = st.tabs([
                "기초 통계", 
                "연도별 추이", 
                "지역별 분석", 
                "변화량 분석", 
                "시각화"
            ])

            # 탭 1: 기초 통계
            with tabs[0]:
                st.subheader("📄 기초 통계")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text("데이터 구조:")
                st.code(buffer.getvalue())
                st.markdown("요약 통계:")
                st.dataframe(df.describe())

            # 탭 2: 연도별 추이
            with tabs[1]:
                st.subheader("📈 Yearly Population Trend")
                national = df[df['지역'] == '전국']
                yearly = national.groupby('연도')['인구'].sum().reset_index()

                national_recent = national[national['연도'] >= national['연도'].max() - 2]
                birth_mean = national_recent['출생아수(명)'].mean()
                death_mean = national_recent['사망자수(명)'].mean()
                net_change = birth_mean - death_mean

                last_year = yearly['연도'].max()
                last_pop = yearly[yearly['연도'] == last_year]['인구'].values[0]
                predicted_year = 2035
                predicted_pop = last_pop + (predicted_year - last_year) * net_change

                fig, ax = plt.subplots(figsize=(8, 5))
                sns.lineplot(data=yearly, x='연도', y='인구', marker='o', ax=ax)
                ax.axvline(predicted_year, color='red', linestyle='--', label=f"Predicted {predicted_year}")
                ax.scatter(predicted_year, predicted_pop, color='red')
                ax.text(predicted_year, predicted_pop, f'{int(predicted_pop):,}', color='red')
                ax.set_title("Yearly Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                st.pyplot(fig)

            # 탭 3: 지역별 분석
            with tabs[2]:
                st.subheader("📊 Regional Population Change (Last 5 Years)")
                latest_year = df['연도'].max()
                five_years_ago = latest_year - 5
                region_df = df[(df['연도'].isin([latest_year, five_years_ago])) & (df['지역'] != '전국')]

                pivot_df = region_df.pivot(index='지역영문', columns='연도', values='인구').dropna()
                pivot_df['change'] = (pivot_df[latest_year] - pivot_df[five_years_ago]) / 1000
                pivot_df['rate'] = ((pivot_df[latest_year] - pivot_df[five_years_ago]) / pivot_df[five_years_ago]) * 100
                sorted_df = pivot_df.sort_values(by='change', ascending=False)

                fig1, ax1 = plt.subplots(figsize=(10, 6))
                sns.barplot(x='change', y=sorted_df.index, data=sorted_df, ax=ax1)
                for i, value in enumerate(sorted_df['change']):
                    ax1.text(value, i, f'{value:.1f}', va='center')
                ax1.set_title("5-Year Population Change by Region")
                ax1.set_xlabel("Change (thousands)")
                ax1.set_ylabel("Region")
                st.pyplot(fig1)

                fig2, ax2 = plt.subplots(figsize=(10, 6))
                sns.barplot(x='rate', y=sorted_df.index, data=sorted_df, ax=ax2)
                for i, value in enumerate(sorted_df['rate']):
                    ax2.text(value, i, f'{value:.1f}%', va='center')
                ax2.set_title("5-Year Population Change Rate by Region")
                ax2.set_xlabel("Change Rate (%)")
                ax2.set_ylabel("Region")
                st.pyplot(fig2)

            # 탭 4: 변화량 분석
            with tabs[3]:
                st.subheader("📌 Top 100 Regional Annual Population Changes")
                df_non_national = df[df['지역'] != '전국']
                df_non_national = df_non_national.sort_values(by=['지역', '연도'])
                df_non_national['증감'] = df_non_national.groupby('지역')['인구'].diff()

                top_changes = df_non_national.sort_values(by='증감', ascending=False).dropna().head(100).copy()
                top_changes['연도'] = top_changes['연도'].astype(int)
                top_changes['인구'] = top_changes['인구'].apply(lambda x: f"{int(x):,}")
                top_changes['증감'] = top_changes['증감'].apply(lambda x: f"{int(x):,}")

                def highlight(val):
                    try:
                        v = int(val.replace(',', ''))
                        if v > 0:
                            return 'background-color: #cce5ff'  # 파랑 계열
                        elif v < 0:
                            return 'background-color: #f8d7da'  # 빨강 계열
                    except:
                        return ''

                st.dataframe(top_changes.style.applymap(highlight, subset=['증감']))

            # 탭 5: 시각화
            with tabs[4]:
                st.subheader("📊 Stacked Area Chart by Region")
                df_area = df[df['지역'] != '전국']
                pivot_area = df_area.pivot_table(index='연도', columns='지역영문', values='인구', aggfunc='sum').fillna(0)

                fig_area, ax_area = plt.subplots(figsize=(12, 6))
                pivot_area.plot.area(ax=ax_area, cmap='tab20')
                ax_area.set_title("Stacked Area Chart by Region")
                ax_area.set_xlabel("Year")
                ax_area.set_ylabel("Population")
                ax_area.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
                st.pyplot(fig_area)

        else:
            st.info("먼저 population_trends.csv 파일을 업로드해주세요.")


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()