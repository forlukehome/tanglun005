import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple
import json
import math
from scipy import stats as scipy_stats

# ===========================
# 页面配置
# ===========================
st.set_page_config(
    page_title="库存管理互动游戏",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
    }
    .step-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .action-box {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    .success-message {
        background: #d4edda;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: #155724;
    }
    .error-message {
        background: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: #721c24;
    }
    .info-card {
        background: white;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    .quiz-box {
        background: #e7f3ff;
        border: 2px solid #0066cc;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .highlight-box {
        background: #fffbf0;
        border: 2px dashed #ff9800;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
    }
    .formula-box {
        background: #f0f8ff;
        border: 2px solid #4169e1;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)


# ===========================
# 数据类
# ===========================

@dataclass
class SimpleProduct:
    """简化的商品类"""
    id: str
    name: str
    icon: str
    price: float
    cost: float
    current_stock: int
    daily_demand: int
    lead_time: int
    order_interval: int  # 下单间隔天数

    def get_margin(self) -> float:
        """计算毛利率"""
        return (self.price - self.cost) / self.price * 100


# ===========================
# 游戏核心类
# ===========================

class InteractiveInventoryGame:
    """互动式库存管理游戏"""

    def __init__(self):
        self.initialize_game()

    def initialize_game(self):
        """初始化游戏"""
        if 'game_initialized' not in st.session_state:
            # 初始化游戏状态
            st.session_state.current_step = 0
            st.session_state.day = 1
            st.session_state.cash = 10000
            st.session_state.total_revenue = 0
            st.session_state.total_profit = 0
            st.session_state.products = self.create_products()
            st.session_state.sales_history = self.create_sales_history()
            st.session_state.pending_orders = {}
            st.session_state.daily_reports = []

            # 玩家输入存储
            st.session_state.player_predictions = {}
            st.session_state.player_orders = {}
            st.session_state.player_service_levels = {}
            st.session_state.player_order_intervals = {}

            # 添加一个标记哪些商品需要订货的字典
            st.session_state.products_need_order = {}

            # 系统建议（用于对比）
            st.session_state.system_predictions = {}
            st.session_state.system_orders = {}

            # 步骤完成标记
            st.session_state.step_completed = [False] * 10

            # 添加步骤6和步骤7的完成标记
            st.session_state.order_submitted = False
            st.session_state.simulation_run = False

            # 分数系统
            st.session_state.score = 0
            st.session_state.score_details = []

            st.session_state.game_initialized = True

    def create_products(self) -> Dict[str, SimpleProduct]:
        """创建3个简单商品"""
        return {
            'WATER': SimpleProduct(
                id='WATER',
                name='矿泉水',
                icon='💧',
                price=3.0,
                cost=1.0,
                current_stock=120,  # 修改为120件
                daily_demand=30,
                lead_time=3,
                order_interval=3
            ),
            'BREAD': SimpleProduct(
                id='BREAD',
                name='面包',
                icon='🍞',
                price=8.0,
                cost=4.0,
                current_stock=60,  # 保持60件
                daily_demand=20,
                lead_time=5,
                order_interval=5
            ),
            'MILK': SimpleProduct(
                id='MILK',
                name='牛奶',
                icon='🥛',
                price=12.0,
                cost=7.0,
                current_stock=50,  # 保持50件
                daily_demand=15,
                lead_time=2,
                order_interval=5
            )
        }

    def create_sales_history(self) -> Dict[str, List[int]]:
        """创建过去7天的销售历史"""
        return {
            'WATER': [28, 32, 30, 35, 29, 31, 33],  # 相对稳定
            'BREAD': [12, 28, 15, 35, 10, 30, 25],  # 波动很大，变异系数高
            'MILK': [14, 16, 15, 13, 17, 15, 16]  # 很稳定
        }

    def calculate_demand_stats(self, product_id: str) -> dict:
        """计算需求统计数据"""
        history = st.session_state.sales_history[product_id]
        return {
            'mean': np.mean(history),
            'std': np.std(history),
            'cv': np.std(history) / np.mean(history) if np.mean(history) > 0 else 0
        }

    def calculate_safety_stock(self, product_id: str, service_level: float) -> float:
        """计算安全库存
        安全库存 = 服务水平 × 需求标准差 × √采购提前期
        """
        product = st.session_state.products[product_id]
        demand_stats = self.calculate_demand_stats(product_id)

        # 根据服务水平获取z值
        z_score = scipy_stats.norm.ppf(service_level)

        # 计算安全库存
        safety_stock = z_score * demand_stats['std'] * math.sqrt(product.lead_time)

        return safety_stock

    def calculate_reorder_point(self, product_id: str, safety_stock: float) -> float:
        """计算重订货点
        重订货点 = 预测日平均需求 × 采购提前期 + 安全库存
        """
        product = st.session_state.products[product_id]
        demand_stats = self.calculate_demand_stats(product_id)

        reorder_point = demand_stats['mean'] * product.lead_time + safety_stock

        return reorder_point

    def calculate_target_stock(self, product_id: str, forecast: float, order_interval: int,
                               safety_stock: float) -> float:
        """计算目标库存
        目标库存 = 预测日平均需求 × (采购提前期 + 下单间隔天数) + 安全库存
        """
        product = st.session_state.products[product_id]

        target_stock = forecast * (product.lead_time + order_interval) + safety_stock

        return target_stock

    def should_reorder(self, product_id: str, reorder_point: float) -> bool:
        """判断是否需要重新订货
        只有当库存低于或等于重订货点时，才触发重新订货
        """
        product = st.session_state.products[product_id]
        return product.current_stock <= reorder_point

    def calculate_order_quantity(self, product_id: str, target_stock: float) -> int:
        """计算订货量
        订货量 = 目标库存 - 当前库存
        """
        product = st.session_state.products[product_id]
        order_qty = max(0, target_stock - product.current_stock)
        return int(order_qty)

    def evaluate_prediction(self, product_id: str, player_prediction: float) -> dict:
        """评估玩家的预测"""
        demand_stats = self.calculate_demand_stats(product_id)
        actual_demand = st.session_state.products[product_id].daily_demand

        # 计算误差
        player_error = abs(player_prediction - actual_demand)
        system_error = abs(demand_stats['mean'] - actual_demand)

        # 评分（0-100）
        max_error = actual_demand * 0.5  # 允许50%的误差
        score = max(0, 100 - (player_error / max_error * 100))

        return {
            'player_prediction': player_prediction,
            'system_prediction': demand_stats['mean'],
            'actual_demand': actual_demand,
            'player_error': player_error,
            'system_error': system_error,
            'score': score,
            'better_than_system': player_error <= system_error
        }

    def process_daily_sales(self) -> Dict:
        """处理每日销售"""
        products = st.session_state.products
        daily_sales = {}
        total_revenue = 0
        total_cost = 0
        stockouts = []

        for product_id, product in products.items():
            # 基础需求（加入随机性）
            base_demand = product.daily_demand
            actual_demand = max(1, int(base_demand * random.uniform(0.7, 1.3)))

            # 实际销售
            actual_sales = min(actual_demand, product.current_stock)
            product.current_stock -= actual_sales

            # 计算收入
            revenue = actual_sales * product.price
            cost = actual_sales * product.cost

            total_revenue += revenue
            total_cost += cost

            if actual_sales < actual_demand:
                stockouts.append({
                    'product': product.name,
                    'shortage': actual_demand - actual_sales,
                    'lost_revenue': (actual_demand - actual_sales) * product.price
                })

            daily_sales[product_id] = {
                'demand': actual_demand,
                'sales': actual_sales,
                'revenue': revenue,
                'profit': revenue - cost,
                'stock_after': product.current_stock
            }

            # 更新历史
            st.session_state.sales_history[product_id].append(actual_sales)
            if len(st.session_state.sales_history[product_id]) > 7:
                st.session_state.sales_history[product_id].pop(0)

        # 处理订单到货
        for product_id in list(st.session_state.pending_orders.keys()):
            order = st.session_state.pending_orders[product_id]
            order['days_remaining'] -= 1

            if order['days_remaining'] <= 0:
                products[product_id].current_stock += order['quantity']
                del st.session_state.pending_orders[product_id]

        # 更新状态
        profit = total_revenue - total_cost
        st.session_state.cash += profit
        st.session_state.total_revenue += total_revenue
        st.session_state.total_profit += profit
        st.session_state.day += 1

        # 计算得分
        score_today = 0
        if profit > 0:
            score_today += profit * 0.1
        if not stockouts:
            score_today += 50

        st.session_state.score += score_today

        report = {
            'day': st.session_state.day - 1,
            'sales': daily_sales,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'profit': profit,
            'stockouts': stockouts,
            'cash': st.session_state.cash,
            'score_today': score_today
        }

        st.session_state.daily_reports.append(report)
        return report


# ===========================
# 步骤渲染函数
# ===========================

def render_step_0_welcome():
    """步骤0：欢迎"""
    st.markdown("""
    <div class="info-card">
        <h3>🎯 游戏目标</h3>
        <p>你是一家小便利店的店长，需要管理3种商品的库存。</p>
        <p><strong>你将学习科学的库存管理方法，包括重订货点和安全库存计算！</strong></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 📋 你需要做的决策：
        - 🔮 **预测需求** - 估计平均销量
        - 📊 **设定服务水平** - 确定库存可靠性
        - 📦 **计算订货量** - 使用科学公式
        - ⏰ **确定订货时机** - 基于重订货点
        """)

    with col2:
        st.markdown("""
        ### 🏆 评分标准：
        - ✅ 预测准确度
        - ✅ 库存管理效率
        - ✅ 利润最大化
        - ❌ 避免缺货
        - ❌ 避免库存积压
        """)

    st.markdown("""
    <div class="formula-box">
        <h4>📐 核心公式预览</h4>
        <p>• <b>安全库存</b> = 服务水平 × 需求标准差 × √采购提前期</p>
        <p>• <b>重订货点</b> = 日均需求 × 采购提前期 + 安全库存</p>
        <p>• <b>目标库存</b> = 日均需求 × (采购提前期 + 下单间隔) + 安全库存</p>
        <p>• <b>订货量</b> = 目标库存 - 当前库存</p>
    </div>
    """, unsafe_allow_html=True)


def render_step_1_products():
    """步骤1：查看商品"""
    products = st.session_state.products

    st.markdown("""
    <div class="action-box">
        <strong>👀 仔细观察这3种商品的特性，特别注意采购提前期！</strong>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (product_id, product) in enumerate(products.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="info-card" style="text-align: center;">
                <h1>{product.icon}</h1>
                <h3>{product.name}</h3>
            </div>
            """, unsafe_allow_html=True)

            st.metric("售价", f"¥{product.price}")
            st.metric("成本", f"¥{product.cost}")
            st.metric("毛利率", f"{product.get_margin():.1f}%")
            st.metric("采购提前期", f"{product.lead_time}天", help="从下单到收货需要的天数")
            st.metric("建议订货间隔", f"{product.order_interval}天", help="多久检查一次是否需要订货")

    # 互动问题
    st.markdown("""
    <div class="quiz-box">
        <h4>💡 思考题：哪个商品的补货最紧急？</h4>
        <p>提示：采购提前期越长，需要提前准备的库存越多</p>
    </div>
    """, unsafe_allow_html=True)

    answer = st.radio(
        "选择补货挑战最大的商品：",
        ["💧 矿泉水（提前期3天）", "🍞 面包（提前期5天）", "🥛 牛奶（提前期2天）"],
        key="quiz_leadtime"
    )

    if st.button("提交答案", key="submit_leadtime"):
        if "面包" in answer:
            st.success("✅ 正确！面包的采购提前期最长（5天），需要最早计划补货")
            st.session_state.score += 10
        else:
            st.warning("❌ 再想想，面包的采购提前期是5天，最长")


def render_step_2_inventory():
    """步骤2：检查库存"""
    products = st.session_state.products
    game = InteractiveInventoryGame()

    st.markdown("""
    <div class="action-box">
        <strong>📦 评估当前库存状况，计算可销售天数</strong>
    </div>
    """, unsafe_allow_html=True)

    # 显示库存表
    inventory_data = []
    for product_id, product in products.items():
        demand_stats = game.calculate_demand_stats(product_id)
        days_of_stock = product.current_stock / demand_stats['mean']

        if days_of_stock < product.lead_time:
            status = "🔴 紧急"
            advice = "库存低于采购提前期！"
        elif days_of_stock < product.lead_time + 2:
            status = "🟡 警告"
            advice = "接近重订货点"
        else:
            status = "🟢 充足"
            advice = "暂时安全"

        inventory_data.append({
            '商品': f"{product.icon} {product.name}",
            '当前库存': f"{product.current_stock} 件",
            '日均销量': f"{demand_stats['mean']:.1f} 件",
            '可销售天数': f"{days_of_stock:.1f} 天",
            '采购提前期': f"{product.lead_time} 天",
            '状态': status,
            '建议': advice
        })

    df = pd.DataFrame(inventory_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # 重订货点概念介绍
    st.markdown("""
    <div class="info-card">
        <h4>📌 重订货点（ROP）概念</h4>
        <p>重订货点是触发补货的库存水平。当库存降到这个点时，就应该立即下单。</p>
        <p><b>重订货点 = 采购提前期内的需求 + 安全库存</b></p>
    </div>
    """, unsafe_allow_html=True)


def render_step_3_history():
    """步骤3：分析历史"""
    history = st.session_state.sales_history
    products = st.session_state.products
    game = InteractiveInventoryGame()

    st.markdown("""
    <div class="action-box">
        <strong>📊 分析历史销售数据，计算需求的平均值和标准差</strong>
    </div>
    """, unsafe_allow_html=True)

    # 创建交互式图表
    fig = go.Figure()

    for product_id, sales in history.items():
        product = products[product_id]
        demand_stats = game.calculate_demand_stats(product_id)

        fig.add_trace(go.Scatter(
            x=list(range(1, 8)),
            y=sales,
            mode='lines+markers',
            name=f"{product.icon} {product.name}",
            line=dict(width=3),
            marker=dict(size=10),
            hovertemplate='第%{x}天<br>销量: %{y}件<extra></extra>'
        ))

        # 添加平均线
        fig.add_trace(go.Scatter(
            x=list(range(1, 8)),
            y=[demand_stats['mean']] * 7,
            mode='lines',
            name=f"{product.name} 平均值",
            line=dict(dash='dash', width=1),
            showlegend=True
        ))

    fig.update_layout(
        title="过去7天销售趋势与平均值",
        xaxis_title="天数",
        yaxis_title="销量（件）",
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 统计分析
    st.markdown("### 📈 需求统计分析")

    col1, col2, col3 = st.columns(3)
    for i, (product_id, sales) in enumerate(history.items()):
        product = products[product_id]
        demand_stats = game.calculate_demand_stats(product_id)

        with [col1, col2, col3][i]:
            st.markdown(f"#### {product.icon} {product.name}")
            st.metric("平均需求(μ)", f"{demand_stats['mean']:.1f} 件/天")
            st.metric("标准差(σ)", f"{demand_stats['std']:.2f} 件")
            st.metric("变异系数(CV)", f"{demand_stats['cv'] * 100:.1f}%")

            # 需求稳定性判断
            if demand_stats['cv'] < 0.1:
                st.success("需求很稳定")
            elif demand_stats['cv'] < 0.2:
                st.info("需求较稳定")
            elif demand_stats['cv'] < 0.4:
                st.warning("需求波动较大")
            else:
                st.error("需求极不稳定！")

    st.markdown("""
    <div class="info-card">
        <h4>📊 标准差的意义</h4>
        <p>标准差反映需求的波动程度。标准差越大，需求越不稳定，需要的安全库存就越多。</p>
        <p>变异系数(CV) = 标准差 / 平均值，用于比较不同商品的相对波动性。</p>
    </div>
    """, unsafe_allow_html=True)


def render_step_4_predict():
    """步骤4：预测需求与设定服务水平"""
    game = InteractiveInventoryGame()
    products = st.session_state.products

    st.markdown("""
    <div class="action-box">
        <strong>🔮 预测日均需求并设定服务水平</strong>
        <p>服务水平决定了你希望避免缺货的概率</p>
    </div>
    """, unsafe_allow_html=True)

    for product_id, product in products.items():
        with st.expander(f"{product.icon} {product.name} - 需求预测与服务水平", expanded=True):
            demand_stats = game.calculate_demand_stats(product_id)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📊 历史数据分析")
                st.info(f"7天平均: {demand_stats['mean']:.1f}件/天")
                st.info(f"标准差: {demand_stats['std']:.2f}件")
                st.info(f"最近3天平均: {np.mean(st.session_state.sales_history[product_id][-3:]):.1f}件/天")

                # 预测输入 - 不设置默认值
                player_prediction = st.number_input(
                    "预测日均需求（件/天）：",
                    min_value=0.0,
                    max_value=100.0,
                    value=None,  # 留空让玩家输入
                    step=0.5,
                    key=f"predict_{product_id}",
                    placeholder="请输入你的预测"
                )
                if player_prediction is not None:
                    st.session_state.player_predictions[product_id] = player_prediction
                else:
                    st.warning("请输入需求预测")

            with col2:
                st.markdown("### 🎯 服务水平设定")
                st.markdown("""
                <div class="info-card">
                    <p><b>服务水平含义：</b></p>
                    <p>• 90% = 10天中允许1天缺货</p>
                    <p>• 95% = 20天中允许1天缺货</p>
                    <p>• 99% = 100天中允许1天缺货</p>
                </div>
                """, unsafe_allow_html=True)

                # 使用数字输入代替slider避免格式问题 - 不设置默认值
                service_level_percent = st.number_input(
                    "选择服务水平（%）：",
                    min_value=80,
                    max_value=99,
                    value=None,  # 留空让玩家输入
                    step=1,
                    key=f"service_{product_id}",
                    placeholder="80-99之间"
                )

                if service_level_percent is not None:
                    service_level = service_level_percent / 100
                    st.session_state.player_service_levels[product_id] = service_level

                    # 显示对应的z值
                    z_score = scipy_stats.norm.ppf(service_level)
                    st.info(f"服务水平: {service_level_percent}%")
                    st.info(f"对应Z值: {z_score:.2f}")
                else:
                    st.warning("请输入服务水平")

    if len(st.session_state.player_predictions) == 3 and len(st.session_state.player_service_levels) == 3:
        all_valid = True
        for product_id in st.session_state.products:
            if st.session_state.player_predictions.get(product_id) is None:
                all_valid = False
                break
            if st.session_state.player_service_levels.get(product_id) is None:
                all_valid = False
                break

        if all_valid:
            st.success("✅ 所有商品的需求预测和服务水平设定完成！")
        else:
            st.warning("请完成所有商品的预测和服务水平设定")


def render_step_5_calculate():
    """步骤5：计算安全库存和重订货点"""
    game = InteractiveInventoryGame()
    products = st.session_state.products

    st.markdown("""
    <div class="action-box">
        <strong>📝 根据公式计算安全库存、重订货点和订货量</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="formula-box">
        <h4>📐 计算公式</h4>
        <p>1. <b>安全库存(SS)</b> = Z × σ × √L</p>
        <p>   其中：Z=服务水平对应的标准正态分布值, σ=需求标准差, L=采购提前期</p>
        <p>2. <b>重订货点(ROP)</b> = μ × L + SS</p>
        <p>   其中：μ=日均需求</p>
        <p>3. <b>目标库存</b> = μ × (L + T) + SS</p>
        <p>   其中：T=下单间隔天数</p>
        <p>4. <b>订货量</b> = 目标库存 - 当前库存（当库存≤ROP时才订货）</p>
    </div>
    """, unsafe_allow_html=True)

    # 清空需要订货的商品列表
    st.session_state.products_need_order = {}

    for product_id, product in products.items():
        with st.expander(f"{product.icon} {product.name} - 库存计算", expanded=True):
            demand_stats = game.calculate_demand_stats(product_id)
            forecast = st.session_state.player_predictions.get(product_id, demand_stats['mean'])
            service_level = st.session_state.player_service_levels.get(product_id, 0.95)

            # 计算参数
            z_score = scipy_stats.norm.ppf(service_level)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 📊 基础参数")
                st.metric("当前库存", f"{product.current_stock}件")
                st.metric("预测日均需求(μ)", f"{forecast:.1f}件")
                st.metric("需求标准差(σ)", f"{demand_stats['std']:.2f}件")
                st.metric("采购提前期(L)", f"{product.lead_time}天")

            with col2:
                st.markdown("### 🛡️ 安全库存计算")
                safety_stock = z_score * demand_stats['std'] * math.sqrt(product.lead_time)
                st.info(f"SS = {z_score:.2f} × {demand_stats['std']:.2f} × √{product.lead_time}")
                st.metric("安全库存", f"{safety_stock:.1f}件")

                st.markdown("### 🎯 重订货点计算")
                reorder_point = forecast * product.lead_time + safety_stock
                st.info(f"ROP = {forecast:.1f} × {product.lead_time} + {safety_stock:.1f}")
                st.metric("重订货点", f"{reorder_point:.1f}件")

            with col3:
                st.markdown("### 📦 订货决策")

                # 下单间隔选择
                order_interval = st.number_input(
                    "下单间隔天数(T)：",
                    min_value=1,
                    max_value=10,
                    value=product.order_interval,
                    key=f"interval_{product_id}"
                )
                st.session_state.player_order_intervals[product_id] = order_interval

                # 计算目标库存
                target_stock = forecast * (product.lead_time + order_interval) + safety_stock
                st.info(f"目标库存 = {forecast:.1f} × ({product.lead_time} + {order_interval}) + {safety_stock:.1f}")
                st.metric("目标库存", f"{target_stock:.1f}件")

                # 判断是否需要订货
                should_order = product.current_stock <= reorder_point

                if should_order:
                    st.error(f"⚠️ 当前库存({product.current_stock}) ≤ ROP({reorder_point:.1f})")
                    st.markdown("**需要立即订货！**")

                    # 标记这个商品需要订货
                    st.session_state.products_need_order[product_id] = True

                    # 计算订货量
                    order_qty = max(0, target_stock - product.current_stock)
                    st.metric("建议订货量", f"{order_qty:.0f}件")

                    # 玩家输入 - 不设置默认值
                    player_order = st.number_input(
                        "你的订货量（件）：",
                        min_value=0,
                        max_value=500,
                        value=None,  # 留空让玩家输入
                        step=10,
                        key=f"order_{product_id}",
                        placeholder="请输入订货量"
                    )

                    if player_order is not None:
                        st.session_state.player_orders[product_id] = player_order
                        order_cost = player_order * product.cost
                        st.metric("订货成本", f"¥{order_cost:.2f}")
                    else:
                        st.warning("请输入订货量")
                else:
                    st.success(f"✅ 当前库存({product.current_stock}) > ROP({reorder_point:.1f})")
                    st.markdown("**暂不需要订货**")
                    st.session_state.player_orders[product_id] = 0
                    st.session_state.products_need_order[product_id] = False


def render_step_6_order():
    """步骤6：确认订单"""
    products = st.session_state.products
    player_orders = st.session_state.player_orders

    st.markdown("""
    <div class="action-box">
        <strong>📦 确认并提交订单（只对需要补货的商品下单）</strong>
    </div>
    """, unsafe_allow_html=True)

    # 订单详情
    st.markdown("### 📋 订单确认")

    order_details = []
    total_cost = 0
    no_order_items = []

    for product_id, qty in player_orders.items():
        product = products[product_id]
        if qty > 0:
            cost = qty * product.cost
            total_cost += cost
            order_details.append({
                '商品': f"{product.icon} {product.name}",
                '订货量': f"{qty} 件",
                '单价': f"¥{product.cost}",
                '小计': f"¥{cost:.2f}",
                '到货时间': f"{product.lead_time} 天后"
            })
        else:
            no_order_items.append(f"{product.icon} {product.name}")

    if order_details:
        st.markdown("#### 📦 需要订货的商品")
        df = pd.DataFrame(order_details)
        st.dataframe(df, hide_index=True, use_container_width=True)

        # 资金状况
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("当前资金", f"¥{st.session_state.cash:.2f}")
        with col2:
            st.metric("订单总额", f"¥{total_cost:.2f}")
        with col3:
            remaining = st.session_state.cash - total_cost
            st.metric("剩余资金", f"¥{remaining:.2f}")

        if remaining >= 0:
            if st.button("✅ 确认提交订单", type="primary", use_container_width=True):
                for product_id, qty in player_orders.items():
                    if qty > 0:
                        product = products[product_id]
                        st.session_state.pending_orders[product_id] = {
                            'quantity': qty,
                            'days_remaining': product.lead_time,
                            'cost': qty * product.cost
                        }
                st.session_state.cash -= total_cost
                st.session_state.order_submitted = True  # 标记订单已提交
                st.success(f"✅ 订单提交成功！共花费¥{total_cost:.2f}")
                st.balloons()
        else:
            st.error("❌ 资金不足！请调整订货量")
    else:
        # 如果没有需要订货的商品，直接标记为已完成
        st.session_state.order_submitted = True

    if no_order_items:
        st.markdown("#### ✅ 库存充足，暂不需要订货的商品")
        for item in no_order_items:
            st.info(f"{item} - 库存高于重订货点")

    # 显示当前状态
    if st.session_state.order_submitted:
        st.markdown("""
        <div class="success-message">
            <strong>✅ 订单处理完成，可以进入下一步了！</strong>
        </div>
        """, unsafe_allow_html=True)


def render_step_7_run():
    """步骤7：运行模拟"""
    game = InteractiveInventoryGame()

    st.markdown("""
    <div class="action-box">
        <strong>🏃 运行一天，看看你的库存管理效果！</strong>
    </div>
    """, unsafe_allow_html=True)

    # 显示决策摘要
    st.markdown("### 📋 决策摘要")

    summary_data = []
    for product_id in st.session_state.products:
        product = st.session_state.products[product_id]
        demand_stats = game.calculate_demand_stats(product_id)
        forecast = st.session_state.player_predictions.get(product_id, demand_stats['mean'])
        service_level = st.session_state.player_service_levels.get(product_id, 0.95)
        order_qty = st.session_state.player_orders.get(product_id, 0)

        summary_data.append({
            '商品': f"{product.icon} {product.name}",
            '预测需求': f"{forecast:.1f}件/天",
            '服务水平': f"{service_level:.0%}",
            '订货量': f"{order_qty}件" if order_qty > 0 else "不订货"
        })

    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, hide_index=True, use_container_width=True)

    # 运行按钮
    if st.button("▶️ 开始营业", type="primary", use_container_width=True):
        report = game.process_daily_sales()
        st.session_state.simulation_run = True  # 标记模拟已运行

        # 显示结果
        st.markdown("### 📊 经营结果")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总收入", f"¥{report['total_revenue']:.2f}")
        with col2:
            st.metric("总成本", f"¥{report['total_cost']:.2f}")
        with col3:
            st.metric("利润", f"¥{report['profit']:.2f}")
        with col4:
            st.metric("今日得分", f"+{report['score_today']:.0f}分")

        # 缺货情况
        if report['stockouts']:
            st.markdown("### ⚠️ 缺货警告")
            for stockout in report['stockouts']:
                st.error(
                    f"{stockout['product']} 缺货 {stockout['shortage']} 件，损失收入 ¥{stockout['lost_revenue']:.2f}")
        else:
            st.success("✅ 所有商品供应充足，没有缺货！+50分奖励")

        # 库存状态更新（添加预测需求列）
        st.markdown("### 📦 库存状态更新")
        status_data = []
        for product_id, sales_data in report['sales'].items():
            product = st.session_state.products[product_id]
            demand_stats = game.calculate_demand_stats(product_id)
            forecast = st.session_state.player_predictions.get(product_id, demand_stats['mean'])

            status_data.append({
                '商品': f"{product.icon} {product.name}",
                '预测需求': f"{forecast:.1f}件",
                '实际需求': f"{sales_data['demand']}件",
                '实际销售': f"{sales_data['sales']}件",
                '剩余库存': f"{sales_data['stock_after']}件"
            })

        df_status = pd.DataFrame(status_data)
        st.dataframe(df_status, hide_index=True, use_container_width=True)

    # 显示当前状态
    if st.session_state.simulation_run:
        st.markdown("""
        <div class="success-message">
            <strong>✅ 营业日已完成，可以查看分析报告了！</strong>
        </div>
        """, unsafe_allow_html=True)


def render_step_8_report():
    """步骤8：分析报告"""
    if st.session_state.daily_reports:
        report = st.session_state.daily_reports[-1]
        products = st.session_state.products
        game = InteractiveInventoryGame()

        st.markdown("""
        <div class="action-box">
            <strong>📈 详细分析你的库存管理表现</strong>
        </div>
        """, unsafe_allow_html=True)

        # 总体表现
        st.markdown("### 🏆 总体表现")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("累计得分", f"{st.session_state.score:.0f}分")
        with col2:
            st.metric("累计利润", f"¥{st.session_state.total_profit:.2f}")
        with col3:
            margin = (
                    st.session_state.total_profit / st.session_state.total_revenue * 100) if st.session_state.total_revenue > 0 else 0
            st.metric("利润率", f"{margin:.1f}%")
        with col4:
            st.metric("剩余资金", f"¥{st.session_state.cash:.2f}")

        # 决策评价
        st.markdown("### 💡 决策分析")

        for product_id in products:
            product = products[product_id]
            demand_stats = game.calculate_demand_stats(product_id)

            with st.expander(f"{product.icon} {product.name} 决策分析"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 预测准确度")
                    if product_id in st.session_state.player_predictions:
                        pred = st.session_state.player_predictions[product_id]
                        actual = report['sales'][product_id]['demand']
                        error = abs(pred - actual) / actual * 100

                        st.metric("你的预测", f"{pred:.1f}件")
                        st.metric("实际需求", f"{actual}件")

                        if error < 20:
                            st.success(f"预测准确！误差仅{error:.1f}%")
                        else:
                            st.warning(f"预测偏差{error:.1f}%")

                with col2:
                    st.markdown("#### 库存管理")
                    if product_id in st.session_state.player_orders:
                        order = st.session_state.player_orders[product_id]
                        service_level = st.session_state.player_service_levels.get(product_id, 0.95)

                        st.metric("服务水平设定", f"{service_level:.0%}")
                        st.metric("订货量", f"{order}件")

                        # 评估是否合理
                        if order > 0:
                            forecast = st.session_state.player_predictions.get(product_id, demand_stats['mean'])
                            z_score = scipy_stats.norm.ppf(service_level)
                            safety_stock = z_score * demand_stats['std'] * math.sqrt(product.lead_time)
                            reorder_point = forecast * product.lead_time + safety_stock

                            if product.current_stock <= reorder_point:
                                st.success("✅ 正确识别需要补货")
                            else:
                                st.warning("⚠️ 可能过早补货")

        # 经验总结
        st.markdown("""
        <div class="info-card">
            <h4>📚 关键学习点</h4>
            <ul>
                <li>重订货点帮助确定<b>何时</b>订货</li>
                <li>安全库存用于应对需求的不确定性</li>
                <li>服务水平越高，需要的安全库存越多</li>
                <li>只有库存降到重订货点以下才需要补货</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def render_step_9_complete():
    """步骤9：完成"""
    st.balloons()

    st.markdown("""
    <div class="success-message" style="text-align: center; padding: 30px;">
        <h1>🎉 恭喜完成库存管理教程！</h1>
    </div>
    """, unsafe_allow_html=True)

    # 最终成绩
    st.markdown("### 🏆 最终成绩单")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("最终得分", f"{st.session_state.score:.0f}分")
    with col2:
        st.metric("总利润", f"¥{st.session_state.total_profit:.2f}")
    with col3:
        st.metric("总收入", f"¥{st.session_state.total_revenue:.2f}")
    with col4:
        st.metric("剩余资金", f"¥{st.session_state.cash:.2f}")

    # 评级
    score = st.session_state.score
    if score >= 150:
        grade = "S"
        comment = "库存管理大师！完美掌握了科学的库存管理方法！"
        st.success(f"🏆 评级：{grade} - {comment}")
    elif score >= 100:
        grade = "A"
        comment = "优秀！你已经理解了重订货点和安全库存的概念"
        st.success(f"🥇 评级：{grade} - {comment}")
    elif score >= 50:
        grade = "B"
        comment = "不错！继续练习会更好地掌握"
        st.info(f"🥈 评级：{grade} - {comment}")
    else:
        grade = "C"
        comment = "还需要更多练习来理解库存管理"
        st.warning(f"🥉 评级：{grade} - {comment}")

    # 学习总结
    st.markdown("### 📚 你掌握的知识")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **库存管理核心公式：**
        - ✅ 安全库存 = Z × σ × √L
        - ✅ 重订货点 = μ × L + SS
        - ✅ 目标库存 = μ × (L + T) + SS
        - ✅ 订货量 = 目标库存 - 当前库存
        """)

    with col2:
        st.markdown("""
        **关键决策技能：**
        - ✅ 设定合适的服务水平
        - ✅ 计算科学的安全库存
        - ✅ 确定正确的订货时机
        - ✅ 平衡库存成本和服务水平
        """)

    # 高级概念介绍
    st.markdown("""
    <div class="info-card">
        <h4>🎓 进阶学习方向</h4>
        <ul>
            <li><b>EOQ模型：</b>经济订货批量，优化订货成本和持有成本</li>
            <li><b>ABC分析：</b>根据价值对库存分类管理</li>
            <li><b>JIT管理：</b>准时制库存管理，减少库存积压</li>
            <li><b>VMI模式：</b>供应商管理库存，提高供应链效率</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # 再玩一次
    if st.button("🔄 再玩一次", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ===========================
# 主程序
# ===========================

def main():
    """主函数"""
    # 初始化游戏
    game = InteractiveInventoryGame()

    # 页面标题
    st.markdown('<h1 class="main-header">📦 库存管理互动游戏</h1>', unsafe_allow_html=True)

    # 步骤信息
    steps = [
        ("欢迎", "了解游戏目标和公式", "🎯"),
        ("认识商品", "了解商品特性", "📦"),
        ("检查库存", "评估库存状况", "📊"),
        ("分析历史", "计算需求统计", "📈"),
        ("预测与服务水平", "设定关键参数", "🔮"),
        ("计算库存参数", "应用科学公式", "🧮"),
        ("确认订单", "提交补货申请", "📝"),
        ("运行模拟", "查看经营结果", "🏃"),
        ("分析报告", "总结经验教训", "📋"),
        ("完成", "查看最终成绩", "🎉")
    ]

    current_step = st.session_state.current_step

    # 进度显示
    progress = (current_step + 1) / len(steps)
    st.progress(progress)

    # 步骤指示器
    cols = st.columns(len(steps))
    for i, (title, desc, icon) in enumerate(steps):
        with cols[i]:
            if i < current_step:
                st.markdown(f"<div style='text-align:center;color:#28a745;'>{icon}<br>✅</div>",
                            unsafe_allow_html=True)
            elif i == current_step:
                st.markdown(f"<div style='text-align:center;color:#667eea;font-weight:bold;'>{icon}<br>▶️</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;color:#dee2e6;'>{icon}<br>⭕</div>",
                            unsafe_allow_html=True)

    # 当前步骤标题
    st.markdown(f"""
    <div class="step-header">
        <h2 style="color: white; margin: 0;">步骤 {current_step + 1}: {steps[current_step][0]}</h2>
        <p style="color: #f0f0f0; margin-top: 10px;">{steps[current_step][1]}</p>
    </div>
    """, unsafe_allow_html=True)

    # 渲染当前步骤内容
    step_functions = [
        render_step_0_welcome,
        render_step_1_products,
        render_step_2_inventory,
        render_step_3_history,
        render_step_4_predict,
        render_step_5_calculate,
        render_step_6_order,
        render_step_7_run,
        render_step_8_report,
        render_step_9_complete
    ]

    if current_step < len(step_functions):
        step_functions[current_step]()

    # 导航按钮
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_step > 0:
            if st.button("⬅️ 上一步", use_container_width=True):
                st.session_state.current_step -= 1
                # 重置下一步的完成标记
                if st.session_state.current_step == 5:
                    st.session_state.order_submitted = False
                elif st.session_state.current_step == 6:
                    st.session_state.simulation_run = False
                st.rerun()

    with col3:
        if current_step < len(steps) - 1:
            # 检查当前步骤是否可以继续
            can_proceed = True
            proceed_hint = ""

            if current_step == 4:  # 预测步骤
                can_proceed = True
                for product_id in ['WATER', 'BREAD', 'MILK']:
                    if product_id not in st.session_state.player_predictions or st.session_state.player_predictions[
                        product_id] is None:
                        can_proceed = False
                        break
                    if product_id not in st.session_state.player_service_levels or \
                            st.session_state.player_service_levels[product_id] is None:
                        can_proceed = False
                        break
                proceed_hint = "请完成所有商品的预测和服务水平设定" if not can_proceed else ""

            elif current_step == 5:  # 计算步骤 - 优化订货量检查逻辑
                can_proceed = True
                missing_orders = []

                # 检查每个需要订货的商品是否已输入订货量
                for product_id in ['WATER', 'BREAD', 'MILK']:
                    # 只检查标记为需要订货的商品
                    if st.session_state.products_need_order.get(product_id, False):
                        # 如果需要订货但没有输入订货量
                        if product_id not in st.session_state.player_orders or \
                                st.session_state.player_orders.get(product_id) is None:
                            can_proceed = False
                            product = st.session_state.products[product_id]
                            missing_orders.append(f"{product.icon} {product.name}")

                if missing_orders:
                    proceed_hint = f"请完成以下商品的订货量输入：{', '.join(missing_orders)}"
                else:
                    proceed_hint = ""

            elif current_step == 6:  # 确认订单步骤
                can_proceed = st.session_state.order_submitted
                proceed_hint = "请先确认提交订单" if not can_proceed else ""

            elif current_step == 7:  # 运行模拟步骤
                can_proceed = st.session_state.simulation_run
                proceed_hint = "请先点击'开始营业'运行模拟" if not can_proceed else ""

            if can_proceed:
                if st.button("➡️ 下一步", type="primary", use_container_width=True):
                    st.session_state.current_step += 1
                    st.rerun()
            else:
                st.button("➡️ 下一步", disabled=True, use_container_width=True)
                if proceed_hint:
                    st.warning(proceed_hint)

    # 侧边栏
    with st.sidebar:
        st.title("📚 学习助手")

        st.markdown("### 📍 当前进度")
        st.progress(progress)
        st.write(f"步骤 {current_step + 1} / {len(steps)}")

        st.markdown("### 🏆 游戏状态")
        st.metric("当前得分", f"{st.session_state.score:.0f}分")
        st.metric("当前资金", f"¥{st.session_state.cash:.2f}")
        st.metric("累计利润", f"¥{st.session_state.total_profit:.2f}")

        st.markdown("### 📖 知识点")

        knowledge_points = {
            0: "理解库存管理核心公式",
            1: "认识采购提前期的重要性",
            2: "学习库存状态评估",
            3: "掌握需求统计分析",
            4: "理解服务水平概念",
            5: "应用库存管理公式",
            6: "执行订货决策",
            7: "验证决策效果",
            8: "分析管理绩效",
            9: "总结提升"
        }

        if current_step in knowledge_points:
            st.info(f"本步骤重点：\n{knowledge_points[current_step]}")

        st.markdown("### ⚡ 快捷操作")
        if st.button("🔄 重新开始", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        with st.expander("📐 公式速查"):
            st.markdown("""
            **安全库存(SS):**
            ```
            SS = Z × σ × √L
            ```

            **重订货点(ROP):**
            ```
            ROP = μ × L + SS
            ```

            **目标库存:**
            ```
            目标 = μ × (L + T) + SS
            ```

            **订货量:**
            ```
            Q = 目标库存 - 当前库存
            (仅当库存 ≤ ROP时)
            ```

            其中：
            - Z: 服务水平对应的z值
            - σ: 需求标准差
            - L: 采购提前期
            - μ: 日均需求
            - T: 下单间隔
            """)


if __name__ == "__main__":
    main()
