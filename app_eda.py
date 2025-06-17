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

            # 🔧 전처리 시작
            df.replace("-", 0, inplace=True)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju', '전국': 'National'
            }
            df['지역영문'] = df['지역'].map(region_map).fillna(df['지역'])

            tabs = st.tabs([
                "기초 통계", 
                "연도별 추이", 
                "지역별 분석", 
                "변화량 분석", 
                "시각화"
            ])

            # 탭 0: 기초 통계
            with tabs[0]:
                st.subheader("📄 기초 통계")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text("데이터 구조:")
                st.code(buffer.getvalue())
                st.markdown("요약 통계:")
                st.dataframe(df.describe())

           # 탭 1: 연도별 추이
            with tabs[1]:
                st.subheader("📈 Yearly Population Trend with Prediction")
                df_national = df[df['지역'] == '전국']
                df_national = df_national[['연도', '인구', '출생아수(명)', '사망자수(명)']].sort_values('연도')
                df_national[['인구', '출생아수(명)', '사망자수(명)']] = df_national[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric, errors='coerce')

                recent = df_national[df_national['연도'] >= df_national['연도'].max() - 2]
                net_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
                last_year = df_national['연도'].max()
                last_pop = df_national[df_national['연도'] == last_year]['인구'].values[0]
                predicted_year = 2035
                predicted_pop = last_pop + (predicted_year - last_year) * net_change

                df_pred = df_national[['연도', '인구']].copy()
                df_pred = pd.concat([df_pred, pd.DataFrame({'연도': [predicted_year], '인구': [predicted_pop]})], ignore_index=True)

                fig, ax = plt.subplots(figsize=(10, 5))
                sns.lineplot(data=df_pred, x='연도', y='인구', marker='o', ax=ax)
                ax.axvline(predicted_year, linestyle='--', color='red', label=f"Prediction {predicted_year}")
                ax.annotate(f'{int(predicted_pop):,}', (predicted_year, predicted_pop), color='red', xytext=(5, 10), textcoords='offset points')
                ax.set_title("Yearly Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                st.pyplot(fig)

                st.markdown("""
                ### 해설

                이 그래프는 전국의 총인구 변화 추이를 시각화한 것입니다. 
                실선은 실제 관측된 인구 수를, 점선은 현재 추세를 바탕으로 예측한 미래 인구(2035년)를 나타냅니다.

                - 🔴 빨간 점선은 예측 연도(2035년)를 의미하며, 최근 2년간 평균 순인구 변화량(출생 - 사망)을 기준으로 예측하였습니다.
                - 📉 전반적인 감소 추세 또는 정체 여부를 시각적으로 파악할 수 있습니다.
                - 🧮 예측된 인구: {predicted_year}년에는 약 {int(predicted_pop):,}명으로 예상됩니다.
                """)
                
            # 탭 2: 지역별 분석
            with tabs[2]:
                st.subheader("Regional Population Change (Last 5 Years)")
                df_filtered = df[df['지역'] != '전국']
                latest_year = df_filtered['연도'].max()
                base_year = latest_year - 5
                df_latest = df_filtered[df_filtered['연도'] == latest_year]
                df_base = df_filtered[df_filtered['연도'] == base_year]
                df_delta = df_latest.set_index('지역영문')['인구'] - df_base.set_index('지역영문')['인구']
                df_pct = ((df_latest.set_index('지역영문')['인구'] - df_base.set_index('지역영문')['인구']) / df_base.set_index('지역영문')['인구']) * 100

                fig1, ax1 = plt.subplots(figsize=(10, 6))
                delta_sorted = df_delta.sort_values(ascending=False) / 1000
                sns.barplot(x=delta_sorted.values, y=delta_sorted.index, ax=ax1)
                ax1.set_title("Population Change (Last 5 Years)")
                ax1.set_xlabel("Change (thousands)")
                ax1.set_ylabel("Region")
                for i, v in enumerate(delta_sorted.values):
                    ax1.text(v, i, f"{v:.1f}", va='center')
                st.pyplot(fig1)

                fig2, ax2 = plt.subplots(figsize=(10, 6))
                pct_sorted = df_pct.sort_values(ascending=False)
                sns.barplot(x=pct_sorted.values, y=pct_sorted.index, ax=ax2)
                ax2.set_title("Rate of Change (%)")
                ax2.set_xlabel("Percent Change")
                ax2.set_ylabel("Region")
                for i, v in enumerate(pct_sorted.values):
                    ax2.text(v, i, f"{v:.1f}%", va='center')
                st.pyplot(fig2)

                st.markdown("""
                ### 해설

                첫 번째 그래프는 최근 5년 동안 각 지역의 인구 변화량을 천 명 단위로 나타냅니다. 오른쪽으로 길수록 인구가 많이 증가했음을, 왼쪽이나 짧을수록 증가가 적거나 감소했음을 나타냅니다.

                두 번째 그래프는 변화율을 보여주며, 인구 규모와 관계없이 각 지역의 상대적 성장률을 비교할 수 있게 합니다.
                """)

            # 탭 3: 변화량 분석
            with tabs[3]:
                st.subheader("📈 Top 100 Population Changes (Diff)")
                df_diff = df[df['지역'] != '전국'].copy()
                df_diff.sort_values(by=['지역영문', '연도'], inplace=True)
                df_diff['증감'] = df_diff.groupby('지역영문')['인구'].diff()

                top100 = df_diff[['지역영문', '연도', '증감']].dropna().copy()
                top100['증감'] = top100['증감'].astype(int)
                top100 = top100.reindex(top100['증감'].abs().sort_values(ascending=False).index).head(100)

                def colorbar(val):
                    if val > 0:
                        ratio = min(1.0, val / top100['증감'].max())
                        return f'background-color: rgba(0, 100, 255, {ratio})'
                    elif val < 0:
                        ratio = min(1.0, abs(val) / abs(top100['증감'].min()))
                        return f'background-color: rgba(255, 80, 80, {ratio})'
                    return ''

                styled = top100.style \
                    .format({'증감': '{:,}'}) \
                    .applymap(colorbar, subset=['증감']) \
                    .set_properties(**{'text-align': 'center'}) \
                    .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])

                st.markdown("### 🔍 Top 100 Absolute Population Changes (Positive & Negative Combined)")
                st.write(styled)

                st.markdown("""
                ### 해설

                이 표는 전국을 제외한 각 지역의 연도별 인구 변화량 중 가장 큰 100건을 나열한 것입니다. 
                - 파란색 셀은 인구 증가를, 붉은색 셀은 인구 감소를 나타냅니다.
                - 색이 진할수록 변화량이 크다는 의미입니다.
                - 증감 수치는 천 단위 콤마로 표기되어 가독성을 높였습니다.
                """)

            # 탭 5: 시각화
            with tabs[4]:
                st.subheader("🗺️ Stacked Area Chart by Region")
                pivot_area = df[df['지역'] != '전국'].pivot(index='연도', columns='지역영문', values='인구').fillna(0)
                pivot_area = pivot_area / 1000
                fig, ax = plt.subplots(figsize=(12, 6))
                pivot_area.plot.area(ax=ax, colormap='tab20')
                ax.set_title("Population Trends by Region (in Thousands)")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population (Thousands)")
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                st.pyplot(fig)

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