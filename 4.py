import streamlit as st
import requests
import time
import pandas as pd

# ---------------------- 模型配置（直填密钥） ----------------------
MODEL_CONFIG = {
    "DeepSeek": {
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "api_key": "sk-e936f8e6da874661a93f3eb4251e5aef",
        "model_name": "deepseek-chat"
    },
    "智谱GLM4": {
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key": "此处替换密钥",
        "model_name": "glm-4"
    },
    "通义千问": {
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "api_key": "此处替换密钥",
        
        "model_name": "qwen-turbo"
    }
}

# ---------------------- 统一调用函数（优化版） ----------------------
def call_ai_model(model_name, prompt):
    config = MODEL_CONFIG[model_name]
    # 清除密钥首尾空格、换行等不可见字符
    real_api_key = config["api_key"].strip()

    headers = {
        "Authorization": f"Bearer {real_api_key}",
        "Content-Type": "application/json"
    }
    request_data = {
        "model": config["model_name"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature":
    }

    start_time = time.time()
    try:
        # 设置30秒超时，避免网络卡死
        response = requests.post(
            url=config["api_url"],
            headers=headers,
            json=request_data,
            timeout=30
        )
        # 打印接口原始返回内容，方便排查401错误
        print(f"\n===== {model_name} 接口返回信息 =====")
        print(response.text)
        # 抛出HTTP错误（401/404/500等）
        response.raise_for_status()

        resp_json = response.json()
        result_text = resp_json["choices"][0]["message"]["content"]
        end_time = time.time()

        cost_time = round(end_time - start_time, 2)
        char_count = len(result_text)
        speed = round(char_count / cost_time, 2) if cost_time > 0 else 0

        metrics = {
            "模型名称": model_name,
            "响应时间(秒)": cost_time,
            "输出长度(字符)": char_count,
            "输出速度(字符/秒)": speed,
            "状态": "成功"
        }
        return result_text, metrics

    except Exception as e:
        end_time = time.time()
        cost_time = round(end_time - start_time, 2)
        metrics = {
            "模型名称": model_name,
            "响应时间(秒)": cost_time,
            "输出长度(字符)": 0,
            "输出速度(字符/秒)": 0,
            "状态": f"失败: {str(e)}"
        }
        return None, metrics

# ---------------------- Streamlit 页面逻辑 ----------------------
st.title("多AI模型对比工具（优化调试版）")

# 多选模型下拉框
selected_models = st.multiselect(
    "请选择要对比的AI模型：",
    options=list(MODEL_CONFIG.keys()),
    default=list(MODEL_CONFIG.keys())
)

# 用户输入提示词
user_prompt = st.text_area("请输入你的问题：", height=150)

# 点击按钮执行对比
if st.button("开始对比") and user_prompt and selected_models:
    metric_list = []

    with st.spinner("正在调用所有选中模型，请稍候..."):
        for model in selected_models:
            st.subheader(f"【{model}】回答结果")
            content, metric = call_ai_model(model, user_prompt)
            metric_list.append(metric)

            if content:
                st.write(content)
            else:
                st.error(metric["状态"])

    # 指标表格展示
    st.divider()
    st.subheader("📊 模型性能对比数据")
    df = pd.DataFrame(metric_list)
    st.dataframe(df, use_container_width=True)

    # 可视化图表
    st.subheader("⏱ 各模型响应时间对比")
    st.bar_chart(df.set_index("模型名称")["响应时间(秒)"])

    st.subheader("⚡ 各模型输出速度对比")
    st.bar_chart(df.set_index("模型名称")["输出速度(字符/秒)"])