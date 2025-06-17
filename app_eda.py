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
                st.write(f"총 행 개수: {len(df):,}")
                st.write(f"중복 행 개수: {df.duplicated().sum():,}")
                st.text("데이터 구조:")
                st.code(buffer.getvalue())
                st.markdown("요약 통계:")
                st.dataframe(df.describe())

                st.markdown("""
                ### 해설
                - 이 탭에서는 전체 데이터의 구조, 결측치, 중복 여부 및 요약 통계를 확인할 수 있습니다.
                - 각 열의 데이터 타입, 결측치 여부, 기본적인 기술통계를 파악하여 전처리 필요성을 검토할 수 있습니다.
                """)

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

                st.markdown(f"""
                ### 해설
                - 전국 인구의 연도별 추이를 시각화한 그래프입니다.
                - {predicted_year}년에는 약 {int(predicted_pop):,}명으로 예측되며, 최근 2년간의 순변화량을 기반으로 선형 예측을 수행했습니다.
                - 전국 인구는 특정 시점 이후 감소세에 접어든 것으로 보이며, 인구 감소 문제의 심각성을 파악할 수 있습니다.
                """)

            # 탭 2: 지역별 분석
            with tabs[2]:
                st.subheader("📌 지역별 인구 변화 (최근 5년)")
                df_filtered = df[df['지역'] != '전국']
                latest_year = df_filtered['연도'].max()
                base_year = latest_year - 5
                df_latest = df_filtered[df_filtered['연도'] == latest_year]
                df_base = df_filtered[df_filtered['연도'] == base_year]
                df_delta = df_latest.set_index('지역영문')['인구'] - df_base.set_index('지역영문')['인구']
                df_pct = ((df_latest.set_index('지역영문')['인구'] - df_base.set_index('지역영문')['인구']) / df_base.set_index('지역영문')['인구']) * 100

                fig1, ax1 = plt.subplots(figsize=(10, 6))
                delta_sorted = df_delta.sort_values(ascending=False) / 1000
                sns.barplot(x=delta_sorted.values, y=delta_sorted.index, ax=ax1, palette='Blues_r')
                ax1.set_title("Population Change (Last 5 Years)")
                ax1.set_xlabel("Change (thousands)")
                ax1.set_ylabel("Region")
                for i, v in enumerate(delta_sorted.values):
                    ax1.text(v, i, f"{v:.1f}", va='center')
                st.pyplot(fig1)

                fig2, ax2 = plt.subplots(figsize=(10, 6))
                pct_sorted = df_pct.sort_values(ascending=False)
                sns.barplot(x=pct_sorted.values, y=pct_sorted.index, ax=ax2, palette='coolwarm')
                ax2.set_title("Rate of Change (%)")
                ax2.set_xlabel("Percent Change")
                ax2.set_ylabel("Region")
                for i, v in enumerate(pct_sorted.values):
                    ax2.text(v, i, f"{v:.1f}%", va='center')
                st.pyplot(fig2)

                top_region = delta_sorted.idxmax()
                top_rate = pct_sorted.idxmax()

                st.markdown(f"""
                ### 해설
                - 최근 5년간 인구가 가장 많이 증가한 지역은 **{top_region}**이며,
                  비율상 가장 큰 증가를 보인 지역은 **{top_rate}**입니다.
                - 첫 번째 그래프는 절대 인구 증감량을, 두 번째 그래프는 비율 기준 증감을 보여줍니다.
                - 수도권 일부 지역은 증가세를, 지방 중 일부는 뚜렷한 감소세를 보입니다.
                """)

            # 탭 3: 변화량 분석
            with tabs[3]:
                st.subheader("📌 연도별 인구 증감 Top 100")
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
                - 연도별 인구 증감이 큰 사례를 추출한 표로, 특정 연도의 급격한 변화 현상을 분석할 수 있습니다.
                - 파란 배경은 증가, 빨간 배경은 감소를 의미합니다.
                - 강원, 경북, 전남 지역에서 대규모 감소가 다수 포착되었으며, 수도권 일부는 반대로 대규모 유입을 보였습니다.
                """)

            # 탭 4: 시각화
            with tabs[4]:
                st.subheader("📊 누적 영역 시각화")
                df_filtered = df[df['지역'] != '전국']
                df_pivot = df_filtered.pivot_table(index='연도', columns='지역영문', values='인구', aggfunc='sum')
                df_pivot = df_pivot.fillna(0)

                fig, ax = plt.subplots(figsize=(12, 6))
                df_pivot.div(1000).plot.area(ax=ax)
                ax.set_title("Population Trend by Region (Stacked Area, in Thousands)")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population (thousands)")
                ax.legend(title="Region", loc='center left', bbox_to_anchor=(1.0, 0.5))  # 범례 오른쪽 외부로 이동
                st.pyplot(fig)

                st.markdown("""
                ### 해설
                - 이 그래프는 전국을 제외한 지역들의 인구를 연도별로 누적하여 표현합니다.
                - 면적이 넓을수록 인구 규모가 크며, 지역 간 상대적 비중 변화를 시각적으로 비교할 수 있습니다.
                - 수도권 지역의 누적 면적은 시간이 지남에 따라 꾸준히 확대되는 경향을 보입니다.
                """)

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