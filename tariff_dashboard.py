import streamlit as st
import requests
import urllib.parse
import datetime
import time
import pandas as pd
import threading
from bs4 import BeautifulSoup

# -------------------- CONFIGURATION -------------------- #
LANGUAGE_OPTIONS = ["zh", "en", "ja", "es"]
DEFAULT_CLIENTS = ["东京世纪", "伊藤忠商事", "商船三井", "丸红", "三菱HC", "路易达浮", "Tokyo Century", "Itochu", "Mitsui O.S.K.", "Marubeni", "Mitsubishi HC", "Louis Dreyfus"]
NEWS_API_KEY = "f3f6cd3bf7c44a9c92c433c6db0af15d"

if "history" not in st.session_state:
    st.session_state.history = []

# -------------------- SIDEBAR -------------------- #
st.sidebar.title("设置 Settings")
search_keywords = st.sidebar.text_input("关键词（多个语言，以空格分隔）", "2025 关税 贸易战 特朗普")
selected_languages = st.sidebar.multiselect("语言选择", LANGUAGE_OPTIONS, default=["zh", "en"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 客户列表")
if "clients" not in st.session_state:
    st.session_state.clients = DEFAULT_CLIENTS.copy()

new_client = st.sidebar.text_input("添加客户名称")
if st.sidebar.button("添加客户") and new_client:
    st.session_state.clients.append(new_client)
    st.sidebar.success(f"已添加客户：{new_client}")

remove_client = st.sidebar.selectbox("选择要删除的客户", ["无"] + st.session_state.clients)
if st.sidebar.button("删除客户") and remove_client != "无":
    st.session_state.clients.remove(remove_client)
    st.sidebar.warning(f"已删除客户：{remove_client}")

# -------------------- FUNCTION: Fetch News -------------------- #
def fetch_news(query, language, page_size=20):
    url = (
        f"https://newsapi.org/v2/everything?q={urllib.parse.quote(query)}"
        f"&language={language}&sortBy=publishedAt&pageSize={page_size}&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        return []

# -------------------- FUNCTION: Analyze Impact -------------------- #
def analyze_articles(articles, clients):
    results = []
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        content = (title or "") + " " + (description or "")
        url = article.get("url", "")
        published_at = article.get("publishedAt", "")
        matched_clients = [client for client in clients if client.lower() in content.lower()]

        for client in matched_clients:
            impact = "业务冲击" if "suspend" in content.lower() or "delay" in content.lower() else                      "盈利预警" if "profit" in content.lower() or "earnings" in content.lower() else                      "股价影响" if "stock" in content.lower() or "share price" in content.lower() else "未分类"

            results.append({
                "时间": published_at,
                "客户": client,
                "影响": impact,
                "标题": title,
                "链接": url
            })
    return results

# -------------------- FUNCTION: Scheduled Task -------------------- #
def scheduled_task():
    all_results = []
    st.write("🔍 正在抓取新闻...")
    for lang in selected_languages:
        for keyword in search_keywords.split():
            news = fetch_news(keyword, lang)
            st.write(f"📦 {lang} 语言关键词【{keyword}】共抓取 {len(news)} 条新闻")
            analysis = analyze_articles(news, st.session_state.clients)
            st.write(f"✅ 识别到 {len(analysis)} 条与客户相关的新闻")
            all_results.extend(analysis)

    if all_results:
        st.session_state.history.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": all_results
        })
    else:
        st.warning("❗没有识别出任何客户相关内容，建议检查关键词或客户名称是否能匹配新闻正文")


# -------------------- UI: Main Page -------------------- #
st.title("📊 关税新闻智能分析系统")

if st.button("立即抓取并分析"):
    with st.spinner("正在抓取和分析，请稍候..."):
        scheduled_task()
    st.success("本次分析已完成 ✅")

st.markdown("---")
st.subheader("📋 最新分析结果")
if st.session_state.history:
    latest = st.session_state.history[-1]
    df = pd.DataFrame(latest["results"])
    st.markdown(f"🕒 抓取时间：{latest['time']}")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("未识别到相关客户影响")
else:
    st.info("尚未进行分析，请点击上方按钮开始")

st.markdown("---")
st.subheader("📜 历史分析记录")
for record in reversed(st.session_state.history[:-1]):
    st.markdown(f"#### 🕒 {record['time']}")
    if record['results']:
        st.dataframe(pd.DataFrame(record['results']))
    else:
        st.markdown("无相关影响")
