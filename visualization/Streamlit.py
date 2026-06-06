
import time
import random
# Import your sensor libraries here (e.g., import adafruit_bme280, board, busio)

def visualization(st,current_time,t_val,h_val,p_val):
   

    st.title("リアルタイム気象観測データ")
    st.markdown("Raspberry Piのセンサーからデータをリアルタイムに取得・描画しています。")
    st.write("---")

    # --- データ履歴の保持（セッション状態の初期化） ---
    # Streamlitは再実行されると変数がリセットされるため、st.session_stateを使ってデータを保持します
        # --- センサーデータの取得処理 ---
    # 実際のセンサーを初期化して読み込む場合はここを有効にしてください
    # @st.cache_resource # 毎回初期化されないようにキャッシュ
    # def get_sensor():
    #     i2c = busio.I2C(board.SCL, board.SDA)
    #     return adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
    # sensor = get_sensor()

    # データ取得（ダミーデータ。実機では sensor.temperature などに置き換え）
    t_val = round(random.uniform(20.0, 26.0), 2)
    h_val = round(random.uniform(45.0, 65.0), 2)
    p_val = round(random.uniform(1008.0, 1013.0), 1)
    current_time = time.strftime("%H:%M:%S")

    # 履歴に追加（最大30件保持）
    st.session_state.history.append({"Time": current_time, "Pressure (hPa)": p_val})
    if len(st.session_state.history) > 30:
        st.session_state.history.pop(0)

    # --- UIの描画 ---
    # メトリクス表示（3列）
    col1, col2, col3 = st.columns(3)
    col1.metric(label="気温 (Temperature)", value=f"{t_val} °C")
    col2.metric(label="湿度 (Humidity)", value=f"{h_val} %")
    col3.metric(label="気圧 (Pressure)", value=f"{p_val} hPa")

    st.write("---")

    # グラフ表示
    st.subheader("気圧の変動傾向（直近30データ）")
    st.line_chart(
        data=st.session_state.history, 
        x="Time", 
        y="Pressure (hPa)", 
        height=300
    )

    # --- 重要：リアルタイム更新のコントロール ---
    # 1秒待機したあと、スクリプトを安全に再実行してデータを更新する
    time.sleep(1)
    return st
