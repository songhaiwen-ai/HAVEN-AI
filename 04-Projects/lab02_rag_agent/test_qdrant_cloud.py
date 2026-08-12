"""
test_qdrant_cloud.py - 直连测试用户 Qdrant Cloud 真实线上集群脚本
"""

import sys
from haven_research.storage import VectorStoreFactory
from haven_research.config import settings

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def test_qdrant_connection():
    print(f"=== 🚀 正在测试直连 Qdrant Cloud 真实云端集群 ===")
    print(f"集群 URL: {settings.qdrant_url}")
    print(f"集合名称: {settings.default_collection_name}\n")

    try:
        store = VectorStoreFactory.get_vector_store("qdrant")
        print("✅ 第一步: 成功建立 TLS/HTTPS 连接到 Qdrant Cloud 云端数据库！")
        
        # 写入测试
        print("\n正在测试向 Qdrant 云端写入测试文本向量...")
        ids = store.add_texts(
            texts=["这是写入 Qdrant Cloud 线上集群的测试文本"],
            metadatas=[{"source": "test.md", "page": 1}]
        )
        print(f"✅ 第二步: 成功写入 1 条数据！记录 ID: {ids}")

        # 检索测试
        print("\n正在测试向 Qdrant 云端执行向量相似度检索...")
        results = store.similarity_search("测试文本", k=1)
        print(f"✅ 第三步: 检索成功！匹配内容: '{results[0].content}' (得分: {results[0].score})")

        print("\n🎉【结论】: 您的 Qdrant Cloud 云端向量数据库已 100% 联通成功！")

    except Exception as e:
        print(f"\n❌ 【连接失败】: {e}")
        print("📌 排查提示: 请检查本地科学上网/梯子软件的系统代理/全局代理状态。")


if __name__ == "__main__":
    test_qdrant_connection()
